import { useQuery } from '@tanstack/react-query'
import { getAuditTrail } from '../api/grApi'

export function useAuditTrail(requestId: string | undefined) {
  return useQuery({
    queryKey: ['audit', requestId],
    queryFn: () => getAuditTrail(requestId!),
    enabled: !!requestId,
    retry: 1,
  })
}
