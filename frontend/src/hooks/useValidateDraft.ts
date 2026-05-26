import { useMutation, useQueryClient } from '@tanstack/react-query'
import { validateGrDraft } from '../api/grApi'
import { upsertLocalDraft } from '../lib/localDraftStore'

export function useValidateDraft(requestId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => validateGrDraft(requestId),
    onSuccess: (data) => {
      upsertLocalDraft({
        request_id: data.request_id,
        status: data.status,
        po_number: data.parsed?.po_number ?? null,
        material_document: null,
        created_at: data.created_at ?? null,
        updated_at: data.updated_at ?? null,
      })
      qc.setQueryData(['gr-draft', requestId], data)
    },
  })
}
