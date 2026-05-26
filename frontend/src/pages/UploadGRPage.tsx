import { useState } from 'react'
import { CheckCircle2, Send, XCircle } from 'lucide-react'
import { ImageUploadCard } from '../components/gr/ImageUploadCard'
import { ImagePreviewCard } from '../components/gr/ImagePreviewCard'
import { OcrTextCard } from '../components/gr/OcrTextCard'
import { ParsedFieldsForm } from '../components/gr/ParsedFieldsForm'
import { ValidationMessages } from '../components/gr/ValidationMessages'
import { MatchedPoItemCard } from '../components/gr/MatchedPoItemCard'
import { ConfirmPostDialog } from '../components/gr/ConfirmPostDialog'
import { PostingResultCard } from '../components/gr/PostingResultCard'
import { StatusBadge } from '../components/gr/StatusBadge'
import { Button } from '../components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert'
import { Separator } from '../components/ui/separator'
import { useCreateGrDraft } from '../hooks/useCreateGrDraft'
import { usePatchDraft } from '../hooks/usePatchDraft'
import { useValidateDraft } from '../hooks/useValidateDraft'
import { useConfirmDraft } from '../hooks/useConfirmDraft'
import { useRejectDraft } from '../hooks/useRejectDraft'
import type { GRDraftResponse, GRConfirmResponse, GRDraftPatchRequest } from '../types/gr'

export default function UploadGRPage() {
  const [file, setFile] = useState<File | null>(null)
  const [draft, setDraft] = useState<GRDraftResponse | null>(null)
  const [confirmResult, setConfirmResult] = useState<GRConfirmResponse | null>(null)
  const [globalError, setGlobalError] = useState<string | null>(null)

  const createMutation = useCreateGrDraft()
  const patchMutation = usePatchDraft(draft?.request_id ?? '')
  const validateMutation = useValidateDraft(draft?.request_id ?? '')
  const confirmMutation = useConfirmDraft(draft?.request_id ?? '')
  const rejectMutation = useRejectDraft(draft?.request_id ?? '')

  const isPosted = draft?.status === 'POSTED'
  const isRejected = draft?.status === 'REJECTED'
  const isDone = isPosted || isRejected
  const canConfirm = draft?.can_post || draft?.status === 'READY_FOR_CONFIRMATION' || draft?.status === 'VALIDATED'
  const canReject = draft && !isDone

  async function handleCreate() {
    if (!file) return
    setGlobalError(null)
    try {
      const result = await createMutation.mutateAsync({ file })
      setDraft(result)
    } catch (e) {
      setGlobalError((e as Error).message)
    }
  }

  async function handlePatch(patch: GRDraftPatchRequest) {
    setGlobalError(null)
    try {
      const result = await patchMutation.mutateAsync(patch)
      setDraft(result)
    } catch (e) {
      setGlobalError((e as Error).message)
    }
  }

  async function handleValidate() {
    setGlobalError(null)
    try {
      const result = await validateMutation.mutateAsync()
      setDraft(result)
    } catch (e) {
      setGlobalError((e as Error).message)
    }
  }

  async function handleConfirm(req: Parameters<typeof confirmMutation.mutateAsync>[0]) {
    setGlobalError(null)
    try {
      const result = await confirmMutation.mutateAsync(req)
      setConfirmResult(result)
      // Refresh draft status
      setDraft((prev) => prev ? { ...prev, status: result.status as GRDraftResponse['status'] } : prev)
    } catch (e) {
      setGlobalError((e as Error).message)
    }
  }

  async function handleReject() {
    setGlobalError(null)
    const reason = prompt('Enter rejection reason:')
    if (reason === null) return
    try {
      const result = await rejectMutation.mutateAsync({ rejected_by: 'ui-user', reason })
      setDraft(result)
    } catch (e) {
      setGlobalError((e as Error).message)
    }
  }

  const isCreating = createMutation.isPending

  return (
    <div className="space-y-4 max-w-5xl">
      <div>
        <h1 className="text-xl font-semibold">Upload Package Label</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Upload a package/label image to begin the goods receipt process.
        </p>
      </div>

      {globalError && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left column */}
        <div className="space-y-4">
          <ImageUploadCard
            onFileSelected={setFile}
            selectedFile={file}
            onClear={() => { setFile(null); setDraft(null); setConfirmResult(null) }}
          />
          <ImagePreviewCard file={file} />

          {!draft && (
            <Button
              onClick={handleCreate}
              loading={isCreating}
              disabled={!file || isCreating}
              className="w-full"
            >
              <Send className="h-4 w-4" />
              Create GR Draft
            </Button>
          )}

          {draft && (
            <div className="flex items-center gap-2 rounded-md border px-4 py-2.5 bg-card">
              <span className="text-xs text-muted-foreground">Status</span>
              <StatusBadge status={draft.status} />
              <span className="text-xs font-mono text-muted-foreground ml-auto">{draft.request_id}</span>
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-4">
          <OcrTextCard ocrText={draft?.ocr_text} loading={isCreating} />

          {draft && (
            <>
              {(draft.validation_messages?.length ?? 0) > 0 && (
                <ValidationMessages messages={draft.validation_messages ?? []} />
              )}

              <ParsedFieldsForm
                draft={draft}
                onSave={handlePatch}
                onValidate={handleValidate}
                saving={patchMutation.isPending}
                validating={validateMutation.isPending}
                readOnly={isDone}
              />

              <MatchedPoItemCard
                matched={draft.matched_po_item}
                candidates={draft.candidate_items}
              />
            </>
          )}
        </div>
      </div>

      {draft && !isDone && (
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
              <Button
                variant="outline"
                onClick={handleReject}
                loading={rejectMutation.isPending}
              >
                <XCircle className="h-4 w-4" />
                Reject Draft
              </Button>
            )}
          </div>
        </>
      )}

      {confirmResult && <PostingResultCard result={confirmResult} />}
    </div>
  )
}
