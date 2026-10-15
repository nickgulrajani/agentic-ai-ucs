"""Runtime configuration. Prefer AI Studio free tier over Vertex for demos."""

from __future__ import annotations

import os
import socket
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "agentthree-ai-dev-511709")
GOOGLE_CLOUD_PROJECT_NUMBER = os.getenv("GOOGLE_CLOUD_PROJECT_NUMBER", "31543876598")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() in {
    "1",
    "TRUE",
    "YES",
}

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}

MCP_PORT = int(os.getenv("MCP_PORT", "8080"))
API_PORT = int(os.getenv("API_PORT", "8000"))
INTAKE_A2A_PORT = int(os.getenv("INTAKE_A2A_PORT", "9001"))
PA_A2A_PORT = int(os.getenv("PA_A2A_PORT", "9002"))
CDS_A2A_PORT = int(os.getenv("CDS_A2A_PORT", "9003"))

MCP_URL = os.getenv("MCP_URL", f"http://127.0.0.1:{MCP_PORT}/mcp")
DATA_DIR = ROOT / "data"


def port_is_free(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def pick_port(preferred: int, *, host: str = "0.0.0.0", search: int = 40) -> int:
    """Return preferred if free; otherwise the next free port in [preferred, preferred+search)."""
    if port_is_free(preferred, host):
        return preferred
    for candidate in range(preferred + 1, preferred + search):
        if port_is_free(candidate, host):
            return candidate
    # Last resort: OS-assigned ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def ensure_genai_env() -> None:
    """Point ADK/genai at AI Studio free tier unless Vertex is explicitly enabled."""
    if GOOGLE_GENAI_USE_VERTEXAI:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", GOOGLE_CLOUD_PROJECT)
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", GOOGLE_CLOUD_LOCATION)
    else:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
        if GOOGLE_API_KEY:
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

