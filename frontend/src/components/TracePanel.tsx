import { CheckCircle2, GitBranch, Search, ShieldCheck, Wrench } from 'lucide-react'
import type { TraceEvent } from '../types/api'

const icons = {
  supervisor: GitBranch,
  retrieval_agent: Search,
  sql_agent: Search,
  reasoning_agent: Wrench,
  action_agent: Wrench,
  validator_agent: ShieldCheck,
  repair_node: CheckCircle2,
}

export function TracePanel({ trace }: { trace: TraceEvent[] }) {
  if (!trace.length) return null

  return (
    <section className="panel trace-panel">
      <div className="panel-title">Workflow trace</div>
      <div className="trace-list">
        {trace.map((item, index) => {
          const Icon = icons[item.node as keyof typeof icons] || CheckCircle2
          return (
            <div className="trace-item" key={`${item.node}-${index}`}>
              <span className="trace-icon"><Icon size={15} /></span>
              <div>
                <strong>{item.node.replaceAll('_', ' ')}</strong>
                <p>{item.detail}</p>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
