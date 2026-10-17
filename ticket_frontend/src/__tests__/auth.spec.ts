import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { RouterView } from 'vue-router'
import router from '../router'
import { pinia } from '../stores/pinia'

const mocks = vi.hoisted(() => ({
  loginRequest: vi.fn(),
  registerRequest: vi.fn(),
  refreshRequest: vi.fn(),
  currentUserRequest: vi.fn(),
}))

vi.mock('@/services/auth', () => ({
  ...mocks,
  readableAuthError: (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback,
}))

import { useAuthStore } from '../stores/auth'

const mounted: VueWrapper[] = []
const mountRouter = () => {
  const wrapper = mount(RouterView, { global: { plugins: [pinia, router] } })
  mounted.push(wrapper)
  return wrapper
}
const customerLogin = {
  message: 'Successfully logged in',
  account: { id: 7, username: 'casey', role: 'CUSTOMER' as const },
  tokens: { access: 'header.eyJ1c2VyX2lkIjo3fQ.signature', refresh: 'refresh-token' },
}

describe('authentication flow', () => {
  beforeEach(async () => {
    sessionStorage.clear()
    vi.clearAllMocks()
    mocks.loginRequest.mockResolvedValue(customerLogin)
    mocks.registerRequest.mockResolvedValue({ id: 9, username: 'newcustomer', address: 'Campus' })
    const auth = useAuthStore(pinia)
    auth.logout()
    auth.status = 'unknown'
    await router.replace('/')
  })

  afterEach(() => {
    mounted.splice(0).forEach((wrapper) => wrapper.unmount())
  })

  it('validates login fields before making a request', async () => {
    const wrapper = mountRouter()
    await router.push('/login')
    await flushPromises()

    expect(wrapper.find('input[name="username"]').attributes('required')).toBeDefined()
    expect(wrapper.find('input[name="password"]').attributes('required')).toBeDefined()
    await wrapper.get('form').trigger('submit')
    expect(mocks.loginRequest).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Enter your username and password.')
  })

  it('requires a contact number and toggles confirmation visibility independently', async () => {
    const wrapper = mountRouter()
    await router.push('/register')
    await flushPromises()
    expect(wrapper.get('input[name="contact_number"]').attributes('required')).toBeDefined()
    await wrapper.get('input[name="confirm-password"]').setValue('ExamplePass123!')
    await wrapper.get('button[aria-label="Show confirm password"]').trigger('click')
    expect(wrapper.get('input[name="confirm-password"]').attributes('type')).toBe('text')
    expect(wrapper.get('input[name="new-password"]').attributes('type')).toBe('password')
    await wrapper.get('button[aria-label="Hide confirm password"]').trigger('click')
    expect(wrapper.get('input[name="confirm-password"]').attributes('type')).toBe('password')
    expect((wrapper.get('input[name="confirm-password"]').element as HTMLInputElement).value).toBe('ExamplePass123!')
  })

  it('logs in and sends customers to their role route', async () => {
    const wrapper = mountRouter()
    await router.push('/login')
    await flushPromises()
    await wrapper.get('input[name="username"]').setValue('casey')
    await wrapper.get('input[name="password"]').setValue('ExamplePass123!')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(mocks.loginRequest).toHaveBeenCalled()
    expect(sessionStorage.getItem('tickarla.refresh')).toBe('refresh-token')
    expect(router.currentRoute.value.path).toBe('/customer')
    expect(wrapper.text()).toContain('Customer Dashboard')
  })

  it('sends technicians to their own role route', async () => {
    mocks.loginRequest.mockResolvedValueOnce({
      ...customerLogin,
      account: { ...customerLogin.account, role: 'TECHNICIAN' as const },
    })
    const wrapper = mountRouter()
    await router.push('/login')
    await flushPromises()
    await wrapper.get('input[name="username"]').setValue('tech')
    await wrapper.get('input[name="password"]').setValue('ExamplePass123!')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/technician')
    expect(wrapper.text()).toContain('Technician Dashboard')
  })

  it('shows a useful message when login fails', async () => {
    mocks.loginRequest.mockRejectedValueOnce(new Error('Username or password is incorrect.'))
    const wrapper = mountRouter()
    await router.push('/login')
    await flushPromises()
    await wrapper.get('input[name="username"]').setValue('casey')
    await wrapper.get('input[name="password"]').setValue('bad-password')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Username or password is incorrect.')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('creates a customer account and routes to login without signing in', async () => {
    const wrapper = mountRouter()
    await router.push('/register')
    await flushPromises()
    await wrapper.get('input[name="username"]').setValue('newcustomer')
    await wrapper.get('input[name="email"]').setValue('')
    await wrapper.get('input[name="address"]').setValue('Campus')
    await wrapper.get('input[name="new-password"]').setValue('ExamplePass123!')
    await wrapper.get('input[name="contact_number"]').setValue('09171234567')
    await wrapper.get('input[name="confirm-password"]').setValue('ExamplePass123!')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(mocks.registerRequest).toHaveBeenCalledWith({
      username: 'newcustomer', email: undefined, address: 'Campus', contact_number: '09171234567', password: 'ExamplePass123!',
    })
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.registered).toBe('1')
    expect(sessionStorage.getItem('tickarla.access')).toBeNull()
  })

  it('rejects mismatched registration passwords', async () => {
    const wrapper = mountRouter()
    await router.push('/register')
    await flushPromises()
    await wrapper.get('input[name="username"]').setValue('newcustomer')
    await wrapper.get('input[name="address"]').setValue('Campus')
    await wrapper.get('input[name="new-password"]').setValue('ExamplePass123!')
    await wrapper.get('input[name="contact_number"]').setValue('09171234567')
    await wrapper.get('input[name="confirm-password"]').setValue('different-pass')
    await wrapper.get('form').trigger('submit')

    expect(mocks.registerRequest).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Passwords do not match.')
  })

  it('displays backend registration validation errors', async () => {
    mocks.registerRequest.mockRejectedValueOnce(new Error('A user with that username already exists.'))
    const wrapper = mountRouter()
    await router.push('/register')
    await flushPromises()
    await wrapper.get('input[name="username"]').setValue('already-used')
    await wrapper.get('input[name="address"]').setValue('Campus')
    await wrapper.get('input[name="new-password"]').setValue('ExamplePass123!')
    await wrapper.get('input[name="contact_number"]').setValue('09171234567')
    await wrapper.get('input[name="confirm-password"]').setValue('ExamplePass123!')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('A user with that username already exists.')
    expect(router.currentRoute.value.path).toBe('/register')
  })

  it('blocks a customer from the admin route and logs out locally', async () => {
    const auth = useAuthStore(pinia)
    await auth.login({ username: 'casey', password: 'ExamplePass123!' })
    const wrapper = mountRouter()

    await router.push('/admin')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/customer')

    await wrapper.get('.dashboard-logout').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(sessionStorage.getItem('tickarla.refresh')).toBeNull()

    await router.push('/customer')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('restores an admin session from the account list response', async () => {
    const auth = useAuthStore(pinia)
    sessionStorage.setItem('tickarla.refresh', 'stored-refresh')
    auth.status = 'unknown'
    mocks.refreshRequest.mockResolvedValueOnce({ access: 'header.eyJ1c2VyX2lkIjo4fQ.signature' })
    mocks.currentUserRequest.mockResolvedValueOnce([
      { id: 3, username: 'other-admin', role: 'ADMIN' },
      { id: 8, username: 'root', role: 'ADMIN' },
    ])

    expect(await auth.restoreSession()).toBe(true)
    expect(auth.user?.username).toBe('root')
    await router.push('/login')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin')
  })
})
