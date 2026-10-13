import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { clearTokens, REFRESH_TOKEN_KEY, saveAccessToken, saveTokens } from '@/services/api'
import { currentUserRequest, loginRequest, refreshRequest, registerRequest } from '@/services/auth'
import type { AuthUser, LoginCredentials, RegistrationDetails, UserRole } from '@/types/auth'

type SessionStatus = 'unknown' | 'authenticated' | 'unauthenticated'

const rolePaths: Record<UserRole, string> = {
  ADMIN: '/admin',
  TECHNICIAN: '/technician',
  CUSTOMER: '/customer',
}

function isRole(value: unknown): value is UserRole {
  return value === 'ADMIN' || value === 'TECHNICIAN' || value === 'CUSTOMER'
}

function accountFromResponse(response: AuthUser | AuthUser[], access: string): AuthUser | null {
  if (!Array.isArray(response)) return response

  try {
    const segment = access.split('.')[1]
    if (!segment) return null
    const base64 = segment.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=')
    const payload = JSON.parse(atob(padded)) as { user_id?: number | string }
    return response.find((account) => String(account.id) === String(payload.user_id)) ?? null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const status = ref<SessionStatus>('unknown')
  const isAuthenticated = computed(() => status.value === 'authenticated' && user.value !== null)
  let restoreInProgress: Promise<boolean> | null = null

  function clearSession() {
    clearTokens()
    user.value = null
    status.value = 'unauthenticated'
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('tickarla:session-expired', clearSession)
  }

  async function login(credentials: LoginCredentials) {
    const result = await loginRequest(credentials)
    if (!result.account || !isRole(result.account.role)) {
      clearSession()
      throw new Error('The server returned an unsupported account role.')
    }
    saveTokens(result.tokens.access, result.tokens.refresh)
    user.value = result.account
    status.value = 'authenticated'
    return rolePaths[result.account.role]
  }

  async function register(details: RegistrationDetails) {
    return registerRequest(details)
  }

  async function restoreSession(): Promise<boolean> {
    if (status.value !== 'unknown') return isAuthenticated.value
    if (restoreInProgress) return restoreInProgress

    restoreInProgress = (async () => {
      const refresh = sessionStorage.getItem(REFRESH_TOKEN_KEY)
      if (!refresh) {
        status.value = 'unauthenticated'
        return false
      }

      try {
        const refreshed = await refreshRequest(refresh)
        saveAccessToken(refreshed.access)
        const response = await currentUserRequest()
        const account = accountFromResponse(response, refreshed.access)
        if (!account || !isRole(account.role)) {
          clearSession()
          return false
        }
        user.value = account
        status.value = 'authenticated'
        return true
      } catch {
        clearSession()
        return false
      }
    })()

    try {
      return await restoreInProgress
    } finally {
      restoreInProgress = null
    }
  }

  function logout() {
    clearSession()
  }

  function dashboardPath() {
    return user.value && isRole(user.value.role) ? rolePaths[user.value.role] : '/login'
  }

  return { user, status, isAuthenticated, login, register, restoreSession, logout, dashboardPath }
})
