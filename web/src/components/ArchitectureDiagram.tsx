/** Architecture SVG from the AgentThree guide (Overview). */
export function ArchitectureDiagram() {
  return (
    <div className="diagram" role="img" aria-label="Architecture: Provider to Intake, Prior Auth, CDS over A2A, MCP tools below, HITL and audit.">
      <svg viewBox="0 0 1100 520" xmlns="http://www.w3.org/2000/svg" fontFamily="DM Sans, sans-serif">
        <defs>
          <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#ff4fd8" />
          </marker>
          <marker id="arc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#22d3ee" />
          </marker>
          <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#b9cdf0" />
          </marker>
        </defs>
        <rect x="14" y="70" width="128" height="120" rx="10" fill="#151a25" stroke="#33405c" />
        <text x="78" y="112" textAnchor="middle" fill="#f2f6ff" fontFamily="Syne, sans-serif" fontWeight="700" fontSize="14">
          Provider
        </text>
        <text x="78" y="132" textAnchor="middle" fill="#b9cdf0" fontSize="11.5">
          EHR / portal
        </text>
        <text x="78" y="150" textAnchor="middle" fill="#b9cdf0" fontSize="11.5">
          Da Vinci PAS
        </text>
        <text x="78" y="168" textAnchor="middle" fill="#b9cdf0" fontSize="11.5">
          FHIR bundle
        </text>
        <line x1="144" y1="130" x2="172" y2="130" stroke="#b9cdf0" strokeWidth="1.5" markerEnd="url(#arw)" />

        <g>
          <rect x="176" y="50" width="200" height="160" rx="12" fill="#0f1117" stroke="#a3e635" strokeWidth="1.5" />
          <rect x="176" y="50" width="200" height="5" rx="2" fill="#a3e635" />
          <text x="192" y="82" fill="#a3e635" fontFamily="DM Mono, monospace" fontSize="10.5" letterSpacing="1.2">
            AGENT 1 · ADK
          </text>
          <text x="192" y="104" fill="#f2f6ff" fontFamily="Syne, sans-serif" fontWeight="700" fontSize="16">
            Clinical Intake
          </text>
          <text x="192" y="128" fill="#b9cdf0" fontSize="12">
            Extract conditions, meds, findings
          </text>
          <text x="192" y="146" fill="#b9cdf0" fontSize="12">
            Normalize to FHIR R4 / RxNorm
          </text>
          <text x="192" y="164" fill="#b9cdf0" fontSize="12">
            Detect documentation gaps
          </text>
          <text x="192" y="190" fill="#8fa6cf" fontFamily="DM Mono, monospace" fontSize="10.5">
            /.well-known/agent-card.json
          </text>
        </g>
        <g>
          <rect x="446" y="50" width="200" height="160" rx="12" fill="#0f1117" stroke="#a78bfa" strokeWidth="1.5" />
          <rect x="446" y="50" width="200" height="5" rx="2" fill="#a78bfa" />
          <text x="462" y="82" fill="#a78bfa" fontFamily="DM Mono, monospace" fontSize="10.5" letterSpacing="1.2">
            AGENT 2 · ADK
          </text>
          <text x="462" y="104" fill="#f2f6ff" fontFamily="Syne, sans-serif" fontWeight="700" fontSize="16">
            Prior Authorization
          </text>
          <text x="462" y="128" fill="#b9cdf0" fontSize="12">
            Check eligibility and benefits
          </text>
          <text x="462" y="146" fill="#b9cdf0" fontSize="12">
            Retrieve policy criteria (RAG)
          </text>
          <text x="462" y="164" fill="#b9cdf0" fontSize="12">
            Match criterion by criterion
          </text>
          <text x="462" y="190" fill="#8fa6cf" fontFamily="DM Mono, monospace" fontSize="10.5">
            /.well-known/agent-card.json
          </text>
        </g>
        <g>
          <rect x="716" y="50" width="200" height="160" rx="12" fill="#0f1117" stroke="#ffb020" strokeWidth="1.5" />
          <rect x="716" y="50" width="200" height="5" rx="2" fill="#ffb020" />
          <text x="732" y="82" fill="#ffb020" fontFamily="DM Mono, monospace" fontSize="10.5" letterSpacing="1.2">
            AGENT 3 · ADK
          </text>
          <text x="732" y="104" fill="#f2f6ff" fontFamily="Syne, sans-serif" fontWeight="700" fontSize="16">
            Clinical Decision Support
          </text>
          <text x="732" y="128" fill="#b9cdf0" fontSize="12">
            Retrieve guidelines (vector+graph)
          </text>
          <text x="732" y="146" fill="#b9cdf0" fontSize="12">
            Cited, confidence-scored findings
          </text>
          <text x="732" y="164" fill="#b9cdf0" fontSize="12">
            Grounding guardrail
          </text>
          <text x="732" y="190" fill="#8fa6cf" fontFamily="DM Mono, monospace" fontSize="10.5">
            /.well-known/agent-card.json
          </text>
        </g>

        <line x1="380" y1="118" x2="442" y2="118" stroke="#ff4fd8" strokeWidth="2" markerEnd="url(#ar)" />
        <text x="411" y="106" textAnchor="middle" fill="#ff4fd8" fontFamily="DM Mono, monospace" fontSize="11">
          A2A
        </text>
        <text x="411" y="140" textAnchor="middle" fill="#ff4fd8" fontFamily="DM Mono, monospace" fontSize="9.5">
          message/send
        </text>
        <line x1="650" y1="118" x2="712" y2="118" stroke="#ff4fd8" strokeWidth="2" markerEnd="url(#ar)" />
        <text x="681" y="106" textAnchor="middle" fill="#ff4fd8" fontFamily="DM Mono, monospace" fontSize="11">
          A2A
        </text>
        <text x="681" y="140" textAnchor="middle" fill="#ff4fd8" fontFamily="DM Mono, monospace" fontSize="9.5">
          task context
        </text>

        <line x1="920" y1="130" x2="952" y2="130" stroke="#ff4fd8" strokeWidth="2" markerEnd="url(#ar)" />
        <rect x="956" y="70" width="130" height="120" rx="10" fill="#151a25" stroke="#22d3ee" strokeWidth="1.5" />
        <text x="1021" y="104" textAnchor="middle" fill="#22d3ee" fontFamily="DM Mono, monospace" fontSize="10.5" letterSpacing="1.2">
          HITL GATE
        </text>
        <text x="1021" y="126" textAnchor="middle" fill="#f2f6ff" fontFamily="Syne, sans-serif" fontWeight="700" fontSize="15">
          Human review
        </text>
        <text x="1021" y="148" textAnchor="middle" fill="#b9cdf0" fontSize="11.5">
          Approve · Request info
        </text>
        <text x="1021" y="166" textAnchor="middle" fill="#b9cdf0" fontSize="11.5">
          Escalate to MD
        </text>

        <line x1="276" y1="212" x2="276" y2="262" stroke="#22d3ee" strokeWidth="1.5" markerEnd="url(#arc)" />
        <line x1="546" y1="212" x2="546" y2="262" stroke="#22d3ee" strokeWidth="1.5" markerEnd="url(#arc)" />
        <line x1="816" y1="212" x2="816" y2="262" stroke="#22d3ee" strokeWidth="1.5" markerEnd="url(#arc)" />
        <rect x="176" y="266" width="740" height="54" rx="10" fill="rgba(34,211,238,.08)" stroke="#22d3ee" strokeWidth="1.5" />
        <text x="546" y="290" textAnchor="middle" fill="#f2f6ff" fontFamily="Syne, sans-serif" fontWeight="700" fontSize="15">
          Model Context Protocol
        </text>
        <text x="546" y="309" textAnchor="middle" fill="#b9cdf0" fontSize="11.5">
          tools/list · tools/call · streamable HTTP · scoped identity · PHI-minimized responses
        </text>

        <g fontSize="11.5">
          <g transform="translate(176,350)">
            <rect width="114" height="76" rx="8" fill="#151a25" stroke="#33405c" />
            <text x="10" y="22" fill="#f2f6ff" fontWeight="700">
              FHIR R4
            </text>
            <text x="10" y="42" fill="#b9cdf0">
              Patient, Condition
            </text>
            <text x="10" y="58" fill="#b9cdf0">
              MedicationStatement
            </text>
          </g>
          <g transform="translate(301,350)">
            <rect width="114" height="76" rx="8" fill="#151a25" stroke="#33405c" />
            <text x="10" y="22" fill="#f2f6ff" fontWeight="700">
              Terminology
            </text>
            <text x="10" y="42" fill="#b9cdf0">
              RxNorm (RxNav)
            </text>
            <text x="10" y="58" fill="#b9cdf0">
              ICD-10-CM, CPT
            </text>
          </g>
          <g transform="translate(426,350)">
            <rect width="114" height="76" rx="8" fill="#151a25" stroke="#33405c" />
            <text x="10" y="22" fill="#f2f6ff" fontWeight="700">
              Payer policy
            </text>
            <text x="10" y="42" fill="#b9cdf0">
              Coverage criteria
            </text>
            <text x="10" y="58" fill="#b9cdf0">
              versioned chunks
            </text>
          </g>
          <g transform="translate(551,350)">
            <rect width="114" height="76" rx="8" fill="#151a25" stroke="#33405c" />
            <text x="10" y="22" fill="#f2f6ff" fontWeight="700">
              Eligibility
            </text>
            <text x="10" y="42" fill="#b9cdf0">
              Benefits, plan
            </text>
            <text x="10" y="58" fill="#b9cdf0">
              claims history
            </text>
          </g>
          <g transform="translate(676,350)">
            <rect width="114" height="76" rx="8" fill="#151a25" stroke="#33405c" />
            <text x="10" y="22" fill="#f2f6ff" fontWeight="700">
              Knowledge
            </text>
            <text x="10" y="42" fill="#b9cdf0">
              Guidelines
            </text>
            <text x="10" y="58" fill="#b9cdf0">
              literature
            </text>
          </g>
          <g transform="translate(801,350)">
            <rect width="115" height="76" rx="8" fill="#151a25" stroke="#33405c" />
            <text x="10" y="22" fill="#f2f6ff" fontWeight="700">
              Vector + graph
            </text>
            <text x="10" y="42" fill="#b9cdf0">
              FAISS / Weaviate
            </text>
            <text x="10" y="58" fill="#b9cdf0">
              Neo4j
            </text>
          </g>
        </g>
        <line x1="546" y1="322" x2="546" y2="346" stroke="#22d3ee" strokeWidth="1.5" markerEnd="url(#arc)" />

        <rect x="14" y="452" width="1072" height="50" rx="10" fill="rgba(163,230,53,.06)" stroke="#a3e635" strokeDasharray="5 4" />
        <text x="32" y="482" fill="#a3e635" fontFamily="DM Mono, monospace" fontSize="12" letterSpacing="1">
          AUDIT + OBSERVABILITY
        </text>
        <text x="210" y="482" fill="#b9cdf0" fontSize="12">
          Every A2A message, MCP call, model call, guardrail, and human decision → OTel span + SHA-256 hash-chained ledger
        </text>
      </svg>
    </div>
  )
}
