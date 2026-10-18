<script setup lang="ts">
import { validMobileNumber, mobileNumberMessage } from '@/utils/phone'
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { readableAuthError } from '@/services/auth'
import { createTicket } from '@/services/tickets'
import { listCustomers } from '@/services/directories'

const router = useRouter()
const title = ref('')
const description = ref('')
const contactNumber = ref('')
const address = ref('')
const profileMessage = ref('')
onMounted(async () => {
  try {
    const [customer] = await listCustomers()
    if (customer) {
      if (!address.value) address.value = customer.address || ''
      if (!contactNumber.value) contactNumber.value = customer.contact_number || ''
    }
  } catch { profileMessage.value = 'Enter your contact details below; your saved profile could not be loaded.' }
})
const isSubmitting = ref(false)
const errorMessage = ref('')
const fieldErrors = reactive({ problem_title: '', problem_description: '', contact_number: '', address: '' })

function validationMessage(value: unknown) {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.filter((item): item is string => typeof item === 'string').join(' ')
  return ''
}

async function submitTicket() {
  if (isSubmitting.value) return
  errorMessage.value = ''
  fieldErrors.problem_title = ''
  fieldErrors.problem_description = ''
  fieldErrors.address = ''
  fieldErrors.contact_number = ''
  if (!title.value.trim()) fieldErrors.problem_title = 'Enter a title for your support request.'
  if (!description.value.trim()) fieldErrors.problem_description = 'Describe the problem you are experiencing.'
  if (title.value.trim().length > 200) fieldErrors.problem_title = 'The title must be 200 characters or fewer.'
  if (!address.value.trim()) fieldErrors.address = 'Enter the address where support is needed.'
  if (address.value.trim().length > 100) fieldErrors.address = 'Address must be 100 characters or fewer.'
  if (!validMobileNumber(contactNumber.value)) fieldErrors.contact_number = mobileNumberMessage
  if (Object.values(fieldErrors).some(Boolean)) return

  isSubmitting.value = true
  try {
    const ticket = await createTicket({
      problem_title: title.value.trim(),
      problem_description: description.value.trim(),
      address: address.value.trim(),
      contact_number: contactNumber.value.trim(),
    })
    await router.push({ name: 'customer-ticket-detail', params: { id: ticket.id }, query: { created: '1' } })
  } catch (error) {
    errorMessage.value = readableAuthError(error, 'Could not create your ticket. Please try again.')
    const response = (error as { response?: { data?: unknown } }).response?.data
    if (response && typeof response === 'object') {
      const errors = response as Record<string, unknown>
      fieldErrors.problem_title = validationMessage(errors.problem_title)
      fieldErrors.problem_description = validationMessage(errors.problem_description)
      fieldErrors.address = validationMessage(errors.address)
      fieldErrors.contact_number = validationMessage(errors.contact_number)
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <section class="dashboard-view" aria-labelledby="create-ticket-heading">
    <div class="dashboard-view-heading">
      <div><p class="eyebrow">Support request</p><h2 id="create-ticket-heading">Create Ticket</h2><p>Tell us what is going wrong, and the support team will take a look.</p></div>
    </div>
    <form class="ticket-form-card" novalidate @submit.prevent="submitTicket">
      <div v-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</div>
      <label class="ticket-form-field" for="problem-title">Problem title
        <input id="problem-title" v-model="title" name="problem_title" type="text" maxlength="200" required :aria-invalid="Boolean(fieldErrors.problem_title)" aria-describedby="problem-title-error" placeholder="For example, Unable to connect to Wi-Fi" />
        <small v-if="fieldErrors.problem_title" id="problem-title-error" class="ticket-field-error">{{ fieldErrors.problem_title }}</small>
      </label>
      <label class="ticket-form-field" for="problem-description">Description
        <textarea id="problem-description" v-model="description" name="problem_description" rows="7" required :aria-invalid="Boolean(fieldErrors.problem_description)" aria-describedby="problem-description-error" placeholder="Describe what you were doing and what happened."></textarea>
        <small v-if="fieldErrors.problem_description" id="problem-description-error" class="ticket-field-error">{{ fieldErrors.problem_description }}</small>
      </label>
      <fieldset class="ticket-contact-fields">
        <legend>Contact and location</legend>
        <p class="directory-detail">Confirm where support is needed and how we can reach you for this ticket.</p>
        <p v-if="profileMessage" class="directory-detail" role="status">{{ profileMessage }}</p>
        <label class="ticket-form-field" for="ticket-contact-number">Contact number <span class="optional-label">(optional)</span>
          <input id="ticket-contact-number" v-model="contactNumber" type="tel" name="contact_number" autocomplete="tel" maxlength="30" placeholder="e.g. +63 917 123 4567" :aria-invalid="Boolean(fieldErrors.contact_number)" aria-describedby="ticket-contact-error" />
          <small v-if="fieldErrors.contact_number" id="ticket-contact-error" class="ticket-field-error">{{ fieldErrors.contact_number }}</small>
        </label>
        <label class="ticket-form-field" for="ticket-address">Address
          <input id="ticket-address" v-model="address" name="address" autocomplete="street-address" maxlength="100" required :aria-invalid="Boolean(fieldErrors.address)" aria-describedby="ticket-address-error" placeholder="Building, room, or service address" />
          <small v-if="fieldErrors.address" id="ticket-address-error" class="ticket-field-error">{{ fieldErrors.address }}</small>
        </label>
      </fieldset>
      <div class="ticket-form-actions">
        <RouterLink class="button button-secondary" to="/customer/tickets">Cancel</RouterLink>
        <button class="button button-primary" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Submitting…' : 'Submit Ticket' }}
        </button>
      </div>
    </form>
  </section>
</template>
