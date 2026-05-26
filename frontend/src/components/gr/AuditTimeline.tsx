import { useState } from 'react'
import { ChevronDown, ChevronRight, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Skeleton } from '../ui/skeleton'
import { formatDate } from '../../lib/utils'
import type { AuditEvent } from '../../types/gr'

interface Props {
  events: AuditEvent[]
  loading?: boolean
}

export function AuditTimeline({ events, loading }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-primary" />
          Audit Trail
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : events.length === 0 ? (
          <p className="text-sm text-muted-foreground">No audit events recorded yet.</p>
        ) : (
          <ol className="relative border-l border-border ml-3 space-y-0">
            {events.map((ev) => (
              <AuditItem key={ev.id} event={ev} />
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}

function AuditItem({ event: ev }: { event: AuditEvent }) {
  const [expanded, setExpanded] = useState(false)
  const hasPayload = ev.payload && Object.keys(ev.payload).length > 0

  return (
    <li className="ml-4 pb-4 last:pb-0">
      <div className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full border border-background bg-primary/60" />
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{ev.event_type}</p>
          <p className="text-xs text-muted-foreground">
            {ev.actor_type}{ev.actor_id ? ` · ${ev.actor_id}` : ''} · {formatDate(ev.created_at)}
          </p>
        </div>
        {hasPayload && (
          <button
            onClick={() => setExpanded((p) => !p)}
            className="shrink-0 text-muted-foreground hover:text-foreground mt-0.5"
          >
            {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>
        )}
      </div>
      {expanded && hasPayload && (
        <pre className="mt-2 text-xs font-mono bg-muted/50 rounded-md p-2 overflow-auto max-h-40 border">
          {JSON.stringify(ev.payload, null, 2)}
        </pre>
      )}
    </li>
  )
}
