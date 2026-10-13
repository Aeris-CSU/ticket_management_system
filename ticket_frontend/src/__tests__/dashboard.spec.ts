import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { RouterView } from 'vue-router'
import router from '@/router'
import { pinia } from '@/stores/pinia'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

const ticketApi = vi.hoisted(() => ({ listTickets: vi.fn() }))
const assignmentApi = vi.hoisted(() => ({ listAssignments: vi.fn() }))
vi.mock('@/services/tickets', () => ({ listTickets: ticketApi.listTickets }))
vi.mock('@/services/assignments', () => ({ listAssignments: assignmentApi.listAssignments }))

const mounted: VueWrapper[] = []
const mountRouter = () => {
  const wrapper = mount(RouterView, { global: { plugins: [pinia, router] } })
  mounted.push(wrapper)
  return wrapper
}

describe('shared role dashboards', () => {
  beforeEach(async () => {
    ticketApi.listTickets.mockReset().mockResolvedValue([])
    assignmentApi.listAssignments.mockReset().mockResolvedValue([])
    const auth = useAuthStore(pinia)
    auth.logout()
    auth.user = null
    auth.status = 'unauthenticated'
    await router.replace('/')
  })

  afterEach(() => mounted.splice(0).forEach((wrapper) => wrapper.unmount()))

  it.each([
    ['ADMIN', '/admin', 'Admin Dashboard', ['All Tickets', 'Assignments', 'Customers', 'Technicians']],
    ['TECHNICIAN', '/technician', 'Technician Dashboard', ['Assigned Tickets']],
    ['CUSTOMER', '/customer', 'Customer Dashboard', ['My Tickets', 'Create Ticket']],
  ] as const)('shows the %s overview and its role navigation', async (role, path, heading, links) => {
    const auth = useAuthStore(pinia)
    auth.user = { id: 11, username: 'dashboard-user', role: role as UserRole }
    auth.status = 'authenticated'
    const wrapper = mountRouter()

    await router.push(path)
    await flushPromises()

    expect(wrapper.get('#dashboard-heading').text()).toBe(heading)
    expect(wrapper.get('.dashboard-account-copy').text()).toContain('dashboard-user')
    expect(wrapper.get('.dashboard-account-copy').text()).toContain(role === 'ADMIN' ? 'Admin' : role === 'TECHNICIAN' ? 'Technician' : 'Customer')
    expect(wrapper.findAll('.dashboard-stat-card')).toHaveLength(4)
    if (role === 'TECHNICIAN') {
      expect(wrapper.findAll('.dashboard-stat-card strong').every((value) => value.text() === '0')).toBe(true)
      expect(wrapper.get('.dashboard-nav').text()).not.toContain('Coming soon')
    } else {
      expect(wrapper.findAll('.dashboard-stat-card strong').every((value) => value.text() === '0')).toBe(true)
    }
    for (const link of links) expect(wrapper.get('.dashboard-nav').text()).toContain(link)
  })

  it('redirects unauthenticated visitors to login and blocks another role', async () => {
    const wrapper = mountRouter()
    await router.push('/customer')
    expect(router.currentRoute.value.path).toBe('/login')

    const auth = useAuthStore(pinia)
    auth.user = { id: 12, username: 'customer', role: 'CUSTOMER' }
    auth.status = 'authenticated'
    await router.push('/admin')
    expect(router.currentRoute.value.path).toBe('/customer')
    expect(wrapper.text()).toContain('Customer Dashboard')
  })

  it('opens and closes the mobile navigation and logs out using the auth store', async () => {
    const auth = useAuthStore(pinia)
    auth.user = { id: 13, username: 'casey', role: 'CUSTOMER' }
    auth.status = 'authenticated'
    const wrapper = mountRouter()
    await router.push('/customer')

    const menu = wrapper.get('.dashboard-menu-button')
    expect(menu.attributes('aria-expanded')).toBe('false')
    await menu.trigger('click')
    expect(wrapper.get('.dashboard-sidebar').classes()).toContain('is-open')
    expect(wrapper.get('.dashboard-menu-button').attributes('aria-expanded')).toBe('true')
    await wrapper.get('.dashboard-overlay').trigger('click')
    expect(wrapper.get('.dashboard-sidebar').classes()).not.toContain('is-open')

    await wrapper.get('.dashboard-logout').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(auth.isAuthenticated).toBe(false)
  })
})
