"""MCP tools/call client over streamable HTTP."""

from __future__ import annotations

import json
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from agentthree.config import MCP_URL


@asynccontextmanager
async def mcp_session(url: str = MCP_URL) -> AsyncIterator[ClientSession]:
    async with streamable_http_client(url) as streams:
        read, write = streams[0], streams[1]
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call_tool(
    name: str,
    arguments: dict[str, Any],
    url: str = MCP_URL,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """Call an MCP tool. Returns (request_envelope, response_envelope, duration_ms)."""
    req = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1_000_000,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    t0 = time.perf_counter()
    try:
        async with mcp_session(url) as session:
            result = await session.call_tool(name, arguments)
        dur = int((time.perf_counter() - t0) * 1000)

        structured = getattr(result, "structured_content", None) or getattr(
            result, "structuredContent", None
        )
        texts: list[str] = []
        for block in getattr(result, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                texts.append(text)
        if structured is None and texts:
            try:
                structured = json.loads(texts[0])
            except Exception:  # noqa: BLE001
                structured = {"text": texts[0]}
        if structured is None:
            structured = {}

        is_error = bool(getattr(result, "is_error", None) or getattr(result, "isError", False))
        if is_error:
            res = {
                "jsonrpc": "2.0",
                "id": req["id"],
                "error": {"code": -32603, "message": str(structured or texts or "tool error")},
            }
        else:
            res = {
                "jsonrpc": "2.0",
                "id": req["id"],
                "result": {
                    "content": [{"type": "text", "text": "(structured result below)"}],
                    "structuredContent": structured,
                    "isError": False,
                },
            }
        return req, res, dur
    except Exception as exc:  # noqa: BLE001
        dur = int((time.perf_counter() - t0) * 1000)
        res = {
            "jsonrpc": "2.0",
            "id": req["id"],
            "error": {"code": -32603, "message": str(exc)},
        }
        return req, res, dur


def structured_from(response: dict[str, Any]) -> Any:
    if "error" in response:
        raise RuntimeError(response["error"].get("message", str(response["error"])))
    return (response.get("result") or {}).get("structuredContent")
