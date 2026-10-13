<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import { listAssignments } from '@/services/assignments'
import { listTickets } from '@/services/tickets'
import { readableAuthError } from '@/services/auth'
import type { Assignment } from '@/types/admin'
import type { Ticket } from '@/types/ticket'

const assignments = ref<Assignment[]>([])
const tickets = ref<Ticket[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const ticketById = computed(() => new Map(tickets.value.map((ticket) => [ticket.id, ticket])))

onMounted(async () => {
  try {
    const [assignmentRecords, ticketRecords] = await Promise.all([listAssignments(), listTickets()])
    assignments.value = assignmentRecords
    tickets.value = ticketRecords
  } catch (error) {
    errorMessage.value = readableAuthError(error, 'Could not load assignment records. Please try again.')
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <section class="dashboard-view" aria-labelledby="assignments-heading">
    <div class="dashboard-view-heading">
      <div><p class="eyebrow">Ticket management</p><h2 id="assignments-heading">Assignments</h2><p>Review current and previous technician assignments.</p></div>
    </div>
    <div v-if="isLoading" class="dashboard-message" role="status">Loading assignments…</div>
    <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
    <div v-else-if="assignments.length === 0" class="ticket-empty-state">
      <h3>No assignments yet</h3><p>Technician assignments will appear here after tickets are assigned.</p>
      <RouterLink class="button button-primary" to="/admin/tickets">View All Tickets</RouterLink>
    </div>
    <div v-else class="ticket-table-wrap">
      <table class="ticket-table">
        <thead><tr><th scope="col">Assignment</th><th scope="col">Ticket</th><th scope="col">Technician</th><th scope="col">Assignment state</th><th scope="col">Ticket status</th><th scope="col">Assigned</th></tr></thead>
        <tbody>
          <tr v-for="assignment in assignments" :key="assignment.id">
            <td><span class="ticket-table-id">#{{ assignment.id }}</span></td>
            <td>
              <RouterLink class="dashboard-text-link" :to="`/admin/tickets/${assignment.tickets}`">#{{ assignment.tickets }} · {{ assignment.ticket_title }}</RouterLink>
            </td>
            <td>{{ assignment.technician_name }}</td>
            <td><span class="assignment-state" :class="assignment.is_active ? 'is-active' : 'is-inactive'">{{ assignment.is_active ? 'Active' : 'History' }}</span></td>
            <td><TicketStatusBadge v-if="ticketById.get(assignment.tickets)" :status="ticketById.get(assignment.tickets)!.status" /><span v-else>—</span></td>
            <td><time :datetime="assignment.assigned_at">{{ new Date(assignment.assigned_at).toLocaleDateString() }}</time></td>
          </tr>
        </tbody>
      </table>
      <div class="assignment-mobile-list">
        <article v-for="assignment in assignments" :key="assignment.id" class="ticket-mobile-card">
          <div class="ticket-mobile-top"><span class="ticket-table-id">Assignment #{{ assignment.id }}</span><span class="assignment-state" :class="assignment.is_active ? 'is-active' : 'is-inactive'">{{ assignment.is_active ? 'Active' : 'History' }}</span></div>
          <RouterLink class="dashboard-text-link" :to="`/admin/tickets/${assignment.tickets}`">Ticket #{{ assignment.tickets }} · {{ assignment.ticket_title }}</RouterLink>
          <p class="assignment-mobile-technician">{{ assignment.technician_name }}</p>
          <TicketStatusBadge v-if="ticketById.get(assignment.tickets)" :status="ticketById.get(assignment.tickets)!.status" />
          <time :datetime="assignment.assigned_at">Assigned {{ new Date(assignment.assigned_at).toLocaleDateString() }}</time>
        </article>
      </div>
    </div>
  </section>
</template>
