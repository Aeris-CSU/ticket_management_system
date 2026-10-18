<script setup lang="ts">
import PersonalInformationDropdown from './PersonalInformationDropdown.vue'
import { onMounted, reactive, ref } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { readableAuthError } from '@/services/auth'
interface Profile { id: number; first_name: string; last_name: string; email: string; specialization: string }
const auth = useAuthStore()
const profileId = ref<number | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')
const form = reactive({ first_name: '', last_name: '', email: '', specialization: '' })
onMounted(async () => {
  try {
    const { data } = await api.get<Profile[]>('technicians/')
    const profile = data[0]
    if (!profile) throw new Error('Missing profile')
    profileId.value = profile.id
    for (const key of Object.keys(form) as (keyof typeof form)[]) form[key] = profile[key] || ''
  } catch (err) { error.value = readableAuthError(err, 'Could not load your profile. Reload the page to try again.') }
  finally { loading.value = false }
})
async function save() {
  if (!profileId.value || saving.value) return
  error.value = message.value = ''
  if (!form.specialization.trim()) { error.value = 'Enter your specialization.'; return }
  saving.value = true
  try {
    const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()]))
    const { data } = await api.put<Profile>(`technicians/update/${profileId.value}/`, payload)
    for (const key of Object.keys(form) as (keyof typeof form)[]) form[key] = data[key] || ''
    if (auth.user) Object.assign(auth.user, { first_name: data.first_name, last_name: data.last_name, email: data.email })
    message.value = 'Your profile has been updated.'
  } catch (err) { error.value = readableAuthError(err, 'Could not save your profile. Please try again.') }
  finally { saving.value = false }
}
</script>
<template>
  <PersonalInformationDropdown>
  <section class="technician-personal-profile" aria-label="Edit technician profile">
    <p v-if="loading" class="dashboard-message" role="status">Loading your profile...</p>
    <p v-if="error" class="form-message form-error" role="alert">{{ error }}</p>
    <form v-if="!loading && profileId" class="ticket-form-card technician-personal-form" :aria-busy="saving" @submit.prevent="save">
      <p v-if="message" class="form-message form-success" role="status">{{ message }}</p>
      <label class="ticket-form-field">First name<input v-model="form.first_name" name="first_name" autocomplete="given-name" maxlength="150" :disabled="saving" /></label>
      <label class="ticket-form-field">Last name<input v-model="form.last_name" name="last_name" autocomplete="family-name" maxlength="150" :disabled="saving" /></label>
      <label class="ticket-form-field">Email<input v-model="form.email" name="email" type="email" autocomplete="email" maxlength="254" :disabled="saving" /></label>
      <label class="ticket-form-field">Specialization<input v-model="form.specialization" name="specialization" maxlength="100" required :disabled="saving" /></label>
      <div class="ticket-form-actions"><button class="button button-primary" type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button></div>
    </form>
  </section>
  </PersonalInformationDropdown>
</template>
<style scoped>
.technician-personal-profile { max-width: 780px; margin: 0; }
.technician-personal-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px; padding: 0 24px 24px; border: 0; box-shadow: none; }
.technician-personal-form h3, .technician-personal-form > p, .ticket-form-actions { grid-column: 1 / -1; }
.technician-personal-form h3 { margin: 0; font-size: 17px; }
.ticket-form-actions { display: flex; justify-content: flex-end; }
@media (max-width: 600px) { .technician-personal-form { grid-template-columns: minmax(0, 1fr); padding: 22px; } }
</style>
