<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { listTickets } from '@/services/tickets'
import { listAssignments } from '@/services/assignments'
import { readableAuthError } from '@/services/auth'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import TicketStatusOverview from '@/components/dashboard/TicketStatusOverview.vue'
import ActiveTicketQueue from '@/components/dashboard/ActiveTicketQueue.vue'
import TicketDetailsModal from '@/components/dashboard/TicketDetailsModal.vue'
import type { Assignment } from '@/types/admin'
import type { Ticket } from '@/types/ticket'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

const auth = useAuthStore()
const route = useRoute()
const role = computed(() => route.meta.role as UserRole)
const quickActions = computed(() => role.value === 'ADMIN' ? [
  { title: 'Manage tickets', text: 'Review requests and assign support.', path: '/admin/tickets', icon: 'tickets' },
  { title: 'Your technicians', text: 'View your team and availability.', path: '/admin/technicians', icon: 'team' },
  { title: 'Customer directory', text: 'Find customer account details.', path: '/admin/customers', icon: 'people' },
] : role.value === 'TECHNICIAN' ? [
  { title: 'Assigned tickets', text: 'Review your work and update progress.', path: '/technician/tickets', icon: 'tickets' },
] : [
  { title: 'Create a ticket', text: 'Tell your support team what you need.', path: '/customer/tickets/new', icon: 'plus' },
  { title: 'My support requests', text: 'See the latest status of your tickets.', path: '/customer/tickets', icon: 'tickets' },
])
const tickets = ref<Ticket[]>([])
const assignments = ref<Assignment[]>([])
const assignmentError = ref('')
const selectedTicketId = ref<number | null>(null)

async function ticketChanged(updated: Ticket) {
  tickets.value = tickets.value.map((item) => item.id === updated.id ? updated : item)
  if (role.value === 'CUSTOMER') return
  try {
    assignments.value = await listAssignments()
    if (role.value === 'TECHNICIAN') {
      const activeIds = new Set(assignments.value.filter(item => item.is_active).map(item => item.tickets))
      tickets.value = tickets.value.filter(item => activeIds.has(item.id) && !['RESOLVED', 'CANCELLED'].includes(item.status))
    }
  }
  catch { assignmentError.value = 'Could not refresh technician assignments. Refresh tickets to try again.' }
}
const isLoading = ref(false)
const errorMessage = ref('')
const hasLoaded = ref(false)

const stats = computed(() => [
  { label: role.value === 'ADMIN' ? 'Total Tickets' : role.value === 'TECHNICIAN' ? 'Total Assigned Tickets' : 'My Tickets', value: tickets.value.length },
  { label: role.value === 'TECHNICIAN' ? 'Assigned' : 'Open Tickets', value: role.value === 'TECHNICIAN' ? tickets.value.filter((ticket) => ticket.status === 'ASSIGNED').length : tickets.value.filter((ticket) => ticket.status === 'OPEN').length },
  { label: role.value === 'ADMIN' ? 'Ongoing Tickets' : role.value === 'TECHNICIAN' ? 'Ongoing' : 'Ongoing', value: role.value === 'TECHNICIAN' ? tickets.value.filter((ticket) => ticket.status === 'ONGOING').length : tickets.value.filter((ticket) => ticket.status === 'ASSIGNED' || ticket.status === 'ONGOING').length },
  { label: role.value === 'ADMIN' ? 'Resolved Tickets' : 'Resolved', value: tickets.value.filter((ticket) => ticket.status === 'RESOLVED').length },
])
const recentTickets = computed(() => tickets.value.slice(0, 5))

