<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import DirectoryDetailsModal from '@/components/dashboard/DirectoryDetailsModal.vue'
import TicketDetailsModal from '@/components/dashboard/TicketDetailsModal.vue'
import { listAssignments } from '@/services/assignments'
import { deleteTicket, listTickets } from '@/services/tickets'
import { readableAuthError } from '@/services/auth'
import type { Ticket, TicketStatus } from '@/types/ticket'
import { matchesSearch, manilaDate } from '@/utils/search'
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
const moreFiltersOpen = ref(false)
const advancedFilterCount = computed(() => Number(Boolean(dateFrom.value)) + Number(Boolean(dateTo.value)) + Number(technicianFilter.value !== 'ALL'))
const dateFrom = ref('')
const dateTo = ref('')
const technicianFilter = ref('ALL')
const technicianOptions = computed(() => [...new Map(assignments.value.map(item => [String(item.technicians), item.technician_name])).entries()].sort((a, b) => a[1].localeCompare(b[1])))
const dateError = computed(() => dateFrom.value && dateTo.value && dateFrom.value > dateTo.value ? 'The end date must be on or after the start date.' : '')
function clearFilters() {
  search.value = ''
  selectedStatus.value = 'ALL'
  dateFrom.value = dateTo.value = ''
  technicianFilter.value = 'ALL'
  sortOrder.value = 'newest'
}
const ticketTotal = computed(() => tickets.value.filter(ticket => !isResolvedView.value || ticket.status === 'RESOLVED').length)
const assignments = ref<Assignment[]>([])
const assignmentError = ref('')
const pendingDelete = ref<Ticket | null>(null)
const isDeleting = ref(false)
const deleteError = ref('')
const deleteMessage = ref('')
function requestDelete(ticket: Ticket) {
  pendingDelete.value = ticket
  deleteError.value = ''
}
async function confirmDelete() {
  if (!pendingDelete.value || isDeleting.value || !isAdminView.value) return
  isDeleting.value = true
  deleteError.value = ''
  try {
    const id = pendingDelete.value.id
    await deleteTicket(id)
    tickets.value = tickets.value.filter(ticket => ticket.id !== id)
    pendingDelete.value = null
    deleteMessage.value = 'Ticket deleted.'
  } catch (error) {
    deleteError.value = readableAuthError(error, 'Could not delete this ticket. Please try again.')
  } finally { isDeleting.value = false }
}
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
  const history = assignments.value.filter(item => item.tickets === ticket.id)
  const textMatches = matchesSearch(search.value, [ticket.ticket_number, ticket.id, ticket.problem_title, ticket.problem_description, ticket.customer_name, ticket.status, ticket.address, ticket.customer_address, ticket.contact_number, ...history.map(item => item.technician_name)])
  const date = manilaDate(ticket.created_at)
  const dateMatches = !dateError.value && (!dateFrom.value || date >= dateFrom.value) && (!dateTo.value || date <= dateTo.value)
  const technicianMatches = technicianFilter.value === 'ALL' || (technicianFilter.value === 'UNASSIGNED' ? !history.some(item => item.is_active) : history.some(item => String(item.technicians) === technicianFilter.value))
  return statusMatches && textMatches && dateMatches && technicianMatches
}).sort((a, b) => {
  const byDate = Date.parse(a.created_at) - Date.parse(b.created_at) || a.id - b.id
  return sortOrder.value === 'oldest' ? byDate : -byDate
}))

