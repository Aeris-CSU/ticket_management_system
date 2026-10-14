import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { RouterView } from 'vue-router'
import router from '@/router'
import { pinia } from '@/stores/pinia'
import { useAuthStore } from '@/stores/auth'
import type { Ticket } from '@/types/ticket'

const ticketApi = vi.hoisted(() => ({
  listTickets: vi.fn(),
  createTicket: vi.fn(),
  getTicket: vi.fn(),
  updateTicketStatus: vi.fn(),
}))

vi.mock('@/services/tickets', () => ticketApi)
vi.mock('@/services/assignments', () => ({ listAssignments: vi.fn().mockResolvedValue([]) }))
vi.mock('@/services/directories', () => ({ listCustomers: vi.fn().mockResolvedValue([{ id: 4, address: 'Main Campus', contact_number: '09171234567' }]) }))

const mounted: VueWrapper[] = []
const mountRouter = () => {
  const wrapper = mount(RouterView, { global: { plugins: [pinia, router] } })
  mounted.push(wrapper)
  return wrapper
}

const tickets: Ticket[] = [
  { id: 18, problem_title: 'Wi-Fi is unavailable', problem_description: 'The laptop cannot connect.', status: 'ONGOING', customer: 4, customer_name: 'Casey', created_at: '2026-05-12T09:30:00Z', updated_at: '2026-05-12T10:00:00Z' },
  { id: 17, problem_title: 'Printer paper jam', problem_description: 'The printer is stuck.', status: 'RESOLVED', customer: 4, customer_name: 'Casey', created_at: '2026-05-10T09:30:00Z', updated_at: '2026-05-10T10:00:00Z' },
]

