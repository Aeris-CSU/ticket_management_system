<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import { readableAuthError } from '@/services/auth'
import { createAssignment, listAssignments, reassignTechnician } from '@/services/assignments'
import { listTechnicians } from '@/services/directories'
import { getTicket, updateTicketStatus } from '@/services/tickets'
import type { Assignment, Technician } from '@/types/admin'
import type { Ticket } from '@/types/ticket'

const route = useRoute()
const ticket = ref<Ticket | null>(null)
const assignments = ref<Assignment[]>([])
const technicians = ref<Technician[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const assignmentError = ref('')
const assignmentMessage = ref('')
const statusError = ref('')
const statusMessage = ref('')
const isAssigning = ref(false)
const isUpdatingStatus = ref(false)
const selectedTechnicianId = ref('')
const isAdmin = computed(() => route.meta.role === 'ADMIN')
const isTechnician = computed(() => route.meta.role === 'TECHNICIAN')
const basePath = computed(() => isAdmin.value ? '/admin' : isTechnician.value ? '/technician' : '/customer')
const availableTechnicians = computed(() => technicians.value.filter((technician) => technician.availability_status === 'AVAILABLE'))
const activeAssignment = computed(() => assignments.value.find((assignment) => assignment.tickets === ticket.value?.id && assignment.is_active))
const assignmentHistory = computed(() => assignments.value.filter((assignment) => assignment.tickets === ticket.value?.id))
const canAssign = computed(() => ticket.value?.status === 'OPEN' && !activeAssignment.value)
const canReassign = computed(() => Boolean(activeAssignment.value && (ticket.value?.status === 'ASSIGNED' || ticket.value?.status === 'ONGOING')))
const canStartWork = computed(() => isTechnician.value && Boolean(activeAssignment.value) && ticket.value?.status === 'ASSIGNED')
const canResolve = computed(() => isTechnician.value && Boolean(activeAssignment.value) && ticket.value?.status === 'ONGOING')

async function loadTicketAndAdminData() {
  const id = String(route.params.id)
  ticket.value = await getTicket(id)
  if (isTechnician.value) {
    try {
      assignments.value = await listAssignments()
    } catch (error) {
      assignmentError.value = readableAuthError(error, 'Could not verify your active ticket assignment.')
    }
    return
  }
  if (!isAdmin.value) return

  const [assignmentResult, technicianResult] = await Promise.allSettled([listAssignments(), listTechnicians()])
  if (assignmentResult.status === 'fulfilled') {
    assignments.value = assignmentResult.value
    selectedTechnicianId.value = String(assignmentResult.value.find((item) => item.tickets === ticket.value?.id && item.is_active)?.technicians ?? '')
  } else {
    assignmentError.value = readableAuthError(assignmentResult.reason, 'Could not load assignment information.')
  }
  if (technicianResult.status === 'fulfilled') technicians.value = technicianResult.value
  else assignmentError.value = readableAuthError(technicianResult.reason, 'Could not load technician options.')
}

async function refreshAssignmentData() {
  if (!ticket.value) return
  const [updatedTicket, updatedAssignments] = await Promise.all([getTicket(String(ticket.value.id)), listAssignments()])
  ticket.value = updatedTicket
  assignments.value = updatedAssignments
  selectedTechnicianId.value = String(updatedAssignments.find((item) => item.tickets === updatedTicket.id && item.is_active)?.technicians ?? '')
}

async function submitAssignment() {
  if (!ticket.value || !selectedTechnicianId.value || isAssigning.value || (!canAssign.value && !canReassign.value)) return
  isAssigning.value = true
  assignmentError.value = ''
  assignmentMessage.value = ''
  const isReassignment = Boolean(activeAssignment.value)
  try {
    const technicianId = Number(selectedTechnicianId.value)
    if (activeAssignment.value) await reassignTechnician(activeAssignment.value.id, technicianId)
    else await createAssignment(ticket.value.id, technicianId)
    assignmentMessage.value = isReassignment ? 'Technician assignment updated.' : 'Technician assigned successfully.'
    try {
      await refreshAssignmentData()
    } catch (error) {
      assignmentError.value = readableAuthError(error, 'The assignment was saved, but the latest ticket information could not be refreshed.')
    }
  } catch (error) {
    assignmentError.value = readableAuthError(error, 'Could not update the technician assignment. Please try again.')
  } finally {
    isAssigning.value = false
  }
}

async function updateStatus(nextStatus: 'ONGOING' | 'RESOLVED') {
  if (!ticket.value || isUpdatingStatus.value || (!canStartWork.value && !canResolve.value)) return
  isUpdatingStatus.value = true
  statusError.value = ''
  statusMessage.value = ''
  try {
    ticket.value = await updateTicketStatus(String(ticket.value.id), nextStatus)
    statusMessage.value = nextStatus === 'ONGOING' ? 'Work started. Ticket status updated.' : 'Ticket marked as resolved.'
    try {
      assignments.value = await listAssignments()
    } catch {
      // Keep the confirmed ticket returned by the update endpoint if refreshing fails.
    }
  } catch (error) {
    statusError.value = readableAuthError(error, 'Could not update this ticket status. Please try again.')
  } finally {
    isUpdatingStatus.value = false
  }
}

onMounted(async () => {
  try {
    await loadTicketAndAdminData()
  } catch (error) {
    errorMessage.value = readableAuthError(error, 'Could not load this ticket. It may not exist or you may not have access.')
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <section class="dashboard-view" aria-labelledby="ticket-details-heading">
    <div class="dashboard-view-heading">
      <div><p class="eyebrow">{{ isAdmin ? 'Ticket management' : isTechnician ? 'Assigned work' : 'Support request' }}</p><h2 id="ticket-details-heading">Ticket Details</h2></div>
      <RouterLink class="button button-secondary" :to="`${basePath}/tickets`">{{ isAdmin ? 'Back to All Tickets' : isTechnician ? 'Back to Assigned Tickets' : 'Back to My Tickets' }}</RouterLink>
    </div>
    <div v-if="isLoading" class="dashboard-message" role="status">Loading ticket details…</div>
    <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
    <template v-else-if="ticket">
      <div v-if="route.query.created === '1'" class="form-message form-success" role="status">Your ticket was created successfully.</div>
      <div v-if="isAdmin && assignmentError" class="form-message form-error" role="alert">{{ assignmentError }}</div>
      <div v-if="isAdmin && assignmentMessage" class="form-message form-success" role="status">{{ assignmentMessage }}</div>
      <div v-if="isTechnician && assignmentError" class="form-message form-error" role="alert">{{ assignmentError }}</div>
      <div v-if="isTechnician && statusError" class="form-message form-error" role="alert">{{ statusError }}</div>
      <div v-if="isTechnician && statusMessage" class="form-message form-success" role="status">{{ statusMessage }}</div>
      <article class="ticket-detail-card">
        <div class="ticket-detail-top"><span class="ticket-table-id">Ticket #{{ ticket.id }}</span><TicketStatusBadge :status="ticket.status" /></div>
        <h3>{{ ticket.problem_title }}</h3>
        <p v-if="isAdmin || isTechnician" class="ticket-detail-customer">Customer: <strong>{{ ticket.customer_name }}</strong></p>
        <div class="ticket-detail-dates">
          <p><span>Created</span><time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleString() }}</time></p>
          <p><span>Last updated</span><time :datetime="ticket.updated_at">{{ new Date(ticket.updated_at).toLocaleString() }}</time></p>
        </div>
        <div class="ticket-detail-description"><h4>Description</h4><p>{{ ticket.problem_description }}</p></div>
      </article>
      <section v-if="isTechnician" class="assignment-panel technician-status-panel" aria-labelledby="ticket-status-heading">
        <div class="dashboard-section-heading"><div><h3 id="ticket-status-heading">Ticket Status</h3><p>Current status: <TicketStatusBadge :status="ticket.status" /></p></div></div>
        <p v-if="!assignmentError && !activeAssignment" class="assignment-hint">This ticket is not currently assigned to your account, so status actions are unavailable.</p>
        <p v-else-if="!canStartWork && !canResolve" class="assignment-hint">No status action is available for this ticket at its current status.</p>
        <div v-if="canStartWork || canResolve" class="technician-status-actions">
          <button v-if="canStartWork" class="button button-primary" type="button" :disabled="isUpdatingStatus" @click="updateStatus('ONGOING')">{{ isUpdatingStatus ? 'Updating…' : 'Start Work' }}</button>
          <button v-else class="button button-primary" type="button" :disabled="isUpdatingStatus" @click="updateStatus('RESOLVED')">{{ isUpdatingStatus ? 'Updating…' : 'Mark as Resolved' }}</button>
        </div>
      </section>
      <section v-if="isAdmin" class="assignment-panel" aria-labelledby="assignment-heading">
        <div class="dashboard-section-heading"><div><h3 id="assignment-heading">Technician Assignment</h3><p>Assignment options follow the ticket's current status and technician availability.</p></div></div>
        <div v-if="activeAssignment" class="active-assignment-summary">
          <span class="assignment-state is-active">Active</span>
          <span>Assigned to <strong>{{ activeAssignment.technician_name }}</strong></span>
          <time :datetime="activeAssignment.assigned_at">{{ new Date(activeAssignment.assigned_at).toLocaleString() }}</time>
        </div>
        <form v-if="canAssign || canReassign" class="assignment-form" @submit.prevent="submitAssignment">
          <label class="ticket-filter-control">{{ canReassign ? 'Reassign to technician' : 'Select an available technician' }}
            <select v-model="selectedTechnicianId" required>
              <option value="" disabled>Select a technician</option>
              <option v-for="technician in availableTechnicians" :key="technician.id" :value="String(technician.id)">
                {{ technician.first_name || technician.last_name ? `${technician.first_name} ${technician.last_name}`.trim() : technician.username }} · {{ technician.specialization }}
              </option>
            </select>
          </label>
          <p v-if="canReassign" class="assignment-hint">Reassignment is supported by the backend and moves this ticket back to Assigned.</p>
          <p v-if="availableTechnicians.length === 0" class="assignment-hint">No technicians are currently available.</p>
          <button class="button button-primary" type="submit" :disabled="isAssigning || !selectedTechnicianId || availableTechnicians.length === 0 || (canReassign && selectedTechnicianId === String(activeAssignment?.technicians))">
            {{ isAssigning ? 'Saving…' : canReassign ? 'Reassign Technician' : 'Assign Technician' }}
          </button>
        </form>
        <p v-else-if="!activeAssignment" class="assignment-hint">This ticket cannot be assigned in its current status.</p>
        <div v-if="assignmentHistory.length > (activeAssignment ? 1 : 0)" class="assignment-history">
          <h4>Assignment history</h4>
          <p v-for="record in assignmentHistory" :key="record.id">#{{ record.id }} · {{ record.technician_name }} · {{ record.is_active ? 'Active' : 'Previous assignment' }}</p>
        </div>
      </section>
    </template>
  </section>
</template>
