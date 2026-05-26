export type DraftStatus =
  | 'CREATED'
  | 'IMAGE_UPLOADED'
  | 'OCR_COMPLETED'
  | 'PARSING_COMPLETED'
  | 'NEEDS_CORRECTION'
  | 'VALIDATED'
  | 'READY_FOR_CONFIRMATION'
  | 'POSTING_IN_PROGRESS'
  | 'POSTED'
  | 'REJECTED'
  | 'FAILED'
  | 'BLOCKED'

export interface HealthResponse {
  status: string
  version?: string
  uptime_seconds?: number
}

export interface SapPingResponse {
  status: string
  sap_mode: string
  message?: string
}

export interface ValidationMessage {
  code: string
  severity: 'error' | 'warning' | 'info'
  message: string
  details?: Record<string, unknown> | null
}

export interface GRDraftParsedView {
  po_number?: string | null
  purchase_order_item?: string | null
  quantity?: number | null
  entry_unit?: string | null
  batch?: string | null
  serial_numbers?: string[]
  material_text_hint?: string | null
}

export interface GRMatchedPOItemView {
  purchase_order?: string | null
  purchase_order_item?: string | null
  material?: string | null
  description?: string | null
  plant?: string | null
  storage_location?: string | null
  open_quantity?: number | null
  unit?: string | null
}

export interface PurchaseOrderItem {
  purchase_order_item: string
  material: string
  description: string
  plant: string
  storage_location?: string | null
  order_quantity: number
  received_quantity: number
  open_quantity?: number | null
  unit: string
  batch_required?: boolean
  serial_required?: boolean
  deleted?: boolean
  delivery_completed?: boolean
}

export interface GRDraftResponse {
  request_id: string
  status: DraftStatus
  sap_mode: string
  ocr_text?: string | null
  parsed?: GRDraftParsedView | null
  matched_po_item?: GRMatchedPOItemView | null
  validation_messages?: ValidationMessage[]
  candidate_items?: PurchaseOrderItem[]
  requires_human_confirmation?: boolean
  can_post?: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface GRDraftPatchRequest {
  po_number?: string | null
  purchase_order_item?: string | null
  quantity?: number | null
  entry_unit?: string | null
  batch?: string | null
  serial_numbers?: string[] | null
  storage_location?: string | null
}

export interface GRConfirmRequest {
  confirmed_by: string
  posting_date?: string | null
  document_date?: string | null
}

export interface GRConfirmResponse {
  request_id: string
  status: string
  material_document?: string | null
  material_document_year?: string | null
  message: string
}

export interface GRRejectRequest {
  rejected_by: string
  reason: string
}

export interface AuditEvent {
  id: number
  request_id: string
  event_type: string
  actor_type: string
  actor_id?: string | null
  payload?: Record<string, unknown>
  created_at: string
}

export type AuditTrailResponse = AuditEvent[]

export interface LocalDraftSummary {
  request_id: string
  status: DraftStatus
  po_number?: string | null
  material_document?: string | null
  material_document_year?: string | null
  created_at?: string | null
  updated_at?: string | null
}
