import { Badge } from '../ui/badge'
import type { DraftStatus } from '../../types/gr'
import type { BadgeProps } from '../ui/badge'

const STATUS_CONFIG: Record<DraftStatus, { label: string; variant: BadgeProps['variant'] }> = {
  CREATED: { label: 'Created', variant: 'secondary' },
  IMAGE_UPLOADED: { label: 'Image Uploaded', variant: 'secondary' },
  OCR_COMPLETED: { label: 'OCR Completed', variant: 'default' },
  PARSING_COMPLETED: { label: 'Parsing Completed', variant: 'default' },
  NEEDS_CORRECTION: { label: 'Needs Correction', variant: 'warning' },
  VALIDATED: { label: 'Validated', variant: 'default' },
  READY_FOR_CONFIRMATION: { label: 'Ready for Confirmation', variant: 'success' },
  POSTING_IN_PROGRESS: { label: 'Posting…', variant: 'default' },
  POSTED: { label: 'Posted', variant: 'success' },
  REJECTED: { label: 'Rejected', variant: 'secondary' },
  FAILED: { label: 'Failed', variant: 'destructive' },
  BLOCKED: { label: 'Blocked', variant: 'destructive' },
}

export function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status as DraftStatus] ?? { label: status, variant: 'secondary' as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}
