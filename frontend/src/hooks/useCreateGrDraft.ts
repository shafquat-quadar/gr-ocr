import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createGrDraft } from '../api/grApi'
import { upsertLocalDraft } from '../lib/localDraftStore'

export function useCreateGrDraft() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createGrDraft,
    onSuccess: (data) => {
      upsertLocalDraft({
        request_id: data.request_id,
        status: data.status,
        po_number: data.parsed?.po_number ?? null,
        material_document: null,
        created_at: data.created_at ?? null,
        updated_at: data.updated_at ?? null,
      })
      qc.setQueryData(['gr-draft', data.request_id], data)
    },
  })
}
