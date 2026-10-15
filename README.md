# AgentThree — Prior Authorization (ADK · A2A · MCP · Gemini)

One complete end-to-end prior authorization scenario for **CPT 72148 (MRI lumbar spine)**: three Google ADK agents coordinate over A2A-shaped handoffs, call clinical tools through MCP, reason with Gemini, and pause for a human reviewer in the Live Run UI.

This implements the architecture described in [`agentthree-prior-auth.html`](./agentthree-prior-auth.html).

| Layer | What runs locally |
|--------|-------------------|
| **Agents** | Google ADK `LlmAgent`s — Clinical Intake, Prior Authorization, Clinical Decision Support |
| **A2A** | Agent Cards via `to_a2a()` (optional) + JSON-RPC `message/send` envelopes per case |
| **MCP** | FastMCP server — FHIR, RxNorm, policy search, eligibility, guidelines |
| **Models** | Gemini via **Google AI Studio free tier** (not Vertex — keeps billing at $0) |
| **UI** | Same Live Run console, switched to **Live** mode against the API |

**GCP project (yours):** `agentthree-ai-dev-511709` · number `31543876598`

---

## Zero / minimal billing setup

You do **not** need a Gemini Workspace / Standard license.

1. Create a free API key: [Google AI Studio → API keys](https://aistudio.google.com/apikey)
2. Prefer attaching the key to a **Free tier** project (do not link a paid billing key unless you want charges)
3. Copy env and paste the key:

```bash
cp .env.example .env
# edit .env:
#   GOOGLE_API_KEY=...
#   DEMO_MODE=false
#   GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

With `DEMO_MODE=true` (default in the checked-in `.env`), the pipeline still exercises **real MCP** and **A2A envelopes**; Gemini steps use deterministic fixtures so you can demo with **no API key**.

---

## Quick start

```bash
cd agentic-ai-ucs
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1 — MCP + API + UI  (always use the project venv)
.venv/bin/python -m agentthree
# or:  source .venv/bin/activate && python -m agentthree
```

> If you see `No module named 'fastmcp'` or `cannot import name 'streamable_http_client'`, you ran with system/pyenv Python instead of `.venv`. Use `.venv/bin/python -m agentthree`.

Open **http://127.0.0.1:8000**

1. Stay on **Live** mode (or switch to Simulation for the pure in-browser demo)
2. Pick scenario **Meets criteria**
3. **Submit request** → watch Intake → Prior Auth → Decision Support
4. On the **Review** tab, Approve / Request info / Escalate
5. Inspect **MCP tool calls**, **A2A messages**, and the **SHA-256 audit** tab

### Optional: A2A Agent Card servers

```bash
# in .env
START_A2A=true
```

Then:

```bash
curl -s http://127.0.0.1:9001/.well-known/agent-card.json | head
curl -s http://127.0.0.1:9002/.well-known/agent-card.json | head
curl -s http://127.0.0.1:9003/.well-known/agent-card.json | head
```

### Health

```bash
curl -s http://127.0.0.1:8000/api/health | python -m json.tool
```

---

## Repository layout

```
agentthree/
  mcp/server.py          # FastMCP tools (FHIR, RxNorm, policy, eligibility, guidelines)
  agents/                # Three ADK LlmAgents (MCP toolsets)
  a2a_servers.py         # to_a2a() Agent Card servers
  pipeline.py            # End-to-end case runner + audit ledger
  gemini_steps.py        # Structured Gemini calls (AI Studio)
  api/server.py          # FastAPI + SSE + UI
data/                    # Demo FHIR patients + AHP-RAD-014 policy
ui/live-bridge.js        # Wires the HTML Live Run tab to the API
agentthree-prior-auth.html
```

---

## Scenario covered

**Happy path:** Jordan Rivera · CPT `72148` · ICD-10 `M54.16` · 6+ weeks PT · neurologic findings → recommend approval → human gate.

Fault injection (UI dropdown) still works in Live mode: MCP timeout, eligibility outage, missing policy, grounding failure.

---

## Notes

- Fictional patients, payer, and policy — **not for clinical use**
- Agents **cannot deny**; adverse paths escalate to a human
- Keep `GOOGLE_GENAI_USE_VERTEXAI=FALSE` for free-tier AI Studio usage
- Vertex / Cloud Run / Confidential Computing remain future build items on the guide’s Build status list
