import axios from 'axios'
import { api } from './api'
import type { AuthUser, LoginCredentials, LoginResponse, RegistrationDetails, TokenRefreshResponse } from '@/types/auth'

export async function loginRequest(credentials: LoginCredentials) {
  const { data } = await api.post<LoginResponse>('login/', credentials)
  return data
}

export async function registerRequest(details: RegistrationDetails) {
  const { data } = await api.post('register/', details)
  return data
}

export async function refreshRequest(refresh: string) {
  const { data } = await api.post<TokenRefreshResponse>('token/refresh/', { refresh })
  return data
}

export async function currentUserRequest() {
  const { data } = await api.get<AuthUser | AuthUser[]>('accounts/')
  return data
}

export async function changePasswordRequest(payload: { current_password: string; new_password: string; confirm_password: string }) {
  await api.post('change-password/', payload)
}

export function readableAuthError(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback

  const data: unknown = error.response?.data
  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>
    const detail = record.detail
    if (typeof detail === 'string') return detail

    const messages = Object.values(record).flatMap((value) => {
      if (typeof value === 'string') return [value]
      if (Array.isArray(value)) return value.filter((item): item is string => typeof item === 'string')
      return []
    })
    if (messages.length) return messages.join(' ')
  }

  if (error.request && !error.response) {
    return 'Could not reach the server. Check your connection and try again.'
  }
  return fallback
}