onMounted(async () => {
  try {
    if (isTechnicianView.value) {
      const [assignedTickets, loadedAssignments] = await Promise.all([listTickets(), listAssignments()])
      assignments.value = loadedAssignments
      const activeTicketIds = new Set(loadedAssignments.filter((assignment) => assignment.is_active).map((assignment) => assignment.tickets))
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

    <div class="ticket-filters ticket-filter-toolbar" aria-label="Filter tickets">
      <div class="ticket-filter-primary">
      <label class="ticket-filter-control ticket-search-wide">Search tickets<input v-model="search" type="search" placeholder="Number, issue, name, address or contact" /></label>
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
      <label class="ticket-filter-control">Sort by
        <select v-model="sortOrder"><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select>
      </label>
      <button class="button button-secondary ticket-more-filters" type="button" :aria-expanded="moreFiltersOpen" aria-controls="ticket-extra-filters" @click="moreFiltersOpen = !moreFiltersOpen">
        <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="2" fill="currentColor"/><circle cx="15" cy="17" r="2" fill="currentColor"/></svg>
        {{ moreFiltersOpen ? 'Fewer filters' : 'More filters' }}<span v-if="advancedFilterCount" class="queue-count">{{ advancedFilterCount }}</span>
      </button>
      <button class="ticket-clear-filters" type="button" @click="clearFilters">Clear filters</button>
      </div>
      <div v-show="moreFiltersOpen" id="ticket-extra-filters" class="ticket-filter-extra">
      <label class="ticket-filter-control">From date (PH)<input v-model="dateFrom" type="date" aria-label="Submitted from" :max="dateTo || undefined" /></label>
      <label class="ticket-filter-control">To date (PH)<input v-model="dateTo" type="date" aria-label="Submitted through" :min="dateFrom || undefined" /></label>
      <label v-if="isAdminView" class="ticket-filter-control">Technician history<select v-model="technicianFilter" :disabled="Boolean(assignmentError)"><option value="ALL">All technicians</option><option value="UNASSIGNED">No active assignment</option><option v-for="[id, name] in technicianOptions" :key="id" :value="id">{{ name }}</option></select></label>
      </div>
    </div>
    <p v-if="dateError" class="form-message form-error" role="alert">{{ dateError }}</p>
    <p v-if="!isLoading && !errorMessage" class="filter-result-count" role="status">{{ filteredTickets.length }} of {{ ticketTotal }} tickets</p>
    <p v-if="deleteMessage" class="form-message form-success" role="status">{{ deleteMessage }}</p>
    <p v-if="assignmentError" class="form-message form-error" role="alert">{{ assignmentError }}</p>
    <div v-if="isLoading" class="dashboard-message" role="status">Loading your tickets…</div>
    <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
    <div v-else-if="tickets.length === 0" class="ticket-empty-state">
      <h3>{{ isTechnicianView ? 'No assigned tickets' : 'No tickets yet' }}</h3><p>{{ isAdminView ? 'Customer support requests will appear here.' : isTechnicianView ? 'Tickets assigned to you will appear here.' : 'When you submit a support request, it will appear here.' }}</p>
      <RouterLink v-if="!isAdminView && !isTechnicianView" class="button button-primary" to="/customer/tickets/new">Create your first ticket</RouterLink>
    </div>
    <div v-else-if="filteredTickets.length === 0" class="ticket-empty-state">
      <h3>{{ isResolvedView && !search.trim() && !dateFrom && !dateTo && technicianFilter === 'ALL' ? 'No resolved tickets yet' : 'No matching tickets' }}</h3><p>{{ isResolvedView && !search.trim() && !dateFrom && !dateTo && technicianFilter === 'ALL' ? 'Tickets appear here once they are marked as resolved.' : 'Try a different search or filter.' }}</p>
    </div>
    <div v-else class="ticket-table-wrap">
      <table class="ticket-table">
        <thead><tr><th scope="col">Ticket Number</th><th v-if="isAdminView" scope="col">Issue</th><th v-if="isAdminView || isTechnicianView" scope="col">Customer</th><th scope="col">Date Submitted</th><th v-if="isAdminView" scope="col">Assigned Technician</th><th scope="col">Status</th><th scope="col">Action</th></tr></thead>
        <tbody>
          <tr v-for="ticket in filteredTickets" :key="ticket.id">
            <td><span class="ticket-table-id">{{ ticket.ticket_number || `#${ticket.id}` }}</span><strong v-if="!isAdminView">{{ ticket.problem_title }}</strong></td>
            <td v-if="isAdminView">{{ ticket.problem_title }}</td>
            <td v-if="isAdminView || isTechnicianView">{{ ticket.customer_name }}</td>
            <td><time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleString() }}</time></td>
            <td v-if="isAdminView">{{ assignmentError ? 'Unavailable' : technicianByTicket.get(ticket.id) || 'Unassigned' }}</td>
            <td><TicketStatusBadge :status="ticket.status" /></td>
            <td><div class="directory-row-actions"><button class="dashboard-text-link" type="button" @click="selectedTicketId = ticket.id">View details</button><button v-if="isAdminView && ['RESOLVED', 'CANCELLED'].includes(ticket.status)" class="technician-delete-icon ticket-delete-icon" type="button" :aria-label="`Delete ticket ${ticket.ticket_number || ticket.id}`" title="Delete ticket" @click="requestDelete(ticket)"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6" /></svg></button></div></td>
          </tr>
        </tbody>
      </table>
      <div class="ticket-mobile-list">
        <article v-for="ticket in filteredTickets" :key="ticket.id" class="ticket-mobile-card">
          <div class="ticket-mobile-top"><span class="ticket-table-id">{{ ticket.ticket_number || `#${ticket.id}` }}</span><TicketStatusBadge :status="ticket.status" /></div>
          <h3>{{ ticket.problem_title }}</h3>
          <p v-if="isAdminView || isTechnicianView" class="ticket-mobile-customer">Customer: {{ ticket.customer_name }}</p>
          <p v-if="isAdminView" class="directory-detail">Technician: {{ assignmentError ? 'Unavailable' : technicianByTicket.get(ticket.id) || 'Unassigned' }}</p>
          <time :datetime="ticket.created_at">Created {{ new Date(ticket.created_at).toLocaleDateString() }}</time>
          <button class="dashboard-text-link" type="button" @click="selectedTicketId = ticket.id">View details</button><button v-if="isAdminView && ['RESOLVED', 'CANCELLED'].includes(ticket.status)" class="technician-delete-icon ticket-delete-icon" type="button" :aria-label="`Delete ticket ${ticket.ticket_number || ticket.id}`" title="Delete ticket" @click="requestDelete(ticket)"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6" /></svg></button>
        </article>
      </div>
    </div>
    <DirectoryDetailsModal v-if="pendingDelete" title="Delete Ticket" :dismissible="!isDeleting" @close="pendingDelete = null">
      <p>Delete {{ pendingDelete.ticket_number || `ticket #${pendingDelete.id}` }} from the ticket lists? Its record and assignment history will be retained.</p>
      <p v-if="deleteError" class="form-message form-error" role="alert">{{ deleteError }}</p>
      <div class="ticket-form-actions"><button class="button button-secondary" type="button" :disabled="isDeleting" @click="pendingDelete = null">Keep Ticket</button><button class="button button-primary confirm-ticket-delete" type="button" :disabled="isDeleting" @click="confirmDelete">{{ isDeleting ? 'Deleting...' : 'Confirm Delete' }}</button></div>
    </DirectoryDetailsModal>
    <TicketDetailsModal v-if="selectedTicketId !== null" :ticket-id="selectedTicketId" @close="selectedTicketId = null" @changed="ticketChanged" />
  </section>
</template>
