<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import DirectoryDetailsModal from './DirectoryDetailsModal.vue'
import { api } from '@/services/api'
import { readableAuthError } from '@/services/auth'
import { useAuthStore } from '@/stores/auth'

interface CustomerProfile {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  address: string
  contact_number: string
}
const emit = defineEmits<{ close: [] }>()
const auth = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')
const profileId = ref<number | null>(null)
const form = reactive({ username: '', first_name: '', last_name: '', email: '', address: '', contact_number: '' })
onMounted(async () => {
  try {
    const { data } = await api.get<CustomerProfile[]>('customers/')
    const profile = data[0]
    if (!profile) throw new Error('Customer profile missing')
    profileId.value = profile.id
    for (const key of Object.keys(form) as (keyof typeof form)[]) form[key] = profile[key] || ''
  } catch (err) { error.value = readableAuthError(err, 'Could not load your profile. Close this window and try again.') }
  finally { loading.value = false }
})
async function save() {
  if (saving.value || profileId.value === null) return
  saving.value = true
  error.value = message.value = ''
  try {
    const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()]))
    const { data } = await api.put<CustomerProfile>(`customers/${profileId.value}/`, payload)
    Object.assign(form, { username: data.username, first_name: data.first_name, last_name: data.last_name, email: data.email, address: data.address, contact_number: data.contact_number })
    if (auth.user) Object.assign(auth.user, { username: data.username, first_name: data.first_name, last_name: data.last_name, email: data.email })
    message.value = 'Your profile has been updated.'
  } catch (err) { error.value = readableAuthError(err, 'Could not save your profile. Please try again.') }
  finally { saving.value = false }
}
</script>

<template>
  <DirectoryDetailsModal title="My Profile" :dismissible="!saving" @close="emit('close')">
    <p v-if="loading" class="dashboard-message" role="status">Loading your profile...</p>
    <p v-if="error" class="form-message form-error" role="alert">{{ error }}</p>
    <form v-if="!loading && profileId !== null" class="ticket-form-card technician-create-form" @submit.prevent="save">
      <p v-if="message" class="form-message form-success" role="status">{{ message }}</p>
      <label class="ticket-form-field">Username<input v-model="form.username" name="username" autocomplete="username" maxlength="150" required :disabled="saving" /></label>
      <label class="ticket-form-field">First name<input v-model="form.first_name" name="first_name" autocomplete="given-name" maxlength="150" :disabled="saving" /></label>
      <label class="ticket-form-field">Last name<input v-model="form.last_name" name="last_name" autocomplete="family-name" maxlength="150" :disabled="saving" /></label>
      <label class="ticket-form-field">Email<input v-model="form.email" name="email" type="email" autocomplete="email" maxlength="254" :disabled="saving" /></label>
      <label class="ticket-form-field">Contact number<input v-model="form.contact_number" name="contact_number" type="tel" autocomplete="tel" maxlength="30" :disabled="saving" /></label>
      <label class="ticket-form-field">Address<input v-model="form.address" name="address" autocomplete="street-address" maxlength="100" required :disabled="saving" /></label>
      <div class="ticket-form-actions"><button class="button button-secondary" type="button" :disabled="saving" @click="emit('close')">Close</button><button class="button button-primary" type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button></div>
    </form>
  </DirectoryDetailsModal>
</template>
