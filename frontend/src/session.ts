/*
 * Auth session state — the single source of truth for tokens + current user.
 * Kept separate from api.ts and useAuth.ts so both can import it without a
 * circular dependency. Tokens are persisted to localStorage so a refresh keeps
 * the user signed in.
 */
import { ref } from 'vue'
import type { AuthResponse, User } from './types'

const ACCESS_KEY  = 'ft_access_token'
const REFRESH_KEY = 'ft_refresh_token'
const USER_KEY    = 'ft_user'

function readUser(): User | null {
  try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null') } catch { return null }
}

export const accessToken  = ref<string | null>(localStorage.getItem(ACCESS_KEY))
export const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY))
export const user         = ref<User | null>(readUser())

/* Store a full login/register result (tokens + user). */
export function setSession(res: AuthResponse): void {
  setTokens(res.access_token, res.refresh_token)
  user.value = res.user
  localStorage.setItem(USER_KEY, JSON.stringify(res.user))
}

/* Update just the tokens (used by silent refresh). */
export function setTokens(access: string, refresh: string): void {
  accessToken.value  = access
  refreshToken.value = refresh
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

/* Wipe everything — logout or unrecoverable 401. */
export function clearSession(): void {
  accessToken.value = refreshToken.value = null
  user.value = null
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}
