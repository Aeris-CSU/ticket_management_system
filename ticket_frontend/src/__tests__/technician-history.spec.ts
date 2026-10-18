import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import TechnicianHistoryView from '@/views/TechnicianHistoryView.vue'
const mocks = vi.hoisted(() => ({ get: vi.fn() }))
vi.mock('@/services/api', () => ({ api: { get: mocks.get } }))
afterEach(() => vi.resetAllMocks())
it('shows read-only history with distinct assignment outcome and current ticket status', async () => {
  mocks.get.mockResolvedValue({ data: { count: 1, next: null, results: [{ id: 1, ticket_id: 7, ticket_number: 'TCK 20261018-0001', problem_title: 'Printer issue', problem_description: 'Offline', current_status: 'RESOLVED', customer_name: 'Casey', created_at: '2026-10-18T01:00:00Z', ended_at: '2026-10-18T02:00:00Z', end_reason: 'REASSIGNED' }] } })
  const w = mount(TechnicianHistoryView, { global: { stubs: { DirectoryDetailsModal: { template: '<section><slot /></section>' } } } })
  await flushPromises()
  expect(w.text()).toContain('Reassigned away')
  expect(w.get('tbody').text()).toContain('Resolved')
  await w.get('tbody button').trigger('click')
  expect(w.text()).toContain('Historical access only')
  expect(w.find('.ticket-edit-button').exists()).toBe(false)
  await w.get('select').setValue('RESOLVED')
  await flushPromises()
  expect(mocks.get).toHaveBeenLastCalledWith('assignments/history/', { params: { page: 1, search: '', outcome: 'RESOLVED' } })
  w.unmount()
})
