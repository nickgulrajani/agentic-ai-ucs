"""Runtime configuration. Prefer AI Studio free tier over Vertex for demos."""

from __future__ import annotations

import os
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
