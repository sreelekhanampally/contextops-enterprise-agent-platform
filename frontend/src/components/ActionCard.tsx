import { AlertTriangle, Check, X } from 'lucide-react'
import { useState } from 'react'
import { resolveAction } from '../lib/api'
import type { PendingAction } from '../types/api'

export function ActionCard({ action }: { action: PendingAction }) {
  const [status, setStatus] = useState(action.status)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  async function decide(decision: 'approve' | 'reject') {
    setBusy(true)
    try {
      const result = await resolveAction(action.id, decision)
      setStatus(result.status as PendingAction['status'])
      setMessage(result.created_incident_id ? `Incident created: ${result.created_incident_id}` : 'Action rejected. No incident was created.')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="action-card">
      <div className="action-title"><AlertTriangle size={18} /> Human approval required</div>
      <div className="action-grid">
        <span>Title</span><strong>{action.payload.title}</strong>
        <span>Priority</span><strong>{action.payload.priority}</strong>
        <span>Team</span><strong>{action.payload.team}</strong>
        <span>Description</span><strong>{action.payload.description}</strong>
      </div>
      {status === 'pending' ? (
        <div className="action-buttons">
          <button disabled={busy} className="approve" onClick={() => decide('approve')}><Check size={15} /> Approve</button>
          <button disabled={busy} className="reject" onClick={() => decide('reject')}><X size={15} /> Reject</button>
        </div>
      ) : <div className={`action-status ${status}`}>{status.toUpperCase()}</div>}
      {message && <p className="action-message">{message}</p>}
    </section>
  )
}
