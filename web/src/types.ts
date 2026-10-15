export type AgentKey = 'intake' | 'pa' | 'cds' | 'human'
export type AgentStatus = 'idle' | 'working' | 'done' | 'waiting' | 'halted' | 'skipped'

export type StreamMsg = {
  type: string
  contextId?: string
  traceId?: string
  agentState?: Partial<Record<AgentKey, AgentStatus>>
  event?: TimelineEvent
  tool?: ToolCall
  a2a?: A2AMessage
  intake?: unknown
  pol?: PolicyResult
  cds?: CdsResult
  faults?: Fault[]
  result?: CaseResult
  steps?: number
  tokens?: number
  audit?: unknown
  awaitingHuman?: boolean
  message?: string
  caseId?: string
}

export type TimelineEvent = {
  seq: number
  kind: string
  agent: string
  title: string
  ts: string
  simStartMs: number
  durMs: number
  detail?: string
}

export type ToolCall = {
  agent: string
  server: string
  tool: string
  attempt: number
  error?: boolean
  req: unknown
  res: unknown
  dur: number
}

export type A2AMessage = {
  from: string
  to: string
  msg: unknown
  resp: unknown
}

export type PolicyResult = {
  outcome?: string
  reason?: string
  crit?: Array<{ id: string; text: string; sec: string; st: string; ev: string }>
  policy?: { id: string; title: string; version: string; effective: string } | null
}

export type CdsResult = {
  recs?: Array<{ t: string; conf: number; cite: string[] }>
  risks?: string[]
  grounding?: { claims: number; cited: number; unsupported: number }
}

export type Fault = {
  type: string
  component: string
  handling: string
  recovered: boolean
  escalated: boolean
}

export type CaseResult = {
  contextId: string
  traceId: string
  events: TimelineEvent[]
  tools: ToolCall[]
  a2a: A2AMessage[]
  agent: Record<AgentKey, AgentStatus>
  intake?: unknown
  pol?: PolicyResult
  cds?: CdsResult
  faults?: Fault[]
  tokens?: number
  awaitingHuman?: boolean
  decision?: { action: string; label: string; reviewer: string; note?: string }
}

export type CaseForm = {
  patient: string
  dob: string
  member: string
  payer: string
  cpt: string
  icd: string
  note: string
  fault: string
}

export type Health = {
  ok: boolean
  model: string
  demoMode: boolean
  hasApiKey: boolean
  project: string
  ports: { api: number; mcp: number }
}
