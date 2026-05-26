import { useMutation, useQueryClient } from '@tanstack/react-query'
import { confirmGrDraft } from '../api/grApi'
import { upsertLocalDraft } from '../lib/localDraftStore'
import type { GRConfirmRequest } from '../types/gr'

export function useConfirmDraft(requestId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: GRConfirmRequest) => confirmGrDraft(requestId, payload),
    onSuccess: (data) => {
      upsertLocalDraft({
        request_id: data.request_id,
        status: data.status as import('../types/gr').DraftStatus,
        po_number: null,
        material_document: data.material_document ?? null,
        material_document_year: data.material_document_year ?? null,
        created_at: null,
        updated_at: new Date().toISOString(),
      })
      qc.invalidateQueries({ queryKey: ['gr-draft', requestId] })
    },
  })
}
