import { NavLink } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Card, CardContent } from '../ui/card'
import { StatusBadge } from './StatusBadge'
import { formatDate } from '../../lib/utils'
import type { LocalDraftSummary } from '../../types/gr'

export function DraftSummaryCard({ draft }: { draft: LocalDraftSummary }) {
  return (
    <Card className="hover:border-primary/40 transition-colors">
      <CardContent className="flex items-center justify-between gap-4 py-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-medium">{draft.request_id}</span>
            <StatusBadge status={draft.status} />
          </div>
          <div className="mt-1 flex flex-wrap gap-x-3 text-xs text-muted-foreground">
            {draft.po_number && <span>PO {draft.po_number}</span>}
            {draft.material_document && <span>Doc {draft.material_document}</span>}
            <span>{formatDate(draft.updated_at ?? draft.created_at)}</span>
          </div>
        </div>
        <NavLink
          to={`/drafts/${draft.request_id}`}
          className="shrink-0 text-muted-foreground hover:text-primary transition-colors"
        >
          <ArrowRight className="h-4 w-4" />
        </NavLink>
      </CardContent>
    </Card>
  )
}
