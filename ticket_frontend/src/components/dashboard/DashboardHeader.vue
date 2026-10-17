<script setup lang="ts">
import { computed, ref } from 'vue'
import AdminProfileModal from './AdminProfileModal.vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'
import type { UserRole } from '@/types/auth'

const emit = defineEmits<{ openMenu: [] }>()
defineProps<{ menuOpen: boolean }>()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const username = computed(() => auth.user?.username || 'Account')
const roleLabel = computed(() => ({ ADMIN: 'Admin', TECHNICIAN: 'Technician', CUSTOMER: 'Customer' }[auth.user?.role as UserRole] || 'User'))
const title = computed(() => String(route.meta.title || 'Dashboard'))
const profileOpen = ref(false)

function logout() {
  auth.logout()
  void router.replace('/login')
}
</script>

<template>
  <header class="dashboard-header">
    <button
      class="dashboard-menu-button"
      type="button"
      aria-label="Open navigation menu"
      aria-controls="dashboard-sidebar"
      :aria-expanded="menuOpen"
      @click="emit('openMenu')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
    </button>
    <h1>{{ title }}</h1>
    <div class="dashboard-account">
      <button v-if="auth.user?.role === 'ADMIN'" class="dashboard-profile-button" type="button" aria-label="Open admin profile" :aria-expanded="profileOpen" @click="profileOpen = true">
      <span class="dashboard-avatar" aria-hidden="true">{{ username.charAt(0).toUpperCase() }}</span>
      <span class="dashboard-account-copy"><strong>{{ username }}</strong><small>{{ roleLabel }}</small></span>
      </button>
      <template v-else><span class="dashboard-avatar" aria-hidden="true">{{ username.charAt(0).toUpperCase() }}</span><span class="dashboard-account-copy"><strong>{{ username }}</strong><small>{{ roleLabel }}</small></span></template>
      <ThemeToggle />
      <button class="dashboard-logout" type="button" @click="logout">Log out</button>
    </div>
  </header>
  <AdminProfileModal v-if="profileOpen && auth.user?.role === 'ADMIN'" @close="profileOpen = false" />
</template>
