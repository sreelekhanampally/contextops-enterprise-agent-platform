import { FormEvent, KeyboardEvent, useRef, useState } from 'react'
import {
  Activity,
  Bot,
  CheckCircle2,
  Database,
  FileUp,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { ActionCard } from './components/ActionCard'
import { Citations } from './components/Citations'
import { TracePanel } from './components/TracePanel'
import { SQLResultPanel } from './components/SQLResultPanel'
import { ingestDocument, sendChat } from './lib/api'
import type { ChatResponse, Route } from './types/api'
import './styles.css'

const examples = [
  'How many annual leave days do employees receive?',
  'Which department has the highest number of open tickets?',
  'Compare our incident-response policy with the current unresolved incidents.',
  'Create a high-priority incident for a production database outage assigned to Platform Engineering.',
]

const routeLabels: Record<Route, string> = {
  retrieval: 'Knowledge retrieval',
  sql: 'SQL analytics',
  hybrid: 'Hybrid analysis',
  reasoning: 'Reasoning',
  action: 'Controlled action',
}

export default function App() {
  const [input, setInput] = useState('')
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [uploadMessage, setUploadMessage] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  async function submit(e?: FormEvent) {
    e?.preventDefault()
    if (!input.trim() || loading) return

    setLoading(true)
    setError('')
    try {
      setResponse(await sendChat(input.trim()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault()
      void submit()
    }
  }

  async function upload(file?: File) {
    if (!file) return

    setUploadMessage(`Indexing ${file.name}…`)
    try {
      const result = await ingestDocument(file)
      setUploadMessage(`${result.filename} · ${result.chunks_created} chunks indexed`)
    } catch (err) {
      setUploadMessage(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand">
            <div className="brand-mark"><Sparkles size={18} /></div>
            <div>
              <strong>ContextOps</strong>
              <span>Knowledge & Action Platform</span>
            </div>
          </div>

          <p className="sidebar-copy">
            A traceable enterprise workflow for grounded knowledge retrieval,
            operational analytics, and approval-gated actions.
          </p>

          <div className="capabilities">
            <div><Bot size={17} /><span><strong>LangGraph</strong> workflow routing</span></div>
            <div><Database size={17} /><span><strong>pgvector</strong> + PostgreSQL evidence</span></div>
            <div><ShieldCheck size={17} /><span><strong>Guarded writes</strong> with human approval</span></div>
          </div>

          <button className="upload-button" onClick={() => fileRef.current?.click()}>
            <FileUp size={16} /> Add enterprise document
          </button>
          <input
            ref={fileRef}
            hidden
            type="file"
            accept=".pdf,.txt,.md"
            aria-label="Upload enterprise document"
            onChange={(e) => void upload(e.target.files?.[0])}
          />
          {uploadMessage && <div className="upload-message">{uploadMessage}</div>}
        </div>

        <div className="sidebar-footer">
          <div className="architecture-note">
            Generation is replaceable. MiniLM handles embeddings, pgvector handles retrieval,
            SQL is read-only, and writes require explicit approval.
          </div>
        </div>
      </aside>

      <main>
        <header className="hero">
          <span className="eyebrow">ENTERPRISE KNOWLEDGE OPERATIONS</span>
          <h1>One workspace for knowledge, analytics, and controlled actions.</h1>
          <p>
            ContextOps selects the appropriate specialist path, grounds responses in enterprise
            evidence, and exposes the workflow instead of hiding it behind a single chat response.
          </p>

          <div className="trust-row" aria-label="ContextOps safeguards">
            <span><CheckCircle2 size={14} /> Local embeddings</span>
            <span><CheckCircle2 size={14} /> Read-only SQL</span>
            <span><CheckCircle2 size={14} /> Human-approved writes</span>
          </div>
        </header>

        <section className="examples" aria-label="Example requests">
          {examples.map((example) => (
            <button key={example} onClick={() => setInput(example)}>{example}</button>
          ))}
        </section>

        <form className="composer" onSubmit={submit}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleComposerKeyDown}
            placeholder="Ask about policy, query operations, or propose an incident…"
            rows={3}
            aria-label="Enterprise request"
          />
          <div className="composer-footer">
            <span className="keyboard-hint">Ctrl/⌘ + Enter to run</span>
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? <><Activity className="spin" size={16} /> Running workflow…</> : <><Send size={16} /> Run workflow</>}
            </button>
          </div>
        </form>

        {error && <div className="error" role="alert">{error}</div>}

        {!response && !loading && (
          <section className="welcome-grid">
            <article>
              <span className="welcome-icon"><Search size={17} /></span>
              <strong>Knowledge retrieval</strong>
              <p>Semantic search over indexed PDF, Markdown, and text evidence with citations.</p>
            </article>
            <article>
              <span className="welcome-icon"><Database size={17} /></span>
              <strong>Operational analytics</strong>
              <p>Natural-language questions become validated, read-only PostgreSQL queries.</p>
            </article>
            <article>
              <span className="welcome-icon"><ShieldCheck size={17} /></span>
              <strong>Controlled actions</strong>
              <p>Write intents become proposals first. A human must explicitly approve execution.</p>
            </article>
          </section>
        )}

        {loading && !response && (
          <section className="loading-card" aria-live="polite">
            <Activity className="spin" size={18} />
            <div><strong>Running ContextOps</strong><span>Routing the request and gathering evidence…</span></div>
          </section>
        )}

        {response && (
          <div className="result-grid">
            <section className="answer-card">
              <div className="answer-meta">
                <span className="route">{routeLabels[response.route]}</span>
                {response.validation && (
                  <span className={response.validation.grounded ? 'grounded' : 'ungrounded'}>
                    {response.validation.grounded ? 'Evidence check passed' : 'Needs review'} · {Math.round(response.validation.confidence * 100)}%
                  </span>
                )}
              </div>

              <div className="answer-text">{response.answer}</div>

              {response.validation?.notes && (
                <div className="validation-note">
                  <ShieldCheck size={15} />
                  <span>{response.validation.notes}</span>
                </div>
              )}

              {response.pending_action && <ActionCard action={response.pending_action} />}
            </section>

            <div className="inspector-grid">
              <TracePanel trace={response.trace} />
              <SQLResultPanel result={response.sql_result} />
            </div>

            <Citations citations={response.citations} />
          </div>
        )}
      </main>
    </div>
  )
}
