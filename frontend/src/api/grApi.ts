import { apiClient } from './client'
import type {
  HealthResponse,
  SapPingResponse,
  GRDraftResponse,
  GRDraftPatchRequest,
  GRConfirmRequest,
  GRConfirmResponse,
  GRRejectRequest,
  AuditTrailResponse,
} from '../types/gr'

export async function health(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}

export async function sapPing(): Promise<SapPingResponse> {
  const { data } = await apiClient.get<SapPingResponse>('/api/v1/sap/ping')
  return data
}

export async function createGrDraft(params: {
  file: File
  createdBy?: string
  plantHint?: string
  storageLocationHint?: string
}): Promise<GRDraftResponse> {
  const form = new FormData()
  form.append('file', params.file)
  if (params.createdBy) form.append('created_by', params.createdBy)
  if (params.plantHint) form.append('plant_hint', params.plantHint)
  if (params.storageLocationHint) form.append('storage_location_hint', params.storageLocationHint)

  const { data } = await apiClient.post<GRDraftResponse>('/api/v1/gr/drafts', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getGrDraft(requestId: string): Promise<GRDraftResponse> {
  const { data } = await apiClient.get<GRDraftResponse>(`/api/v1/gr/drafts/${requestId}`)
  return data
}

export async function patchGrDraft(requestId: string, payload: GRDraftPatchRequest): Promise<GRDraftResponse> {
  const { data } = await apiClient.patch<GRDraftResponse>(`/api/v1/gr/drafts/${requestId}`, payload)
  return data
}

export async function validateGrDraft(requestId: string): Promise<GRDraftResponse> {
  const { data } = await apiClient.post<GRDraftResponse>(`/api/v1/gr/drafts/${requestId}/validate`)
  return data
}

export async function confirmGrDraft(requestId: string, payload: GRConfirmRequest): Promise<GRConfirmResponse> {
  const { data } = await apiClient.post<GRConfirmResponse>(`/api/v1/gr/drafts/${requestId}/confirm`, payload)
  return data
}

export async function rejectGrDraft(requestId: string, payload: GRRejectRequest): Promise<GRDraftResponse> {
  const { data } = await apiClient.post<GRDraftResponse>(`/api/v1/gr/drafts/${requestId}/reject`, payload)
  return data
}

export async function getAuditTrail(requestId: string): Promise<AuditTrailResponse> {
  const { data } = await apiClient.get<AuditTrailResponse>(`/api/v1/gr/drafts/${requestId}/audit`)
  return data
}
