import type { ChatResponse } from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(body.detail || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function sendChat(message: string): Promise<ChatResponse> {
  return parse<ChatResponse>(await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  }))
}

export async function ingestDocument(file: File): Promise<{ document_id: string; filename: string; chunks_created: number }> {
  const form = new FormData()
  form.append('file', file)
  return parse(await fetch(`${API_BASE}/documents/ingest`, { method: 'POST', body: form }))
}

export async function resolveAction(actionId: string, decision: 'approve' | 'reject') {
  return parse<{ action_id: string; status: string; created_incident_id?: string }>(
    await fetch(`${API_BASE}/actions/${actionId}/${decision}`, { method: 'POST' })
  )
}
