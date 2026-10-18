<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { API_BASE_URL } from '@/services/api'
const auth = useAuthStore()
const failed = ref(false)
const picture = computed(() => auth.user?.profile_picture ? new URL(auth.user.profile_picture, API_BASE_URL).href : '')
watch(picture, () => { failed.value = false })
</script>
<template><img v-if="picture && !failed" :src="picture" alt="" class="account-avatar-image" @error="failed = true" /><span v-else>{{ (auth.user?.username || 'A').charAt(0).toUpperCase() }}</span></template>
<style scoped>.account-avatar-image { width: 100%; height: 100%; object-fit: cover; border-radius: inherit; }</style>
