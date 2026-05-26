import { useQuery } from '@tanstack/react-query'
import { sapPing } from '../api/grApi'

export function useSapPing() {
  return useQuery({
    queryKey: ['sap-ping'],
    queryFn: sapPing,
    refetchInterval: 60_000,
    retry: 1,
  })
}
