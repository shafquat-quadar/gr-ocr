import type { LocalDraftSummary, DraftStatus } from '../types/gr'

const STORAGE_KEY = 'gr-agent.localDrafts'

interface StorageShape {
  drafts: LocalDraftSummary[]
}

function load(): StorageShape {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { drafts: [] }
    const parsed = JSON.parse(raw) as unknown
    if (typeof parsed === 'object' && parsed !== null && Array.isArray((parsed as StorageShape).drafts)) {
      return parsed as StorageShape
    }
    return { drafts: [] }
  } catch {
    return { drafts: [] }
  }
}

function save(shape: StorageShape): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(shape))
  } catch {
    // quota exceeded or private mode — silently ignore
  }
}

export function getLocalDrafts(): LocalDraftSummary[] {
  return load().drafts
}

export function upsertLocalDraft(draft: LocalDraftSummary): void {
  const store = load()
  const idx = store.drafts.findIndex((d) => d.request_id === draft.request_id)
  if (idx >= 0) {
    store.drafts[idx] = draft
  } else {
    store.drafts.unshift(draft)
  }
  save(store)
}

export function removeLocalDraft(requestId: string): void {
  const store = load()
  store.drafts = store.drafts.filter((d) => d.request_id !== requestId)
  save(store)
}

export function getLocalDraftsByStatus(...statuses: DraftStatus[]): LocalDraftSummary[] {
  const set = new Set<string>(statuses)
  return load().drafts.filter((d) => set.has(d.status))
}
