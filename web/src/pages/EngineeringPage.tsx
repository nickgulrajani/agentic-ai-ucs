const CAPS = [
  {
    k: 'Agent Orchestration',
    t: 'Google ADK / A2A',
    c: 'var(--lime)',
    ev: [
      '3 ADK agents in agents/',
      'A2A message/send envelopes + shared contextId',
      'Optional Agent Cards via START_A2A=true',
      'Gemini on AI Studio free tier',
    ],
  },
  {
    k: 'Tool Integration',
    t: 'MCP / FastMCP / FHIR',
    c: 'var(--cyan)',
    ev: [
      'mcp_servers/clinical — FHIR, RxNorm, policy, eligibility, guidelines',
      'Typed tool schemas; streamable HTTP',
      'Live run MCP tab shows request/response',
      'Fault injection: timeout, outage, missing policy',
    ],
  },
  {
    k: 'Grounding & Retrieval',
    t: 'Policy RAG + citations',
    c: 'var(--violet)',
    ev: [
      'Local policy chunks (AHP-RAD-014)',
      'Guideline retrieval for CDS',
      'Grounding guardrail on citations',
      'Agents cannot issue a denial',
    ],
  },
  {
    k: 'Security & Governance',
    t: 'HITL + audit',
    c: 'var(--amber)',
    ev: [
      'Human review gate before any final act',
      'SHA-256 hash-chained audit ledger',
      'Synthetic / fictional PHI only',
      'Local demo — no GKE required',
    ],
  },
]

export function EngineeringPage() {
  return (
    <div className="page">
      <div className="sec-head" style={{ marginTop: 0 }}>
        <span className="label">Engineering</span>
        <h2>What this repo actually runs</h2>
      </div>
      <p className="lede" style={{ marginBottom: 24 }}>
        Capabilities you can demonstrate locally without Cloud Run or Confidential GKE.
      </p>
      <div className="grid2">
        {CAPS.map((c) => (
          <div key={c.k} className="card cap" style={{ ['--c' as string]: c.c }}>
            <div className="label" style={{ color: c.c }}>
              {c.k}
            </div>
            <div className="tech">{c.t}</div>
            <ul>
              {c.ev.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
