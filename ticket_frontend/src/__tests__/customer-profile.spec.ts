import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CustomerProfileModal from '@/views/CustomerProfileView.vue'
const mocks = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn(), user: { username: 'owner' } }))
vi.mock('@/services/api', () => ({ api: { get: mocks.get, put: mocks.put } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: mocks.user }) }))
const profile = { id: 42, username: 'owner', first_name: '', last_name: '', email: '', address: 'Old address', contact_number: '' }
afterEach(() => vi.resetAllMocks())
it('loads the own customer profile and saves using its profile ID', async () => {
  mocks.get.mockResolvedValueOnce({ data: [profile] })
  mocks.put.mockResolvedValueOnce({ data: { ...profile, first_name: 'Updated', address: 'New address' } })
  const wrapper = mount(CustomerProfileModal, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
  await flushPromises()
  expect(wrapper.find('[name="username"]').exists()).toBe(false)
  await wrapper.get('[name="first_name"]').setValue('Updated')
  await wrapper.get('[name="address"]').setValue('New address')
  await wrapper.get('form').trigger('submit')
  await flushPromises()
  expect(mocks.get).toHaveBeenCalledWith('customers/')
  expect(mocks.put).toHaveBeenCalledWith('customers/42/', expect.objectContaining({ first_name: 'Updated', address: 'New address' }))
  expect(mocks.user.username).toBe('owner')
  expect(wrapper.text()).toContain('Your profile has been updated.')
  wrapper.unmount()
})

it('saves a changed address without resubmitting a legacy contact number and reloads saved data', async () => {
  const old = { ...profile, contact_number: '123' }
  const updated = { ...old, address: 'Saved address' }
  mocks.get.mockResolvedValueOnce({ data: [old] }).mockResolvedValueOnce({ data: [updated] })
  mocks.put.mockResolvedValueOnce({ data: updated })
  const options = { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } }
  const wrapper = mount(CustomerProfileModal, options)
  await flushPromises()
  await wrapper.get('[name="address"]').setValue('Saved address')
  await wrapper.get('form').trigger('submit')
  await flushPromises()
  expect(mocks.put).toHaveBeenCalledWith('customers/42/', { address: 'Saved address' })
  expect(wrapper.text()).toContain('Your profile has been updated.')
  wrapper.unmount()
  const reopened = mount(CustomerProfileModal, options)
  await flushPromises()
  expect((reopened.get('[name="address"]').element as HTMLInputElement).value).toBe('Saved address')
  reopened.unmount()
})
it('blocks a newly entered invalid contact number and shows an error', async () => {
  mocks.get.mockResolvedValueOnce({ data: [profile] })
  const wrapper = mount(CustomerProfileModal, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
  await flushPromises()
  await wrapper.get('[name="contact_number"]').setValue('123')
  await wrapper.get('form').trigger('submit')
  expect(mocks.put).not.toHaveBeenCalled()
  expect(wrapper.get('form [role="alert"]').text()).toContain('Philippine mobile number')
  wrapper.unmount()
})
