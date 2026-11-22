import type { Observation, ObservationFilters, ObservationPage } from '../types/observation'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { headers: { Accept: 'application/json' } })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: { message?: string } } | null
    throw new ApiError(body?.detail?.message ?? 'Unable to reach the HazeGuard API.', response.status)
  }
  return response.json() as Promise<T>
}

export function getObservations(filters: ObservationFilters = {}): Promise<ObservationPage> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => { if (value !== undefined && value !== '') params.set(key, String(value)) })
  const query = params.toString()
  return request<ObservationPage>(`/observations${query ? `?${query}` : ''}`)
}
export function getObservation(id: string): Promise<Observation> { return request<Observation>(`/observations/${encodeURIComponent(id)}`) }
export function getHealth(): Promise<{ status: 'ok' }> { return request<{ status: 'ok' }>('/health') }
