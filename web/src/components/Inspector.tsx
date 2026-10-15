import type { A2AMessage, CdsResult, PolicyResult, TimelineEvent, ToolCall } from '../types'

type Tab = 'events' | 'tools' | 'a2a' | 'output' | 'review'

const KIND: Record<string, string> = {
  a2a: 't-a2a',
  mcp: 't-mcp',
  llm: 't-llm',
  guard: 't-guard',
  gate: 't-gate',
  sys: 't-sys',
  err: 't-err',
  retry: 't-retry',
}

export function Inspector({
  tab,
  onTab,
  events,
  tools,
  a2a,
  pol,
  cds,
  awaitingHuman,
  decision,
  onDecide,
}: {
  tab: Tab
  onTab: (t: Tab) => void
  events: TimelineEvent[]
  tools: ToolCall[]
  a2a: A2AMessage[]
  pol?: PolicyResult
  cds?: CdsResult
  awaitingHuman: boolean
  decision?: { label: string; reviewer: string; note?: string }
  onDecide: (action: string, reviewer: string, note: string) => void
}) {
  return (
    <div className="pane">
      <div className="itabs" role="tablist">
        {(
          [
            ['events', 'Timeline', events.length],
            ['output', 'Agent outputs', 0],
            ['tools', 'MCP tool calls', tools.length],
            ['a2a', 'A2A messages', a2a.length],
            ['review', 'Human review', 0],
          ] as const
        ).map(([id, label, n]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            onClick={() => onTab(id)}
          >
            {label}
            {n ? <span className="n">{n}</span> : null}
          </button>
        ))}
      </div>
      <div className="ibody">
        {tab === 'events' && <EventsPanel events={events} />}
        {tab === 'tools' && <ToolsPanel tools={tools} />}
        {tab === 'a2a' && <A2APanel a2a={a2a} />}
        {tab === 'output' && <OutputPanel pol={pol} cds={cds} />}
        {tab === 'review' && (
          <ReviewPanel
            awaitingHuman={awaitingHuman}
            pol={pol}
            decision={decision}
            onDecide={onDecide}
          />
        )}
      </div>
    </div>
  )
}

function EventsPanel({ events }: { events: TimelineEvent[] }) {
  if (!events.length) return <div className="empty">No run yet. Submit a request to watch agents work.</div>
  return (
    <>
      {[...events].reverse().map((e) => (
        <div className="ev" key={e.seq}>
          <span className={`tag ${KIND[e.kind] || 't-sys'}`}>{e.kind}</span>
          <div>
            <div className="ttl">{e.title}</div>
            <div className="meta">
              #{e.seq} · {e.agent} · {e.durMs} ms
              {e.detail ? ` · ${e.detail}` : ''}
            </div>
          </div>
        </div>
      ))}
    </>
  )
}

function ToolsPanel({ tools }: { tools: ToolCall[] }) {
  if (!tools.length) return <div className="empty">No MCP calls yet.</div>
  return (
    <>
      {tools.map((t, i) => (
        <details className="call" key={`${t.tool}-${i}`} open={i === tools.length - 1}>
          <summary>
            <span className={`tag ${t.error ? 't-err' : 't-mcp'}`}>{t.server}</span>
            <span className="mono">
              {t.tool}()
              {t.attempt > 1 || t.error ? ` · attempt ${t.attempt}` : ''}
            </span>
            <span className="meta" style={{ marginLeft: 'auto' }}>
              {t.agent} · {t.dur} ms
            </span>
          </summary>
          <div className="inner">
            <div className="label">Request</div>
            <pre className="json">{JSON.stringify(t.req, null, 2)}</pre>
            <div className="label" style={{ marginTop: 10 }}>
              Response
            </div>
            <pre className="json">{JSON.stringify(t.res, null, 2)}</pre>
          </div>
        </details>
      ))}
    </>
  )
}

function A2APanel({ a2a }: { a2a: A2AMessage[] }) {
  if (!a2a.length) return <div className="empty">No A2A messages yet.</div>
  return (
    <>
      {a2a.map((a, i) => (
        <details className="call" key={i} open={i === a2a.length - 1}>
          <summary>
            <span className="tag t-a2a">message/send</span>
            <span className="mono">
              {a.from} → {a.to}
            </span>
          </summary>
          <div className="inner">
            <div className="label">Request</div>
            <pre className="json">{JSON.stringify(a.msg, null, 2)}</pre>
            <div className="label" style={{ marginTop: 10 }}>
              Response
            </div>
            <pre className="json">{JSON.stringify(a.resp, null, 2)}</pre>
          </div>
        </details>
      ))}
    </>
  )
}

