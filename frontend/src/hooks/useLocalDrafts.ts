import { useState, useEffect, useCallback } from 'react'
import { getLocalDrafts, getLocalDraftsByStatus } from '../lib/localDraftStore'
import type { LocalDraftSummary, DraftStatus } from '../types/gr'

export function useLocalDrafts(...statuses: DraftStatus[]) {
  const [drafts, setDrafts] = useState<LocalDraftSummary[]>([])

  const refresh = useCallback(() => {
    if (statuses.length > 0) {
      setDrafts(getLocalDraftsByStatus(...statuses))
    } else {
      setDrafts(getLocalDrafts())
    }
  }, [JSON.stringify(statuses)]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    refresh()

    const onStorage = (e: StorageEvent) => {
      if (e.key === 'gr-agent.localDrafts') refresh()
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [refresh])

  return { drafts, refresh }
}
