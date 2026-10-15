# Architecture

AgentThree coordinates three Google ADK agents over A2A-shaped handoffs, reaches clinical systems through MCP, and reasons with Gemini. A human reviewer always seals the case.

```mermaid
flowchart LR
  UI["Live Run UI<br/>ui/agentthree-prior-auth.html"]
  API["API Gateway<br/>agentthree/api"]
  IN["Clinical Intake<br/>agents/clinical_intake"]
  PA["Prior Authorization<br/>agents/prior_auth"]
  CDS["Decision Support<br/>agents/clinical_decision_support"]
  HITL["Human Review"]
  MCP["MCP Server<br/>mcp_servers/clinical"]
  DATA["Demo data<br/>FHIR · Policy · Guidelines"]
  GEM["Gemini<br/>AI Studio free tier"]

  UI -->|SSE / REST| API
  API --> IN
  IN -->|A2A message/send| PA
  PA -->|A2A message/send| CDS
  CDS -->|input-required| HITL
  IN --> MCP
  PA --> MCP
  CDS --> MCP
  MCP --> DATA
  IN --> GEM
  PA --> GEM
  CDS --> GEM
```

## Layers

| Layer | Path | Role |
|--------|------|------|
| Agents | `agents/` | ADK `LlmAgent`s with MCP toolsets |
| MCP | `mcp_servers/` | FastMCP tools: FHIR, RxNorm, policy, eligibility, guidelines |
| Orchestration | `agentthree/` | Case pipeline, Gemini steps, audit ledger, A2A envelopes |
| API + UI | `agentthree/api`, `ui/` | Live Run console + SSE |
| Evaluation | `evaluation/` | Synthetic cases and metric scoring |
| Tests | `tests/` | Unit / integration tests |

## Protocol notes

- **A2A** — Agent Cards via `to_a2a()` (optional ports 9001–9003); each case emits JSON-RPC `message/send` envelopes with a shared `contextId`.
- **MCP** — Streamable HTTP at `/mcp`; agents never query stores directly.
- **Safety** — Agents cannot deny; adverse paths escalate to a human. Audit events are SHA-256 hash-chained.
