import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CustomerProfileModal from '@/components/dashboard/CustomerProfileModal.vue'
const mocks = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn(), user: { username: 'owner' } }))
vi.mock('@/services/api', () => ({ api: { get: mocks.get, put: mocks.put } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: mocks.user }) }))
const profile = { id: 42, username: 'owner', first_name: '', last_name: '', email: '', address: 'Old address', contact_number: '' }
afterEach(() => vi.resetAllMocks())
it('loads the own customer profile and saves using its profile ID', async () => {
  mocks.get.mockResolvedValueOnce({ data: [profile] })
  mocks.put.mockResolvedValueOnce({ data: { ...profile, username: 'updated', address: 'New address' } })
  const wrapper = mount(CustomerProfileModal, { global: { stubs: { DirectoryDetailsModal: { template: '<section><slot /></section>' } } } })
  await flushPromises()
  await wrapper.get('[name="username"]').setValue('updated')
  await wrapper.get('[name="address"]').setValue('New address')
  await wrapper.get('form').trigger('submit')
  await flushPromises()
  expect(mocks.get).toHaveBeenCalledWith('customers/')
  expect(mocks.put).toHaveBeenCalledWith('customers/42/', expect.objectContaining({ username: 'updated', address: 'New address' }))
  expect(mocks.user.username).toBe('updated')
  expect(wrapper.text()).toContain('Your profile has been updated.')
  wrapper.unmount()
})
