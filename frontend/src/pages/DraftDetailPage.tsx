import { useParams, NavLink } from 'react-router-dom'
import { ArrowLeft, CheckCircle2, XCircle } from 'lucide-react'
import { useGrDraft } from '../hooks/useGrDraft'
import { useAuditTrail } from '../hooks/useAuditTrail'
import { usePatchDraft } from '../hooks/usePatchDraft'
import { useValidateDraft } from '../hooks/useValidateDraft'
import { useConfirmDraft } from '../hooks/useConfirmDraft'
import { useRejectDraft } from '../hooks/useRejectDraft'
import { OcrTextCard } from '../components/gr/OcrTextCard'
import { ParsedFieldsForm } from '../components/gr/ParsedFieldsForm'
import { ValidationMessages } from '../components/gr/ValidationMessages'
import { MatchedPoItemCard } from '../components/gr/MatchedPoItemCard'
import { ConfirmPostDialog } from '../components/gr/ConfirmPostDialog'
import { PostingResultCard } from '../components/gr/PostingResultCard'
import { AuditTimeline } from '../components/gr/AuditTimeline'
import { StatusBadge } from '../components/gr/StatusBadge'
import { Button } from '../components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert'
import { Skeleton } from '../components/ui/skeleton'
import { Separator } from '../components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import { formatDate } from '../lib/utils'
import { useState } from 'react'
import type { GRDraftPatchRequest, GRConfirmResponse } from '../types/gr'

export default function DraftDetailPage() {
  const { requestId } = useParams<{ requestId: string }>()
  const { data: draft, isLoading, isError, error, refetch } = useGrDraft(requestId)
  const { data: auditEvents = [], isLoading: auditLoading } = useAuditTrail(requestId)

  const patchMutation = usePatchDraft(requestId ?? '')
  const validateMutation = useValidateDraft(requestId ?? '')
  const confirmMutation = useConfirmDraft(requestId ?? '')
  const rejectMutation = useRejectDraft(requestId ?? '')

  const [actionError, setActionError] = useState<string | null>(null)
  const [confirmResult, setConfirmResult] = useState<GRConfirmResponse | null>(null)

  const isPosted = draft?.status === 'POSTED'
  const isRejected = draft?.status === 'REJECTED'
  const isDone = isPosted || isRejected
  const canConfirm = draft?.can_post || draft?.status === 'READY_FOR_CONFIRMATION' || draft?.status === 'VALIDATED'
  const canEdit = draft && !isDone
  const canReject = draft && !isDone

  async function handlePatch(patch: GRDraftPatchRequest) {
    setActionError(null)
    try { await patchMutation.mutateAsync(patch) } catch (e) { setActionError((e as Error).message) }
  }

  async function handleValidate() {
    setActionError(null)
    try { await validateMutation.mutateAsync() } catch (e) { setActionError((e as Error).message) }
  }

  async function handleConfirm(req: Parameters<typeof confirmMutation.mutateAsync>[0]) {
    setActionError(null)
    try {
      const result = await confirmMutation.mutateAsync(req)
      setConfirmResult(result)
      refetch()
    } catch (e) { setActionError((e as Error).message) }
  }

  async function handleReject() {
    setActionError(null)
    const reason = prompt('Enter rejection reason:')
    if (reason === null) return
    try { await rejectMutation.mutateAsync({ rejected_by: 'ui-user', reason }) } catch (e) { setActionError((e as Error).message) }
  }

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-4xl">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (isError || !draft) {
    return (
      <div className="max-w-2xl space-y-4">
        <NavLink to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </NavLink>
        <Alert variant="destructive">
          <AlertTitle>Draft Not Found</AlertTitle>
          <AlertDescription>{(error as Error)?.message ?? 'Could not load draft.'}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-4 max-w-5xl">
      <div className="flex items-start gap-3">
        <NavLink to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mt-1">
          <ArrowLeft className="h-4 w-4" />
        </NavLink>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold font-mono">{draft.request_id}</h1>
            <StatusBadge status={draft.status} />
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Created {formatDate(draft.created_at)} · Updated {formatDate(draft.updated_at)} · SAP: {draft.sap_mode?.toUpperCase()}
          </p>
        </div>
      </div>

      {actionError && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{actionError}</AlertDescription>
        </Alert>
      )}

      {confirmResult && <PostingResultCard result={confirmResult} />}

      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="audit">Audit Trail ({auditEvents.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="space-y-4 mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="space-y-4">
              <OcrTextCard ocrText={draft.ocr_text} />
              {(draft.validation_messages?.length ?? 0) > 0 && (
                <ValidationMessages messages={draft.validation_messages ?? []} />
              )}
            </div>
            <div className="space-y-4">
              <ParsedFieldsForm
                draft={draft}
                onSave={handlePatch}
                onValidate={handleValidate}
                saving={patchMutation.isPending}
                validating={validateMutation.isPending}
                readOnly={!canEdit}
              />
              <MatchedPoItemCard matched={draft.matched_po_item} candidates={draft.candidate_items} />
            </div>
          </div>

          {(canConfirm || canReject) && (
            <>
              <Separator />
              <div className="flex flex-wrap gap-2">
                {canConfirm && (
                  <ConfirmPostDialog
                    draft={draft}
                    onConfirm={handleConfirm}
                    loading={confirmMutation.isPending}
                    trigger={
                      <Button>
                        <CheckCircle2 className="h-4 w-4" />
                        Confirm &amp; Post GR
                      </Button>
                    }
                  />
                )}
                {canReject && (
                  <Button variant="outline" onClick={handleReject} loading={rejectMutation.isPending}>
                    <XCircle className="h-4 w-4" />
                    Reject Draft
                  </Button>
                )}
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          <AuditTimeline events={auditEvents} loading={auditLoading} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
