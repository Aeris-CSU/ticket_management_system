import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { AxiosError } from 'axios'
import { RouterView } from 'vue-router'
import router from '@/router'
import { pinia } from '@/stores/pinia'
import { useAuthStore } from '@/stores/auth'
import type { Assignment } from '@/types/admin'
import type { Ticket } from '@/types/ticket'

const ticketApi = vi.hoisted(() => ({ listTickets: vi.fn(), getTicket: vi.fn(), updateTicketStatus: vi.fn() }))
const assignmentApi = vi.hoisted(() => ({ listAssignments: vi.fn() }))
vi.mock('@/services/tickets', () => ticketApi)
vi.mock('@/services/assignments', () => assignmentApi)

const mounted: VueWrapper[] = []
const mountRouter = () => {
  const wrapper = mount(RouterView, { global: { plugins: [pinia, router] } })
  mounted.push(wrapper)
  return wrapper
}

const tickets: Ticket[] = [
  { id: 91, problem_title: 'Cannot connect to Wi-Fi', problem_description: 'Network is unavailable.', status: 'ASSIGNED', customer: 4, customer_name: 'Casey Rivera', created_at: '2026-05-12T09:30:00Z', updated_at: '2026-05-12T10:00:00Z' },
  { id: 90, problem_title: 'Printer is jammed', problem_description: 'Paper is stuck.', status: 'ONGOING', customer: 5, customer_name: 'Morgan Lee', created_at: '2026-05-10T09:30:00Z', updated_at: '2026-05-10T10:00:00Z' },
  { id: 89, problem_title: 'Laptop setup', problem_description: 'Needs setup.', status: 'RESOLVED', customer: 6, customer_name: 'Riley Chen', created_at: '2026-05-09T09:30:00Z', updated_at: '2026-05-09T10:00:00Z' },
]
const assignments: Assignment[] = [
  { id: 31, tickets: 91, ticket_title: tickets[0]!.problem_title, technicians: 7, technician_name: 'Sam Taylor', is_active: true, created_at: '2026-05-12T10:00:00Z', assigned_at: '2026-05-12T10:00:00Z' },
  { id: 32, tickets: 90, ticket_title: tickets[1]!.problem_title, technicians: 7, technician_name: 'Sam Taylor', is_active: true, created_at: '2026-05-10T10:00:00Z', assigned_at: '2026-05-10T10:00:00Z' },
]

