import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { AxiosError } from 'axios'
import { RouterView } from 'vue-router'
import router from '@/router'
import { pinia } from '@/stores/pinia'
import { useAuthStore } from '@/stores/auth'
import type { Assignment, Technician } from '@/types/admin'
import type { Ticket } from '@/types/ticket'

const ticketApi = vi.hoisted(() => ({ listTickets: vi.fn(), getTicket: vi.fn() }))
const assignmentApi = vi.hoisted(() => ({ listAssignments: vi.fn(), createAssignment: vi.fn(), reassignTechnician: vi.fn() }))
const directoryApi = vi.hoisted(() => ({ listCustomers: vi.fn(), listTechnicians: vi.fn(), createTechnician: vi.fn() }))

vi.mock('@/services/tickets', () => ticketApi)
vi.mock('@/services/assignments', () => assignmentApi)
vi.mock('@/services/directories', () => directoryApi)

const mounted: VueWrapper[] = []
const mountRouter = () => {
  const wrapper = mount(RouterView, { global: { plugins: [pinia, router] } })
  mounted.push(wrapper)
  return wrapper
}

const ticketRecords: Ticket[] = [
  { id: 51, problem_title: 'Cannot connect to Wi-Fi', problem_description: 'Network is unavailable.', status: 'OPEN', customer: 4, customer_name: 'Casey Rivera', created_at: '2026-05-12T09:30:00Z', updated_at: '2026-05-12T09:30:00Z' },
  { id: 50, problem_title: 'Printer is jammed', problem_description: 'Paper is stuck.', status: 'ONGOING', customer: 5, customer_name: 'Morgan Lee', created_at: '2026-05-10T09:30:00Z', updated_at: '2026-05-10T10:00:00Z' },
]
const technicianRecords: Technician[] = [
  { id: 7, username: 'tech-sam', first_name: 'Sam', last_name: 'Taylor', email: 'sam@example.test', role: 'TECHNICIAN', specialization: 'Network support', availability_status: 'AVAILABLE' },
  { id: 8, username: 'tech-jules', first_name: 'Jules', last_name: 'Park', email: 'jules@example.test', role: 'TECHNICIAN', specialization: 'Hardware', availability_status: 'UNAVAILABLE' },
]
const assignmentRecord: Assignment = {
  id: 14, tickets: 51, ticket_title: 'Cannot connect to Wi-Fi', technicians: 7,
  technician_name: 'Sam Taylor', is_active: true, created_at: '2026-05-12T10:00:00Z', assigned_at: '2026-05-12T10:00:00Z',
}

