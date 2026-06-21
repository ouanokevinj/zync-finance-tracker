/*
 * Typed fetch wrapper — all API calls go through here.
 * Throws on non-2xx so callers can catch and show toasts.
 */
import type { Earning, Spending, Subscription, Summary } from './types'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  if (res.status === 204) return null as T
  return res.json() as Promise<T>
}

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
