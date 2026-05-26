import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger,
} from '../ui/dialog'
import { Button } from '../ui/button'
import { Label } from '../ui/label'
import { Input } from '../ui/input'
import type { GRDraftResponse, GRConfirmRequest } from '../../types/gr'

interface Props {
  draft: GRDraftResponse
  onConfirm: (req: GRConfirmRequest) => Promise<void>
  loading?: boolean
  trigger: React.ReactNode
}

export function ConfirmPostDialog({ draft, onConfirm, loading, trigger }: Props) {
  const [open, setOpen] = useState(false)
  const [confirmedBy, setConfirmedBy] = useState('')
  const [postingDate, setPostingDate] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleConfirm() {
    if (!confirmedBy.trim()) { setError('Please enter your name or user ID.'); return }
    setError(null)
    await onConfirm({
      confirmed_by: confirmedBy.trim(),
      posting_date: postingDate || null,
    })
    setOpen(false)
  }

  const m = draft.matched_po_item
  const p = draft.parsed

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Confirm Goods Receipt Posting</DialogTitle>
          <DialogDescription>
            Review the details carefully before posting.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-md border bg-amber-50 border-amber-200 px-3 py-2 flex items-start gap-2 text-sm text-amber-800">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>
            This will post a goods receipt in <strong>SAP / mock SAP</strong> after confirmation. This action cannot be undone.
          </span>
        </div>

        <div className="space-y-1 text-sm">
          <Row label="PO Number" value={m?.purchase_order ?? p?.po_number} />
          <Row label="PO Item" value={m?.purchase_order_item ?? p?.purchase_order_item} />
          <Row label="Quantity" value={p?.quantity != null ? `${p.quantity} ${p.entry_unit ?? ''}` : null} />
          <Row label="Batch" value={p?.batch} />
          <Row label="Material" value={m?.material} />
          <Row label="SAP Mode" value={draft.sap_mode?.toUpperCase()} />
        </div>

        <div className="space-y-2">
          <div>
            <Label className="mb-1.5 block">Confirmed By *</Label>
            <Input
              placeholder="your.name@example.com"
              value={confirmedBy}
              onChange={(e) => setConfirmedBy(e.target.value)}
            />
          </div>
          <div>
            <Label className="mb-1.5 block">Posting Date (optional)</Label>
            <Input
              type="date"
              value={postingDate}
              onChange={(e) => setPostingDate(e.target.value)}
            />
          </div>
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleConfirm} loading={loading} variant="default">
            Post Goods Receipt
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Row({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="flex justify-between gap-4 border-b py-1 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value ?? '—'}</span>
    </div>
  )
}