async function refreshTickets() {
  isLoading.value = true
  errorMessage.value = ''
  assignmentError.value = ''
  try {
    if (role.value === 'TECHNICIAN') {
      const [assignedTickets, assignments] = await Promise.all([listTickets(), listAssignments()])
      const activeTicketIds = new Set(assignments.filter((assignment) => assignment.is_active).map((assignment) => assignment.tickets))
      tickets.value = assignedTickets.filter((ticket) => activeTicketIds.has(ticket.id))
    } else if (role.value === 'ADMIN') {
      const [ticketResult, assignmentResult] = await Promise.allSettled([listTickets(), listAssignments()])
      if (ticketResult.status === 'rejected') throw ticketResult.reason
      tickets.value = ticketResult.value
      if (assignmentResult.status === 'fulfilled') assignments.value = assignmentResult.value
      else {
        assignments.value = []
        assignmentError.value = 'Technician assignments could not be loaded. Refresh to try again.'
      }
    } else {
      tickets.value = await listTickets()
    }
    hasLoaded.value = true
  } catch (error) {
    errorMessage.value = readableAuthError(error, role.value === 'ADMIN' ? 'Could not load ticket data. Please try again.' : role.value === 'TECHNICIAN' ? 'Could not load your assigned tickets. Please try again.' : 'Could not load your tickets. Please try again.')
  } finally {
    isLoading.value = false
  }
}
onMounted(refreshTickets)
const overview = computed(() => ({
  ADMIN: {
    heading: 'Admin Dashboard',
    description: 'Monitor active support requests in submission order and manage technician assignments.',
  },
  TECHNICIAN: {
    heading: 'Technician Dashboard',
    description: 'View and manage your assigned support requests.',
  },
  CUSTOMER: {
    heading: 'Customer Dashboard',
    description: 'Track your support requests and stay updated on their progress.',
  },
}[role.value]))
</script>

