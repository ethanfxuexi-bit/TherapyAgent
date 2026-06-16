import { auth } from './firebase'
import type {
  HistoryEntry,
  HistoryListResponse,
  MoodPrediction,
  RewardsStatus,
} from '../types'

function resolveApiUrl(raw: string | undefined): string {
  const fallback = 'http://localhost:8000'
  let value = (raw || fallback).trim()
  if (!value) value = fallback
  if (!/^https?:\/\//i.test(value)) {
    value = `https://${value.replace(/^\/+/, '')}`
  }
  return value.replace(/\/$/, '')
}

const API_BASE = resolveApiUrl(import.meta.env.VITE_API_URL)

/** Build an absolute API URL so GitHub Pages never treats the host as a relative path. */
function apiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path
  return new URL(normalizedPath, `${API_BASE}/`).toString()
}

export function getApiBaseUrl(): string {
  return API_BASE
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const user = auth.currentUser
  if (!user) throw new Error('Not authenticated')
  const token = await user.getIdToken()
  return { Authorization: `Bearer ${token}` }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = await getAuthHeaders()
  const res = await fetch(apiUrl(path), {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Request failed')
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export async function predictMood(imageBlob: Blob, notes?: string): Promise<MoodPrediction> {
  const headers = await getAuthHeaders()
  const form = new FormData()
  form.append('file', imageBlob, 'drawing.png')
  if (notes) form.append('notes', notes)

  const res = await fetch(apiUrl('/predict'), {
    method: 'POST',
    headers,
    body: form,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Analysis failed')
  }

  return res.json()
}

export async function getHistory(params?: {
  limit?: number
  offset?: number
  mood?: string
  from?: string
  to?: string
}): Promise<HistoryListResponse> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  if (params?.mood) qs.set('mood', params.mood)
  if (params?.from) qs.set('from', params.from)
  if (params?.to) qs.set('to', params.to)
  const query = qs.toString()
  return apiFetch(`/history${query ? `?${query}` : ''}`)
}

export async function getHistoryEntry(id: string): Promise<HistoryEntry> {
  return apiFetch(`/history/${id}`)
}

export async function deleteHistoryEntry(id: string): Promise<void> {
  await apiFetch(`/history/${id}`, { method: 'DELETE' })
}

export async function clearHistory(): Promise<{ deleted_count: number }> {
  return apiFetch('/history', { method: 'DELETE' })
}

export async function getRewardsStatus(): Promise<RewardsStatus> {
  return apiFetch('/rewards/status')
}

export async function getMoods(): Promise<{ moods: string[] }> {
  const res = await fetch(apiUrl('/moods'))
  return res.json()
}

export async function checkHealth(): Promise<{
  status: string
  analyzer_ready: boolean
}> {
  const res = await fetch(apiUrl('/health'))
  return res.json()
}

export function exportHistoryCsv(items: HistoryEntry[]): void {
  const headers = ['date', 'mood', 'confidence', 'notes']
  const rows = items.map((e) => [
    new Date(e.timestamp).toISOString(),
    e.mood,
    (e.confidence * 100).toFixed(1) + '%',
    (e.notes || '').replace(/"/g, '""'),
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.map((c) => `"${c}"`).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `mood-history-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
