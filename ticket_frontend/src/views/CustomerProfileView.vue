<script setup lang="ts">
import ChangePasswordForm from '@/components/ChangePasswordForm.vue'
import ProfilePictureEditor from '@/components/ProfilePictureEditor.vue'
import { validMobileNumber, mobileNumberMessage } from '@/utils/phone'
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
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
const auth = useAuthStore()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')
const profileId = ref<number | null>(null)
const form = reactive({ first_name: '', last_name: '', email: '', address: '', contact_number: '' })
const savedForm = ref({ ...form })
onMounted(async () => {
  try {
    const { data } = await api.get<CustomerProfile[]>('customers/')
    const profile = data[0]
    if (!profile) throw new Error('Customer profile missing')
    profileId.value = profile.id
    for (const key of Object.keys(form) as (keyof typeof form)[]) form[key] = profile[key] || ''
    savedForm.value = { ...form }
  } catch (err) { error.value = readableAuthError(err, 'Could not load your profile. Reload this page to try again.') }
  finally { loading.value = false }
})
async function save() {
  if (saving.value || profileId.value === null) return
  error.value = message.value = ''
  if (!form.address.trim()) { error.value = 'Address is required.'; return }
  const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()]).filter(([key, value]) => value !== savedForm.value[key as keyof typeof form]))
  if ('contact_number' in payload && !validMobileNumber(form.contact_number)) { error.value = mobileNumberMessage; return }
  if (!Object.keys(payload).length) { message.value = 'Your profile is already up to date.'; return }
  saving.value = true
  error.value = message.value = ''
  try {
    const { data } = await api.put<CustomerProfile>(`customers/${profileId.value}/`, payload)
    Object.assign(form, { first_name: data.first_name, last_name: data.last_name, email: data.email, address: data.address, contact_number: data.contact_number })
    savedForm.value = { ...form }
    if (auth.user) Object.assign(auth.user, { username: data.username, first_name: data.first_name, last_name: data.last_name, email: data.email })
    message.value = 'Your profile has been updated.'
  } catch (err) { error.value = readableAuthError(err, 'Could not save your profile. Please try again.') }
  finally { saving.value = false }
}
</script>

<template>
  <section class="dashboard-view customer-profile-page" aria-labelledby="customer-profile-heading">
    <div class="dashboard-view-heading"><div><p class="eyebrow">MY ACCOUNT</p><h2 id="customer-profile-heading">Edit profile</h2><p>Keep your personal and contact information up to date.</p></div><RouterLink class="button button-secondary" to="/customer">Back to dashboard</RouterLink></div>
    <ProfilePictureEditor />
    <p v-if="loading" class="dashboard-message" role="status">Loading your profile...</p>
    <p v-if="error && profileId === null" class="form-message form-error" role="alert">{{ error }}</p>
    <form v-if="!loading && profileId !== null" class="ticket-form-card customer-profile-form" :aria-busy="saving" @submit.prevent="save">
      <p v-if="message" class="form-message form-success" role="status">{{ message }}</p>
      <label class="ticket-form-field">First name<input v-model="form.first_name" name="first_name" autocomplete="given-name" maxlength="150" :disabled="saving" /></label>
      <label class="ticket-form-field">Last name<input v-model="form.last_name" name="last_name" autocomplete="family-name" maxlength="150" :disabled="saving" /></label>
      <label class="ticket-form-field">Email<input v-model="form.email" name="email" type="email" autocomplete="email" maxlength="254" :disabled="saving" /></label>
      <label class="ticket-form-field">Contact number<input v-model="form.contact_number" name="contact_number" type="tel" autocomplete="tel" maxlength="30" :disabled="saving" /></label>
      <label class="ticket-form-field">Address<input v-model="form.address" name="address" autocomplete="street-address" maxlength="100" required :disabled="saving" /></label>
      <p v-if="error" class="form-message form-error" role="alert">{{ error }}</p>
      <div class="ticket-form-actions"><button class="button button-primary" type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button></div>
    </form>
    <details class="customer-password-section">
      <summary>Change password <span aria-hidden="true">&#8964;</span></summary>
      <ChangePasswordForm />
    </details>
  </section>
</template>

<style scoped>
.customer-profile-form { max-width: 780px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px; margin-top: 24px; padding: 28px; }
.customer-profile-form > .form-message, .customer-profile-form > .ticket-form-actions { grid-column: 1 / -1; }
.customer-profile-form > .ticket-form-actions { display: flex; justify-content: flex-end; padding-top: 20px; border-top: 1px solid var(--border); }
@media (max-width: 600px) { .customer-profile-form { grid-template-columns: minmax(0, 1fr); padding: 22px; gap: 18px; } }
.customer-password-section { max-width: 780px; margin-top: 24px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
.customer-password-section > summary { display: flex; justify-content: space-between; padding: 20px 24px; cursor: pointer; color: var(--text-primary); font-size: 14px; font-weight: 650; list-style: none; }
.customer-password-section > summary::-webkit-details-marker { display: none; }
.customer-password-section > summary:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; }
.customer-password-section :deep(form) { border: 0; margin: 0; padding: 0 24px 24px; box-shadow: none; }
</style>