<template>
  <section class="dashboard-overview" :class="{ 'admin-overview': role === 'ADMIN' }" aria-labelledby="dashboard-heading">
    <div class="dashboard-page-intro">
      <div class="dashboard-intro-copy">
      <p class="eyebrow">YOUR {{ role === 'ADMIN' ? 'SUPPORT OPERATIONS' : role === 'TECHNICIAN' ? 'TECHNICIAN WORKSPACE' : 'CUSTOMER WORKSPACE' }}</p>
      <h2 id="dashboard-heading">{{ overview.heading }}</h2>
      <p>{{ overview.description }}</p>
      <div class="dashboard-welcome-name">Welcome back, {{ auth.user?.first_name || auth.user?.username || 'there' }}.</div>
      </div>
      <div class="dashboard-hero-art" aria-hidden="true"><svg viewBox="0 0 160 150" fill="none"><rect x="39" y="24" width="87" height="110" rx="13" fill="white" fill-opacity=".08" stroke="white" stroke-opacity=".25"/><rect x="54" y="13" width="57" height="22" rx="7" fill="#76a8ee"/><path d="M57 57h49M57 71h34M57 85h42" stroke="#a7c9f8" stroke-width="5" stroke-linecap="round"/><circle cx="113" cy="113" r="24" fill="#345f94" stroke="#a7c9f8" stroke-opacity=".4"/><path d="m102 113 8 8 15-17" stroke="#c8f3e3" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
      <button v-if="role === 'ADMIN'" class="button button-secondary dashboard-refresh" type="button" :disabled="isLoading" @click="refreshTickets"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M20 7v5h-5M4 17v-5h5M6.1 7a7 7 0 0 1 11.5-1L20 9M4 15l2.4 3A7 7 0 0 0 17.9 17" /></svg>{{ isLoading ? 'Refreshing...' : 'Refresh Tickets' }}</button>
    </div>
    <div v-if="isLoading" class="dashboard-message" role="status">{{ role === 'ADMIN' ? 'Loading ticket overview…' : role === 'TECHNICIAN' ? 'Loading your assigned tickets…' : 'Loading your ticket overview…' }}</div>
      <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
      <div v-else-if="hasLoaded" class="dashboard-stat-grid" aria-label="Ticket overview">
        <article v-for="(stat, index) in stats" :key="stat.label" class="dashboard-stat-card">
          <span class="dashboard-stat-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <template v-if="index === 0"><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4V2h6v2M9 10h6M9 14h6M9 18h3" /></template>
              <template v-else-if="index === 1"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></template>
              <template v-else-if="index === 2"><path d="m14 6 4-3 3 3-3 4M10 18l-4 3-3-3 3-4M8 16l8-8" /><path d="m5 5 14 14" /></template>
              <template v-else><circle cx="12" cy="12" r="9" /><path d="m8 12 3 3 5-6" /></template>
            </svg>
          </span>
          <span>{{ stat.label }}</span><strong>{{ stat.value }}</strong>
          <small v-if="role === 'ADMIN'">{{ stat.label === 'Ongoing Tickets' ? 'Assigned or currently being handled.' : stat.label === 'Total Tickets' ? 'All submitted support requests.' : stat.label === 'Open Tickets' ? 'Waiting to be assigned.' : 'Completed support requests.' }}</small>
        </article>
      </div>
      <div v-if="role !== 'TECHNICIAN'" class="dashboard-workspace-panels">
      <TicketStatusOverview v-if="hasLoaded && !isLoading && !errorMessage" :tickets="tickets" />
      <div class="dashboard-action-panel"><div class="dashboard-action-heading"><span>YOUR WORKSPACE</span><h3>What would you like to do?</h3></div>
      <nav class="dashboard-quick-actions" aria-label="Workspace shortcuts">
        <RouterLink v-for="action in quickActions" :key="action.path" :to="action.path" class="dashboard-quick-card">
          <span class="dashboard-quick-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path v-if="action.icon === 'plus'" d="M12 5v14M5 12h14"/><template v-else-if="action.icon === 'tickets'"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></template><template v-else><circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M18 15a5 5 0 0 1 3 5"/></template></svg></span>
          <span><strong>{{ action.title }}</strong><small>{{ action.text }}</small></span><span class="dashboard-quick-arrow" aria-hidden="true">&#8599;</span>
        </RouterLink>
      </nav>
      </div>
      </div>
      <p v-if="assignmentError" class="form-message form-error" role="alert">{{ assignmentError }}</p>
      <ActiveTicketQueue v-if="role === 'ADMIN' && !isLoading && !errorMessage && hasLoaded && !assignmentError" :tickets="tickets" :assignments="assignments" @view-ticket="selectedTicketId = $event" />
      <TicketDetailsModal v-if="selectedTicketId !== null" :ticket-id="selectedTicketId" @close="selectedTicketId = null" @changed="ticketChanged" />
      <section v-if="role !== 'ADMIN' && !isLoading && !errorMessage && hasLoaded" class="dashboard-recent" aria-labelledby="recent-tickets-heading">
        <div class="dashboard-section-heading">
          <div><h3 id="recent-tickets-heading">{{ role === 'TECHNICIAN' ? 'Recent Assigned Tickets' : 'Recent Tickets' }}</h3><p>{{ role === 'TECHNICIAN' ? 'The latest tickets assigned to you.' : 'Your latest support requests.' }}</p></div>
          <RouterLink :to="role === 'TECHNICIAN' ? '/technician/tickets' : '/customer/tickets'" class="dashboard-text-link">View all</RouterLink>
        </div>
        <div v-if="recentTickets.length" class="dashboard-recent-list">
          <button type="button" @click="selectedTicketId = ticket.id" v-for="ticket in recentTickets" :key="ticket.id" class="dashboard-recent-row" :class="{ 'is-admin': role === 'TECHNICIAN' }">
            <span class="dashboard-ticket-id">{{ ticket.ticket_number || `#${ticket.id}` }}</span>
            <span class="dashboard-ticket-title">{{ ticket.problem_title }}</span>
            <span v-if="role === 'TECHNICIAN'" class="dashboard-ticket-customer">{{ ticket.customer_name }}</span>
            <TicketStatusBadge :status="ticket.status" />
            <time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleDateString() }}</time>
          </button>
        </div>
        <div v-else class="dashboard-list-empty">
          <p>{{ role === 'TECHNICIAN' ? 'No tickets are currently assigned to you.' : 'You have not created any tickets yet.' }}</p>
        </div>
      </section>
  </section>
</template>

<style scoped>
.dashboard-workspace-panels { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 24px; }
.dashboard-action-panel { padding: 26px; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); }
.dashboard-action-heading > span { color: var(--muted); font-size: 9px; font-weight: 750; letter-spacing: .14em; }
.dashboard-action-heading h3 { margin: 10px 0 23px; color: var(--text-primary); font-size: 20px; letter-spacing: -.035em; }
.dashboard-action-panel .dashboard-quick-actions { flex-direction: column; gap: 10px; }
.dashboard-action-panel .dashboard-quick-card { flex: none; padding: 15px; background: var(--surface-raised); border-color: transparent; border-radius: 12px; }
.dashboard-action-panel .dashboard-quick-card:hover { border-color: #8aafe4; }
@media (max-width: 950px) { .dashboard-workspace-panels { grid-template-columns: minmax(0, 1fr); } }
</style>
