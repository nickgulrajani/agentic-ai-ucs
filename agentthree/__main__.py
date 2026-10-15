"""Start MCP + API (+ optional A2A agent cards) for the local demo.

Usage (prefer the project venv):
  source .venv/bin/activate && python -m agentthree
  # or:
  .venv/bin/python -m agentthree
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _maybe_reexec_venv() -> None:
    """If .venv exists and we are not inside it, re-exec with that interpreter."""
    venv_python = ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return
    try:
        current = Path(sys.executable).resolve()
        target = venv_python.resolve()
    except OSError:
        return
    if current == target:
        return
    if os.environ.get("AGENTTHREE_VENV_REEXEC") == "1":
        return
    env = os.environ.copy()
    env["AGENTTHREE_VENV_REEXEC"] = "1"
    env["VIRTUAL_ENV"] = str(ROOT / ".venv")
    os.execve(str(target), [str(target), "-m", "agentthree", *sys.argv[1:]], env)


_maybe_reexec_venv()

import httpx  # noqa: E402
import uvicorn  # noqa: E402

import agentthree.config as cfg  # noqa: E402
from agentthree.config import ensure_genai_env, pick_port  # noqa: E402

logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger("agentthree")


def _wait_mcp(proc: subprocess.Popen, mcp_url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"MCP process exited early with code {proc.returncode}. "
                "Use the project venv: .venv/bin/python -m agentthree"
            )
        try:
            httpx.get(mcp_url, timeout=1.0)
            return
        except Exception:  # noqa: BLE001
            time.sleep(0.3)
    raise RuntimeError(f"MCP server did not start at {mcp_url}")


def main() -> None:
    ensure_genai_env()
    logger.info("Using Python: %s", sys.executable)

    preferred_mcp = int(os.getenv("MCP_PORT", str(cfg.MCP_PORT)))
    preferred_api = int(os.getenv("API_PORT", str(cfg.API_PORT)))
    mcp_port = pick_port(preferred_mcp)
    api_port = pick_port(preferred_api)
    if api_port == mcp_port:
        api_port = pick_port(api_port + 1)

    if mcp_port != preferred_mcp:
        logger.warning("MCP port %s busy — using %s", preferred_mcp, mcp_port)
    if api_port != preferred_api:
        logger.warning("API port %s busy — using %s", preferred_api, api_port)

    mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"
    os.environ["MCP_PORT"] = str(mcp_port)
    os.environ["API_PORT"] = str(api_port)
    os.environ["MCP_URL"] = mcp_url
    os.environ["PORT"] = str(mcp_port)  # FastMCP / Cloud Run style
    # Keep already-imported config in sync for health + MCP client
    cfg.MCP_PORT = mcp_port
    cfg.API_PORT = api_port
    cfg.MCP_URL = mcp_url

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    mcp_proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_servers.clinical.server"],
        cwd=str(ROOT),
        env=env,
    )
    logger.info("Starting MCP on port %s (pid %s)", mcp_port, mcp_proc.pid)

    try:
        _wait_mcp(mcp_proc, mcp_url)
        logger.info("MCP ready at %s", mcp_url)

        start_a2a = os.getenv("START_A2A", "false").lower() in {"1", "true", "yes"}
        if start_a2a:
            try:
                from agentthree.a2a_servers import start_background

                start_background()
                logger.info("A2A agent card servers starting (ports 9001–9003)")
            except Exception as exc:  # noqa: BLE001
                logger.warning("A2A servers not started: %s", exc)

        logger.info("API + UI on http://127.0.0.1:%s", api_port)
        uvicorn.run(
            "agentthree.api.server:app",
            host="0.0.0.0",
            port=api_port,
            log_level="info",
        )
    finally:
        mcp_proc.terminate()
        try:
            mcp_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mcp_proc.kill()


if __name__ == "__main__":
    main()
