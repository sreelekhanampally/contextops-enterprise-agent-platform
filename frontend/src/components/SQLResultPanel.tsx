import { Database } from 'lucide-react'

interface SQLResult {
  sql: string
  columns: string[]
  rows: Record<string, unknown>[]
  explanation: string
}

export function SQLResultPanel({ result }: { result?: SQLResult | null }) {
  if (!result) return null
  return (
    <section className="panel sql-panel">
      <div className="panel-title"><Database size={16} /> Structured-data evidence</div>
      {result.explanation && <p className="sql-explanation">{result.explanation}</p>}
      <pre className="sql-query"><code>{result.sql}</code></pre>
      {result.rows.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead><tr>{result.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
            <tbody>
              {result.rows.map((row, index) => (
                <tr key={index}>{result.columns.map((column) => <td key={column}>{String(row[column] ?? '')}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <p className="empty-result">The validated query returned no rows.</p>}
    </section>
  )
}
