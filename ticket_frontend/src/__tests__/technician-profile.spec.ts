import { expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import TechnicianProfileForm from '@/components/TechnicianProfileForm.vue'
const mocks = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn(), user: { first_name: 'Old' } }))
vi.mock('@/services/api', () => ({ api: { get: mocks.get, put: mocks.put } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: mocks.user }) }))
it('saves personal details using the technician profile ID and updates the greeting state', async () => {
  const profile = { id: 17, first_name: 'Old', last_name: '', email: '', specialization: 'IT' }
  mocks.get.mockResolvedValueOnce({ data: [profile] })
  mocks.put.mockResolvedValueOnce({ data: { ...profile, first_name: 'Sam' } })
  const w = mount(TechnicianProfileForm)
  await flushPromises()
  await w.get('[name="first_name"]').setValue('Sam')
  await w.get('form').trigger('submit')
  await flushPromises()
  expect(mocks.put).toHaveBeenCalledWith('technicians/update/17/', expect.objectContaining({ first_name: 'Sam' }))
  expect(mocks.user.first_name).toBe('Sam')
  expect(w.text()).toContain('Your profile has been updated.')
  expect(w.find('[name="username"]').exists()).toBe(false)
  w.unmount()
})
