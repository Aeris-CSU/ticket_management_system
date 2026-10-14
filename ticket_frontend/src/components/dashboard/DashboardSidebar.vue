<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import type { UserRole } from '@/types/auth'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const route = useRoute()
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
    <p class="dashboard-sidebar-note">Support Made Simple.</p>
  </aside>
</template>
