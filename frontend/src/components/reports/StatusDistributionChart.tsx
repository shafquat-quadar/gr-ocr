import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import type { LocalDraftSummary } from '../../types/gr'

const COLORS: Record<string, string> = {
  POSTED: '#10b981',
  READY_FOR_CONFIRMATION: '#3b82f6',
  VALIDATED: '#6366f1',
  NEEDS_CORRECTION: '#f59e0b',
  BLOCKED: '#ef4444',
  FAILED: '#dc2626',
  REJECTED: '#94a3b8',
  CREATED: '#cbd5e1',
  IMAGE_UPLOADED: '#cbd5e1',
  OCR_COMPLETED: '#94a3b8',
  PARSING_COMPLETED: '#94a3b8',
  POSTING_IN_PROGRESS: '#8b5cf6',
}

export function StatusDistributionChart({ drafts }: { drafts: LocalDraftSummary[] }) {
  const counts: Record<string, number> = {}
  for (const d of drafts) {
    counts[d.status] = (counts[d.status] ?? 0) + 1
  }
  const data = Object.entries(counts).map(([name, value]) => ({ name, value }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Status Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8 text-center">No data</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={false}>
                {data.map((entry) => (
                  <Cell key={entry.name} fill={COLORS[entry.name] ?? '#cbd5e1'} />
                ))}
              </Pie>
              <Tooltip />
              <Legend
                formatter={(value) => <span className="text-xs">{value}</span>}
                iconSize={10}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
