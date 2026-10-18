<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getNotifications, updateNotifications, type NotificationItem } from '@/services/notifications'
import { readableAuthError } from '@/services/auth'
const route = useRoute()
const router = useRouter()
const items = ref<NotificationItem[]>([])
const filter = ref('all')
const page = ref(1)
const hasMore = ref(false)
const total = ref(0)
const unread = ref(0)
const selected = ref<number[]>([])
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const pendingDelete = ref<'selected' | 'all' | null>(null)
const allSelected = computed(() => items.value.length > 0 && items.value.every(item => selected.value.includes(item.id)))
let timer: ReturnType<typeof setInterval> | undefined
let active = true
let generation = 0
async function load(reset = true) {
  const request = ++generation
  try {
    const lastPage = reset ? 1 : page.value
    const pages = await Promise.all(Array.from({ length: lastPage }, (_, index) => getNotifications(filter.value, index + 1)))
    if (!active || request !== generation) return
    items.value = pages.flatMap(result => result.results)
    total.value = pages[0]!.total; unread.value = pages[0]!.unread_count
    hasMore.value = pages[pages.length - 1]!.has_more
    page.value = lastPage
    selected.value = selected.value.filter(id => items.value.some(item => item.id === id))
    error.value = ''
  } catch (err) { if (active && request === generation) error.value = readableAuthError(err, 'Could not load notifications. Please try again.') }
  finally { if (active && request === generation) loading.value = false }
}
async function changeFilter(value: string) { filter.value = value; selected.value = []; loading.value = true; await load() }
function selectAll() { selected.value = allSelected.value ? [] : items.value.map(item => item.id) }
async function act(action: 'read' | 'delete', all = false, ids = selected.value) {
  if (busy.value || (!all && !ids.length)) return false
  busy.value = true
  try {
    await updateNotifications(action, ids, all)
    pendingDelete.value = null; selected.value = []
    await load(false)
    return true
  } catch (err) { error.value = readableAuthError(err, 'Could not update notifications. Please try again.'); return false }
  finally { busy.value = false }
}
async function open(item: NotificationItem) {
  if (busy.value) return
  if (!item.is_read && !await act('read', false, [item.id])) return
  if (item.ticket_id) await router.push(`/${String(route.meta.role).toLowerCase()}/tickets/${item.ticket_id}`)
}
async function more() { if (loading.value || busy.value) return; page.value++; loading.value = true; await load(false) }
function refresh() { if (!document.hidden && !busy.value && !loading.value) void load(false) }
onMounted(() => { void load(); timer = setInterval(refresh, 20000); document.addEventListener('visibilitychange', refresh) })
onUnmounted(() => { active = false; clearInterval(timer); document.removeEventListener('visibilitychange', refresh) })
</script>
<template>
  <section class="dashboard-view" aria-labelledby="notifications-heading">
    <div class="dashboard-view-heading"><div><p class="eyebrow">YOUR UPDATES</p><h2 id="notifications-heading">Notifications</h2><p>Ticket activity for your account. Updates refresh every 20 seconds.</p></div></div>
    <div class="notification-inbox">
      <div class="notification-toolbar">
        <div class="notification-tabs" aria-label="Notification filters"><button type="button" :aria-pressed="filter === 'all'" @click="changeFilter('all')">All</button><button type="button" :aria-pressed="filter === 'unread'" @click="changeFilter('unread')">Unread ({{ unread }})</button></div>
        <button type="button" class="dashboard-text-link" :disabled="busy || !unread" @click="act('read', true)">Mark all as read</button>
        <button type="button" class="notification-danger" :disabled="busy" @click="pendingDelete = 'all'">Delete all</button>
      </div>
      <p v-if="error" class="form-message form-error" role="alert">{{ error }} <button type="button" @click="load(false)">Retry</button></p>
      <div v-if="pendingDelete" class="notification-confirm" role="group" aria-label="Confirm notification deletion"><p>{{ pendingDelete === 'all' ? 'Delete all your notifications, including read and unread history?' : `Delete ${selected.length} selected notifications?` }} This cannot be undone.</p><button type="button" class="button button-secondary" :disabled="busy" @click="pendingDelete = null">Keep notifications</button><button type="button" class="button button-primary" :disabled="busy" @click="act('delete', pendingDelete === 'all')">Confirm delete</button></div>
      <div v-if="items.length" class="notification-selection"><label><input type="checkbox" :checked="allSelected" :disabled="busy" @change="selectAll" /> Select displayed</label><span>{{ selected.length }} selected</span><button type="button" :disabled="busy || !selected.length" @click="act('read')">Mark as read</button><button type="button" class="notification-danger" :disabled="busy || !selected.length" @click="pendingDelete = 'selected'">Delete selected</button></div>
      <p v-if="loading" class="dashboard-message" role="status">Loading notifications...</p>
      <p v-else-if="!items.length && !error" class="notification-empty">{{ filter === 'unread' ? 'You are all caught up. No unread notifications.' : 'No notifications yet. Ticket updates will appear here.' }}</p>
      <ul class="notification-list"><li v-for="item in items" :key="item.id" :class="{ unread: !item.is_read }"><input v-model="selected" type="checkbox" :value="item.id" :disabled="busy" :aria-label="`Select notification: ${item.message}`" /><button type="button" class="notification-message" :disabled="busy" @click="open(item)"><span>{{ item.message }}</span><small><time :datetime="item.created_at">{{ new Date(item.created_at).toLocaleString() }}</time><span v-if="!item.is_read"> ? Unread</span><span v-if="!item.ticket_id"> ? Ticket no longer available to your account</span></small></button><button v-if="!item.is_read" type="button" class="notification-read" :disabled="busy" :aria-label="`Mark as read: ${item.message}`" @click="act('read', false, [item.id])">Mark read</button></li></ul>
      <div class="notification-bottom"><span>{{ items.length }} of {{ total }} notifications</span><button v-if="hasMore" type="button" class="button button-secondary" :disabled="loading || busy" @click="more">Load more</button></div>
    </div>
  </section>
