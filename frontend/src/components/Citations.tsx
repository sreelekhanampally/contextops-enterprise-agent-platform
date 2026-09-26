import { FileText } from 'lucide-react'
import type { Citation } from '../types/api'

export function Citations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null

  return (
    <section className="panel citations-panel">
      <div className="panel-title">Grounding sources</div>
      <div className="citation-grid">
        {citations.map((citation) => (
          <article className="citation" key={citation.chunk_id}>
            <div className="citation-head">
              <FileText size={15} />
              <strong>{citation.source}</strong>
            </div>
            <p>{citation.excerpt}</p>
            {typeof citation.score === 'number' && (
              <span className="score">relevance {Math.round(citation.score * 100)}%</span>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}
