import { useQuery } from '@tanstack/react-query'
import { health } from '../api/grApi'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: health,
    refetchInterval: 30_000,
    retry: 1,
  })
}
