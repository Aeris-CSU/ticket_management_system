<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import TicketDetailsModal from '@/components/dashboard/TicketDetailsModal.vue'
import { listAssignments } from '@/services/assignments'
import { listTickets } from '@/services/tickets'
import { readableAuthError } from '@/services/auth'
import type { Ticket, TicketStatus } from '@/types/ticket'
import type { Assignment } from '@/types/admin'

const tickets = ref<Ticket[]>([])
const route = useRoute()
const isAdminView = computed(() => route.meta.audience === 'admin')
const isResolvedView = computed(() => route.meta.resolvedOnly === true)
const isTechnicianView = computed(() => route.meta.audience === 'technician')
const isLoading = ref(true)
const errorMessage = ref('')
const selectedStatus = ref<'ALL' | TicketStatus>('ALL')
const search = ref('')
const sortOrder = ref('newest')
const assignments = ref<Assignment[]>([])
const assignmentError = ref('')
const selectedTicketId = ref<number | null>(null)
async function ticketChanged(updated: Ticket) {
  tickets.value = tickets.value.map((item) => item.id === updated.id ? updated : item)
  if (!isAdminView.value && !isTechnicianView.value) return
  try {
    assignments.value = await listAssignments()
    if (isTechnicianView.value) {
      const activeIds = new Set(assignments.value.filter(item => item.is_active).map(item => item.tickets))
      tickets.value = tickets.value.filter(item => activeIds.has(item.id) && !['RESOLVED', 'CANCELLED'].includes(item.status))
    }
    assignmentError.value = ''
  }
  catch { assignmentError.value = 'Could not refresh assigned technicians. Reload this page to try again.' }
}
const technicianByTicket = computed(() => new Map(assignments.value.filter((item) => item.is_active).map((item) => [item.tickets, item.technician_name])))

const filteredTickets = computed(() => tickets.value.filter((ticket) => {
  const statusMatches = isResolvedView.value ? ticket.status === 'RESOLVED' : selectedStatus.value === 'ALL' || ticket.status === selectedStatus.value
  const text = isAdminView.value ? `${ticket.id} ${ticket.problem_title} ${ticket.customer_name} ${technicianByTicket.value.get(ticket.id) || ''}` : ticket.problem_title
  return statusMatches && text.toLowerCase().includes(search.value.trim().toLowerCase())
}).sort((a, b) => {
  const byDate = Date.parse(a.created_at) - Date.parse(b.created_at) || a.id - b.id
  return sortOrder.value === 'oldest' ? byDate : -byDate
}))

