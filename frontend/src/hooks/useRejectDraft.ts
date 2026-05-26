import { useMutation, useQueryClient } from '@tanstack/react-query'
import { rejectGrDraft } from '../api/grApi'
import { upsertLocalDraft } from '../lib/localDraftStore'
import type { GRRejectRequest } from '../types/gr'

export function useRejectDraft(requestId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: GRRejectRequest) => rejectGrDraft(requestId, payload),
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
