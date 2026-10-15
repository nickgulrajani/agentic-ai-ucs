"""Expose the three ADK agents as A2A servers (Agent Cards + message/send)."""

from __future__ import annotations

import logging
import threading

import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from agentthree.agents.clinical_decision_support.agent import root_agent as cds_agent
from agentthree.agents.clinical_intake.agent import root_agent as intake_agent
from agentthree.agents.prior_auth.agent import root_agent as pa_agent
from agentthree.config import CDS_A2A_PORT, INTAKE_A2A_PORT, PA_A2A_PORT, ensure_genai_env

logger = logging.getLogger(__name__)
ensure_genai_env()


def _serve(agent, host: str, port: int, name: str) -> None:
    app = to_a2a(agent, host=host, port=port)
    logger.info("A2A %s on http://%s:%s/.well-known/agent-card.json", name, host, port)
    uvicorn.run(app, host=host, port=port, log_level="warning")


def start_background() -> list[threading.Thread]:
    specs = [
        (intake_agent, INTAKE_A2A_PORT, "clinical-intake"),
        (pa_agent, PA_A2A_PORT, "prior-auth"),
        (cds_agent, CDS_A2A_PORT, "clinical-decision-support"),
    ]
    threads = []
    for agent, port, name in specs:
        t = threading.Thread(
            target=_serve,
            args=(agent, "127.0.0.1", port, name),
            name=f"a2a-{name}",
            daemon=True,
        )
        t.start()
        threads.append(t)
    return threads


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_background()
    threading.Event().wait()