describe('technician ticket workflow', () => {
  beforeEach(async () => {
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', { configurable: true, value() { this.setAttribute('open', '') } })
    Object.defineProperty(HTMLDialogElement.prototype, 'close', { configurable: true, value() { this.removeAttribute('open') } })
    vi.clearAllMocks()
    tickets[0]!.status = 'ASSIGNED'
    tickets[1]!.status = 'ONGOING'
    tickets[2]!.status = 'RESOLVED'
    ticketApi.listTickets.mockResolvedValue(tickets)
    ticketApi.getTicket.mockImplementation(async (id: string) => ({ ...tickets.find((ticket) => String(ticket.id) === id)! }))
    ticketApi.updateTicketStatus.mockImplementation(async (id: string, status: Ticket['status']) => {
      const current = tickets.find((ticket) => String(ticket.id) === id)!
      current.status = status
      return { ...current }
    })
    assignmentApi.listAssignments.mockResolvedValue(assignments)
    const auth = useAuthStore(pinia)
    auth.logout()
    auth.user = { id: 7, username: 'sam', role: 'TECHNICIAN' }
    auth.status = 'authenticated'
    await router.replace('/')
  })

  afterEach(() => mounted.splice(0).forEach((wrapper) => wrapper.unmount()))

  it.each(['/technician', '/technician/tickets'])('opens a ticket popup from %s and updates its work status without navigating', async (path) => {
    const wrapper = mountRouter()
    await router.push(path)
    await flushPromises()
    await wrapper.get(path === '/technician' ? 'button.dashboard-recent-row' : '.ticket-table button').trigger('click')
    await flushPromises()
    const popup = document.querySelector('dialog')!
    expect(popup.hasAttribute('open')).toBe(true)
    expect(router.currentRoute.value.path).toBe(path)
    expect(popup.textContent).toContain('Casey Rivera')
    expect(popup.querySelector('.ticket-edit-button')).toBeNull()
    expect(popup.querySelector('.ticket-detail-edit')).toBeNull()
    ;(popup.querySelector('.technician-status-actions button') as HTMLButtonElement).click()
    await flushPromises()
    expect(ticketApi.updateTicketStatus).toHaveBeenCalledWith('91', 'ONGOING')
    expect(popup.textContent).toContain('Mark as Resolved')
    ;(popup.querySelector('.technician-status-actions button') as HTMLButtonElement).click()
    await flushPromises()
    expect(ticketApi.updateTicketStatus).toHaveBeenCalledWith('91', 'RESOLVED')
    expect(popup.textContent).toContain('Ticket marked as resolved.')
    popup.dispatchEvent(new Event('cancel', { cancelable: true }))
    await flushPromises()
    expect(document.querySelector('dialog')).toBeNull()
    expect(router.currentRoute.value.path).toBe(path)
    expect(wrapper.text()).not.toContain('Cannot connect to Wi-Fi')
  })

  it('shows backend ticket statistics and recent assigned ticket information', async () => {
    const wrapper = mountRouter()
    await router.push('/technician')
    await flushPromises()

    expect(ticketApi.listTickets).toHaveBeenCalledOnce()
    expect(wrapper.findAll('.dashboard-stat-card strong').map((card) => card.text())).toEqual(['2', '1', '1', '0'])
    expect(wrapper.get('.dashboard-recent').text()).toContain('Casey Rivera')
    expect(wrapper.get('.dashboard-recent').text()).toContain('Recent Assigned Tickets')
    expect(wrapper.get('.dashboard-recent').attributes('aria-labelledby')).toBe('recent-tickets-heading')
    expect(wrapper.get('.dashboard-recent-list button').text()).toContain('Cannot connect to Wi-Fi')
    expect(wrapper.get('.dashboard-recent').text()).not.toContain('Laptop setup')
  })

  it('lists and filters tickets returned for the technician by the backend', async () => {
    const wrapper = mountRouter()
    await router.push('/technician/tickets')
    await flushPromises()

    expect(wrapper.get('#tickets-heading').text()).toBe('Assigned Tickets')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Casey Rivera')
    expect(wrapper.get('.ticket-table-wrap').text()).not.toContain('Laptop setup')
    await wrapper.get('input[type="search"]').setValue('printer')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Printer is jammed')
    expect(wrapper.get('.ticket-table-wrap').text()).not.toContain('Cannot connect to Wi-Fi')
    expect(wrapper.get('.ticket-table-wrap button').text()).toBe('View details')
    expect(wrapper.find('a[href="/customer/tickets/new"]').exists()).toBe(false)
  })

  it('shows empty, loading, and API error states on the assigned ticket list', async () => {
    ticketApi.listTickets.mockReturnValueOnce(new Promise<Ticket[]>(() => {}))
    const pendingWrapper = mountRouter()
    await router.push('/technician/tickets')
    expect(pendingWrapper.text()).toContain('Loading your tickets')
    pendingWrapper.unmount()
    mounted.pop()

    ticketApi.listTickets.mockResolvedValueOnce([])
    const emptyWrapper = mountRouter()
    await router.push('/technician/tickets')
    await flushPromises()
    expect(emptyWrapper.text()).toContain('No assigned tickets')
    emptyWrapper.unmount()
    mounted.pop()

    ticketApi.listTickets.mockRejectedValueOnce(new Error('offline'))
    const errorWrapper = mountRouter()
    await router.push('/technician/tickets')
    await flushPromises()
    expect(errorWrapper.get('[role="alert"]').text()).toContain('Could not load your tickets')
  })

  it('shows ticket details and starts work only for a current assignment', async () => {
    const wrapper = mountRouter()
    await router.push('/technician/tickets/91')
    await flushPromises()

    expect(wrapper.text()).toContain('Casey Rivera')
    expect(wrapper.text()).toContain('Network is unavailable.')
    expect(wrapper.get('.technician-status-panel').text()).toContain('Assigned')
    await wrapper.get('.technician-status-panel button').trigger('click')
    await flushPromises()

    expect(ticketApi.updateTicketStatus).toHaveBeenCalledWith('91', 'ONGOING')
    expect(ticketApi.getTicket).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Work started. Ticket status updated.')
    expect(wrapper.get('.ticket-status-ongoing').text()).toBe('Ongoing')
    expect(wrapper.text()).not.toContain('Technician Assignment')
  })

  it('marks ongoing work resolved and provides no action for terminal tickets', async () => {
    const wrapper = mountRouter()
    await router.push('/technician/tickets/90')
    await flushPromises()
    await wrapper.get('.technician-status-panel button').trigger('click')
    await flushPromises()

    expect(ticketApi.updateTicketStatus).toHaveBeenCalledWith('90', 'RESOLVED')
    expect(ticketApi.getTicket).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Ticket marked as resolved.')
    expect(wrapper.get('.ticket-status-resolved').text()).toBe('Resolved')
    expect(wrapper.find('.technician-status-panel button').exists()).toBe(false)

    await router.push('/technician/tickets')
    await flushPromises()
    await router.push('/technician/tickets/89')
    await flushPromises()
    expect(wrapper.find('.technician-status-panel button').exists()).toBe(false)
  })

  it('does not offer status actions when assignment is inactive', async () => {
    assignmentApi.listAssignments.mockResolvedValueOnce([])
    const wrapper = mountRouter()
    await router.push('/technician/tickets/91')
    await flushPromises()
    expect(wrapper.find('.technician-status-panel button').exists()).toBe(false)
    expect(wrapper.text()).toContain('not currently assigned')
  })

  it('shows backend transition and permission errors without optimistic updates', async () => {
    const apiError = Object.assign(new AxiosError('Forbidden'), {
      response: { status: 403, data: { detail: 'Technicians can only update tickets currently assigned to them.' } },
    })
    ticketApi.updateTicketStatus.mockRejectedValueOnce(apiError)
    const wrapper = mountRouter()
    await router.push('/technician/tickets/91')
    await flushPromises()
    await wrapper.get('.technician-status-panel button').trigger('click')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('currently assigned to them')
    expect(wrapper.get('.ticket-status-assigned').text()).toBe('Assigned')
  })

  it('surfaces an invalid transition response and keeps the current status', async () => {
    ticketApi.updateTicketStatus.mockRejectedValueOnce(Object.assign(new AxiosError('Invalid transition'), {
      response: { status: 400, data: { status: ['Cannot transition a ASSIGNED ticket to RESOLVED.'] } },
    }))
    const wrapper = mountRouter()
    await router.push('/technician/tickets/91')
    await flushPromises()
    await wrapper.get('.technician-status-panel button').trigger('click')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('Cannot transition a ASSIGNED ticket to RESOLVED.')
    expect(wrapper.get('.ticket-status-assigned').text()).toBe('Assigned')
  })

  it('prevents duplicate status requests while an update is pending', async () => {
    let finishUpdate!: (ticket: Ticket) => void
    ticketApi.updateTicketStatus.mockReturnValueOnce(new Promise<Ticket>((resolve) => { finishUpdate = resolve }))
    const wrapper = mountRouter()
    await router.push('/technician/tickets/91')
    await flushPromises()
    const button = wrapper.get('.technician-status-panel button')
    await button.trigger('click')
    await button.trigger('click')

    expect(ticketApi.updateTicketStatus).toHaveBeenCalledOnce()
    expect(button.attributes('disabled')).toBeDefined()
    finishUpdate({ ...tickets[0]!, status: 'ONGOING' })
    await flushPromises()
  })

  it('blocks other roles and surfaces unauthorized ticket details', async () => {
    const auth = useAuthStore(pinia)
    auth.user = { id: 12, username: 'customer', role: 'CUSTOMER' }
    const wrapper = mountRouter()
    await router.push('/technician/tickets')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/customer')

    auth.user = { id: 7, username: 'sam', role: 'TECHNICIAN' }
    await router.push('/')
    ticketApi.getTicket.mockRejectedValueOnce(Object.assign(new AxiosError('Forbidden'), {
      response: { status: 403, data: { detail: 'You do not have permission to access this ticket.' } },
    }))
    await router.push('/technician/tickets/999')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('permission')
  })
})
