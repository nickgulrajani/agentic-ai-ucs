"""Prior Authorization Agent — ADK LlmAgent with MCP tools."""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from agentthree.config import GEMINI_MODEL, MCP_URL, ensure_genai_env

ensure_genai_env()

INSTRUCTION = """You are the Prior Authorization Agent for a fictional payer demo.
Use check_eligibility and policy_search MCP tools.
Match criteria to the structured intake context.
Allowed outcomes only: recommend_approve, pend_info, urgent_review.
You MUST NOT issue a denial. If policy is missing, escalate to a human.
Return JSON with crit (id, text, sec, st=met|not|waive, ev), outcome (meets|pend|urgent), policy.
"""

root_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="prior_authorization",
    description="Eligibility, policy retrieval, and criterion matching for PA.",
    instruction=INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=MCP_URL),
            tool_filter=["check_eligibility", "policy_search"],
        )
    ],
)
