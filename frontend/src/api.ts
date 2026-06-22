/*
 * Typed fetch wrapper — all API calls go through here.
 * Throws on non-2xx so callers can catch and show toasts.
 *
 * Authenticated requests carry the access token as a Bearer header. On a 401 we
 * try a single silent token refresh, then retry once; if that fails the session
 * is cleared so the app falls back to the auth screen.
 */
import type { AuthResponse, AuthTokens, Earning, Spending, Subscription, Summary } from './types'
import { accessToken, refreshToken, setTokens, clearSession } from './session'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function authHeaders(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (accessToken.value) h['Authorization'] = `Bearer ${accessToken.value}`
  return h
}

/* Exchange the refresh token for a fresh pair. Returns false if not possible. */
async function tryRefresh(): Promise<boolean> {
  if (!refreshToken.value) return false
  try {
    const res = await fetch(`${BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken.value }),
    })
    if (!res.ok) return false
    const tokens = (await res.json()) as AuthTokens
    setTokens(tokens.access_token, tokens.refresh_token)
    return true
  } catch {
    return false
  }
}

async function request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders(), ...options })

  if (res.status === 401 && retry) {
    if (await tryRefresh()) return request<T>(path, options, false)
    clearSession()
    throw new Error('HTTP 401')
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  if (res.status === 204) return null as T
  return res.json() as Promise<T>
}

/* ── Auth (no bearer / no auto-refresh) ─────────────────────── */
export const register = (data: { email: string; username: string; password: string }) =>
  request<AuthResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }, false)
export const login = (data: { email: string; password: string }) =>
  request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify(data) }, false)

export const getEarnings   = ()              => request<Earning[]>('/api/earnings')
export const createEarning = (data: Omit<Earning, 'id' | 'created_at'>) =>
  request<Earning>('/api/earnings', { method: 'POST', body: JSON.stringify(data) })
export const updateEarning = (id: string, data: Omit<Earning, 'id' | 'created_at'>) =>
  request<Earning>(`/api/earnings/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteEarning = (id: string)    => request<null>(`/api/earnings/${id}`, { method: 'DELETE' })

export const getSubscriptions   = ()              => request<Subscription[]>('/api/subscriptions')
export const createSubscription = (data: Omit<Subscription, 'id' | 'created_at'>) =>
  request<Subscription>('/api/subscriptions', { method: 'POST', body: JSON.stringify(data) })
export const updateSubscription = (id: string, data: Omit<Subscription, 'id' | 'created_at'>) =>
  request<Subscription>(`/api/subscriptions/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteSubscription = (id: string)    => request<null>(`/api/subscriptions/${id}`, { method: 'DELETE' })

export const getSpending    = ()                                    => request<Spending[]>('/api/spending')
export const createSpending = (data: Omit<Spending, 'id' | 'created_at'>) =>
  request<Spending>('/api/spending', { method: 'POST', body: JSON.stringify(data) })
export const updateSpending = (id: string, data: Omit<Spending, 'id' | 'created_at'>) =>
  request<Spending>(`/api/spending/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteSpending = (id: string)                          => request<null>(`/api/spending/${id}`, { method: 'DELETE' })

export const getSummary = () => request<Summary>('/api/summary')