onMounted(async () => {
  try {
    if (isTechnicianView.value) {
      const [assignedTickets, assignments] = await Promise.all([listTickets(), listAssignments()])
      const activeTicketIds = new Set(assignments.filter((assignment) => assignment.is_active).map((assignment) => assignment.tickets))
      tickets.value = assignedTickets.filter((ticket) => activeTicketIds.has(ticket.id))
    } else if (isAdminView.value) {
      const [ticketResult, assignmentResult] = await Promise.allSettled([listTickets(), listAssignments()])
      if (ticketResult.status === 'rejected') throw ticketResult.reason
      tickets.value = ticketResult.value
      if (assignmentResult.status === 'fulfilled') assignments.value = assignmentResult.value
      else assignmentError.value = 'Could not load assigned technicians. Reload this page to try again.'
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
      <div><p class="eyebrow">{{ isAdminView ? 'Ticket management' : isTechnicianView ? 'Assigned work' : 'Support requests' }}</p><h2 id="tickets-heading">{{ isResolvedView ? 'Resolved Tickets' : isAdminView ? 'All Support Tickets' : isTechnicianView ? 'Assigned Tickets' : 'My Tickets' }}</h2><p>{{ isResolvedView ? 'View completed customer support requests.' : isAdminView ? 'View and manage submitted customer support requests.' : isTechnicianView ? 'Review support requests currently available to your technician account.' : 'View and track the support tickets you have submitted.' }}</p></div>
      <RouterLink v-if="!isAdminView && !isTechnicianView" class="button button-primary" to="/customer/tickets/new">Create Ticket</RouterLink>
    </div>

    <div class="ticket-filters" aria-label="Filter tickets">
      <label class="ticket-filter-control">{{ isAdminView ? 'Search tickets' : 'Search title' }}<input v-model="search" type="search" placeholder="Search tickets" /></label>
      <label v-if="!isResolvedView" class="ticket-filter-control">Status
        <select v-model="selectedStatus">
          <option value="ALL">All statuses</option>
          <option value="OPEN">Open</option>
          <option value="ASSIGNED">Assigned</option>
          <option value="ONGOING">Ongoing</option>
          <option value="RESOLVED">Resolved</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </label>
      <label v-if="isAdminView" class="ticket-filter-control">Sort by submission date
        <select v-model="sortOrder"><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select>
      </label>
    </div>
    <p v-if="assignmentError" class="form-message form-error" role="alert">{{ assignmentError }}</p>
    <div v-if="isLoading" class="dashboard-message" role="status">Loading your tickets…</div>
    <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
    <div v-else-if="tickets.length === 0" class="ticket-empty-state">
      <h3>{{ isTechnicianView ? 'No assigned tickets' : 'No tickets yet' }}</h3><p>{{ isAdminView ? 'Customer support requests will appear here.' : isTechnicianView ? 'Tickets assigned to you will appear here.' : 'When you submit a support request, it will appear here.' }}</p>
      <RouterLink v-if="!isAdminView && !isTechnicianView" class="button button-primary" to="/customer/tickets/new">Create your first ticket</RouterLink>
    </div>
    <div v-else-if="filteredTickets.length === 0" class="ticket-empty-state">
      <h3>{{ isResolvedView && !search.trim() ? 'No resolved tickets yet' : 'No matching tickets' }}</h3><p>{{ isResolvedView && !search.trim() ? 'Tickets appear here once they are marked as resolved.' : 'Try a different search or filter.' }}</p>
    </div>
    <div v-else class="ticket-table-wrap">
      <table class="ticket-table">
        <thead><tr><th scope="col">Ticket ID</th><th v-if="isAdminView" scope="col">Issue</th><th v-if="isAdminView || isTechnicianView" scope="col">Customer</th><th scope="col">Date Submitted</th><th v-if="isAdminView" scope="col">Assigned Technician</th><th scope="col">Status</th><th scope="col">Action</th></tr></thead>
        <tbody>
          <tr v-for="ticket in filteredTickets" :key="ticket.id">
            <td><span class="ticket-table-id">#{{ ticket.id }}</span><strong v-if="!isAdminView">{{ ticket.problem_title }}</strong></td>
            <td v-if="isAdminView">{{ ticket.problem_title }}</td>
            <td v-if="isAdminView || isTechnicianView">{{ ticket.customer_name }}</td>
            <td><time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleString() }}</time></td>
            <td v-if="isAdminView">{{ assignmentError ? 'Unavailable' : technicianByTicket.get(ticket.id) || 'Unassigned' }}</td>
            <td><TicketStatusBadge :status="ticket.status" /></td>
            <td><button class="dashboard-text-link" type="button" @click="selectedTicketId = ticket.id">View details</button></td>
          </tr>
        </tbody>
      </table>
      <div class="ticket-mobile-list">
        <article v-for="ticket in filteredTickets" :key="ticket.id" class="ticket-mobile-card">
          <div class="ticket-mobile-top"><span class="ticket-table-id">#{{ ticket.id }}</span><TicketStatusBadge :status="ticket.status" /></div>
          <h3>{{ ticket.problem_title }}</h3>
          <p v-if="isAdminView || isTechnicianView" class="ticket-mobile-customer">Customer: {{ ticket.customer_name }}</p>
          <p v-if="isAdminView" class="directory-detail">Technician: {{ assignmentError ? 'Unavailable' : technicianByTicket.get(ticket.id) || 'Unassigned' }}</p>
          <time :datetime="ticket.created_at">Created {{ new Date(ticket.created_at).toLocaleDateString() }}</time>
          <button class="dashboard-text-link" type="button" @click="selectedTicketId = ticket.id">View details</button>
        </article>
      </div>
    </div>
    <TicketDetailsModal v-if="selectedTicketId !== null" :ticket-id="selectedTicketId" @close="selectedTicketId = null" @changed="ticketChanged" />
  </section>
</template>
