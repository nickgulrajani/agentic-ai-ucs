type Row = { name: string; detail: string; status: 'built' | 'prog' | 'sim' }

const ROWS: Row[] = [
  { name: 'Clinical Intake Agent', detail: 'ADK agent · entity extraction · FHIR/RxNorm', status: 'built' },
  { name: 'Prior Authorization Agent', detail: 'ADK agent · eligibility · policy match', status: 'built' },
  { name: 'Clinical Decision Support Agent', detail: 'ADK agent · guidelines · citations', status: 'built' },
  { name: 'A2A wiring + envelopes', detail: 'message/send · contextId · HITL pause', status: 'built' },
  { name: 'MCP server · clinical', detail: 'FHIR, RxNorm, policy, eligibility, guidelines', status: 'built' },
  { name: 'React Live Run UI', detail: 'web/ — agents in play + inspector', status: 'built' },
  { name: 'Overview architecture UI', detail: 'Same React app — diagram + stack', status: 'built' },
  { name: 'Audit ledger', detail: 'SHA-256 hash chain per case', status: 'built' },
  { name: 'Evaluation harness', detail: 'evaluation/ golden cases', status: 'built' },
  { name: 'A2A Agent Card servers', detail: 'Optional START_A2A=true', status: 'prog' },
  { name: 'Cloud Run / GKE deploy', detail: 'Deferred — keep local for $0 demo', status: 'sim' },
  { name: 'Confidential Computing', detail: 'Deferred enterprise path', status: 'sim' },
]

const LABEL = { built: 'Built', prog: 'In progress', sim: 'Deferred' } as const

export function BuildStatusPage() {
  const counts = {
    built: ROWS.filter((r) => r.status === 'built').length,
    prog: ROWS.filter((r) => r.status === 'prog').length,
    sim: ROWS.filter((r) => r.status === 'sim').length,
  }
  return (
    <div className="page">
      <div className="sec-head" style={{ marginTop: 0 }}>
        <span className="label">Build status</span>
        <h2>What exists outside the slideware</h2>
      </div>
      <p className="lede">
        {counts.built} built · {counts.prog} optional · {counts.sim} deferred (cost control)
      </p>
      <div className="tablewrap" style={{ marginTop: 18 }}>
        <table className="stack">
          <thead>
            <tr>
              <th>Component</th>
              <th>What it does</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.name}>
                <td>{r.name}</td>
                <td>{r.detail}</td>
                <td>
                  <span className={`pill ${r.status === 'built' ? 'p-met' : r.status === 'prog' ? 'p-waive' : 'p-not'}`}>
                    {LABEL[r.status]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
