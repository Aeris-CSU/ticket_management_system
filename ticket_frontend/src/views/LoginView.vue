<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { readableAuthError } from '@/services/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const registered = computed(() => route.query.registered === '1')

async function submitLogin() {
  if (submitting.value) return
  errorMessage.value = ''
  if (!username.value.trim() || !password.value) {
    errorMessage.value = 'Enter your username and password.'
    return
  }
  submitting.value = true
  try {
    const path = await auth.login({ username: username.value.trim(), password: password.value })
    await router.replace(path)
  } catch (error) {
    errorMessage.value = readableAuthError(error, 'Unable to sign in. Please check your details and try again.')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card" aria-labelledby="login-heading">
      <RouterLink class="brand auth-brand" to="/" aria-label="Tickarla home">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none"><path d="M4.5 7.5h15v10a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-10Z"/><path d="M4.5 10h4a2 2 0 1 0 0-4h-4m15 4h-4a2 2 0 1 1 0-4h4M12 10v1m0 2v1m0 2v1"/></svg>
        </span>
        <span>Tickarla</span>
      </RouterLink>

      <span class="eyebrow">WELCOME BACK</span>
      <h1 id="login-heading">Sign in to Tickarla</h1>
      <p class="auth-intro">Access your support account to follow tickets and updates.</p>

      <p v-if="registered" class="form-message form-success" role="status">Your account was created. You can sign in now.</p>
      <p v-if="errorMessage" class="form-message form-error" role="alert">{{ errorMessage }}</p>

      <form class="auth-form" @submit.prevent="submitLogin">
        <label class="auth-field">
          <span>Username</span>
          <input v-model="username" type="text" name="username" autocomplete="username" required maxlength="150" autofocus>
        </label>
        <label class="auth-field">
          <span>Password</span>
          <span class="password-input-wrap">
            <input v-model="password" :type="showPassword ? 'text' : 'password'" name="password" autocomplete="current-password" required>
            <button class="password-toggle" type="button" :aria-label="showPassword ? 'Hide password' : 'Show password'" :aria-pressed="showPassword" @click="showPassword = !showPassword">
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </span>
        </label>
        <button class="button button-primary auth-submit" type="submit" :disabled="submitting">
          {{ submitting ? 'Signing in...' : 'Login' }}
        </button>
      </form>

      <p class="auth-switch">New to Tickarla? <RouterLink to="/register">Create an account</RouterLink></p>
      <RouterLink class="auth-home-link" to="/">Back to home</RouterLink>
    </section>
  </main>
</template>
