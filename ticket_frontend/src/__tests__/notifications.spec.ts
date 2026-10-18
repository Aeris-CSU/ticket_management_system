import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import NotificationsView from '@/views/NotificationsView.vue'
const mocks = vi.hoisted(() => ({ get: vi.fn(), update: vi.fn(), push: vi.fn() }))
vi.mock('@/services/notifications', () => ({ getNotifications: mocks.get, updateNotifications: mocks.update }))
vi.mock('vue-router', () => ({ useRoute: () => ({ meta: { role: 'ADMIN' } }), useRouter: () => ({ push: mocks.push }) }))
const first = { id: 1, message: 'New ticket TCK 20261018-0001 was submitted by a customer.', event: 'SUBMITTED', is_read: false, created_at: '2026-10-18T12:00:00Z', ticket_id: 7 }
let wrappers: ReturnType<typeof mount>[] = []
beforeEach(() => {
  vi.resetAllMocks()
  mocks.get.mockResolvedValue({ results: [first], unread_count: 1, total: 1, has_more: false })
  mocks.update.mockResolvedValue(undefined)
})
afterEach(() => { wrappers.forEach(w => w.unmount()); wrappers = [] })
async function create() { const w = mount(NotificationsView); wrappers.push(w); await flushPromises(); return w }
it('marks a clicked notification read before opening the permitted ticket', async () => {
  const w = await create()
  await w.get('.notification-message').trigger('click')
  await flushPromises()
  expect(mocks.update).toHaveBeenCalledWith('read', [1], false)
  expect(mocks.push).toHaveBeenCalledWith('/admin/tickets/7')
})
it('requires confirmation before deleting selected notifications', async () => {
  const w = await create()
  await w.get('.notification-list input').setValue(true)
  await w.findAll('button').find(b => b.text() === 'Delete selected')!.trigger('click')
  expect(mocks.update).not.toHaveBeenCalled()
  await w.get('.notification-confirm .button-primary').trigger('click')
  await flushPromises()
  expect(mocks.update).toHaveBeenCalledWith('delete', [1], false)
})
it('supports unread filtering and explicit confirmed deletion of all history', async () => {
  const w = await create()
  await w.get('.notification-tabs button:nth-child(2)').trigger('click')
  await flushPromises()
  expect(mocks.get).toHaveBeenCalledWith('unread', 1)
  await w.findAll('button').find(b => b.text() === 'Delete all')!.trigger('click')
  expect(mocks.update).not.toHaveBeenCalled()
  await w.get('.notification-confirm .button-primary').trigger('click')
  await flushPromises()
  expect(mocks.update).toHaveBeenCalledWith('delete', [], true)
})
it('does not navigate when access to the related ticket is no longer available', async () => {
  mocks.get.mockResolvedValue({ results: [{ ...first, ticket_id: null, is_read: true }], unread_count: 0, total: 1, has_more: false })
  const w = await create()
  await w.get('.notification-message').trigger('click')
  await flushPromises()
  expect(mocks.push).not.toHaveBeenCalled()
  expect(w.text()).toContain('Ticket no longer available')
})
