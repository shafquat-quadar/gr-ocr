import { useEffect, useState } from 'react'
import { Save, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../ui/card'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Button } from '../ui/button'
import { Skeleton } from '../ui/skeleton'
import type { GRDraftResponse, GRDraftPatchRequest } from '../../types/gr'

interface Props {
  draft: GRDraftResponse
  loading?: boolean
  onSave: (patch: GRDraftPatchRequest) => Promise<void>
  onValidate: () => Promise<void>
  saving?: boolean
  validating?: boolean
  readOnly?: boolean
}

export function ParsedFieldsForm({ draft, loading, onSave, onValidate, saving, validating, readOnly }: Props) {
  const p = draft.parsed

  const [poNumber, setPoNumber] = useState(p?.po_number ?? '')
  const [poItem, setPoItem] = useState(p?.purchase_order_item ?? '')
  const [quantity, setQuantity] = useState(p?.quantity != null ? String(p.quantity) : '')
  const [unit, setUnit] = useState(p?.entry_unit ?? '')
  const [batch, setBatch] = useState(p?.batch ?? '')
  const [serials, setSerials] = useState((p?.serial_numbers ?? []).join(', '))
  const [storageLocation, setStorageLocation] = useState(draft.matched_po_item?.storage_location ?? '')

  useEffect(() => {
    setPoNumber(draft.parsed?.po_number ?? '')
    setPoItem(draft.parsed?.purchase_order_item ?? '')
    setQuantity(draft.parsed?.quantity != null ? String(draft.parsed.quantity) : '')
    setUnit(draft.parsed?.entry_unit ?? '')
    setBatch(draft.parsed?.batch ?? '')
    setSerials((draft.parsed?.serial_numbers ?? []).join(', '))
    setStorageLocation(draft.matched_po_item?.storage_location ?? '')
  }, [draft])

  async function handleSave() {
    const patch: GRDraftPatchRequest = {}
    if (poNumber !== (p?.po_number ?? '')) patch.po_number = poNumber || null
    if (poItem !== (p?.purchase_order_item ?? '')) patch.purchase_order_item = poItem || null
    const qty = parseFloat(quantity)
    if (!isNaN(qty) && qty !== p?.quantity) patch.quantity = qty
    if (unit !== (p?.entry_unit ?? '')) patch.entry_unit = unit || null
    if (batch !== (p?.batch ?? '')) patch.batch = batch || null
    const snList = serials.split(',').map((s) => s.trim()).filter(Boolean)
    if (JSON.stringify(snList) !== JSON.stringify(p?.serial_numbers ?? [])) patch.serial_numbers = snList
    if (storageLocation !== (draft.matched_po_item?.storage_location ?? '')) patch.storage_location = storageLocation || null
    await onSave(patch)
  }

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Parsed Fields</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parsed Fields</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Field label="PO Number" value={poNumber} onChange={setPoNumber} readOnly={readOnly} />
        <Field label="PO Item" value={poItem} onChange={setPoItem} readOnly={readOnly} />
        <Field label="Quantity" value={quantity} onChange={setQuantity} type="number" readOnly={readOnly} />
        <Field label="Unit" value={unit} onChange={setUnit} readOnly={readOnly} />
        <Field label="Batch / Lot" value={batch} onChange={setBatch} readOnly={readOnly} />
        <Field label="Storage Location" value={storageLocation} onChange={setStorageLocation} readOnly={readOnly} />
        <div className="sm:col-span-2">
          <Label className="mb-1.5 block">Serial Numbers (comma-separated)</Label>
          <Input
            value={serials}
            onChange={(e) => setSerials(e.target.value)}
            placeholder="SN10001, SN10002"
            readOnly={readOnly}
            disabled={readOnly}
          />
        </div>
        {draft.parsed?.material_text_hint && (
          <div className="sm:col-span-2">
            <Label className="mb-1.5 block text-muted-foreground">Material Hint (read-only)</Label>
            <p className="text-sm text-muted-foreground border rounded-md px-3 py-2 bg-muted/30">
              {draft.parsed.material_text_hint}
            </p>
          </div>
        )}
      </CardContent>
      {!readOnly && (
        <CardFooter className="gap-2">
          <Button onClick={handleSave} loading={saving} size="sm">
            <Save className="h-3.5 w-3.5" />
            Save Corrections
          </Button>
          <Button onClick={onValidate} loading={validating} variant="outline" size="sm">
            <RefreshCw className="h-3.5 w-3.5" />
            Revalidate
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}

function Field({
  label, value, onChange, type, readOnly,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  readOnly?: boolean
}) {
  return (
    <div>
      <Label className="mb-1.5 block">{label}</Label>
      <Input
        type={type ?? 'text'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={readOnly}
        disabled={readOnly}
        className={readOnly ? 'bg-muted/30 cursor-default' : ''}
      />
    </div>
  )
}
