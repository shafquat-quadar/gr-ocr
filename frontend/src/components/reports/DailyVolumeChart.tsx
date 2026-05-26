import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import type { LocalDraftSummary } from '../../types/gr'

export function DailyVolumeChart({ drafts }: { drafts: LocalDraftSummary[] }) {
  const byDay: Record<string, number> = {}
  for (const d of drafts) {
    const day = d.created_at ? new Date(d.created_at).toLocaleDateString() : 'Unknown'
    byDay[day] = (byDay[day] ?? 0) + 1
  }

  const data = Object.entries(byDay)
    .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime())
    .map(([date, count]) => ({ date, count }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Daily GR Volume</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8 text-center">No data</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[3, 3, 0, 0]} name="Drafts" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
