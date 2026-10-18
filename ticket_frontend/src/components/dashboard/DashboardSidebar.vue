<script setup lang="ts">
import AccountAvatar from '@/components/AccountAvatar.vue'
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import DirectoryDetailsModal from './DirectoryDetailsModal.vue'
import { api } from '@/services/api'
import { readableAuthError } from '@/services/auth'
import type { UserRole } from '@/types/auth'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const confirmDelete = ref(false)
const deleting = ref(false)
const deleteError = ref('')
async function deleteMyAccount() {
  if (deleting.value) return
  deleting.value = true
  deleteError.value = ''
  try {
    await api.delete('accounts/me/')
    confirmDelete.value = false
    auth.logout()
    await router.replace('/')
  } catch (error) {
    deleteError.value = readableAuthError(error, 'Could not delete your account. Please try again.')
  } finally { deleting.value = false }
}
function logout() {
  auth.logout()
  void router.replace('/')
}
const role = computed(() => route.meta.role as UserRole)

const navigation: Record<UserRole, { label: string; path?: string }[]> = {
  ADMIN: [
    { label: 'Dashboard', path: '/admin' },
    { label: 'All Tickets', path: '/admin/tickets' },
    { label: 'Customers', path: '/admin/customers' },
    { label: 'Technicians', path: '/admin/technicians' },
  ],
  TECHNICIAN: [{ label: 'Dashboard', path: '/technician' }, { label: 'Assigned Tickets', path: '/technician/tickets' }],
  CUSTOMER: [
    { label: 'Dashboard', path: '/customer' },
    { label: 'My Tickets', path: '/customer/tickets' },
    { label: 'Create Ticket', path: '/customer/tickets/new' },
  ],
}

const roleNames: Record<UserRole, string> = {
  ADMIN: 'Administrator',
  TECHNICIAN: 'Technician',
  CUSTOMER: 'Customer',
}
</script>

<template>
  <aside id="dashboard-sidebar" class="dashboard-sidebar" :class="{ 'is-open': open }" aria-label="Main navigation">
    <div class="dashboard-brand">
      <span class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none"><path d="M4.5 7.5h15v10a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-10Z"/><path d="M4.5 10h4a2 2 0 1 0 0-4h-4m15 4h-4a2 2 0 1 1 0-4h4"/></svg>
      </span>
      <span>Tickarla</span>
      <button class="dashboard-close" type="button" aria-label="Close navigation menu" @click="emit('close')">×</button>
    </div>
    <p class="dashboard-role-caption">{{ roleNames[role] }} workspace</p>
    <nav class="dashboard-nav" aria-label="Dashboard">
      <template v-for="item in navigation[role]" :key="item.label">
        <RouterLink
          v-if="item.path"
          :to="item.path"
          class="dashboard-nav-item"
          exact-active-class="is-active"
          @click="emit('close')"
        >
          <span class="dashboard-nav-icon" aria-hidden="true">{{ item.label === 'Dashboard' ? '⌂' : '•' }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
        <span v-else class="dashboard-nav-item is-disabled" aria-disabled="true">
          <span class="dashboard-nav-icon" aria-hidden="true">•</span>
          <span>{{ item.label }}</span>
          <small>Coming soon</small>
        </span>
      </template>
    </nav>
    <div class="dashboard-sidebar-footer">
      <details v-if="auth.user" class="sidebar-account-menu">
        <summary :aria-label="`${roleNames[role]} account menu`"><span class="dashboard-avatar" aria-hidden="true"><AccountAvatar /></span><span class="sidebar-account-copy"><strong>{{ role === 'CUSTOMER' ? (auth.user?.first_name?.trim() || auth.user?.username) : auth.user?.username }}</strong><small>My account</small></span><span class="sidebar-account-chevron" aria-hidden="true">&#8964;</span></summary>
        <div class="sidebar-account-options">
          <RouterLink class="sidebar-edit-profile" :to="`/${role.toLowerCase()}/profile`" @click="emit('close')">Edit profile</RouterLink>
          <button v-if="role !== 'ADMIN'" class="dashboard-delete-account" type="button" @click="confirmDelete = true; deleteError = ''">Delete my account</button>
        </div>
      </details>
      <p class="dashboard-sidebar-note">Support Made Simple.</p>
      <button class="dashboard-logout" type="button" @click="logout">Log out</button>

    </div>
  </aside>
  <DirectoryDetailsModal v-if="confirmDelete" title="Delete my account" :dismissible="!deleting" @close="confirmDelete = false">
    <p>Delete your account and login permanently? This cannot be undone.</p>
    <p>Accounts with ticket or assignment history cannot be deleted.</p>
    <p v-if="deleteError" class="form-message form-error" role="alert">{{ deleteError }}</p>
    <div class="ticket-form-actions"><button class="button button-secondary" type="button" :disabled="deleting" @click="confirmDelete = false">Keep My Account</button><button class="button button-primary confirm-self-delete" type="button" :disabled="deleting" @click="deleteMyAccount">{{ deleting ? 'Deleting...' : 'Delete My Account' }}</button></div>
  </DirectoryDetailsModal>
</template>
