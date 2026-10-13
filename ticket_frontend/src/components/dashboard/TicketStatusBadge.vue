<script setup lang="ts">
import type { TicketStatus } from '@/types/ticket'

defineProps<{ status: TicketStatus }>()

const labels: Record<TicketStatus, string> = {
  OPEN: 'Open',
  ASSIGNED: 'Assigned',
  ONGOING: 'In Progress',
  RESOLVED: 'Resolved',
  CANCELLED: 'Cancelled',
}
</script>

<template>
  <span class="ticket-status-badge" :class="`ticket-status-${status.toLowerCase()}`">{{ labels[status] }}</span>
</template>
