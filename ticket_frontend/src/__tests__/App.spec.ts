import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import App from '../App.vue'
import router from '../router'
import { useAuthStore } from '../stores/auth'
import { pinia } from '../stores/pinia'

const mounted: VueWrapper[] = []

const mountApp = () => {
  const wrapper = mount(App, { global: { plugins: [pinia, router] } })
  mounted.push(wrapper)
  return wrapper
}

describe('App routes', () => {
  beforeEach(async () => {
    sessionStorage.clear()
    const auth = useAuthStore(pinia)
    auth.logout()
    auth.status = 'unknown'
    await router.replace('/')
  })

  afterEach(() => {
    mounted.splice(0).forEach((wrapper) => wrapper.unmount())
  })

  it('renders the public landing page', async () => {
    const wrapper = mountApp()
    await flushPromises()

    expect(wrapper.text()).toContain('Support Made Simple.')
    expect(wrapper.text()).toContain('Simple Tools for Better Support')
  })

  it('routes landing page login links to the login form', async () => {
    const wrapper = mountApp()
    await flushPromises()

    await wrapper.get('a.nav-login').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/login')
    expect(wrapper.text()).toContain('Sign in to Tickarla')
  })
})