describe('administrator ticket management', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    ticketApi.listTickets.mockResolvedValue(ticketRecords)
    ticketApi.getTicket.mockImplementation(async (id: string) => ticketRecords.find((ticket) => String(ticket.id) === id)!)
    assignmentApi.listAssignments.mockResolvedValue([])
    assignmentApi.createAssignment.mockResolvedValue(assignmentRecord)
    assignmentApi.reassignTechnician.mockResolvedValue({ ...assignmentRecord, id: 15, technicians: 9, technician_name: 'Alex Kim' })
    directoryApi.listTechnicians.mockResolvedValue(technicianRecords)
    directoryApi.listCustomers.mockResolvedValue([
      { id: 4, username: 'casey', first_name: 'Casey', last_name: 'Rivera', email: 'casey@example.test', role: 'CUSTOMER' },
    ])
    const auth = useAuthStore(pinia)
    auth.logout()
    auth.user = { id: 1, username: 'admin', role: 'ADMIN' }
    auth.status = 'authenticated'
    await router.replace('/')
  })

  afterEach(() => mounted.splice(0).forEach((wrapper) => wrapper.unmount()))

  it('loads real admin dashboard statistics and recent tickets', async () => {
    const wrapper = mountRouter()
    await router.push('/admin')
    await flushPromises()

    expect(ticketApi.listTickets).toHaveBeenCalledOnce()
    expect(wrapper.get('.dashboard-stat-grid').text()).toContain('Total Tickets')
    expect(wrapper.findAll('.dashboard-stat-card strong').map((item) => item.text())).toEqual(['2', '1', '1', '0'])
    expect(wrapper.get('.dashboard-recent').text()).toContain('Casey Rivera')
    expect(wrapper.get('.dashboard-create-row').text()).toContain('Assignments')
  })

  it('lists and filters all tickets, including customer names', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/tickets')
    await flushPromises()

    expect(wrapper.get('h2#tickets-heading').text()).toBe('All Tickets')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Casey Rivera')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Morgan Lee')
    await wrapper.get('input[type="search"]').setValue('printer')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Printer is jammed')
    expect(wrapper.get('.ticket-table-wrap').text()).not.toContain('Cannot connect to Wi-Fi')
  })

  it('shows only available technicians and creates an assignment', async () => {
    assignmentApi.listAssignments.mockResolvedValueOnce([]).mockResolvedValueOnce([assignmentRecord])
    const wrapper = mountRouter()
    await router.push('/admin/tickets/51')
    await flushPromises()

    expect(wrapper.get('.ticket-detail-card').text()).toContain('Casey Rivera')
    expect(wrapper.get('.assignment-form').text()).toContain('Sam Taylor')
    expect(wrapper.get('.assignment-form').text()).not.toContain('Jules Park')
    await wrapper.get('.assignment-form select').setValue('7')
    await wrapper.get('.assignment-form').trigger('submit')
    await flushPromises()

    expect(assignmentApi.createAssignment).toHaveBeenCalledWith(51, 7)
    expect(wrapper.text()).toContain('Technician assigned successfully.')
    expect(wrapper.text()).toContain('Assigned to Sam Taylor')
  })

  it('surfaces backend assignment validation errors', async () => {
    assignmentApi.listAssignments.mockResolvedValue([])
    const apiError = Object.assign(new AxiosError('Invalid assignment'), {
      response: { data: { technicians: ['The technician is not available.'] } },
    })
    assignmentApi.createAssignment.mockRejectedValueOnce(apiError)
    const wrapper = mountRouter()
    await router.push('/admin/tickets/51')
    await flushPromises()
    await wrapper.get('.assignment-form select').setValue('7')
    await wrapper.get('.assignment-form').trigger('submit')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('The technician is not available.')
  })

  it('prevents duplicate assignment submissions', async () => {
    let resolveAssignment!: (value: Assignment) => void
    assignmentApi.createAssignment.mockReturnValueOnce(new Promise<Assignment>((resolve) => { resolveAssignment = resolve }))
    const wrapper = mountRouter()
    await router.push('/admin/tickets/51')
    await flushPromises()
    await wrapper.get('.assignment-form select').setValue('7')
    await wrapper.get('.assignment-form').trigger('submit')
    await wrapper.get('.assignment-form').trigger('submit')

    expect(assignmentApi.createAssignment).toHaveBeenCalledOnce()
    resolveAssignment(assignmentRecord)
    await flushPromises()
  })

  it('supports backend-authorized reassignment of an active ticket', async () => {
    const ongoingTicket = { ...ticketRecords[1], id: 51, status: 'ONGOING' as const }
    ticketApi.getTicket.mockResolvedValueOnce(ongoingTicket).mockResolvedValueOnce({ ...ongoingTicket, status: 'ASSIGNED' })
    assignmentApi.listAssignments.mockResolvedValueOnce([assignmentRecord]).mockResolvedValueOnce([
      { ...assignmentRecord, id: 15, technicians: 9, technician_name: 'Alex Kim' },
      { ...assignmentRecord, is_active: false },
    ])
    directoryApi.listTechnicians.mockResolvedValueOnce([
      ...technicianRecords,
      { ...technicianRecords[0], id: 9, username: 'tech-alex', first_name: 'Alex', last_name: 'Kim' },
    ])
    const wrapper = mountRouter()
    await router.push('/admin/tickets/51')
    await flushPromises()
    await wrapper.get('.assignment-form select').setValue('9')
    await wrapper.get('.assignment-form').trigger('submit')
    await flushPromises()

    expect(assignmentApi.reassignTechnician).toHaveBeenCalledWith(14, 9)
    expect(wrapper.text()).toContain('Technician assignment updated.')
  })

  it('joins assignment history with ticket status', async () => {
    assignmentApi.listAssignments.mockResolvedValueOnce([assignmentRecord])
    const wrapper = mountRouter()
    await router.push('/admin/assignments')
    await flushPromises()

    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Cannot connect to Wi-Fi')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Sam Taylor')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Open')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Active')
  })

  it('loads customer and technician directories without exposing sensitive fields', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/customers')
    await flushPromises()
    expect(wrapper.text()).toContain('casey@example.test')
    expect(wrapper.text()).toContain('@casey')
    expect(wrapper.text()).not.toContain('address')

    await router.push('/admin/technicians')
    await flushPromises()
    expect(directoryApi.listTechnicians).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Network support')
    expect(wrapper.text()).toContain('Available')
    expect(wrapper.text()).toContain('Unavailable')
    expect(wrapper.text()).not.toContain('password')
  })

  it('lets an admin create a technician account and refreshes the directory', async () => {
    directoryApi.createTechnician.mockResolvedValueOnce({})
    const wrapper = mountRouter()
    await router.push('/admin/technicians')
    await flushPromises()
    await wrapper.get('.dashboard-view-heading button').trigger('click')

    await wrapper.get('#technician-username').setValue('tech-new')
    await wrapper.get('#technician-password').setValue('StrongPassword!2026')
    await wrapper.get('#technician-first-name').setValue('Taylor')
    await wrapper.get('#technician-last-name').setValue('Reed')
    await wrapper.get('#technician-email').setValue('taylor@example.test')
    await wrapper.get('#technician-specialization').setValue('Hardware support')
    await wrapper.get('#create-technician-form').trigger('submit')
    await flushPromises()

    expect(directoryApi.createTechnician).toHaveBeenCalledWith({
      username: 'tech-new',
      password: 'StrongPassword!2026',
      first_name: 'Taylor',
      last_name: 'Reed',
      email: 'taylor@example.test',
      specialization: 'Hardware support',
    })
    expect(directoryApi.listTechnicians).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Technician account created successfully.')
  })

  it('validates required technician account fields before sending the request', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/technicians')
    await flushPromises()
    await wrapper.get('.dashboard-view-heading button').trigger('click')
    await wrapper.get('#create-technician-form').trigger('submit')
    await flushPromises()

    expect(directoryApi.createTechnician).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Enter a username.')
    expect(wrapper.text()).toContain('Enter a temporary password.')
    expect(wrapper.text()).toContain('Enter a specialization.')
  })

  it('redirects customers away from administrator ticket routes', async () => {
    const auth = useAuthStore(pinia)
    auth.user = { id: 4, username: 'casey', role: 'CUSTOMER' }
    const wrapper = mountRouter()
    await router.push('/admin/tickets')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/customer')
    expect(ticketApi.listTickets).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Customer Dashboard')
  })
})
