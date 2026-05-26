import { useQuery } from '@tanstack/react-query'
import { getGrDraft } from '../api/grApi'

export function useGrDraft(requestId: string | undefined) {
  return useQuery({
    queryKey: ['gr-draft', requestId],
    queryFn: () => getGrDraft(requestId!),
    enabled: !!requestId,
    retry: 1,
  })
}
