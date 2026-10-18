<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getNotifications } from '@/services/notifications'
const route = useRoute()
const unread = ref(0)
const unavailable = ref(false)
const path = computed(() => `/${String(route.meta.role || 'CUSTOMER').toLowerCase()}/notifications`)
let timer: ReturnType<typeof setInterval> | undefined
let active = true
let fetching = false
async function refresh() {
  if (fetching || document.hidden) return
  fetching = true
  try { const data = await getNotifications(); if (active) { unread.value = data.unread_count; unavailable.value = false } }
  catch { if (active) unavailable.value = true }
  finally { fetching = false }
}
onMounted(() => { void refresh(); timer = setInterval(refresh, 20000); window.addEventListener('tickarla:notifications-changed', refresh); document.addEventListener('visibilitychange', refresh) })
onUnmounted(() => { active = false; clearInterval(timer); window.removeEventListener('tickarla:notifications-changed', refresh); document.removeEventListener('visibilitychange', refresh) })
</script>
<template><RouterLink :to="path" class="notification-bell" :aria-label="unavailable ? 'Notifications, updates temporarily unavailable' : `Notifications, ${unread} unread`" :title="unavailable ? 'Notifications temporarily unavailable' : 'Notifications'"><svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg><span v-if="unread" class="notification-counter">{{ unread > 99 ? '99+' : unread }}</span></RouterLink></template>
<style scoped>
.notification-bell { position: relative; display: grid; place-items: center; width: 42px; height: 42px; border: 1px solid var(--border); border-radius: 11px; color: var(--text-primary); background: var(--surface); }
.notification-bell:hover { background: var(--surface-raised); }
.notification-counter { position: absolute; right: -5px; top: -6px; min-width: 18px; padding: 3px 4px; border-radius: 20px; font-size: 9px; font-weight: 750; text-align: center; color: white; background: #2563eb; border: 2px solid var(--surface); }
</style>
