<script setup lang="ts">
import TechnicianProfileForm from '@/components/TechnicianProfileForm.vue'
import ProfilePictureEditor from '@/components/ProfilePictureEditor.vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ChangePasswordDropdown from '@/components/ChangePasswordDropdown.vue'
const auth = useAuthStore()
</script>

<template>
  <section class="dashboard-view account-profile-page" aria-labelledby="account-profile-heading">
    <div class="dashboard-view-heading"><div><p class="eyebrow">MY ACCOUNT</p><h2 id="account-profile-heading">My Profile</h2><p>Manage your profile picture and password.</p></div><RouterLink class="button button-secondary" :to="auth.user?.role === 'TECHNICIAN' ? '/technician' : '/admin'">Back to dashboard</RouterLink></div>
    <ProfilePictureEditor />
    <TechnicianProfileForm v-if="auth.user?.role === 'TECHNICIAN'" />
    <ChangePasswordDropdown />
  </section>
</template>

<style scoped>
.account-profile-page > .profile-picture-editor, .account-profile-page > form { max-width: 780px; }
.account-profile-page > form { margin-top: 24px; }
</style>
