import { CheckCircle2, Link } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import type { GRConfirmResponse } from '../../types/gr'

interface Props {
  result: GRConfirmResponse | null
}

export function PostingResultCard({ result }: Props) {
  if (!result || result.status !== 'POSTED') return null

  return (
    <Card className="border-emerald-200 bg-emerald-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-emerald-700">
          <CheckCircle2 className="h-4 w-4" />
          Goods Receipt Posted
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-sm">
        <Row label="Material Document" value={result.material_document} />
        <Row label="Document Year" value={result.material_document_year} />
        <Row label="Message" value={result.message} />
        <div className="pt-2">
          <NavLink
            to={`/drafts/${result.request_id}`}
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <Link className="h-3 w-3" />
            View full draft details
          </NavLink>
        </div>
      </CardContent>
    </Card>
  )
}

function Row({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between gap-4 border-b last:border-0 py-1">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium font-mono">{value ?? '—'}</span>
    </div>
  )
}
