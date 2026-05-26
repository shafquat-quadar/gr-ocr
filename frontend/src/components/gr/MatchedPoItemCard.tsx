import { Link2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import type { GRMatchedPOItemView, PurchaseOrderItem } from '../../types/gr'

interface Props {
  matched?: GRMatchedPOItemView | null
  candidates?: PurchaseOrderItem[]
}

function Row({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="flex justify-between gap-4 text-sm py-1 border-b last:border-0">
      <span className="text-muted-foreground shrink-0">{label}</span>
      <span className="font-medium text-right">{value ?? '—'}</span>
    </div>
  )
}

export function MatchedPoItemCard({ matched, candidates }: Props) {
  if (!matched && (!candidates || candidates.length === 0)) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link2 className="h-4 w-4 text-primary" />
          Matched PO Item
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {matched ? (
          <div>
            <Row label="Purchase Order" value={matched.purchase_order} />
            <Row label="Item" value={matched.purchase_order_item} />
            <Row label="Material" value={matched.material} />
            <Row label="Description" value={matched.description} />
            <Row label="Plant" value={matched.plant} />
            <Row label="Storage Location" value={matched.storage_location} />
            <Row label="Open Quantity" value={matched.open_quantity != null ? `${matched.open_quantity} ${matched.unit ?? ''}` : null} />
          </div>
        ) : null}

        {candidates && candidates.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">
              {matched ? 'Other Candidates' : 'Candidate Items — select the correct PO item'}
            </p>
            <div className="space-y-1">
              {candidates.map((c) => (
                <div key={c.purchase_order_item} className="rounded-md border px-3 py-2 text-xs">
                  <span className="font-mono font-medium">{c.purchase_order_item}</span>{' '}
                  <span className="text-muted-foreground">— {c.description}</span>{' '}
                  <span>({c.open_quantity ?? '?'} {c.unit} open)</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
