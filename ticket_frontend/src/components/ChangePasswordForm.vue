<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { changePasswordRequest, readableAuthError } from '@/services/auth'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ current_password: '', new_password: '', confirm_password: '' })
const saving = ref(false)
const error = ref('')
async function save() {
  if (saving.value) return
  error.value = ''
  if (form.new_password !== form.confirm_password) { error.value = 'Passwords do not match.'; return }
  saving.value = true
  try {
    await changePasswordRequest({ ...form })
    form.current_password = form.new_password = form.confirm_password = ''
    auth.logout()
    await router.replace({ path: '/login', query: { passwordChanged: '1' } })
  } catch (err) { error.value = readableAuthError(err, 'Could not change your password. Please try again.') }
  finally { saving.value = false }
}
</script>
<template>
    <form class="ticket-form-card technician-create-form" @submit.prevent="save">
      <p class="technician-form-note">Signed in as <strong>{{ auth.user?.username }}</strong>. Enter your current password to choose a new one.</p>
      <p v-if="error" class="form-message form-error" role="alert">{{ error }}</p>
      <label class="ticket-form-field">Current password<input v-model="form.current_password" name="current_password" type="password" autocomplete="current-password" required :disabled="saving" /></label>
      <label class="ticket-form-field">New password<input v-model="form.new_password" name="new_password" type="password" autocomplete="new-password" minlength="8" required :disabled="saving" /></label>
      <label class="ticket-form-field">Confirm new password<input v-model="form.confirm_password" name="confirm_password" type="password" autocomplete="new-password" required :disabled="saving" /></label>
      <div class="ticket-form-actions"><button class="button button-primary" type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Change Password' }}</button></div>
    </form>
</template>
