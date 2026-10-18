import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { AxiosError } from 'axios'
import { RouterView } from 'vue-router'
import router from '@/router'
import { pinia } from '@/stores/pinia'
import { useAuthStore } from '@/stores/auth'
import type { Assignment, Technician } from '@/types/admin'
import type { Ticket } from '@/types/ticket'

const ticketApi = vi.hoisted(() => ({ listTickets: vi.fn(), getTicket: vi.fn(), updateTicket: vi.fn(), updateTicketStatus: vi.fn(), deleteTicket: vi.fn() }))
const assignmentApi = vi.hoisted(() => ({ listAssignments: vi.fn(), createAssignment: vi.fn(), reassignTechnician: vi.fn(), unassignTechnician: vi.fn() }))
const directoryApi = vi.hoisted(() => ({ listCustomers: vi.fn(), listTechnicians: vi.fn(), createTechnician: vi.fn(), deleteTechnician: vi.fn(), deleteCustomer: vi.fn() }))

vi.mock('@/services/tickets', () => ticketApi)
vi.mock('@/services/assignments', () => assignmentApi)
vi.mock('@/services/directories', () => directoryApi)

const mounted: VueWrapper[] = []
const mountRouter = (inlineTeleport = false) => {
  const wrapper = mount(RouterView, { global: { plugins: [pinia, router], stubs: inlineTeleport ? { Teleport: true } : {} } })
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
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', { configurable: true, value() { this.setAttribute('open', '') } })
    Object.defineProperty(HTMLDialogElement.prototype, 'close', { configurable: true, value() { this.removeAttribute('open') } })
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
    expect(wrapper.find('.dashboard-create-row').exists()).toBe(false)
  })

  it('lists and filters all tickets, including customer names', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/tickets')
    await flushPromises()

    expect(wrapper.get('h2#tickets-heading').text()).toBe('All Support Tickets')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Casey Rivera')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Morgan Lee')
    await wrapper.get('input[type="search"]').setValue('printer')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Printer is jammed')
    expect(wrapper.get('.ticket-table-wrap').text()).not.toContain('Cannot connect to Wi-Fi')
  })

  it('combines keywords, Philippine dates and technician history and clears filters', async () => {
    assignmentApi.listAssignments.mockResolvedValueOnce([assignmentRecord])
    const wrapper = mountRouter()
    await router.push('/admin/tickets')
    await flushPromises()
    await wrapper.get('input[type="search"]').setValue('RIVERA   network')
    expect(wrapper.get('.ticket-more-filters').attributes('aria-expanded')).toBe('false')
    await wrapper.get('.ticket-more-filters').trigger('click')
    expect(wrapper.get('.ticket-more-filters').attributes('aria-expanded')).toBe('true')
    await wrapper.get('[aria-label="Submitted from"]').setValue('2026-05-12')
    await wrapper.get('[aria-label="Submitted through"]').setValue('2026-05-12')
    await wrapper.findAll('.ticket-filters select')[2]!.setValue('7')
    expect(wrapper.findAll('.ticket-table tbody tr')).toHaveLength(1)
    expect(wrapper.text()).toContain('1 of 2 tickets')
    await wrapper.get('[aria-label="Submitted from"]').setValue('2026-05-13')
    expect(wrapper.text()).toContain('The end date must be on or after the start date.')
    await wrapper.findAll('button').find(button => button.text() === 'Clear filters')!.trigger('click')
    expect(wrapper.findAll('.ticket-table tbody tr')).toHaveLength(2)
  })

  it('combines technician specialization, workload, availability and keywords', async () => {
    assignmentApi.listAssignments.mockResolvedValueOnce([assignmentRecord])
    const wrapper = mountRouter()
    await router.push('/admin/technicians')
    await flushPromises()
    await wrapper.get('input[type="search"]').setValue('Taylor network')
    expect(wrapper.get('.directory-filter-toggle').attributes('aria-expanded')).toBe('false')
    await wrapper.get('.directory-filter-toggle').trigger('click')
    expect(wrapper.get('.directory-filter-toggle').attributes('aria-expanded')).toBe('true')
    const filters = wrapper.findAll('.directory-filter-extra select')
    await filters[0]!.setValue('AVAILABLE')
    await filters[1]!.setValue('Network support')
    await filters[2]!.setValue('WITH')
    expect(wrapper.findAll('.directory-table tbody tr')).toHaveLength(1)
    expect(wrapper.get('.directory-table').text()).toContain('Sam Taylor')
    await filters[2]!.setValue('WITHOUT')
    expect(wrapper.text()).toContain('No matching technicians')
    await wrapper.findAll('button').find(button => button.text() === 'Clear filters')!.trigger('click')
    expect(wrapper.findAll('.directory-table tbody tr')).toHaveLength(2)
  })

  it('counts backend statuses accurately and refreshes the active queue', async () => {
    const completed = { ...ticketRecords[0]!, id: 52, status: 'RESOLVED' as const }
    const cancelled = { ...ticketRecords[0]!, id: 53, status: 'CANCELLED' as const }
    const assigned = { ...ticketRecords[0]!, id: 54, status: 'ASSIGNED' as const }
    ticketApi.listTickets.mockResolvedValueOnce([...ticketRecords, completed, cancelled, assigned])
    const wrapper = mountRouter()
    await router.push('/admin')
    await flushPromises()
    expect(wrapper.findAll('.dashboard-stat-card strong').map((item) => item.text())).toEqual(['5', '1', '2', '1'])
    expect(wrapper.text()).toContain('Assigned or currently being handled.')
    expect(wrapper.findAll('.queue-table tbody tr')).toHaveLength(3)
    ticketApi.listTickets.mockResolvedValueOnce([completed, cancelled])
    await wrapper.get('.dashboard-page-intro button').trigger('click')
    await flushPromises()
    expect(wrapper.find('.queue-table').exists()).toBe(false)
    expect(wrapper.text()).toContain('No active support requests')
  })

  it('keeps resolved and cancelled tickets searchable and supports oldest-first sorting', async () => {
    ticketApi.listTickets.mockResolvedValueOnce([
      ticketRecords[0], ticketRecords[1],
      { ...ticketRecords[0], id: 60, status: 'RESOLVED', problem_title: 'Completed issue' },
      { ...ticketRecords[0], id: 61, status: 'CANCELLED', problem_title: 'Cancelled issue' },
    ])
    const wrapper = mountRouter()
    await router.push('/admin/tickets')
    await flushPromises()
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Completed issue')
    expect(wrapper.get('.ticket-table-wrap').text()).toContain('Cancelled issue')
    await wrapper.findAll('.ticket-filters select')[1]!.setValue('oldest')
    expect(wrapper.findAll('.ticket-table tbody tr')[0]!.text()).toContain('#50')
    await wrapper.get('input[type="search"]').setValue('Morgan')
    expect(wrapper.findAll('.ticket-table tbody tr')).toHaveLength(1)
  })


  it('shows a customer address and their ticket links in directory details', async () => {
    directoryApi.listCustomers.mockResolvedValueOnce([{ id: 4, username: 'casey', first_name: 'Casey', last_name: 'Rivera', email: 'casey@example.test', role: 'CUSTOMER', address: 'Main Street' }])
    const wrapper = mountRouter()
    await router.push('/admin/customers')
    await flushPromises()
    await wrapper.get('.directory-table button').trigger('click')
    const popup = document.querySelector('.directory-details-modal')!
    expect(popup.textContent).toContain('Main Street')
    expect(popup.textContent).toContain('Cannot connect to Wi-Fi')
    expect(popup.textContent).not.toContain('Printer is jammed')
    expect(router.currentRoute.value.path).toBe('/admin/customers')
    popup.dispatchEvent(new Event('cancel', { cancelable: true }))
    await flushPromises()
    expect(document.querySelector('.directory-details-modal')).toBeNull()
  })

  it('searches customers by contact details and clears an empty search result', async () => {
    directoryApi.listCustomers.mockResolvedValueOnce([
      { id: 4, username: 'casey', first_name: 'Casey', last_name: 'Rivera', email: 'casey@example.test', role: 'CUSTOMER', address: 'Main Street', contact_number: '09171234567' },
      { id: 5, username: 'morgan', first_name: 'Morgan', last_name: 'Lee', email: 'morgan@example.test', role: 'CUSTOMER', address: 'Campus', contact_number: '' },
    ])
    const wrapper = mountRouter()
    await router.push('/admin/customers')
    await flushPromises()
    await wrapper.get('#customer-search').setValue('09171234567')
    expect(wrapper.findAll('.directory-table tbody tr')).toHaveLength(1)
    expect(wrapper.get('.directory-table').text()).toContain('Casey Rivera')
    expect(wrapper.get('.directory-table').text()).not.toContain('@casey')
    await wrapper.get('#customer-search').setValue('campus')
    expect(wrapper.get('.directory-table').text()).toContain('Morgan Lee')
    await wrapper.get('#customer-search').setValue('unknown customer')
    expect(wrapper.text()).toContain('No matching customers')
    await wrapper.get('.ticket-empty-state button').trigger('click')
    expect(wrapper.findAll('.directory-table tbody tr')).toHaveLength(2)
  })

  it.each(['/admin', '/admin/tickets'])('opens ticket details in a popup from %s without navigating', async (path) => {
    const wrapper = mountRouter()
    await router.push(path)
    await flushPromises()
    await wrapper.get(path === '/admin' ? '.queue-table button' : '.ticket-table button').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe(path)
    const popup = document.querySelector('dialog')!
    expect(popup.hasAttribute('open')).toBe(true)
    expect(popup.textContent).toContain('Ticket Details')
    expect(document.body.style.overflow).toBe('hidden')
    popup.dispatchEvent(new Event('cancel', { cancelable: true }))
    await flushPromises()
    expect(document.querySelector('dialog')).toBeNull()
    expect(document.body.style.overflow).not.toBe('hidden')
  })

  it('saves ticket edits inside the popup and updates the list behind it', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/tickets')
    await flushPromises()
    ticketApi.updateTicket.mockResolvedValueOnce({ ...ticketRecords[0]!, problem_title: 'Updated from popup' })
    await wrapper.get('.ticket-table button').trigger('click')
    await flushPromises()
    const popup = document.querySelector('dialog')!
    ;(popup.querySelector('.ticket-edit-button') as HTMLButtonElement).click()
    await flushPromises()
    const input = popup.querySelector('#edit-ticket-title') as HTMLInputElement
    input.value = 'Updated from popup'
    input.dispatchEvent(new Event('input', { bubbles: true }))
    popup.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flushPromises()
    expect(ticketApi.updateTicket).toHaveBeenCalledWith('51', expect.objectContaining({ problem_title: 'Updated from popup' }))
    expect(wrapper.get('.ticket-table').text()).toContain('Updated from popup')
    ;(popup.querySelector('.ticket-modal-close') as HTMLButtonElement).click()
    await flushPromises()
    expect(document.querySelector('dialog')).toBeNull()
    expect(router.currentRoute.value.path).toBe('/admin/tickets')
  })

  it('shows the submitted contact number and address inside the ticket popup', async () => {
    ticketApi.getTicket.mockResolvedValueOnce({ ...ticketRecords[0]!, contact_number: '09171234567', address: 'Room 204' })
    const wrapper = mountRouter()
    await router.push('/admin/tickets')
    await flushPromises()
    await wrapper.get('.ticket-table button').trigger('click')
    await flushPromises()
    const contact = document.querySelector('dialog .ticket-contact-details')!
    expect(contact.textContent).toContain('09171234567')
    expect(contact.textContent).toContain('Room 204')
  })

  it('shows only resolved tickets in the replacement menu and keeps all records in All Tickets', async () => {
    ticketApi.listTickets.mockResolvedValueOnce([
      ...ticketRecords,
      { ...ticketRecords[0]!, id: 60, status: 'RESOLVED', problem_title: 'Completed issue' },
      { ...ticketRecords[0]!, id: 61, status: 'CANCELLED', problem_title: 'Cancelled issue' },
    ])
    const wrapper = mountRouter()
    await router.push('/admin/resolved-tickets')
    await flushPromises()
    expect(wrapper.get('#tickets-heading').text()).toBe('Resolved Tickets')
    expect(wrapper.findAll('.ticket-table tbody tr')).toHaveLength(1)
    expect(wrapper.get('.ticket-table').text()).toContain('Completed issue')
    expect(wrapper.get('.ticket-table').text()).not.toContain('Cancelled issue')
    expect(wrapper.get('.dashboard-nav').text()).not.toContain('Resolved Tickets')
    expect(wrapper.get('.dashboard-nav').text()).not.toContain('Assignments')
    await router.push('/admin/tickets')
    await flushPromises()
    expect(wrapper.findAll('.ticket-table tbody tr')).toHaveLength(4)
    await router.push('/admin/assignments')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/admin/resolved-tickets')
  })

  it('requires confirmation before deleting a customer account from the action icon', async () => {
    directoryApi.deleteCustomer.mockResolvedValueOnce(undefined)
    const wrapper = mountRouter(true)
    await router.push('/admin/customers')
    await flushPromises()
    await wrapper.get('.directory-table tbody tr .technician-delete-icon').trigger('click')
    expect(directoryApi.deleteCustomer).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('account and login permanently?')
    await wrapper.get('.technician-delete-actions .button-primary').trigger('click')
    await flushPromises()
    expect(directoryApi.deleteCustomer).toHaveBeenCalledWith(4)
    expect(wrapper.text()).toContain('Customer account deleted.')
    expect(wrapper.text()).not.toContain('Casey Rivera')
  })

  it('shows terminal ticket trash icons and requires confirmation before deleting', async () => {
    ticketApi.listTickets.mockResolvedValueOnce([
      ticketRecords[0]!,
      { ...ticketRecords[0]!, id: 70, status: 'RESOLVED' },
      { ...ticketRecords[0]!, id: 71, status: 'CANCELLED' },
    ])
    ticketApi.deleteTicket.mockResolvedValueOnce(undefined)
    const wrapper = mountRouter(true)
    await router.push('/admin/tickets')
    await flushPromises()
    expect(wrapper.findAll('.ticket-table .ticket-delete-icon')).toHaveLength(2)
    await wrapper.get('.ticket-table .ticket-delete-icon').trigger('click')
    expect(ticketApi.deleteTicket).not.toHaveBeenCalled()
    await wrapper.get('.confirm-ticket-delete').trigger('click')
    await flushPromises()
    expect(ticketApi.deleteTicket).toHaveBeenCalledWith(71)
    expect(wrapper.text()).toContain('Ticket deleted.')
    expect(wrapper.findAll('.ticket-table .ticket-delete-icon')).toHaveLength(1)
  })

  it('confirms technician account deletion and removes the account from the directory', async () => {
    directoryApi.deleteTechnician.mockResolvedValueOnce(undefined)
    const wrapper = mountRouter(true)
    await router.push('/admin/technicians')
    await flushPromises()
    await wrapper.get('.directory-table tbody tr .technician-delete-icon').trigger('click')
    expect(directoryApi.deleteTechnician).not.toHaveBeenCalled()
    await wrapper.get('.technician-delete-actions .button-primary').trigger('click')
    await flushPromises()
    expect(directoryApi.deleteTechnician).toHaveBeenCalledWith(7)
    expect(wrapper.text()).toContain('Technician account deleted.')
    expect(wrapper.text()).not.toContain('Sam Taylor')
  })

  it('keeps the technician visible when assignment history blocks deletion', async () => {
    directoryApi.deleteTechnician.mockRejectedValueOnce(new Error('Protected'))
    const wrapper = mountRouter(true)
    await router.push('/admin/technicians')
    await flushPromises()
    await wrapper.get('.directory-table tbody tr .technician-delete-icon').trigger('click')
    await wrapper.get('.technician-delete-actions .button-primary').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Could not delete this technician account.')
    expect(wrapper.text()).toContain('Sam Taylor')
  })

  it('counts only active technician assignments and shows their linked tickets', async () => {
    assignmentApi.listAssignments.mockResolvedValueOnce([assignmentRecord, { ...assignmentRecord, id: 16, tickets: 50, is_active: false }])
    const wrapper = mountRouter()
    await router.push('/admin/technicians')
    await flushPromises()
    const firstRow = wrapper.get('.directory-table tbody tr')
    expect(firstRow.findAll('td')[4]!.text()).toBe('1')
    await firstRow.get('button').trigger('click')
    const popup = document.querySelector('.directory-details-modal')!
    expect(popup.textContent).toContain('Technician Details')
    expect(popup.textContent).toContain('Cannot connect to Wi-Fi')
    expect(popup.textContent).not.toContain('Printer is jammed')
    expect(router.currentRoute.value.path).toBe('/admin/technicians')
    ;(popup.querySelector('.ticket-modal-close') as HTMLButtonElement).click()
    await flushPromises()
    expect(document.querySelector('.directory-details-modal')).toBeNull()
  })

  it('edits details inside the same card as the technician assignment', async () => {
    ticketApi.updateTicket.mockResolvedValue({ ...ticketRecords[0], problem_title: 'Updated title', problem_description: 'Updated description' })
    const wrapper = mountRouter()
    await router.push('/admin/tickets/51')
    await flushPromises()

    expect(wrapper.find('.ticket-detail-card .assignment-panel').exists()).toBe(true)
    await wrapper.get('.ticket-edit-button').trigger('click')
    await wrapper.get('#edit-ticket-title').setValue('Updated title')
    await wrapper.get('#edit-ticket-description').setValue('Updated description')
    await wrapper.get('.ticket-detail-edit').trigger('submit')
    await flushPromises()

    expect(ticketApi.updateTicket).toHaveBeenCalledWith('51', { problem_title: 'Updated title', problem_description: 'Updated description' })
    expect(wrapper.get('.ticket-detail-card').text()).toContain('Updated title')
    expect(wrapper.text()).toContain('Ticket details updated.')
    expect(wrapper.find('.ticket-detail-edit').exists()).toBe(false)
  })

  it('cancels editing without saving changes', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/tickets/51')
    await flushPromises()
    await wrapper.get('.ticket-edit-button').trigger('click')
    await wrapper.get('#edit-ticket-title').setValue('Unsaved title')
    await wrapper.get('.ticket-detail-edit button[type="button"]').trigger('click')
    expect(ticketApi.updateTicket).not.toHaveBeenCalled()
    expect(wrapper.get('.ticket-detail-card').text()).toContain('Cannot connect to Wi-Fi')
  })

  it('cancels an active ticket and removes its edit and assignment actions', async () => {
    ticketApi.updateTicketStatus.mockResolvedValueOnce({ ...ticketRecords[0]!, status: 'CANCELLED', cancellation_reason: 'Duplicate request.' })
    const wrapper = mountRouter()
    await router.push('/admin/tickets/51')
    await flushPromises()
    await wrapper.get('.ticket-cancel-actions button').trigger('click')
    expect(ticketApi.updateTicketStatus).not.toHaveBeenCalled()
    await wrapper.get('#ticket-cancellation-reason').setValue('Duplicate request.')
    await wrapper.get('.ticket-cancellation-form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Duplicate request.')
    expect(ticketApi.updateTicketStatus).toHaveBeenCalledWith('51', 'CANCELLED', 'Duplicate request.')
    expect(wrapper.text()).toContain('Ticket cancelled.')
    expect(wrapper.find('.ticket-cancel-actions').exists()).toBe(false)
    expect(wrapper.find('.ticket-edit-button').exists()).toBe(false)
    expect(wrapper.find('.assignment-form').exists()).toBe(false)
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


  it('loads customer and technician directories without exposing sensitive fields', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/customers')
    await flushPromises()
    expect(wrapper.text()).toContain('casey@example.test')
    expect(wrapper.get('.directory-table').text()).not.toContain('@casey')
    expect(wrapper.text()).not.toContain('address')

    await router.push('/admin/technicians')
    await flushPromises()
    expect(directoryApi.listTechnicians).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Network support')
    expect(wrapper.text()).toContain('Available')
    expect(wrapper.text()).toContain('Unavailable')
    expect(wrapper.text()).not.toContain('password')
    await wrapper.get('#technician-search').setValue('Hardware')
    await wrapper.get('.technician-availability-filter select').setValue('UNAVAILABLE')
    expect(wrapper.findAll('.directory-table tbody tr')).toHaveLength(1)
    expect(wrapper.get('.directory-table').text()).toContain('Jules Park')
    expect(wrapper.get('.directory-table').text()).not.toContain('@tech-jules')
    await wrapper.get('.technician-availability-filter select').setValue('AVAILABLE')
    expect(wrapper.text()).toContain('No matching technicians')
  })

  it('lets an admin create a technician account and refreshes the directory', async () => {
    directoryApi.createTechnician.mockResolvedValueOnce({})
    const wrapper = mountRouter(true)
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

  it('opens Add Technician in a popup and closes it without navigating', async () => {
    const wrapper = mountRouter()
    await router.push('/admin/technicians')
    await flushPromises()
    await wrapper.get('.dashboard-view-heading button').trigger('click')
    await flushPromises()
    const popup = document.querySelector('dialog')!
    expect(popup.hasAttribute('open')).toBe(true)
    expect(popup.querySelector('#create-technician-form')).not.toBeNull()
    expect(document.body.style.overflow).toBe('hidden')
    popup.dispatchEvent(new Event('cancel', { cancelable: true }))
    await flushPromises()
    expect(document.querySelector('dialog')).toBeNull()
    expect(router.currentRoute.value.path).toBe('/admin/technicians')
    expect(directoryApi.createTechnician).not.toHaveBeenCalled()
  })

  it('validates required technician account fields before sending the request', async () => {
    const wrapper = mountRouter(true)
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
