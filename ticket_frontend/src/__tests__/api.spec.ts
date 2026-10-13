import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from '../services/api'

const originalAdapter = api.defaults.adapter

describe('API token handling', () => {
  afterEach(() => {
    sessionStorage.clear()
    api.defaults.adapter = originalAdapter
    vi.restoreAllMocks()
  })

  it('refreshes an expired access token once and retries the request', async () => {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, 'old-access')
    sessionStorage.setItem(REFRESH_TOKEN_KEY, 'valid-refresh')
    vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'new-access' } } as never)
    const authorizationHeaders: Array<string | undefined> = []
    api.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
      authorizationHeaders.push(config.headers.get('Authorization') as string | undefined)
      if (authorizationHeaders.length === 1) {
        const error = new AxiosError('Access token expired', 'ERR_BAD_REQUEST', config)
        error.response = { status: 401, statusText: 'Unauthorized', headers: {}, config, data: {} }
        throw error
      }
      return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config }
    }

    const response = await api.get('tickets/')

    expect(response.data).toEqual({ ok: true })
    expect(authorizationHeaders).toEqual(['Bearer old-access', 'Bearer new-access'])
    expect(sessionStorage.getItem(ACCESS_TOKEN_KEY)).toBe('new-access')
    expect(axios.post).toHaveBeenCalledTimes(1)
  })

  it('clears the session if the request still returns 401 after refresh', async () => {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, 'old-access')
    sessionStorage.setItem(REFRESH_TOKEN_KEY, 'valid-refresh')
    vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'new-access' } } as never)
    api.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
      const error = new AxiosError('Unauthorized', 'ERR_BAD_REQUEST', config)
      error.response = { status: 401, statusText: 'Unauthorized', headers: {}, config, data: {} }
      throw error
    }

    await expect(api.get('tickets/')).rejects.toBeInstanceOf(AxiosError)
    expect(sessionStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull()
    expect(sessionStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull()
  })

  it('does not attach an old access token or refresh on public login requests', async () => {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, 'old-access')
    const refreshSpy = vi.spyOn(axios, 'post')
    let authorization: string | undefined
    api.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
      authorization = config.headers.get('Authorization') as string | undefined
      const error = new AxiosError('Invalid credentials', 'ERR_BAD_REQUEST', config)
      error.response = { status: 401, statusText: 'Unauthorized', headers: {}, config, data: {} }
      throw error
    }

    await expect(api.post('login/', { username: 'casey', password: 'hidden' })).rejects.toBeInstanceOf(AxiosError)
    expect(authorization).toBeUndefined()
    expect(refreshSpy).not.toHaveBeenCalled()
    expect(sessionStorage.getItem(ACCESS_TOKEN_KEY)).toBe('old-access')
  })
})
