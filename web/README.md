# AgentThree React FE

Live Run console that streams ADK / MCP / A2A activity from the FastAPI backend.

```bash
# backend must be running first
.venv/bin/python -m agentthree

cd web
npm install
npm run dev
```

Open http://127.0.0.1:5173 (`/api` is proxied to the backend).

```bash
npm run build   # outputs web/dist — served at / when backend restarts
```
