import { ArchitectureDiagram } from '../components/ArchitectureDiagram'

const STACK: Array<[string, string, string]> = [
  ['Agents', 'Google Agent Development Kit (Python)', 'Three LlmAgents with MCP toolsets; optional A2A Agent Cards'],
  ['Agent comms', 'A2A protocol (JSON-RPC)', 'Agent Cards, task lifecycle, shared contextId, HITL via input-required'],
  ['Models', 'Gemini (AI Studio free tier)', 'Entity extraction, criteria matching, cited evidence synthesis'],
  ['Tools', 'MCP servers (FastMCP)', 'FHIR R4, RxNorm, payer policy, eligibility, guidelines'],
  ['Interop', 'FHIR R4 · Da Vinci PAS shape', 'Inbound ServiceRequest-style request'],
  ['Safety', 'Grounding · schema · HITL', 'Agents cannot deny; every claim cites a source'],
  ['Audit', 'SHA-256 hash-chained ledger', 'Tamper-evident record of the case'],
  ['UI', 'React (Vite) + classic HTML', 'One Live Run console; Overview shows this architecture'],
]

export function OverviewPage({ onGoLive }: { onGoLive: () => void }) {
  return (
    <div className="page">
      <div className="hero-grid">
        <div>
          <div className="label" style={{ color: 'var(--cyan)' }}>
            Healthcare AI · Clinical intake → prior authorization
          </div>
          <h1 className="page-title">
            Three agents. One <em>auditable</em> prior authorization decision.
          </h1>
          <p className="lede">
            Clinical Intake, Prior Authorization, and Clinical Decision Support coordinate over A2A, reach systems
            through MCP, and hand a grounded recommendation to a human reviewer. No consequential decision without a
            clinician.
          </p>
          <button type="button" className="btn primary" onClick={onGoLive}>
            Open Live run →
          </button>
        </div>
        <div className="banner">
          <b>How to demo.</b> Start on this Overview for the architecture story, then switch to <b>Live run</b> to
          watch ADK agents, MCP tools, and A2A handoffs on a real local backend (Gemini free tier or fixtures).
        </div>
      </div>

      <div className="sec-head">
        <span className="label">01 · The problem</span>
        <h2>Why prior authorization needs agents, not a chatbot</h2>
      </div>
      <div className="grid3">
        <div className="card">
          <h3>Fragmented evidence</h3>
          <p>
            Facts sit across the EHR, meds, payer policy, and guidelines. Staff assemble them by hand; requests stall on
            missing documentation.
          </p>
        </div>
        <div className="card">
          <h3>Policy matching is criteria work</h3>
          <p>
            Coverage policies are checklists: diagnosis, conservative therapy, exam findings, prior imaging — each needs
            cited evidence.
          </p>
        </div>
        <div className="card">
          <h3>Regulatory clock</h3>
          <p>
            CMS-0057-F sets PA timeframes and FHIR Prior Auth APIs. Speed must come with traceability.
          </p>
        </div>
      </div>

      <div className="sec-head">
        <span className="label">02 · Architecture</span>
        <h2>Agents talk over A2A; tools are reached through MCP</h2>
      </div>
      <ArchitectureDiagram />

      <div className="sec-head">
        <span className="label">03 · Communication</span>
        <h2>Two protocols, two jobs</h2>
      </div>
      <div className="grid2">
        <div className="card" style={{ borderColor: 'rgba(255,79,216,.4)' }}>
          <h3 style={{ color: 'var(--magenta)' }}>A2A · agent to agent</h3>
          <p>
            Agents hand work forward with JSON-RPC <span className="mono">message/send</span>, sharing one{' '}
            <span className="mono">contextId</span>. Structured context as a DataPart; rationale as a TextPart.
          </p>
          <ul>
            <li>
              Task states: <span className="mono">submitted → working → input-required → completed</span>
            </li>
            <li>
              <span className="mono">input-required</span> pauses for a human reviewer
            </li>
            <li>Agents stay independently deployable</li>
          </ul>
        </div>
        <div className="card" style={{ borderColor: 'rgba(34,211,238,.4)' }}>
          <h3 style={{ color: 'var(--cyan)' }}>MCP · agent to tools and data</h3>
          <p>
            Agents never query the EHR or policy store directly. They call MCP tools such as{' '}
            <span className="mono">fhir_search</span>, <span className="mono">rxnorm_normalize</span>, and{' '}
            <span className="mono">policy_search</span>.
          </p>
          <ul>
            <li>Tool schemas constrain what the model can request</li>
            <li>PHI-minimized responses</li>
            <li>Every call appears in the Live run MCP tab</li>
          </ul>
        </div>
      </div>

      <div className="sec-head">
        <span className="label">04 · Stack</span>
        <h2>Technical stack</h2>
      </div>
      <div className="tablewrap">
        <table className="stack">
          <thead>
            <tr>
              <th>Layer</th>
              <th>Technology</th>
              <th>Role in this system</th>
            </tr>
          </thead>
          <tbody>
            {STACK.map(([layer, tech, role]) => (
              <tr key={layer}>
                <td>{layer}</td>
                <td>{tech}</td>
                <td>{role}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
