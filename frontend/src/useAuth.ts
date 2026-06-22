/*
 * Auth composable — thin wrapper over the /api/auth/* endpoints and the shared
 * session state. Components use `isAuthenticated` to gate the UI and call
 * login/register/logout. Token storage + refresh live in session.ts / api.ts.
 */
import { computed } from 'vue'
import * as api from './api'
import { accessToken, user, setSession, clearSession } from './session'

const isAuthenticated = computed(() => !!accessToken.value)

async function login(email: string, password: string): Promise<void> {
  setSession(await api.login({ email, password }))
}

async function register(email: string, username: string, password: string): Promise<void> {
  setSession(await api.register({ email, username, password }))
}

function logout(): void {
  clearSession()
}

export function useAuth() {
  return { user, isAuthenticated, login, register, logout }
}
