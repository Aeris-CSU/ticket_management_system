import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

export const ACCESS_TOKEN_KEY = 'tickarla.access'
export const REFRESH_TOKEN_KEY = 'tickarla.refresh'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/'
export const API_BASE_URL = configuredBaseUrl.endsWith('/') ? configuredBaseUrl : `${configuredBaseUrl}/`

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { Accept: 'application/json' },
})

interface RetryConfig extends InternalAxiosRequestConfig {
  _tickarlaRetried?: boolean
}

let refreshRequest: Promise<string> | null = null

function clearStoredTokens() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
  window.dispatchEvent(new Event('tickarla:session-expired'))
}

function isPublicAuthUrl(url: string | undefined) {
  if (!url) return false
  const normalized = url.startsWith('/') ? url : `/${url}`
  return normalized.endsWith('/login/')
    || normalized.endsWith('/register/')
    || normalized.endsWith('/token/refresh/')
}

async function refreshAccessToken(): Promise<string> {
  if (!refreshRequest) {
    const refresh = sessionStorage.getItem(REFRESH_TOKEN_KEY)
    if (!refresh) throw new Error('No refresh token is available.')

    refreshRequest = axios
      .post<{ access: string }>(`${API_BASE_URL}token/refresh/`, { refresh }, {
        headers: { Accept: 'application/json' },
      })
      .then(({ data }) => {
        sessionStorage.setItem(ACCESS_TOKEN_KEY, data.access)
        return data.access
      })
      .finally(() => {
        refreshRequest = null
      })
  }
  return refreshRequest
}

api.interceptors.request.use((config) => {
  if (isPublicAuthUrl(config.url)) return config
  const access = sessionStorage.getItem(ACCESS_TOKEN_KEY)
  if (access) config.headers.set('Authorization', `Bearer ${access}`)
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined
    const url = original?.url ?? ''
    const isAuthRequest = isPublicAuthUrl(url)

    if (error.response?.status !== 401 || !original || isAuthRequest) {
      return Promise.reject(error)
    }
    if (original._tickarlaRetried) {
      clearStoredTokens()
      return Promise.reject(error)
    }

    original._tickarlaRetried = true
    try {
      const access = await refreshAccessToken()
      original.headers.set('Authorization', `Bearer ${access}`)
      return await api(original)
    } catch (refreshError) {
      const refreshWasRejected = !axios.isAxiosError(refreshError)
        || Boolean(refreshError.response && refreshError.response.status < 500)
      if (refreshWasRejected) {
        clearStoredTokens()
      }
      return Promise.reject(refreshError)
    }
  },
)

export function saveTokens(access: string, refresh: string) {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, access)
  sessionStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function saveAccessToken(access: string) {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, access)
}

export function clearTokens() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}
