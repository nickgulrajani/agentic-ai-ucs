import { useEffect, useState } from 'react'
import './App.css'
import { fetchHealth } from './api'
import { BuildStatusPage } from './pages/BuildStatusPage'
import { EngineeringPage } from './pages/EngineeringPage'
import { LiveRunPage } from './pages/LiveRunPage'
import { OverviewPage } from './pages/OverviewPage'
import type { Health } from './types'

type View = 'overview' | 'run' | 'eng' | 'build'

const NAV: Array<{ id: View; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'run', label: 'Live run' },
  { id: 'eng', label: 'Engineering' },
  { id: 'build', label: 'Build status' },
]

export default function App() {
  const [view, setView] = useState<View>('overview')
  const [health, setHealth] = useState<Health | null>(null)
  const [healthErr, setHealthErr] = useState(false)

  useEffect(() => {
    fetchHealth()
      .then((h) => {
        setHealth(h)
        setHealthErr(false)
      })
      .catch(() => setHealthErr(true))
  }, [])

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
        <span className="badge">ADK · A2A · MCP · Gemini</span>
        <nav className="tabs" role="tablist" aria-label="Sections">
          {NAV.map((n) => (
            <button
              key={n.id}
              type="button"
              role="tab"
              aria-selected={view === n.id}
              onClick={() => setView(n.id)}
            >
              {n.label}
            </button>
          ))}
        </nav>
        <span className={`health ${healthErr ? 'bad' : health ? 'ok' : ''}`}>
          {healthErr
            ? 'backend offline'
            : health
              ? `${health.demoMode ? 'fixtures' : `Gemini · ${health.model}`}`
              : 'checking…'}
        </span>
      </header>

      {view === 'overview' && <OverviewPage onGoLive={() => setView('run')} />}
      {view === 'run' && <LiveRunPage />}
      {view === 'eng' && <EngineeringPage />}
      {view === 'build' && <BuildStatusPage />}
    </div>
  )
}