function OutputPanel({ pol, cds }: { pol?: PolicyResult; cds?: CdsResult }) {
  if (!pol && !cds) return <div className="empty">Agent outputs appear as each agent finishes.</div>
  return (
    <>
      {pol && (
        <>
          <h3 style={{ color: 'var(--violet)', fontFamily: 'var(--display)', fontSize: 16 }}>
            Prior Authorization
          </h3>
          {pol.reason && <p style={{ color: 'var(--soft)' }}>{pol.reason}</p>}
          {pol.crit && pol.crit.length > 0 && (
            <table className="crit">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Criterion</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {pol.crit.map((c) => (
                  <tr key={c.id}>
                    <td className="mono">{c.id}</td>
                    <td>
                      {c.text}
                      <div className="meta">{c.ev}</div>
                    </td>
                    <td>
                      <span className={`pill ${c.st === 'met' ? 'p-met' : c.st === 'waive' ? 'p-waive' : 'p-not'}`}>
                        {c.st}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p style={{ fontWeight: 700, marginTop: 12 }}>
            Recommendation: <span style={{ color: 'var(--cyan)' }}>{pol.outcome}</span>
          </p>
        </>
      )}
      {cds?.recs && (
        <>
          <h3 style={{ color: 'var(--amber)', fontFamily: 'var(--display)', fontSize: 16, marginTop: 22 }}>
            Decision Support
          </h3>
          {cds.recs.map((r, i) => (
            <div className="rec" key={i}>
              <div style={{ fontWeight: 600 }}>{r.t}</div>
              <div className="meta" style={{ marginTop: 6 }}>
                conf {r.conf.toFixed(2)} · {r.cite.join(' · ')}
              </div>
            </div>
          ))}
        </>
      )}
    </>
  )
}

function ReviewPanel({
  awaitingHuman,
  pol,
  decision,
  onDecide,
}: {
  awaitingHuman: boolean
  pol?: PolicyResult
  decision?: { label: string; reviewer: string; note?: string }
  onDecide: (action: string, reviewer: string, note: string) => void
}) {
  if (decision) {
    return (
      <div className="gatebox">
        <div style={{ fontFamily: 'var(--display)', fontSize: 22, fontWeight: 800 }}>{decision.label}</div>
        <div className="meta">
          by {decision.reviewer}
          {decision.note ? ` · ${decision.note}` : ''}
        </div>
      </div>
    )
  }
  if (!awaitingHuman) {
    return <div className="empty">The reviewer gate opens after Decision Support finishes.</div>
  }
  const halted = pol?.outcome === 'system' || pol?.outcome === 'nopolicy'
  return (
    <div className="gatebox">
      <h3 style={{ margin: '0 0 8px', fontFamily: 'var(--display)' }}>Clinician review required</h3>
      <p style={{ color: 'var(--soft)', margin: '0 0 12px' }}>
        Agent recommendation: <b style={{ color: 'var(--fg)' }}>{pol?.outcome || '—'}</b>. Agents cannot deny —
        only a human can approve, request info, or escalate.
      </p>
      <div className="row2">
        <div className="field">
          <label className="label" htmlFor="rv-name">
            Reviewer
          </label>
          <input id="rv-name" defaultValue="Dr. Sam Patel, MD (fictional)" />
        </div>
        <div className="field">
          <label className="label" htmlFor="rv-note">
            Note
          </label>
          <input id="rv-note" placeholder="Rationale for the record" />
        </div>
      </div>
      <div className="gatebtns">
        <button
          type="button"
          className="btn g-ok"
          disabled={halted}
          onClick={() =>
            onDecide(
              'approve',
              (document.getElementById('rv-name') as HTMLInputElement)?.value || 'Reviewer',
              (document.getElementById('rv-note') as HTMLInputElement)?.value || '',
            )
          }
        >
          Approve
        </button>
        <button
          type="button"
          className="btn g-info"
          onClick={() =>
            onDecide(
              'info',
              (document.getElementById('rv-name') as HTMLInputElement)?.value || 'Reviewer',
              (document.getElementById('rv-note') as HTMLInputElement)?.value || '',
            )
          }
        >
          Request more information
        </button>
        <button
          type="button"
          className="btn g-esc"
          onClick={() =>
            onDecide(
              'escalate',
              (document.getElementById('rv-name') as HTMLInputElement)?.value || 'Reviewer',
              (document.getElementById('rv-note') as HTMLInputElement)?.value || '',
            )
          }
        >
          Escalate to medical director
        </button>
      </div>
    </div>
  )
}
