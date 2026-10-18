<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { readableAuthError } from '@/services/auth'
import AccountAvatar from './AccountAvatar.vue'
import type { AuthUser } from '@/types/auth'
const auth = useAuthStore()
const busy = ref(false)
const message = ref('')
const error = ref('')
async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || busy.value) return
  error.value = message.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    error.value = 'Choose a JPG, PNG, or WebP image smaller than 5 MB.'
    input.value = ''
    return
  }
  busy.value = true
  try {
    const payload = new FormData()
    payload.append('profile_picture', file)
    const { data } = await api.put<AuthUser>('accounts/me/picture/', payload)
    if (auth.user) auth.user.profile_picture = data.profile_picture
    message.value = 'Profile picture updated.'
  } catch (err) { error.value = readableAuthError(err, 'Could not upload your picture. Please try again.') }
  finally { busy.value = false; input.value = '' }
}
async function remove() {
  if (busy.value) return
  busy.value = true
  error.value = message.value = ''
  try {
    await api.delete('accounts/me/picture/')
    if (auth.user) auth.user.profile_picture = null
    message.value = 'Profile picture removed.'
  } catch (err) { error.value = readableAuthError(err, 'Could not remove your picture.') }
  finally { busy.value = false }
}
</script>
<template>
  <section class="profile-picture-editor" aria-label="Profile picture" :aria-busy="busy">
    <div class="picture-controls"><span class="picture-avatar"><AccountAvatar /></span><div><label class="picture-upload">Profile picture<input type="file" accept="image/jpeg,image/png,image/webp" :disabled="busy" @change="upload" /></label><small>JPG, PNG or WebP. Up to 5 MB.</small><button v-if="auth.user?.profile_picture" type="button" class="dashboard-text-link picture-remove" :disabled="busy" @click="remove">Remove picture</button></div></div>
    <p v-if="busy" role="status">Saving picture...</p><p v-if="message" class="form-message form-success" role="status">{{ message }}</p><p v-if="error" class="form-message form-error" role="alert">{{ error }}</p>
  </section>
</template>
<style scoped>
.profile-picture-editor { margin: 20px 0; padding: 20px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
.picture-controls { display: flex; gap: 20px; align-items: center; }
.picture-avatar { display: grid; place-items: center; flex-shrink: 0; width: 72px; height: 72px; border-radius: 50%; background: var(--surface-raised); color: var(--blue); font-size: 25px; }
.picture-upload { display: grid; gap: 10px; color: var(--text-primary); font-size: 13px; font-weight: 600; }
.picture-upload input { max-width: 100%; width: 260px; font-size: 12px; }
.picture-controls > div { min-width: 0; }
small { display: block; margin: 10px 0; color: var(--muted); font-size: 11px; line-height: 1.6; }
.picture-controls .picture-remove { font-size: 11px; font-weight: 500; }
</style>
