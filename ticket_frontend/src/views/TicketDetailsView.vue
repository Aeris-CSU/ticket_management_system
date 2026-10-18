<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import { readableAuthError } from '@/services/auth'
import { createAssignment, listAssignments, reassignTechnician } from '@/services/assignments'
import { listTechnicians } from '@/services/directories'
import { getTicket, updateTicket, updateTicketStatus } from '@/services/tickets'
import type { Assignment, Technician } from '@/types/admin'
import type { Ticket } from '@/types/ticket'

const route = useRoute()
const props = defineProps<{ ticketId?: number; embedded?: boolean }>()
const emit = defineEmits<{ changed: [ticket: Ticket] }>()
const ticket = ref<Ticket | null>(null)
const assignments = ref<Assignment[]>([])
const technicians = ref<Technician[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const assignmentError = ref('')
const assignmentMessage = ref('')
const statusError = ref('')
const statusMessage = ref('')
const cancellationReason = ref('')
const showCancellationForm = ref(false)
const isAssigning = ref(false)
const isUpdatingStatus = ref(false)
const selectedTechnicianId = ref('')
const isEditing = ref(false)
const isSavingDetails = ref(false)
const editTitle = ref('')
const editDescription = ref('')
const editAddress = ref('')
const editContactNumber = ref('')
const detailsError = ref('')
const detailsMessage = ref('')
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
const canCancel = computed(() => Boolean(ticket.value && (isAdmin.value
  ? ['OPEN', 'ASSIGNED', 'ONGOING'].includes(ticket.value.status)
  : !isTechnician.value && ticket.value.status === 'OPEN')))
const canEditDetails = computed(() => Boolean(ticket.value && !['RESOLVED', 'CANCELLED'].includes(ticket.value.status) && (isAdmin.value || (route.meta.role === 'CUSTOMER' && ticket.value.status === 'OPEN'))))

function startEditing() {
  if (!ticket.value || !canEditDetails.value) return
  editTitle.value = ticket.value.problem_title
  editDescription.value = ticket.value.problem_description
  editAddress.value = ticket.value.address || ticket.value.customer_address || ''
  editContactNumber.value = ticket.value.contact_number || ''
  detailsError.value = ''
  detailsMessage.value = ''
  isEditing.value = true
}

async function saveDetails() {
  if (!ticket.value || !canEditDetails.value || isSavingDetails.value) return
  detailsError.value = ''
  if (!editTitle.value.trim() || !editDescription.value.trim()) {
    detailsError.value = 'Enter a title and description.'
    return
  }
  isSavingDetails.value = true
  try {
    ticket.value = await updateTicket(String(ticket.value.id), {
      problem_title: editTitle.value.trim(),
      problem_description: editDescription.value.trim(),
      ...(editAddress.value.trim() !== (ticket.value.address || ticket.value.customer_address || '') ? { address: editAddress.value.trim() } : {}),
      ...(editContactNumber.value.trim() !== (ticket.value.contact_number || '') ? { contact_number: editContactNumber.value.trim() } : {}),
    })
    isEditing.value = false
    emit('changed', ticket.value)
    detailsMessage.value = 'Ticket details updated.'
  } catch (error) {
    detailsError.value = readableAuthError(error, 'Could not save ticket details. Please try again.')
  } finally {
    isSavingDetails.value = false
  }
}

async function loadTicketAndAdminData() {
  const id = String(props.ticketId ?? route.params.id)
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
  emit('changed', updatedTicket)
  assignments.value = updatedAssignments
  if (isAdmin.value) technicians.value = await listTechnicians()
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

async function updateStatus(nextStatus: 'ONGOING' | 'RESOLVED' | 'CANCELLED') {
  const permitted = nextStatus === 'CANCELLED' ? canCancel.value : nextStatus === 'ONGOING' ? canStartWork.value : canResolve.value
  if (!ticket.value || isUpdatingStatus.value || !permitted) return
  if (nextStatus === 'CANCELLED' && isAdmin.value && !cancellationReason.value.trim()) {
    statusError.value = 'Explain why you are cancelling this ticket.'
    return
  }
  isUpdatingStatus.value = true
  statusError.value = ''
  statusMessage.value = ''
  try {
    ticket.value = nextStatus === 'CANCELLED' && isAdmin.value
      ? await updateTicketStatus(String(ticket.value.id), nextStatus, cancellationReason.value.trim())
      : await updateTicketStatus(String(ticket.value.id), nextStatus)
    showCancellationForm.value = false
    if (nextStatus === 'CANCELLED' || nextStatus === 'RESOLVED') isEditing.value = false
    emit('changed', ticket.value)
    statusMessage.value = nextStatus === 'CANCELLED' ? 'Ticket cancelled.' : nextStatus === 'ONGOING' ? 'Work started. Ticket status updated.' : 'Ticket marked as resolved.'
    try {
      assignments.value = await listAssignments()
      if (isAdmin.value) technicians.value = await listTechnicians()
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
  <section class="dashboard-view" :aria-labelledby="embedded ? undefined : 'ticket-details-heading'" :aria-label="embedded ? 'Ticket information and actions' : undefined">
    <div v-if="!embedded" class="dashboard-view-heading">
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
      <div v-if="statusError" class="form-message form-error" role="alert">{{ statusError }}</div>
      <div v-if="statusMessage" class="form-message form-success" role="status">{{ statusMessage }}</div>
      <article class="ticket-detail-card">
        <div class="ticket-detail-top"><span class="ticket-table-id">{{ ticket.ticket_number || `Ticket #${ticket.id}` }}</span><TicketStatusBadge :status="ticket.status" /><button v-if="canEditDetails && !isEditing" class="button button-secondary ticket-edit-button" type="button" @click="startEditing">Edit Details</button></div>
        <div v-if="detailsError" class="form-message form-error" role="alert">{{ detailsError }}</div>
        <div v-if="detailsMessage" class="form-message form-success" role="status">{{ detailsMessage }}</div>
        <form v-if="isEditing" class="ticket-detail-edit" @submit.prevent="saveDetails">
          <label class="ticket-form-field" for="edit-ticket-title">Problem title
            <input id="edit-ticket-title" v-model="editTitle" maxlength="200" required :disabled="isSavingDetails" />
          </label>
          <label class="ticket-form-field" for="edit-ticket-description">Description
            <textarea id="edit-ticket-description" v-model="editDescription" rows="5" required :disabled="isSavingDetails"></textarea>
          </label>
          <label class="ticket-form-field" for="edit-ticket-contact">Contact number (optional)<input id="edit-ticket-contact" v-model="editContactNumber" type="tel" maxlength="30" :disabled="isSavingDetails" /></label>
          <label class="ticket-form-field" for="edit-ticket-address">Address<input id="edit-ticket-address" v-model="editAddress" maxlength="100" :disabled="isSavingDetails" /></label>
          <div class="ticket-form-actions">
            <button class="button button-secondary" type="button" :disabled="isSavingDetails" @click="isEditing = false; detailsError = ''">Cancel</button>
            <button class="button button-primary" type="submit" :disabled="isSavingDetails">{{ isSavingDetails ? 'Saving...' : 'Save Changes' }}</button>
          </div>
        </form>
        <template v-else>
        <h3 class="ticket-issue-title">{{ ticket.problem_title }}</h3>
        <p v-if="!embedded && (isAdmin || isTechnician)" class="ticket-detail-customer">Customer: <strong>{{ ticket.customer_name }}</strong></p>
        <div class="ticket-detail-dates">
          <p v-if="embedded && (isAdmin || isTechnician)"><span>Customer</span><strong class="ticket-metadata-value">{{ ticket.customer_name }}</strong></p>
          <p><span>Created</span><time :datetime="ticket.created_at">{{ new Date(ticket.created_at).toLocaleString() }}</time></p>
          <p><span>Last updated</span><time :datetime="ticket.updated_at">{{ new Date(ticket.updated_at).toLocaleString() }}</time></p>
        </div>
        <div v-if="ticket.status === 'CANCELLED' && ticket.cancellation_reason" class="ticket-cancellation-message">
          <h4>Reason for cancellation</h4>
          <p>{{ ticket.cancellation_reason }}</p>
        </div>
        <div class="ticket-info-grid">
        <div class="ticket-detail-description"><h4>Description</h4><p>{{ ticket.problem_description }}</p></div>
        <div class="ticket-detail-description ticket-customer-address"><h4>Contact and location</h4><dl class="ticket-contact-details"><div><dt>Contact number</dt><dd>{{ ticket.contact_number || 'Not provided' }}</dd></div><div><dt>Address</dt><dd>{{ ticket.address || ticket.customer_address || 'Not provided' }}</dd></div></dl></div>
        </div>
        </template>
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
        <div class="dashboard-section-heading"><div><h3 id="assignment-heading">Technician Assignment</h3><p>Assign or change the technician for this ticket.</p></div></div>
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
          <p v-if="canReassign" class="assignment-hint">Changing the technician returns this ticket to Assigned.</p>
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
      <form v-if="canCancel && isAdmin && showCancellationForm" class="ticket-cancellation-form" @submit.prevent="updateStatus('CANCELLED')">
        <label class="ticket-form-field" for="ticket-cancellation-reason">Reason for cancellation
          <textarea id="ticket-cancellation-reason" v-model="cancellationReason" rows="4" maxlength="2000" required :disabled="isUpdatingStatus" aria-describedby="cancellation-help"></textarea>
        </label>
        <p id="cancellation-help" class="assignment-hint">This message will appear in the customer's ticket details.</p>
        <div class="ticket-form-actions">
          <button class="button button-secondary" type="button" :disabled="isUpdatingStatus" @click="showCancellationForm = false">Keep Ticket</button>
          <button class="button button-primary" type="submit" :disabled="isUpdatingStatus || isSavingDetails || isAssigning">{{ isUpdatingStatus ? 'Cancelling...' : 'Confirm Cancellation' }}</button>
        </div>
      </form>
      <div v-if="canCancel && !showCancellationForm" class="ticket-cancel-actions"><button class="button button-secondary" type="button" :disabled="isUpdatingStatus || isSavingDetails || isAssigning" @click="isAdmin ? (showCancellationForm = true) : updateStatus('CANCELLED')">{{ isUpdatingStatus ? 'Cancelling...' : 'Cancel Ticket' }}</button></div>
      </article>
    </template>
  </section>
</template>
