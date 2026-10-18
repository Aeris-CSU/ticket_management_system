import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import AdminProfileModal from '@/views/AccountProfileView.vue'

const mocks = vi.hoisted(() => ({ change: vi.fn(), logout: vi.fn(), replace: vi.fn() }))
vi.mock('@/services/auth', () => ({ changePasswordRequest: mocks.change, readableAuthError: () => 'Current password is incorrect.' }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: { username: 'localadmin' }, logout: mocks.logout }) }))
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: mocks.replace }), RouterLink: { template: '<a><slot /></a>' } }))
const wrappers: ReturnType<typeof mount>[] = []
afterEach(() => { wrappers.splice(0).forEach(w => w.unmount()); vi.resetAllMocks() })
function createForm() {
  const wrapper = mount(AdminProfileModal, { global: { stubs: { DirectoryDetailsModal: { template: '<section><slot /></section>' } } } })
  wrappers.push(wrapper)
  return wrapper
}
async function fill(wrapper: ReturnType<typeof createForm>) {
  expect(wrapper.get('.change-password-dropdown').attributes('open')).toBeUndefined()
  wrapper.get('.change-password-dropdown').element.setAttribute('open', '')
  await wrapper.get('[name="current_password"]').setValue('TickarlaAdmin123!')
  await wrapper.get('[name="new_password"]').setValue('NewAdminPassword123!')
  await wrapper.get('[name="confirm_password"]').setValue('NewAdminPassword123!')
}
describe('admin profile password change', () => {
  it('saves the password and returns to login', async () => {
    mocks.change.mockResolvedValueOnce(undefined)
    const wrapper = createForm()
    await fill(wrapper)
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(mocks.change).toHaveBeenCalledWith({ current_password: 'TickarlaAdmin123!', new_password: 'NewAdminPassword123!', confirm_password: 'NewAdminPassword123!' })
    expect(mocks.logout).toHaveBeenCalledOnce()
    expect(mocks.replace).toHaveBeenCalledWith({ path: '/login', query: { passwordChanged: '1' } })
  })
  it('keeps the form open when the server rejects the current password', async () => {
    mocks.change.mockRejectedValueOnce(new Error('Invalid'))
    const wrapper = createForm()
    await fill(wrapper)
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Current password is incorrect.')
    expect(mocks.logout).not.toHaveBeenCalled()
  })
  it('rejects mismatched confirmation before sending', async () => {
    const wrapper = createForm()
    await fill(wrapper)
    await wrapper.get('[name="confirm_password"]').setValue('different')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.text()).toContain('Passwords do not match.')
    expect(mocks.change).not.toHaveBeenCalled()
  })
})
