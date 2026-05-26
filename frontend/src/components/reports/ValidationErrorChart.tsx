import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import type { LocalDraftSummary, DraftStatus } from '../../types/gr'

const EXCEPTION_STATUSES: DraftStatus[] = ['NEEDS_CORRECTION', 'BLOCKED', 'FAILED', 'REJECTED']

export function ValidationErrorChart({ drafts }: { drafts: LocalDraftSummary[] }) {
  const counts: Record<string, number> = {}
  for (const d of drafts) {
    if (EXCEPTION_STATUSES.includes(d.status)) {
      counts[d.status] = (counts[d.status] ?? 0) + 1
    }
  }

  const data = Object.entries(counts).map(([status, count]) => ({ status, count }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Exception Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8 text-center">No exceptions</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} layout="vertical" margin={{ top: 4, right: 4, left: 40, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fontSize: 10 }} allowDecimals={false} />
              <YAxis type="category" dataKey="status" tick={{ fontSize: 10 }} width={80} />
              <Tooltip />
              <Bar dataKey="count" fill="#f59e0b" radius={[0, 3, 3, 0]} name="Count" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
