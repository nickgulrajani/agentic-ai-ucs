import type { AgentKey, AgentStatus } from '../types'

const AGENTS: Array<{ k: AgentKey; nm: string; c: string }> = [
  { k: 'intake', nm: 'Clinical Intake', c: 'var(--lime)' },
  { k: 'pa', nm: 'Prior Authorization', c: 'var(--violet)' },
  { k: 'cds', nm: 'Decision Support', c: 'var(--amber)' },
  { k: 'human', nm: 'Human Review', c: 'var(--cyan)' },
]

const LABELS: Record<AgentStatus, string> = {
  idle: 'idle',
  working: 'working…',
  done: 'complete',
  waiting: 'awaiting reviewer',
  halted: 'halted · escalated',
  skipped: 'skipped',
}

export function AgentPipeline({
  state,
  contextId,
}: {
  state: Record<AgentKey, AgentStatus>
  contextId: string
}) {
  return (
    <div className="pane">
      <div className="pane-h">
        <h3>Agent pipeline</h3>
        <span className="label mono">contextId · {contextId || '—'}</span>
      </div>
      <div className="pipeline">
        {AGENTS.map((a) => {
          const st = state[a.k] || 'idle'
          return (
            <div key={a.k} className={`node ${st}`} style={{ ['--c' as string]: a.c }}>
              <div className="bar" />
              <div className="nm">{a.nm}</div>
              <div className="st">● {LABELS[st]}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
