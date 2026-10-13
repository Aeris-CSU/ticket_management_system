<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import { listAssignments } from '@/services/assignments'
import { listTickets } from '@/services/tickets'
import { readableAuthError } from '@/services/auth'
import type { Ticket, TicketStatus } from '@/types/ticket'

const tickets = ref<Ticket[]>([])
const route = useRoute()
const isAdminView = computed(() => route.meta.audience === 'admin')
const isTechnicianView = computed(() => route.meta.audience === 'technician')
const basePath = computed(() => isAdminView.value ? '/admin' : isTechnicianView.value ? '/technician' : '/customer')
const isLoading = ref(true)
const errorMessage = ref('')
const selectedStatus = ref<'ALL' | TicketStatus>('ALL')
const search = ref('')

const filteredTickets = computed(() => tickets.value.filter((ticket) => {
  const statusMatches = selectedStatus.value === 'ALL' || ticket.status === selectedStatus.value
  return statusMatches && ticket.problem_title.toLowerCase().includes(search.value.trim().toLowerCase())
}))

onMounted(async () => {
  try {
    if (isTechnicianView.value) {
      const [assignedTickets, assignments] = await Promise.all([listTickets(), listAssignments()])
      const activeTicketIds = new Set(assignments.filter((assignment) => assignment.is_active).map((assignment) => assignment.tickets))
      tickets.value = assignedTickets.filter((ticket) => activeTicketIds.has(ticket.id))
    } else {
      tickets.value = await listTickets()
    }
  } catch (error) {
    errorMessage.value = readableAuthError(error, 'Could not load your tickets. Please try again.')
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <section class="dashboard-view" aria-labelledby="tickets-heading">
    <div class="dashboard-view-heading">
      <div><p class="eyebrow">{{ isAdminView ? 'Ticket management' : isTechnicianView ? 'Assigned work' : 'Support requests' }}</p><h2 id="tickets-heading">{{ isAdminView ? 'All Tickets' : isTechnicianView ? 'Assigned Tickets' : 'My Tickets' }}</h2><p>{{ isAdminView ? 'Review support requests submitted by customers.' : isTechnicianView ? 'Review support requests currently available to your technician account.' : 'View and track the support tickets you have submitted.' }}</p></div>
      <RouterLink v-if="!isAdminView && !isTechnicianView" class="button button-primary" to="/customer/tickets/new">Create Ticket</RouterLink>
    </div>

    <div class="ticket-filters" aria-label="Filter tickets">
      <label class="ticket-filter-control">Search title<input v-model="search" type="search" placeholder="Search tickets" /></label>
      <label class="ticket-filter-control">Status
        <select v-model="selectedStatus">
          <option value="ALL">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="ASSIGNED">Assigned</option>
          <option value="ONGOING">In Progress</option>
          <option value="RESOLVED">Resolved</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </label>
    </div>

    <div v-if="isLoading" class="dashboard-message" role="status">Loading your tickets…</div>
    <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
    <div v-else-if="tickets.length === 0" class="ticket-empty-state">
      <h3>{{ isTechnicianView ? 'No assigned tickets' : 'No tickets yet' }}</h3><p>{{ isAdminView ? 'Customer support requests will appear here.' : isTechnicianView ? 'Tickets assigned to you will appear here.' : 'When you submit a support request, it will appear here.' }}</p>
      <RouterLink v-if="!isAdminView && !isTechnicianView" class="button button-primary" to="/customer/tickets/new">Create your first ticket</RouterLink>
    </div>
    <div v-else-if="filteredTickets.length === 0" class="ticket-empty-state">
      <h3>No matching tickets</h3><p>Try a different title or status filter.</p>
    </div>
    <div v-else class="ticket-table-wrap">
      <table class="ticket-table">
        <thead><tr><th scope="col">Ticket</th><th v-if="isAdminView || isTechnicianView" scope="col">Customer</th><th scope="col">Status</th><th scope="col">Created</th><th scope="col"><span class="visually-hidden">Action</span></th></tr></thead>
        <tbody>
          <tr v-for="ticket in filteredTickets" :key="ticket.id">
            <td><span class="ticket-table-id">#{{ ticket.id }}</span><strong>{{ ticket.problem_title }}</strong></td>
            <td v-if="isAdminView || isTechnicianView">{{ ticket.customer_name }}</td>
            <td><TicketStatusBadge :status="ticket.status" /></td>
            <td><time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleDateString() }}</time></td>
            <td><RouterLink class="dashboard-text-link" :to="`${basePath}/tickets/${ticket.id}`">View details</RouterLink></td>
          </tr>
        </tbody>
      </table>
      <div class="ticket-mobile-list">
        <article v-for="ticket in filteredTickets" :key="ticket.id" class="ticket-mobile-card">
          <div class="ticket-mobile-top"><span class="ticket-table-id">#{{ ticket.id }}</span><TicketStatusBadge :status="ticket.status" /></div>
          <h3>{{ ticket.problem_title }}</h3>
          <p v-if="isAdminView || isTechnicianView" class="ticket-mobile-customer">Customer: {{ ticket.customer_name }}</p>
          <time :datetime="ticket.created_at">Created {{ new Date(ticket.created_at).toLocaleDateString() }}</time>
          <RouterLink class="dashboard-text-link" :to="`${basePath}/tickets/${ticket.id}`">View details</RouterLink>
        </article>
      </div>
    </div>
  </section>
</template>
