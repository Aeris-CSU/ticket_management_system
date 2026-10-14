import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ActiveTicketQueue from '@/components/dashboard/ActiveTicketQueue.vue'
import type { Ticket } from '@/types/ticket'

function ticket(id: number, status: Ticket['status'], created_at: string): Ticket {
  return { id, status, created_at, updated_at: created_at, customer: 1, customer_name: 'Customer', problem_title: `Issue ${id}`, problem_description: 'Problem' }
}

const records = [
  ticket(9, 'OPEN', '2026-10-14T09:00:00Z'),
  ticket(4, 'ASSIGNED', '2026-10-13T09:00:00Z'),
  ticket(2, 'ONGOING', '2026-10-13T09:00:00Z'),
  ticket(1, 'RESOLVED', '2026-10-12T09:00:00Z'),
  ticket(3, 'CANCELLED', '2026-10-12T09:00:00Z'),
]
const mountQueue = () => mount(ActiveTicketQueue, { props: { tickets: records, assignments: [] }, global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
const ids = (wrapper: ReturnType<typeof mountQueue>) => wrapper.findAll('tbody tr').map((row) => row.findAll('td')[1]!.text())

describe('active first come, first served queue', () => {
  it('excludes terminal tickets and sorts by submission time then ID regardless of status', () => {
    const wrapper = mountQueue()
    expect(ids(wrapper)).toEqual(['#2', '#4', '#9'])
    expect(wrapper.findAll('tbody tr').map((row) => row.findAll('td')[0]!.text())).toEqual(['1', '2', '3'])
    expect(records.map((item) => item.id)).toEqual([9, 4, 2, 1, 3])
  })

  it('recomputes positions after resolution and appends newer submissions after refresh', async () => {
    const wrapper = mountQueue()
    await wrapper.setProps({ tickets: records.map((item) => item.id === 2 ? { ...item, status: 'RESOLVED' as const } : item).concat(ticket(10, 'OPEN', '2026-10-15T09:00:00Z')) })
    expect(ids(wrapper)).toEqual(['#4', '#9', '#10'])
    expect(wrapper.findAll('tbody tr').map((row) => row.findAll('td')[0]!.text())).toEqual(['1', '2', '3'])
  })

  it('shows only the active technician and an empty state when the queue clears', async () => {
    const wrapper = mountQueue()
    await wrapper.setProps({ assignments: [
      { id: 1, tickets: 4, ticket_title: 'Issue 4', technicians: 1, technician_name: 'Previous technician', is_active: false, created_at: '', assigned_at: '' },
      { id: 2, tickets: 4, ticket_title: 'Issue 4', technicians: 2, technician_name: 'Current technician', is_active: true, created_at: '', assigned_at: '' },
    ] })
    expect(wrapper.text()).toContain('Current technician')
    expect(wrapper.text()).not.toContain('Previous technician')
    expect(wrapper.text()).toContain('Unassigned')
    await wrapper.setProps({ tickets: [] })
    expect(wrapper.text()).toContain('No active support requests')
  })
})
