<script setup lang="ts">
import AuthBrandPanel from '@/components/AuthBrandPanel.vue'
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { readableAuthError } from '@/services/auth'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const email = ref('')
const address = ref('')
const contactNumber = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

async function submitRegistration() {
  if (submitting.value) return
  errorMessage.value = ''
  if (!username.value.trim() || !address.value.trim() || !contactNumber.value.trim() || !password.value || !confirmPassword.value) {
    errorMessage.value = 'Complete all required fields.'
    return
  }
  if (password.value.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters.'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  submitting.value = true
  try {
    await auth.register({
      username: username.value.trim(),
      email: email.value.trim() || undefined,
      address: address.value.trim(),
      contact_number: contactNumber.value.trim(),
      password: password.value,
    })
    await router.replace({ path: '/login', query: { registered: '1' } })
  } catch (error) {
    errorMessage.value = readableAuthError(error, 'Unable to create your account. Please review the information and try again.')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="auth-page auth-designed">
    <div class="auth-layout">
      <AuthBrandPanel :registration="true" />
    <section class="auth-card" aria-labelledby="register-heading">
      <RouterLink class="brand auth-brand" to="/" aria-label="Tickarla home">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none"><path d="M4.5 7.5h15v10a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-10Z"/><path d="M4.5 10h4a2 2 0 1 0 0-4h-4m15 4h-4a2 2 0 1 1 0-4h4M12 10v1m0 2v1m0 2v1"/></svg>
        </span>
        <span>Tickarla</span>
      </RouterLink>

      <span class="eyebrow">CUSTOMER ACCOUNT</span>
      <h1 id="register-heading">Create your account</h1>
      <p class="auth-intro">Register as a customer to submit and follow your support requests.</p>
      <p v-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</p>

      <form class="auth-form" @submit.prevent="submitRegistration">
        <label class="auth-field">
          <span>Username</span>
          <input v-model="username" type="text" name="username" autocomplete="username" required maxlength="150">
        </label>
        <label class="auth-field">
          <span>Email <span class="optional-label">(optional)</span></span>
          <input v-model="email" type="email" name="email" autocomplete="email">
        </label>
        <label class="auth-field">
          <span>Address</span>
          <input v-model="address" type="text" name="address" autocomplete="street-address" required maxlength="100">
        </label>
        <label class="auth-field">
          <span>Contact number</span>
          <input v-model="contactNumber" type="tel" name="contact_number" autocomplete="tel" required maxlength="30" placeholder="e.g. +63 917 123 4567">
        </label>
        <label class="auth-field">
          <span>Password</span>
          <span class="password-input-wrap">
            <input v-model="password" :type="showPassword ? 'text' : 'password'" name="new-password" autocomplete="new-password" required minlength="8">
            <button class="password-toggle" type="button" :aria-label="showPassword ? 'Hide password' : 'Show password'" :aria-pressed="showPassword" @click="showPassword = !showPassword">
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </span>
        </label>
        <label class="auth-field">
          <span>Confirm password</span>
          <span class="password-input-wrap">
            <input v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" name="confirm-password" autocomplete="new-password" required minlength="8">
            <button class="password-toggle" type="button" :aria-label="showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'" :aria-pressed="showConfirmPassword" @click="showConfirmPassword = !showConfirmPassword">{{ showConfirmPassword ? 'Hide' : 'Show' }}</button>
          </span>
        </label>
        <button class="button button-primary auth-submit" type="submit" :disabled="submitting">
          {{ submitting ? 'Creating account...' : 'Create account' }}
        </button>
      </form>

      <p class="auth-switch">Already registered? <RouterLink to="/login">Login</RouterLink></p>
      <RouterLink class="auth-home-link" to="/">Back to home</RouterLink>
    </section>
    </div>
  </main>
</template>
