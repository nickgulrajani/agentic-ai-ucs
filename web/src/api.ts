import type { CaseForm, CaseResult, Health, StreamMsg } from './types'

const API = import.meta.env.VITE_API_BASE || ''

export async function fetchHealth(): Promise<Health> {
  const r = await fetch(`${API}/api/health`)
  if (!r.ok) throw new Error('Backend offline')
  return r.json()
}

export async function createCase(form: CaseForm): Promise<{ caseId: string; streamUrl: string }> {
  const r = await fetch(`${API}/api/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  })
  const j = await r.json()
  if (!r.ok || !j.caseId) throw new Error(j.detail ? JSON.stringify(j.detail) : 'Failed to create case')
  return j
}

export function streamCase(
  streamUrl: string,
  onMsg: (msg: StreamMsg) => void,
  onDone: () => void,
  onError: (err: Error) => void,
): () => void {
  const es = new EventSource(`${API}${streamUrl}`)
  es.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data) as StreamMsg
      onMsg(msg)
      if (msg.type === 'done') {
        es.close()
        onDone()
      }
      if (msg.type === 'error') {
        es.close()
        onError(new Error(msg.message || 'run failed'))
      }
    } catch (e) {
      es.close()
      onError(e instanceof Error ? e : new Error(String(e)))
    }
  }
  es.onerror = () => {
    es.close()
    onDone()
  }
  return () => es.close()
}

export async function getCase(caseId: string): Promise<CaseResult> {
  for (let i = 0; i < 60; i++) {
    const r = await fetch(`${API}/api/cases/${caseId}`)
    if (r.ok) return r.json()
    await new Promise((res) => setTimeout(res, 400))
  }
  throw new Error('Case result not ready')
}

export async function submitDecision(
  caseId: string,
  body: { action: string; reviewer: string; note: string },
): Promise<CaseResult> {
  const r = await fetch(`${API}/api/cases/${caseId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const j = await r.json()
  if (!r.ok) throw new Error(j.detail || 'Decision failed')
  return j
}
