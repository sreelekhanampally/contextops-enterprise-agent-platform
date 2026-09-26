export type Route = 'retrieval' | 'sql' | 'hybrid' | 'reasoning' | 'action'

export interface Citation {
  source: string
  chunk_id: string
  excerpt: string
  score?: number | null
}

export interface TraceEvent {
  node: string
  detail: string
}

export interface ValidationResult {
  grounded: boolean
  confidence: number
  notes: string
  unsupported_claims: string[]
}

export interface PendingAction {
  id: string
  action_type: 'create_incident'
  payload: {
    title: string
    description: string
    priority: string
    team: string
  }
  status: 'pending' | 'approved' | 'rejected'
}

export interface ChatResponse {
  answer: string
  route: Route
  citations: Citation[]
  trace: TraceEvent[]
  sql_result?: {
    sql: string
    columns: string[]
    rows: Record<string, unknown>[]
    explanation: string
  } | null
  validation?: ValidationResult | null
  pending_action?: PendingAction | null
}
