<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import TicketStatusBadge from './TicketStatusBadge.vue'
import type { Ticket } from '@/types/ticket'
import type { Assignment } from '@/types/admin'

const props = defineProps<{ tickets: Ticket[]; assignments: Assignment[] }>()
const emit = defineEmits<{ viewTicket: [id: number] }>()
const queue = computed(() => props.tickets
  .filter((ticket) => ['OPEN', 'ASSIGNED', 'ONGOING'].includes(ticket.status))
  .sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at) || a.id - b.id))
const technicianByTicket = computed(() => new Map(props.assignments.filter((item) => item.is_active).map((item) => [item.tickets, item.technician_name])))
</script>

<template>
  <section class="dashboard-recent" aria-labelledby="active-queue-heading">
    <div class="dashboard-section-heading">
      <div><h3 id="active-queue-heading">Active Ticket Queue <span class="queue-count">{{ queue.length }} active</span></h3><p>Support requests arranged by submission date, oldest first.</p></div>
      <RouterLink to="/admin/tickets" class="dashboard-text-link">View all</RouterLink>
    </div>
    <div v-if="queue.length" class="admin-table-scroll" tabindex="0" role="region" aria-label="Active ticket queue">
      <table class="ticket-table queue-table">
        <thead><tr><th scope="col">Queue #</th><th scope="col">Ticket ID</th><th scope="col">Issue</th><th scope="col">Customer</th><th scope="col">Date Submitted</th><th scope="col">Technician</th><th scope="col">Status</th><th scope="col">Action</th></tr></thead>
        <tbody>
          <tr v-for="(ticket, index) in queue" :key="ticket.id">
            <td>{{ index + 1 }}</td><td><span class="ticket-table-id">#{{ ticket.id }}</span></td><td>{{ ticket.problem_title }}</td><td>{{ ticket.customer_name }}</td>
            <td><time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleString() }}</time></td>
            <td>{{ technicianByTicket.get(ticket.id) || 'Unassigned' }}</td><td><TicketStatusBadge :status="ticket.status" /></td>
            <td><button class="dashboard-text-link" type="button" @click="emit('viewTicket', ticket.id)">View Details</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="dashboard-list-empty"><p>No active support requests. All ticket records remain available in All Tickets.</p></div>
  </section>
</template>