describe('customer ticket management', () => {
  beforeEach(async () => {
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', { configurable: true, value() { this.setAttribute('open', '') } })
    Object.defineProperty(HTMLDialogElement.prototype, 'close', { configurable: true, value() { this.removeAttribute('open') } })
    vi.clearAllMocks()
    ticketApi.listTickets.mockResolvedValue(tickets)
    ticketApi.createTicket.mockResolvedValue(tickets[0])
    ticketApi.getTicket.mockResolvedValue(tickets[0])
    const auth = useAuthStore(pinia)
    auth.logout()
    auth.user = { id: 4, username: 'casey', role: 'CUSTOMER' }
    auth.status = 'authenticated'
    await router.replace('/')
  })

  afterEach(() => mounted.splice(0).forEach((wrapper) => wrapper.unmount()))

  it.each(['/customer', '/customer/tickets'])('opens customer ticket details from %s without leaving the page', async (path) => {
    const wrapper = mountRouter()
    await router.push(path)
    await flushPromises()
    await wrapper.get(path === '/customer' ? '.dashboard-recent-list button' : '.ticket-table button').trigger('click')
    await flushPromises()
    const popup = document.querySelector('dialog')!
    expect(popup.hasAttribute('open')).toBe(true)
    expect(popup.textContent).toContain('Wi-Fi is unavailable')
    expect(popup.querySelector('.assignment-form')).toBeNull()
    expect(popup.querySelector('.ticket-edit-button')).toBeNull()
    expect(router.currentRoute.value.path).toBe(path)
    expect(document.body.style.overflow).toBe('hidden')
    popup.dispatchEvent(new Event('cancel', { cancelable: true }))
    await flushPromises()
    expect(document.querySelector('dialog')).toBeNull()
    expect(document.body.style.overflow).not.toBe('hidden')
  })

  it('loads customer ticket statistics and recent tickets on the dashboard', async () => {
    const wrapper = mountRouter()
    await router.push('/customer')
    await flushPromises()

    expect(ticketApi.listTickets).toHaveBeenCalledOnce()
    expect(wrapper.get('.dashboard-stat-grid').text()).toContain('2')
    expect(wrapper.get('.dashboard-stat-grid').text()).toContain('1')
    expect(wrapper.get('.dashboard-recent').text()).toContain('Wi-Fi is unavailable')
    expect(wrapper.get('.dashboard-recent').text()).toContain('Ongoing')
  })

  it('renders the empty ticket list state', async () => {
    ticketApi.listTickets.mockResolvedValueOnce([])
    const wrapper = mountRouter()
    await router.push('/customer/tickets')
    await flushPromises()

    expect(wrapper.text()).toContain('No tickets yet')
  })

  it('shows a loading state while the ticket request is pending', async () => {
    let resolveTickets!: (value: Ticket[]) => void
    ticketApi.listTickets.mockReturnValueOnce(new Promise<Ticket[]>((resolve) => { resolveTickets = resolve }))
    const wrapper = mountRouter()
    await router.push('/customer/tickets')

    expect(wrapper.text()).toContain('Loading your tickets…')
    resolveTickets([])
    await flushPromises()
    expect(wrapper.text()).toContain('No tickets yet')
  })

  it('renders tickets and filters by status and title', async () => {
    const wrapper = mountRouter()
    await router.push('/customer/tickets')
    await flushPromises()

    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Wi-Fi is unavailable')
    await wrapper.get('select').setValue('RESOLVED')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Printer paper jam')
    expect(wrapper.get('.ticket-table-wrap').text()).not.toContain('Wi-Fi is unavailable')
    await wrapper.get('select').setValue('ALL')
    await wrapper.get('input[type="search"]').setValue('wi-')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Wi-Fi is unavailable')
    expect(wrapper.get('.ticket-table-wrap').text()).not.toContain('Printer paper jam')
  })

  it('validates required creation fields before calling the API', async () => {
    const wrapper = mountRouter()
    await router.push('/customer/tickets/new')
    await wrapper.get('form').trigger('submit')

    expect(ticketApi.createTicket).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Enter a title for your support request.')
    expect(wrapper.text()).toContain('Describe the problem you are experiencing.')
  })

  it('creates a ticket with only backend-supported fields and shows success on details', async () => {
    const wrapper = mountRouter()
    await router.push('/customer/tickets/new')
    await wrapper.get('#problem-title').setValue('  Wi-Fi issue  ')
    await wrapper.get('#problem-description').setValue('  Cannot connect to campus Wi-Fi.  ')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(ticketApi.createTicket).toHaveBeenCalledWith({
      problem_title: 'Wi-Fi issue',
      problem_description: 'Cannot connect to campus Wi-Fi.',
      address: 'Main Campus',
      contact_number: '09171234567',
    })
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/customer/tickets/18'))
    expect(wrapper.text()).toContain('Your ticket was created successfully.')
  })

  it('shows backend field validation errors on the create form', async () => {
    ticketApi.createTicket.mockRejectedValueOnce({
      response: { data: { problem_title: ['A ticket with this title cannot be accepted.'] } },
    })
    const wrapper = mountRouter()
    await router.push('/customer/tickets/new')
    await wrapper.get('#problem-title').setValue('Wi-Fi issue')
    await wrapper.get('#problem-description').setValue('Unable to connect.')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('A ticket with this title cannot be accepted.')
    expect(wrapper.get('[aria-invalid="true"]').attributes('name')).toBe('problem_title')
  })

  it('loads and renders authorized ticket details', async () => {
    const wrapper = mountRouter()
    await router.push('/customer/tickets/18')
    await flushPromises()

    expect(ticketApi.getTicket).toHaveBeenCalledWith('18')
    expect(wrapper.text()).toContain('Wi-Fi is unavailable')
    expect(wrapper.text()).toContain('The laptop cannot connect.')
    expect(wrapper.text()).toContain('Ongoing')
  })

  it('keeps customer ticket routes restricted to customers', async () => {
    const auth = useAuthStore(pinia)
    auth.user = { id: 9, username: 'admin', role: 'ADMIN' }
    const wrapper = mountRouter()
    await router.push('/customer/tickets')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/admin')
    expect(ticketApi.listTickets).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Admin Dashboard')
  })
})
