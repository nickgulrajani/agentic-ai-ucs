"""FastAPI gateway: run cases, SSE progress, HITL decision, static UI."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from agentthree import __version__
from agentthree.config import (
    API_PORT,
    CDS_A2A_PORT,
    DEMO_MODE,
    GEMINI_MODEL,
    GOOGLE_API_KEY,
    GOOGLE_CLOUD_PROJECT,
    INTAKE_A2A_PORT,
    MCP_PORT,
    PA_A2A_PORT,
    ROOT,
    ensure_genai_env,
)
from agentthree.pipeline import run_case, seal_decision

logger = logging.getLogger(__name__)
ensure_genai_env()

app = FastAPI(title="AgentThree Prior Auth API", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CASES: dict[str, dict[str, Any]] = {}
UI_HTML = ROOT / "ui" / "agentthree-prior-auth.html"
if not UI_HTML.exists():
    UI_HTML = ROOT / "agentthree-prior-auth.html"


class CaseRequest(BaseModel):
    patient: str = "Jordan Rivera (fictional)"
    dob: str = "1968-03-14"
    member: str = "AHP-0042-7781"
    payer: str = "Acme Health Plan (fictional)"
    cpt: str = "72148"
    icd: str = "M54.16"
    note: str = Field(..., min_length=10)
    fault: str = "none"


class DecisionRequest(BaseModel):
    action: str  # approve | info | escalate
    reviewer: str = "Dr. Sam Patel, MD (fictional)"
    note: str = ""


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "version": __version__,
        "project": GOOGLE_CLOUD_PROJECT,
        "model": GEMINI_MODEL,
        "demoMode": DEMO_MODE or not GOOGLE_API_KEY,
        "hasApiKey": bool(GOOGLE_API_KEY),
        "ports": {
            "api": API_PORT,
            "mcp": MCP_PORT,
            "intakeA2A": INTAKE_A2A_PORT,
            "paA2A": PA_A2A_PORT,
            "cdsA2A": CDS_A2A_PORT,
        },
    }


@app.get("/api/agent-cards")
async def agent_cards() -> dict[str, Any]:
    """Pointers to A2A Agent Card endpoints (when a2a servers are running)."""
    return {
        "intake": f"http://127.0.0.1:{INTAKE_A2A_PORT}/.well-known/agent-card.json",
        "priorAuth": f"http://127.0.0.1:{PA_A2A_PORT}/.well-known/agent-card.json",
        "cds": f"http://127.0.0.1:{CDS_A2A_PORT}/.well-known/agent-card.json",
        "mcp": f"http://127.0.0.1:{MCP_PORT}/mcp",
    }


QUEUES: dict[str, asyncio.Queue] = {}


@app.post("/api/cases")
async def create_case(body: CaseRequest) -> dict[str, Any]:
    case_id = str(uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    QUEUES[case_id] = queue

    async def emit(payload: dict[str, Any]) -> None:
        await queue.put(payload)

    async def runner() -> None:
        try:
            result = await run_case(
                patient_name=body.patient,
                dob=body.dob,
                member=body.member,
                payer=body.payer,
                cpt=body.cpt,
                icd=body.icd,
                note=body.note,
                fault=body.fault,
                emit=emit,
            )
            CASES[case_id] = result
            await queue.put({"type": "done", "caseId": case_id})
        except Exception as exc:  # noqa: BLE001
            logger.exception("case failed")
            await queue.put({"type": "error", "message": str(exc)})
        finally:
            await queue.put(None)

    asyncio.create_task(runner())
    return {"caseId": case_id, "streamUrl": f"/api/cases/{case_id}/events"}


@app.get("/api/cases/{case_id}/events")
async def case_events(case_id: str) -> EventSourceResponse:
    queue = QUEUES.get(case_id)
    if queue is None:
        raise HTTPException(404, "Unknown case")

    async def gen():
        while True:
            item = await queue.get()
            if item is None:
                break
            yield {"event": "message", "data": json.dumps(item, default=str)}

    return EventSourceResponse(gen())


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str) -> dict[str, Any]:
    case = CASES.get(case_id)
    if not case:
        raise HTTPException(404, "Case not ready yet — wait for the stream to finish")
    return {k: v for k, v in case.items() if not k.startswith("_")}


@app.post("/api/cases/{case_id}/decision")
async def decide(case_id: str, body: DecisionRequest) -> dict[str, Any]:
    case = CASES.get(case_id)
    if not case or "contextId" not in case:
        raise HTTPException(404, "Case not found or still running")
    labels = {
        "approve": ("Approved", "var(--lime)"),
        "info": ("Request more information", "var(--amber)"),
        "escalate": ("Escalated to medical director", "var(--red)"),
    }
    if body.action not in labels:
        raise HTTPException(400, "action must be approve|info|escalate")
    label, color = labels[body.action]
    halted = (case.get("pol") or {}).get("outcome") in {"system", "nopolicy"}
    if body.action == "approve" and halted:
        raise HTTPException(400, "Approval disabled until coverage criteria can be evaluated")
    decision = {
        "action": body.action,
        "label": label,
        "color": color,
        "reviewer": body.reviewer,
        "note": body.note,
    }
    sealed = await seal_decision(case, decision)
    CASES[case_id] = sealed
    return {k: v for k, v in sealed.items() if not k.startswith("_")}


@app.get("/ui/live-bridge.js")
async def live_bridge() -> FileResponse:
    path = ROOT / "ui" / "live-bridge.js"
    if not path.exists():
        raise HTTPException(404, "live-bridge.js missing")
    return FileResponse(path, media_type="application/javascript")


def _classic_html() -> str:
    html = UI_HTML.read_text(encoding="utf-8")
    boot = "<script>window.AGENTTHREE_LIVE=true;window.AGENTTHREE_API='';</script>\n"
    return boot + html


@app.get("/")
async def index():
    react_index = ROOT / "web" / "dist" / "index.html"
    if react_index.exists():
        return FileResponse(react_index)
    if not UI_HTML.exists():
        return HTMLResponse("<h1>AgentThree</h1><p>UI HTML missing.</p>", status_code=500)
    return HTMLResponse(_classic_html())


@app.get("/classic")
async def classic_ui() -> HTMLResponse:
    if not UI_HTML.exists():
        raise HTTPException(404, "Classic HTML UI missing")
    return HTMLResponse(_classic_html())


_react_assets = ROOT / "web" / "dist" / "assets"
if _react_assets.is_dir():
    app.mount("/assets", StaticFiles(directory=_react_assets), name="react-assets")


def main() -> None:
    import uvicorn

    uvicorn.run(
        "agentthree.api.server:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
