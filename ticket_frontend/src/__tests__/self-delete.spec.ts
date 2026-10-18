import { expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import DashboardSidebar from '@/components/dashboard/DashboardSidebar.vue'
const mocks = vi.hoisted(() => ({ remove: vi.fn(), logout: vi.fn(), replace: vi.fn(), user: { role: 'CUSTOMER' } }))
vi.mock('@/services/api', () => ({ api: { delete: mocks.remove } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: mocks.user, logout: mocks.logout }) }))
vi.mock('vue-router', () => ({ useRoute: () => ({ meta: { role: 'CUSTOMER' } }), useRouter: () => ({ replace: mocks.replace }), RouterLink: { template: '<a><slot /></a>' } }))
it('requires confirmation then deletes the current account and logs out', async () => {
  mocks.remove.mockResolvedValueOnce(undefined)
  const wrapper = mount(DashboardSidebar, { props: { open: true }, global: { stubs: { DirectoryDetailsModal: { template: '<section><slot /></section>' } } } })
  await wrapper.get('.dashboard-delete-account').trigger('click')
  expect(mocks.remove).not.toHaveBeenCalled()
  await wrapper.get('.confirm-self-delete').trigger('click')
  await flushPromises()
  expect(mocks.remove).toHaveBeenCalledWith('accounts/me/')
  expect(mocks.logout).toHaveBeenCalledOnce()
  expect(mocks.replace).toHaveBeenCalledWith('/')
  wrapper.unmount()
})
