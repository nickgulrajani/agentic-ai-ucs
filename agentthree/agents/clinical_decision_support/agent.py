"""Clinical Decision Support Agent — ADK LlmAgent with MCP tools."""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from agentthree.config import GEMINI_MODEL, MCP_URL, ensure_genai_env

ensure_genai_env()

INSTRUCTION = """You are the Clinical Decision Support Agent.
Use guideline_search to retrieve cited evidence.
Every finding MUST include at least one citation id from retrieved sources.
Return JSON: recs (t, conf, cite[]), risks[], grounding {claims, cited, unsupported}.
Do not invent guideline IDs. Do not approve or deny coverage — only evidence for a human reviewer.
"""

root_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="clinical_decision_support",
    description="Guideline retrieval and cited evidence synthesis for PA review.",
    instruction=INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=MCP_URL),
            tool_filter=["guideline_search"],
        )
    ],
)
