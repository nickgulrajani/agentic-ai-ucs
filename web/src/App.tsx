import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { createCase, fetchHealth, getCase, streamCase, submitDecision } from './api'
import { AgentPipeline } from './components/AgentPipeline'
import { CaseFormPanel } from './components/CaseForm'
import { Inspector } from './components/Inspector'
import { PRESETS } from './presets'
import type {
  A2AMessage,
  AgentKey,
  AgentStatus,
  CaseForm,
  CdsResult,
  Health,
  PolicyResult,
  TimelineEvent,
  ToolCall,
} from './types'

const IDLE: Record<AgentKey, AgentStatus> = {
  intake: 'idle',
  pa: 'idle',
  cds: 'idle',
  human: 'idle',
}

export default function App() {
  const [preset, setPreset] = useState('meets')
  const [form, setForm] = useState<CaseForm>(PRESETS.meets.form)
  const [health, setHealth] = useState<Health | null>(null)
  const [healthErr, setHealthErr] = useState(false)
  const [running, setRunning] = useState(false)
  const [status, setStatus] = useState('Ready')
  const [contextId, setContextId] = useState('')
  const [agentState, setAgentState] = useState(IDLE)
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [tools, setTools] = useState<ToolCall[]>([])
  const [a2a, setA2a] = useState<A2AMessage[]>([])
  const [pol, setPol] = useState<PolicyResult | undefined>()
  const [cds, setCds] = useState<CdsResult | undefined>()
  const [awaitingHuman, setAwaitingHuman] = useState(false)
  const [caseId, setCaseId] = useState<string | null>(null)
  const [decision, setDecision] = useState<{ label: string; reviewer: string; note?: string } | undefined>()
  const [tab, setTab] = useState<'events' | 'tools' | 'a2a' | 'output' | 'review'>('events')

  useEffect(() => {
    fetchHealth()
      .then((h) => {
        setHealth(h)
        setHealthErr(false)
      })
      .catch(() => setHealthErr(true))
  }, [])

  const reset = useCallback(() => {
    setRunning(false)
    setStatus('Ready')
    setContextId('')
    setAgentState(IDLE)
    setEvents([])
    setTools([])
    setA2a([])
    setPol(undefined)
    setCds(undefined)
    setAwaitingHuman(false)
    setCaseId(null)
    setDecision(undefined)
    setTab('events')
  }, [])

  const onSubmit = async () => {
    if (running) return
    reset()
    setRunning(true)
    setStatus('Submitting case…')
    try {
      const created = await createCase(form)
      setCaseId(created.caseId)
      setStatus(`Streaming ${created.caseId.slice(0, 8)}…`)

      await new Promise<void>((resolve, reject) => {
        streamCase(
          created.streamUrl,
          (msg) => {
            if (msg.contextId) setContextId(msg.contextId)
            if (msg.agentState) setAgentState((s) => ({ ...s, ...msg.agentState }))
            if (msg.type === 'event' && msg.event) setEvents((e) => [...e, msg.event!])
            if (msg.type === 'tool' && msg.tool) setTools((t) => [...t, msg.tool!])
            if (msg.type === 'a2a' && msg.a2a) setA2a((a) => [...a, msg.a2a!])
            if (msg.pol) setPol(msg.pol)
            if (msg.cds) setCds(msg.cds)
            if (msg.result) {
              if (msg.result.events) setEvents(msg.result.events)
              if (msg.result.tools) setTools(msg.result.tools)
              if (msg.result.a2a) setA2a(msg.result.a2a)
              if (msg.result.agent) setAgentState(msg.result.agent)
              if (msg.result.pol) setPol(msg.result.pol)
              if (msg.result.cds) setCds(msg.result.cds)
              if (msg.result.contextId) setContextId(msg.result.contextId)
            }
            if (msg.awaitingHuman || msg.type === 'ready_for_review' || msg.type === 'halt') {
              setAwaitingHuman(true)
              setTab('review')
            }
          },
          () => resolve(),
          (err) => reject(err),
        )
      })

      const finalCase = await getCase(created.caseId)
      if (finalCase.events) setEvents(finalCase.events)
      if (finalCase.tools) setTools(finalCase.tools)
      if (finalCase.a2a) setA2a(finalCase.a2a)
      if (finalCase.agent) setAgentState(finalCase.agent)
      if (finalCase.pol) setPol(finalCase.pol)
      if (finalCase.cds) setCds(finalCase.cds)
      if (finalCase.contextId) setContextId(finalCase.contextId)
      setAwaitingHuman(true)
      setAgentState((s) => ({ ...s, human: 'waiting' }))
      setTab('review')
      setStatus('Awaiting human review')
      setRunning(false)
    } catch (e) {
      setStatus(e instanceof Error ? e.message : String(e))
      setRunning(false)
    }
  }

  const onDecide = async (action: string, reviewer: string, note: string) => {
    if (!caseId) return
    try {
      const sealed = await submitDecision(caseId, { action, reviewer, note })
      setDecision(sealed.decision)
      setAgentState((s) => ({ ...s, human: 'done' }))
      setAwaitingHuman(false)
      setStatus('Complete')
    } catch (e) {
      setStatus(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <span className="dots">
            <i style={{ background: 'var(--lime)' }} />
            <i style={{ background: 'var(--violet)' }} />
            <i style={{ background: 'var(--amber)' }} />
          </span>
          AgentThree
        </div>
        <span className="badge">Live agents · React</span>
        <span className={`health ${healthErr ? 'bad' : health ? 'ok' : ''}`}>
          {healthErr
            ? 'backend offline — start .venv/bin/python -m agentthree'
            : health
              ? `${health.demoMode ? 'fixtures' : `Gemini · ${health.model}`} · ${health.project}`
              : 'checking…'}
        </span>
      </header>

      <section className="hero">
        <h1>
          Watch three agents <em>work a prior auth</em> case.
        </h1>
        <p>
          Clinical Intake → Prior Authorization → Decision Support over A2A, tools via MCP, reasoning with Gemini —
          then a human seals the decision.
        </p>
      </section>

      <div className="console">
        <CaseFormPanel
          form={form}
          preset={preset}
          running={running}
          onPreset={(k) => {
            setPreset(k)
            setForm(PRESETS[k].form)
            reset()
          }}
          onChange={(patch) => setForm((f) => ({ ...f, ...patch }))}
          onSubmit={onSubmit}
          onReset={reset}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>
          <AgentPipeline state={agentState} contextId={contextId} />
          <Inspector
            tab={tab}
            onTab={setTab}
            events={events}
            tools={tools}
            a2a={a2a}
            pol={pol}
            cds={cds}
            awaitingHuman={awaitingHuman}
            decision={decision}
            onDecide={onDecide}
          />
          <div className="status-line">{status}</div>
        </div>
      </div>
    </div>
  )
}
