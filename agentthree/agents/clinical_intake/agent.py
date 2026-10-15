"""Clinical Intake Agent — ADK LlmAgent with MCP tools."""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from agentthree.config import GEMINI_MODEL, MCP_URL, ensure_genai_env

ensure_genai_env()

INSTRUCTION = """You are the Clinical Intake Agent for a prior authorization demo.
Use MCP tools fhir_read, fhir_search, and rxnorm_normalize to gather context.
Extract structured clinical entities from the provider note.
Return a concise JSON summary with keys:
icd, icdText, meds (name, dose, rxcui, cls), conservativeTherapyWeeks, neuroS, radicS,
redFlags (flag, evidence), prior, gaps.
Never invent PHI. This is a fictional demo. Agents cannot issue denials.
"""

root_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="clinical_intake",
    description="Extracts and normalizes clinical context for prior authorization.",
    instruction=INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=MCP_URL),
            tool_filter=["fhir_read", "fhir_search", "rxnorm_normalize"],
        )
    ],
)
