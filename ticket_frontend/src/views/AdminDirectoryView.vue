<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { createTechnician, listCustomers, listTechnicians } from '@/services/directories'
import { readableAuthError } from '@/services/auth'
import type { CustomerDirectoryEntry, Technician } from '@/types/admin'

interface DirectoryRow {
  id: number
  name: string
  username: string
  email: string
  detail: string
  availability?: Technician['availability_status']
}

const route = useRoute()
const customers = ref<CustomerDirectoryEntry[]>([])
const technicians = ref<Technician[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
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
    id: person.id,
    username: person.username,
    name: `${person.first_name} ${person.last_name}`.trim() || person.username,
    email: person.email,
    detail: person.username,
  })))

watch(isTechnicianDirectory, async (technicianDirectory) => {
  isLoading.value = true
  errorMessage.value = ''
  try {
    if (technicianDirectory) technicians.value = await listTechnicians()
    else customers.value = await listCustomers()
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
  <section class="dashboard-view" aria-labelledby="directory-heading">
    <div class="dashboard-view-heading">
      <div><p class="eyebrow">User directory</p><h2 id="directory-heading">{{ heading }}</h2><p>{{ isTechnicianDirectory ? 'View technician contact and availability information.' : 'View customer account information.' }}</p></div>
      <button v-if="isTechnicianDirectory" class="button button-primary" type="button" :aria-expanded="showCreateForm" aria-controls="create-technician-form" @click="showCreateForm = !showCreateForm; createError = ''; createMessage = ''">{{ showCreateForm ? 'Close form' : 'Add Technician' }}</button>
    </div>
    <p v-if="createMessage" class="form-message form-success" role="status">{{ createMessage }}</p>
    <form v-if="isTechnicianDirectory && showCreateForm" id="create-technician-form" class="ticket-form-card technician-create-form" novalidate @submit.prevent="submitTechnician">
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
        <button class="button button-secondary" type="button" @click="showCreateForm = false">Cancel</button>
        <button class="button button-primary" type="submit" :disabled="isCreating">{{ isCreating ? 'Creating…' : 'Create Technician' }}</button>
      </div>
    </form>
    <div v-if="isLoading" class="dashboard-message" role="status">Loading {{ heading.toLowerCase() }}…</div>
    <div v-else-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
    <div v-else-if="rows.length === 0" class="ticket-empty-state">
      <h3>No {{ heading.toLowerCase() }} found</h3><p>There are no records to display.</p>
    </div>
    <div v-else class="ticket-table-wrap">
      <table class="ticket-table directory-table">
        <thead><tr><th scope="col">Name</th><th scope="col">Email</th><th scope="col">{{ isTechnicianDirectory ? 'Specialization' : 'Username' }}</th><th v-if="isTechnicianDirectory" scope="col">Availability</th></tr></thead>
        <tbody>
          <tr v-for="person in rows" :key="person.id">
            <td><strong>{{ person.name }}</strong><small>@{{ person.username }}</small></td>
            <td>{{ person.email || '—' }}</td>
            <td>{{ person.detail || '—' }}</td>
            <td v-if="isTechnicianDirectory"><span class="assignment-state" :class="person.availability === 'AVAILABLE' ? 'is-active' : 'is-inactive'">{{ person.availability === 'AVAILABLE' ? 'Available' : 'Unavailable' }}</span></td>
          </tr>
        </tbody>
      </table>
      <div class="directory-mobile-list">
        <article v-for="person in rows" :key="person.id" class="ticket-mobile-card">
          <h3>{{ person.name }}</h3><p class="directory-username">@{{ person.username }}</p>
          <a v-if="person.email" class="dashboard-text-link" :href="`mailto:${person.email}`">{{ person.email }}</a>
          <p class="directory-detail">{{ isTechnicianDirectory ? 'Specialization' : 'Username' }}: {{ person.detail || '—' }}</p>
          <span v-if="isTechnicianDirectory" class="assignment-state" :class="person.availability === 'AVAILABLE' ? 'is-active' : 'is-inactive'">{{ person.availability === 'AVAILABLE' ? 'Available' : 'Unavailable' }}</span>
        </article>
      </div>
    </div>
  </section>
</template>
