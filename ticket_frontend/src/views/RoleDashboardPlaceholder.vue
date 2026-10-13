<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { listTickets } from '@/services/tickets'
import { listAssignments } from '@/services/assignments'
import { readableAuthError } from '@/services/auth'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import type { Ticket } from '@/types/ticket'
import type { UserRole } from '@/types/auth'

const route = useRoute()
const role = computed(() => route.meta.role as UserRole)
const tickets = ref<Ticket[]>([])
const isLoading = ref(false)
const errorMessage = ref('')
const hasLoaded = ref(false)

const stats = computed(() => [
  { label: role.value === 'ADMIN' ? 'Total Tickets' : role.value === 'TECHNICIAN' ? 'Total Assigned Tickets' : 'My Tickets', value: tickets.value.length },
  { label: role.value === 'TECHNICIAN' ? 'Assigned' : 'Open Tickets', value: role.value === 'TECHNICIAN' ? tickets.value.filter((ticket) => ticket.status === 'ASSIGNED').length : tickets.value.filter((ticket) => ticket.status === 'OPEN').length },
  { label: role.value === 'TECHNICIAN' ? 'Ongoing' : 'In Progress', value: role.value === 'TECHNICIAN' ? tickets.value.filter((ticket) => ticket.status === 'ONGOING').length : tickets.value.filter((ticket) => ticket.status === 'ASSIGNED' || ticket.status === 'ONGOING').length },
  { label: 'Resolved', value: tickets.value.filter((ticket) => ticket.status === 'RESOLVED').length },
])
const recentTickets = computed(() => tickets.value.slice(0, 5))

onMounted(async () => {
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (role.value === 'TECHNICIAN') {
      const [assignedTickets, assignments] = await Promise.all([listTickets(), listAssignments()])
      const activeTicketIds = new Set(assignments.filter((assignment) => assignment.is_active).map((assignment) => assignment.tickets))
      tickets.value = assignedTickets.filter((ticket) => activeTicketIds.has(ticket.id))
    } else {
      tickets.value = await listTickets()
    }
    hasLoaded.value = true
  } catch (error) {
    errorMessage.value = readableAuthError(error, role.value === 'ADMIN' ? 'Could not load ticket data. Please try again.' : role.value === 'TECHNICIAN' ? 'Could not load your assigned tickets. Please try again.' : 'Could not load your tickets. Please try again.')
  } finally {
    isLoading.value = false
  }
})
const overview = computed(() => ({
  ADMIN: {
    heading: 'Admin Dashboard',
    description: 'Review support tickets, assignments, and user directories from one place.',
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
  <section class="dashboard-overview" aria-labelledby="dashboard-heading">
    <div class="dashboard-page-intro">
      <p class="eyebrow">Overview</p>
      <h2 id="dashboard-heading">{{ overview.heading }}</h2>
      <p>{{ overview.description }}</p>
    </div>
    <div v-if="isLoading" class="dashboard-message" role="status">{{ role === 'ADMIN' ? 'Loading ticket overview…' : role === 'TECHNICIAN' ? 'Loading your assigned tickets…' : 'Loading your ticket overview…' }}</div>
      <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
      <div v-else-if="hasLoaded" class="dashboard-stat-grid" aria-label="Ticket overview">
        <article v-for="stat in stats" :key="stat.label" class="dashboard-stat-card">
          <span>{{ stat.label }}</span><strong>{{ stat.value }}</strong>
        </article>
      </div>
      <section v-if="!isLoading && !errorMessage && hasLoaded" class="dashboard-recent" aria-labelledby="recent-tickets-heading">
        <div class="dashboard-section-heading">
          <div><h3 id="recent-tickets-heading">{{ role === 'TECHNICIAN' ? 'Recent Assigned Tickets' : 'Recent Tickets' }}</h3><p>{{ role === 'ADMIN' ? 'The latest customer support requests.' : role === 'TECHNICIAN' ? 'The latest tickets assigned to you.' : 'Your latest support requests.' }}</p></div>
          <RouterLink :to="role === 'ADMIN' ? '/admin/tickets' : role === 'TECHNICIAN' ? '/technician/tickets' : '/customer/tickets'" class="dashboard-text-link">View all</RouterLink>
        </div>
        <div v-if="recentTickets.length" class="dashboard-recent-list">
          <RouterLink v-for="ticket in recentTickets" :key="ticket.id" :to="`${role === 'ADMIN' ? '/admin' : role === 'TECHNICIAN' ? '/technician' : '/customer'}/tickets/${ticket.id}`" class="dashboard-recent-row" :class="{ 'is-admin': role === 'ADMIN' || role === 'TECHNICIAN' }">
            <span class="dashboard-ticket-id">#{{ ticket.id }}</span>
            <span class="dashboard-ticket-title">{{ ticket.problem_title }}</span>
            <span v-if="role === 'ADMIN' || role === 'TECHNICIAN'" class="dashboard-ticket-customer">{{ ticket.customer_name }}</span>
            <TicketStatusBadge :status="ticket.status" />
            <time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleDateString() }}</time>
          </RouterLink>
        </div>
        <div v-else class="dashboard-list-empty">
          <p>{{ role === 'ADMIN' ? 'No customer tickets have been submitted yet.' : role === 'TECHNICIAN' ? 'No tickets are currently assigned to you.' : 'You have not created any tickets yet.' }}</p>
        </div>
      </section>
      <div v-if="!isLoading && !errorMessage && hasLoaded" class="dashboard-create-row">
        <template v-if="role === 'ADMIN'">
          <RouterLink class="button button-secondary" to="/admin/assignments">Assignments</RouterLink>
          <RouterLink class="button button-primary" to="/admin/tickets">All Tickets</RouterLink>
        </template>
        <RouterLink v-else-if="role === 'CUSTOMER'" class="button button-primary" to="/customer/tickets/new">Create Ticket</RouterLink>
      </div>
  </section>
</template>
