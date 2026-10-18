<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { listTickets } from '@/services/tickets'
import { listAssignments } from '@/services/assignments'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import DirectoryDetailsModal from '@/components/dashboard/DirectoryDetailsModal.vue'
import { matchesSearch } from '@/utils/search'
import type { Ticket } from '@/types/ticket'
import type { Assignment } from '@/types/admin'
import { deleteCustomer, deleteTechnician, createTechnician, listCustomers, listTechnicians } from '@/services/directories'
import { readableAuthError } from '@/services/auth'
import type { CustomerDirectoryEntry, Technician } from '@/types/admin'

interface DirectoryRow {
  id: number
  name: string
  username: string
  email: string
  contactNumber?: string
  detail: string
  availability?: Technician['availability_status']
}

const route = useRoute()
const customers = ref<CustomerDirectoryEntry[]>([])
const technicians = ref<Technician[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const relatedError = ref('')
const tickets = ref<Ticket[]>([])
const assignments = ref<Assignment[]>([])
const selectedPersonId = ref<number | null>(null)
const deleteError = ref('')
const deleteMessage = ref('')
const confirmingDelete = ref(false)
const isDeleting = ref(false)
watch(selectedPersonId, () => { confirmingDelete.value = false; deleteError.value = '' }, { flush: 'sync' })
function confirmAccountDeletion(id: number) {
  selectedPersonId.value = id
  confirmingDelete.value = true
}
async function removeAccount() {
  if (selectedPersonId.value === null || isDeleting.value) return
  const id = selectedPersonId.value
  isDeleting.value = true
  deleteError.value = ''
  try {
    if (isTechnicianDirectory.value) {
      await deleteTechnician(id)
      technicians.value = technicians.value.filter(person => person.id !== id)
    } else {
      await deleteCustomer(id)
      customers.value = customers.value.filter(person => person.id !== id)
    }
    selectedPersonId.value = null
    deleteMessage.value = isTechnicianDirectory.value ? 'Technician account deleted.' : 'Customer account deleted.'
  } catch (error) {
    deleteError.value = readableAuthError(error, `Could not delete this ${isTechnicianDirectory.value ? 'technician' : 'customer'} account. Please try again.`)
  } finally {
    isDeleting.value = false
  }
}
const search = ref('')
const availabilityFilter = ref('ALL')
const directoryFiltersOpen = ref(false)
const directoryFilterCount = computed(() => Number(availabilityFilter.value !== 'ALL') + Number(specializationFilter.value !== 'ALL') + Number(workloadFilter.value !== 'ALL'))
const specializationFilter = ref('ALL')
const workloadFilter = ref('ALL')
const directorySort = ref('default')
const specializations = computed(() => [...new Set(technicians.value.map(person => person.specialization).filter(Boolean))].sort((a, b) => a.localeCompare(b)))
function clearDirectoryFilters() {
  search.value = ''
  availabilityFilter.value = specializationFilter.value = workloadFilter.value = 'ALL'
  directorySort.value = 'default'
}
const selectedPerson = computed(() => rows.value.find((person) => person.id === selectedPersonId.value))
function currentTicket(id: number) {
  const assignment = assignments.value.find(item => item.is_active && item.technicians === id)
  if (!assignment) return null
  const ticket = tickets.value.find(item => item.id === assignment.tickets)
  return { id: assignment.tickets, label: ticket?.ticket_number || `Ticket #${assignment.tickets}` }
}
const activeCount = (id: number) => assignments.value.filter((item) => item.is_active && item.technicians === id).length
const relatedTickets = computed(() => selectedPersonId.value === null ? [] : tickets.value.filter((ticket) => isTechnicianDirectory.value
  ? assignments.value.some((item) => item.is_active && item.technicians === selectedPersonId.value && item.tickets === ticket.id)
  : ticket.customer === selectedPersonId.value))
const showCreateForm = ref(false)
const isCreating = ref(false)
const createError = ref('')
const createMessage = ref('')
const technicianForm = reactive({ username: '', password: '', first_name: '', last_name: '', email: '', specialization: '' })
const technicianFieldErrors = reactive({ username: '', password: '', specialization: '' })
const isTechnicianDirectory = computed(() => route.meta.directory === 'technicians')
const heading = computed(() => isTechnicianDirectory.value ? 'Technicians' : 'Customers')
const rows = computed<DirectoryRow[]>(() => isTechnicianDirectory.value
  ? technicians.value.map((person) => ({
    id: person.id,
    username: person.username,
    name: `${person.first_name} ${person.last_name}`.trim() || person.username,
    email: person.email,
    detail: person.specialization,
    availability: person.availability_status,
  }))
  : customers.value.map((person) => ({
    contactNumber: person.contact_number,
    id: person.id,
    username: person.username,
    name: `${person.first_name} ${person.last_name}`.trim() || person.username,
    email: person.email,
    detail: person.address || '',
  })))
const filteredRows = computed(() => {
  return rows.value.filter((person) => {
    const count = isTechnicianDirectory.value ? activeCount(person.id) : tickets.value.filter(ticket => ticket.customer === person.id).length
    return matchesSearch(search.value, [person.id, person.name, person.username, person.email, person.contactNumber, person.detail, person.availability])
      && (!isTechnicianDirectory.value || availabilityFilter.value === 'ALL' || person.availability === availabilityFilter.value)
      && (!isTechnicianDirectory.value || specializationFilter.value === 'ALL' || person.detail === specializationFilter.value)
      && (workloadFilter.value === 'ALL' || (workloadFilter.value === 'WITH' ? count > 0 : count === 0))
  }).sort((a, b) => directorySort.value === 'name-asc' ? a.name.localeCompare(b.name) : directorySort.value === 'name-desc' ? b.name.localeCompare(a.name) : directorySort.value === 'newest' ? b.id - a.id : a.id - b.id)
})

watch(isTechnicianDirectory, async (technicianDirectory) => {
  isLoading.value = true
  errorMessage.value = ''
  deleteMessage.value = ''
  relatedError.value = ''
  selectedPersonId.value = null
  clearDirectoryFilters()
  try {
    if (technicianDirectory) technicians.value = await listTechnicians()
    else customers.value = await listCustomers()
    const [ticketResult, assignmentResult] = await Promise.allSettled([listTickets(), listAssignments()])
    if (ticketResult.status === 'fulfilled') tickets.value = ticketResult.value
    else { tickets.value = []; relatedError.value = 'Could not load related tickets. Reload this page to try again.' }
    if (assignmentResult.status === 'fulfilled') assignments.value = assignmentResult.value
    else { assignments.value = []; relatedError.value = 'Could not load assignment counts. Reload this page to try again.' }
  } catch (error) {
    errorMessage.value = readableAuthError(error, `Could not load ${heading.value.toLowerCase()}. Please try again.`)
  } finally {
    isLoading.value = false
  }
}, { immediate: true })

function clearTechnicianErrors() {
  technicianFieldErrors.username = ''
  technicianFieldErrors.password = ''
  technicianFieldErrors.specialization = ''
}

function readFieldError(value: unknown) {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.filter((message): message is string => typeof message === 'string').join(' ')
  return ''
}

async function submitTechnician() {
  if (isCreating.value) return
  createError.value = ''
  createMessage.value = ''
  clearTechnicianErrors()
  if (!technicianForm.username.trim()) technicianFieldErrors.username = 'Enter a username.'
  if (!technicianForm.password) technicianFieldErrors.password = 'Enter a temporary password.'
  if (!technicianForm.specialization.trim()) technicianFieldErrors.specialization = 'Enter a specialization.'
  if (technicianFieldErrors.username || technicianFieldErrors.password || technicianFieldErrors.specialization) return

  isCreating.value = true
  try {
    await createTechnician({
      ...technicianForm,
      username: technicianForm.username.trim(),
      first_name: technicianForm.first_name.trim(),
      last_name: technicianForm.last_name.trim(),
      email: technicianForm.email.trim(),
      specialization: technicianForm.specialization.trim(),
    })
    Object.assign(technicianForm, { username: '', password: '', first_name: '', last_name: '', email: '', specialization: '' })
    showCreateForm.value = false
    createMessage.value = 'Technician account created successfully. They can sign in using their username and password.'
    try {
      technicians.value = await listTechnicians()
    } catch {
      errorMessage.value = 'The account was created, but the technician directory could not refresh. Reload this page to see it.'
    }
  } catch (error) {
    createError.value = readableAuthError(error, 'Could not create the technician account. Please try again.')
    const response = (error as { response?: { data?: unknown } }).response?.data
    if (response && typeof response === 'object') {
      const fields = response as Record<string, unknown>
      technicianFieldErrors.username = readFieldError(fields.username)
      technicianFieldErrors.password = readFieldError(fields.password)
      technicianFieldErrors.specialization = readFieldError(fields.specialization)
    }
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <section class="dashboard-view customers-directory" :class="{ 'technicians-directory': isTechnicianDirectory }" aria-labelledby="directory-heading">
    <div class="dashboard-view-heading">
      <div><p class="eyebrow">User directory</p><h2 id="directory-heading">{{ heading }}</h2><p>{{ isTechnicianDirectory ? 'View technician information and availability.' : 'View registered customers and their submitted support tickets.' }}</p></div>
      <button v-if="isTechnicianDirectory" class="button button-primary" type="button" :aria-expanded="showCreateForm" aria-controls="create-technician-form" @click="selectedPersonId = null; showCreateForm = true; createError = ''; createMessage = ''">Add Technician</button>
    </div>
    <p v-if="createMessage" class="form-message form-success" role="status">{{ createMessage }}</p>
    <p v-if="relatedError" class="form-message form-error" role="alert">{{ relatedError }}</p>
    <p v-if="deleteMessage" class="form-message form-success" role="status">{{ deleteMessage }}</p>
    <DirectoryDetailsModal v-if="selectedPerson" :dismissible="!isDeleting" :title="isTechnicianDirectory ? 'Technician Details' : 'Customer Details'" @close="selectedPersonId = null">
    <section class="ticket-detail-card customer-profile-card" aria-labelledby="person-details-heading">
      <template v-if="!isTechnicianDirectory">
        <div class="customer-profile-heading">
          <span class="customer-profile-avatar" aria-hidden="true">{{ selectedPerson.name.split(' ').filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() }}</span>
          <div><h3 id="person-details-heading">{{ selectedPerson.name }}</h3><p class="customer-profile-caption">Customer account</p></div>
        </div>
        <dl class="customer-profile-info">
          <div><dt>Email address</dt><dd>{{ selectedPerson.email || 'Not provided' }}</dd></div>
          <div><dt>Contact number</dt><dd>{{ selectedPerson.contactNumber || 'Not provided' }}</dd></div>
          <div class="customer-profile-address"><dt>Address</dt><dd>{{ selectedPerson.detail || 'Not provided' }}</dd></div>
        </dl>
      </template>
      <template v-else>
        <div class="customer-profile-heading technician-profile-heading">
          <span class="customer-profile-avatar" aria-hidden="true">{{ selectedPerson.name.split(' ').filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() }}</span>
          <div class="technician-profile-name"><h3 id="person-details-heading">{{ selectedPerson.name }}</h3><p class="customer-profile-caption">Technician account</p></div>
          <span class="assignment-state" :class="selectedPerson.availability === 'AVAILABLE' ? 'is-active' : 'is-inactive'">{{ selectedPerson.availability === 'AVAILABLE' ? 'Available' : 'Unavailable' }}</span>
        </div>
        <dl class="customer-profile-info">
          <div><dt>Username</dt><dd>{{ selectedPerson.username }}</dd></div>
          <div><dt>Email address</dt><dd>{{ selectedPerson.email || 'Not provided' }}</dd></div>
          <div><dt>Specialization</dt><dd>{{ selectedPerson.detail || 'Not provided' }}</dd></div>
          <div><dt>Current ticket</dt><dd><span v-if="relatedError">Unavailable</span><RouterLink v-else-if="currentTicket(selectedPerson.id)" class="dashboard-text-link current-ticket-link" :to="`/admin/tickets/${currentTicket(selectedPerson.id)!.id}`">{{ currentTicket(selectedPerson.id)!.label }}</RouterLink><span v-else class="directory-detail">No active ticket</span></dd></div>
        </dl>
      </template>
      <div class="technician-delete-actions">
        <p v-if="deleteError" class="form-message form-error" role="alert">{{ deleteError }}</p>
        <template v-if="confirmingDelete">
          <p>Delete {{ selectedPerson.name }}'s account and login permanently? Accounts with {{ isTechnicianDirectory ? 'assignment' : 'ticket' }} history cannot be deleted.</p>
          <div class="ticket-form-actions">
            <button class="button button-secondary" type="button" :disabled="isDeleting" @click="confirmingDelete = false">Keep Account</button>
            <button class="button button-primary" type="button" :disabled="isDeleting" @click="removeAccount">{{ isDeleting ? 'Deleting...' : 'Confirm Delete' }}</button>
          </div>
        </template>
      </div>
      <h4>{{ isTechnicianDirectory ? 'Current ticket' : 'Submitted support tickets' }} <span v-if="!isTechnicianDirectory && !relatedError" class="queue-count">{{ relatedTickets.length }}</span></h4>
      <p v-if="!relatedError && !relatedTickets.length" class="directory-detail customer-ticket-empty">{{ isTechnicianDirectory ? 'No tickets to display.' : 'This customer has not submitted any support tickets yet.' }}</p>
      <p v-if="relatedError" class="form-message form-error" role="alert">{{ relatedError }}</p>
      <ul v-if="!relatedError" class="directory-ticket-links"><li v-for="item in relatedTickets" :key="item.id"><RouterLink class="dashboard-text-link" :to="`/admin/tickets/${item.id}`">{{ item.ticket_number || `#${item.id}` }} — {{ item.problem_title }}</RouterLink><TicketStatusBadge :status="item.status" /></li></ul>
    </section>
    </DirectoryDetailsModal>
    <DirectoryDetailsModal v-if="isTechnicianDirectory && showCreateForm" title="Add Technician" :dismissible="!isCreating" @close="showCreateForm = false">
    <form id="create-technician-form" class="ticket-form-card technician-create-form" :aria-busy="isCreating" novalidate @submit.prevent="submitTechnician">
      <p class="technician-form-note">Create a technician login. Share the temporary password with them securely so they can sign in on the existing login page.</p>
      <div v-if="createError" class="form-message form-error" role="alert">{{ createError }}</div>
      <label class="ticket-form-field" for="technician-username">Username
        <input id="technician-username" v-model="technicianForm.username" name="username" autocomplete="off" required maxlength="150" :aria-invalid="Boolean(technicianFieldErrors.username)" aria-describedby="technician-username-error" />
        <small v-if="technicianFieldErrors.username" id="technician-username-error" class="ticket-field-error">{{ technicianFieldErrors.username }}</small>
      </label>
      <label class="ticket-form-field" for="technician-password">Temporary password
        <input id="technician-password" v-model="technicianForm.password" name="password" type="password" autocomplete="new-password" required :aria-invalid="Boolean(technicianFieldErrors.password)" aria-describedby="technician-password-error" />
        <small v-if="technicianFieldErrors.password" id="technician-password-error" class="ticket-field-error">{{ technicianFieldErrors.password }}</small>
      </label>
      <div class="technician-form-grid">
        <label class="ticket-form-field" for="technician-first-name">First name<input id="technician-first-name" v-model="technicianForm.first_name" name="first_name" autocomplete="given-name" /></label>
        <label class="ticket-form-field" for="technician-last-name">Last name<input id="technician-last-name" v-model="technicianForm.last_name" name="last_name" autocomplete="family-name" /></label>
      </div>
      <label class="ticket-form-field" for="technician-email">Email<input id="technician-email" v-model="technicianForm.email" name="email" type="email" autocomplete="email" /></label>
      <label class="ticket-form-field" for="technician-specialization">Specialization
        <input id="technician-specialization" v-model="technicianForm.specialization" name="specialization" required maxlength="100" :aria-invalid="Boolean(technicianFieldErrors.specialization)" aria-describedby="technician-specialization-error" placeholder="For example, Network support" />
        <small v-if="technicianFieldErrors.specialization" id="technician-specialization-error" class="ticket-field-error">{{ technicianFieldErrors.specialization }}</small>
      </label>
      <div class="ticket-form-actions">
        <button class="button button-secondary" type="button" :disabled="isCreating" @click="showCreateForm = false">Cancel</button>
        <button class="button button-primary" type="submit" :disabled="isCreating">{{ isCreating ? 'Creating…' : 'Create Technician' }}</button>
      </div>
    </form>
    </DirectoryDetailsModal>
    <div class="customer-search-bar directory-filter-toolbar">
      <div class="directory-filter-main">
      <label class="ticket-filter-control" :for="isTechnicianDirectory ? 'technician-search' : 'customer-search'">Search {{ heading.toLowerCase() }}
        <input :id="isTechnicianDirectory ? 'technician-search' : 'customer-search'" v-model="search" type="search" :placeholder="isTechnicianDirectory ? 'Search by name, email, or specialization' : 'Search by name, email, contact number, or address'" autocomplete="off" />
      </label>
      <label class="ticket-filter-control">Sort by<select v-model="directorySort"><option value="default">Oldest accounts first</option><option value="newest">Newest accounts first</option><option value="name-asc">Name A to Z</option><option value="name-desc">Name Z to A</option></select></label>
        <button class="button button-secondary directory-filter-toggle" type="button" :aria-expanded="directoryFiltersOpen" aria-controls="directory-extra-filters" @click="directoryFiltersOpen = !directoryFiltersOpen">
          <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="2" fill="currentColor"/><circle cx="15" cy="17" r="2" fill="currentColor"/></svg>
          Filters<span v-if="directoryFilterCount" class="queue-count">{{ directoryFilterCount }}</span>
        </button>
        <button class="ticket-clear-filters" type="button" @click="clearDirectoryFilters">Clear filters</button>
      </div>
      <div v-show="directoryFiltersOpen" id="directory-extra-filters" class="directory-filter-extra">
      <label v-if="isTechnicianDirectory" class="ticket-filter-control technician-availability-filter">Availability<select v-model="availabilityFilter"><option value="ALL">All availability</option><option value="AVAILABLE">Available</option><option value="UNAVAILABLE">Unavailable</option></select></label>
      <label v-if="isTechnicianDirectory" class="ticket-filter-control">Specialization<select v-model="specializationFilter"><option value="ALL">All specializations</option><option v-for="item in specializations" :key="item" :value="item">{{ item }}</option></select></label>
      <label class="ticket-filter-control">{{ isTechnicianDirectory ? 'Active assignments' : 'Submitted tickets' }}<select v-model="workloadFilter" :disabled="Boolean(relatedError)"><option value="ALL">All records</option><option value="WITH">With {{ isTechnicianDirectory ? 'active assignments' : 'tickets' }}</option><option value="WITHOUT">Without {{ isTechnicianDirectory ? 'active assignments' : 'tickets' }}</option></select></label>
      </div>
    </div>
    <p v-if="!isLoading && !errorMessage" class="customer-result-count directory-filter-results" role="status">{{ filteredRows.length }} of {{ rows.length }} {{ heading.toLowerCase() }}</p>
    <div v-if="isLoading" class="dashboard-message" role="status">Loading {{ heading.toLowerCase() }}…</div>
    <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
    <div v-else-if="rows.length === 0" class="ticket-empty-state">
      <h3>No {{ heading.toLowerCase() }} found</h3><p>There are no records to display.</p>
    </div>
    <div v-else-if="filteredRows.length === 0" class="ticket-empty-state"><h3>No matching {{ heading.toLowerCase() }}</h3><p>Try a different search or filter.</p><button class="button button-secondary" type="button" @click="clearDirectoryFilters">Clear search</button></div>
    <div v-else class="ticket-table-wrap">
      <table class="ticket-table directory-table">
        <thead><tr><th scope="col">Name</th><th scope="col">Email</th><th v-if="!isTechnicianDirectory" scope="col">Contact number</th><th scope="col">{{ isTechnicianDirectory ? 'Specialization' : 'Address' }}</th><th v-if="isTechnicianDirectory" scope="col">Availability</th><th v-if="isTechnicianDirectory" scope="col">Current Ticket</th><th scope="col">Action</th></tr></thead>
        <tbody>
          <tr v-for="person in filteredRows" :key="person.id">
            <td><strong>{{ person.name }}</strong></td>
            <td>{{ person.email || '—' }}</td>
            <td v-if="!isTechnicianDirectory">{{ person.contactNumber || 'Not provided' }}</td>
            <td>{{ person.detail || '—' }}</td>
            <td v-if="isTechnicianDirectory"><span class="assignment-state" :class="person.availability === 'AVAILABLE' ? 'is-active' : 'is-inactive'">{{ person.availability === 'AVAILABLE' ? 'Available' : 'Unavailable' }}</span></td>
            <td v-if="isTechnicianDirectory"><span v-if="relatedError">Unavailable</span><RouterLink v-else-if="currentTicket(person.id)" class="dashboard-text-link current-ticket-link" :to="`/admin/tickets/${currentTicket(person.id)!.id}`">{{ currentTicket(person.id)!.label }}</RouterLink><span v-else class="directory-detail">No active ticket</span></td>
            <td><div class="directory-row-actions"><button class="dashboard-text-link" type="button" :aria-expanded="selectedPersonId === person.id" @click="selectedPersonId = person.id">View Details</button><button class="technician-delete-icon" type="button" :aria-label="`Delete ${isTechnicianDirectory ? 'technician' : 'customer'} account for ${person.name}`" :title="isTechnicianDirectory ? 'Delete technician account' : 'Delete customer account'" :disabled="isDeleting" @click="confirmAccountDeletion(person.id)">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6" /></svg>
            </button></div></td>
          </tr>
        </tbody>
      </table>
      <div class="directory-mobile-list">
        <article v-for="person in filteredRows" :key="person.id" class="ticket-mobile-card">
          <h3>{{ person.name }}</h3>
          <p v-if="!isTechnicianDirectory" class="directory-detail">Contact number: {{ person.contactNumber || 'Not provided' }}</p>
          <p class="directory-detail">#{{ person.id }} · {{ isTechnicianDirectory ? 'Specialization' : 'Address' }}: {{ person.detail || 'Not provided' }}</p>
          <p v-if="isTechnicianDirectory" class="directory-detail">Current ticket: <span v-if="relatedError">Unavailable</span><RouterLink v-else-if="currentTicket(person.id)" class="dashboard-text-link current-ticket-link" :to="`/admin/tickets/${currentTicket(person.id)!.id}`">{{ currentTicket(person.id)!.label }}</RouterLink><span v-else class="directory-detail">No active ticket</span></p>
          <button class="dashboard-text-link" type="button" :aria-expanded="selectedPersonId === person.id" @click="selectedPersonId = person.id">View Details</button>
          <button class="technician-delete-icon" type="button" :aria-label="`Delete ${isTechnicianDirectory ? 'technician' : 'customer'} account for ${person.name}`" :title="isTechnicianDirectory ? 'Delete technician account' : 'Delete customer account'" :disabled="isDeleting" @click="confirmAccountDeletion(person.id)">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6" /></svg>
            </button>
          <a v-if="person.email" class="dashboard-text-link" :href="`mailto:${person.email}`">{{ person.email }}</a>
          <span v-if="isTechnicianDirectory" class="assignment-state" :class="person.availability === 'AVAILABLE' ? 'is-active' : 'is-inactive'">{{ person.availability === 'AVAILABLE' ? 'Available' : 'Unavailable' }}</span>
        </article>
      </div>
    </div>
  </section>
</template>