</template>
<style scoped>
.notification-inbox { margin-top: 24px; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }
.notification-toolbar, .notification-selection, .notification-bottom { display: flex; align-items: center; flex-wrap: wrap; gap: 16px; padding: 18px 22px; border-bottom: 1px solid var(--border); font-size: 12px; color: var(--muted); }
.notification-tabs { display: flex; gap: 5px; margin-right: auto; }
.notification-tabs button { padding: 9px 15px; border: 0; border-radius: 8px; background: transparent; color: var(--muted); cursor: pointer; font-weight: 650; }
.notification-tabs button[aria-pressed='true'] { background: rgb(59 130 246 / 12%); color: var(--link); }
.notification-danger { color: #c33636; background: transparent; border: 0; cursor: pointer; font-size: 12px; }
.notification-selection label { display: flex; align-items: center; gap: 9px; }
.notification-selection > button, .notification-read { background: transparent; border: 0; color: var(--link); cursor: pointer; font-size: 11px; }
.notification-list { list-style: none; padding: 0; margin: 0; }
.notification-list li { display: flex; align-items: center; gap: 15px; padding: 20px 22px; border-bottom: 1px solid var(--border); }
.notification-list li.unread { background: rgb(59 130 246 / 5%); box-shadow: inset 3px 0 #4c82d6; }
.notification-message { min-width: 0; flex: 1; padding: 0; text-align: left; color: var(--text-primary); background: none; border: 0; cursor: pointer; font-size: 13px; line-height: 1.7; overflow-wrap: anywhere; }
.unread .notification-message > span { font-weight: 650; }
.notification-message small { display: block; margin-top: 8px; font-size: 10px; color: var(--muted); }
.notification-empty { padding: 40px 22px; text-align: center; color: var(--muted); font-size: 13px; }
.notification-bottom { justify-content: space-between; border-bottom: 0; }
.notification-confirm { padding: 22px; background: var(--surface-raised); border-bottom: 1px solid var(--border); font-size: 13px; }
.notification-confirm .button { margin: 8px 10px 0 0; }
button:disabled { opacity: .5; cursor: default; }
html[data-theme='dark'] .notification-danger { color: #fca5a5; }
@media (max-width: 600px) { .notification-list li { padding: 18px 14px; gap: 10px; flex-wrap: wrap; } .notification-message { flex-basis: calc(100% - 35px); } .notification-read { margin-left: 25px; } .notification-toolbar, .notification-selection { padding: 16px; gap: 12px; } }
</style>
