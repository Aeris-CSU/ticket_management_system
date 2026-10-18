<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import CustomerProfileModal from './CustomerProfileModal.vue'
import AdminProfileModal from './AdminProfileModal.vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'
import type { UserRole } from '@/types/auth'

const emit = defineEmits<{ openMenu: [] }>()
const props = defineProps<{ menuOpen: boolean; desktopCollapsed?: boolean }>()
const isDesktop = ref(window.innerWidth > 700)
const menuExpanded = computed(() => isDesktop.value ? !props.desktopCollapsed : props.menuOpen)
function updateViewport() { isDesktop.value = window.innerWidth > 700 }
onMounted(() => window.addEventListener('resize', updateViewport))
onUnmounted(() => window.removeEventListener('resize', updateViewport))
const auth = useAuthStore()
const route = useRoute()
const username = computed(() => auth.user?.username || 'Account')
const roleLabel = computed(() => ({ ADMIN: 'Admin', TECHNICIAN: 'Technician', CUSTOMER: 'Customer' }[auth.user?.role as UserRole] || 'User'))
const title = computed(() => String(route.meta.title || 'Dashboard'))
const profileOpen = ref(false)

</script>

<template>
  <header class="dashboard-header">
    <button
      class="dashboard-menu-button"
      type="button"
      :aria-label="menuExpanded ? 'Hide navigation menu' : 'Show navigation menu'"
      aria-controls="dashboard-sidebar"
      :aria-expanded="menuExpanded"
      @click="emit('openMenu')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
    </button>
    <h1>{{ title }}</h1>
    <div class="dashboard-account">
      <button v-if="auth.user?.role === 'ADMIN' || auth.user?.role === 'CUSTOMER' || auth.user?.role === 'TECHNICIAN'" class="dashboard-profile-button" type="button" :aria-label="auth.user?.role === 'ADMIN' ? 'Open admin profile' : auth.user?.role === 'TECHNICIAN' ? 'Open technician profile' : 'Open customer profile'" :aria-expanded="profileOpen" @click="profileOpen = true">
      <span class="dashboard-avatar" aria-hidden="true">{{ username.charAt(0).toUpperCase() }}</span>
      <span class="dashboard-account-copy"><strong>{{ username }}</strong><small>{{ roleLabel }}</small></span>
      </button>
      <template v-else><span class="dashboard-avatar" aria-hidden="true">{{ username.charAt(0).toUpperCase() }}</span><span class="dashboard-account-copy"><strong>{{ username }}</strong><small>{{ roleLabel }}</small></span></template>
      <ThemeToggle />
    </div>
  </header>
  <CustomerProfileModal v-if="profileOpen && auth.user?.role === 'CUSTOMER'" @close="profileOpen = false" />
  <AdminProfileModal v-if="profileOpen && (auth.user?.role === 'ADMIN' || auth.user?.role === 'TECHNICIAN')" @close="profileOpen = false" />
</template>
