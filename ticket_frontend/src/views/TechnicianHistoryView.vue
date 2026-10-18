<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '@/services/api'
import { readableAuthError } from '@/services/auth'
import TicketStatusBadge from '@/components/dashboard/TicketStatusBadge.vue'
import DirectoryDetailsModal from '@/components/dashboard/DirectoryDetailsModal.vue'
import type { TicketStatus } from '@/types/ticket'
interface HistoryItem { id: number; ticket_id: number; ticket_number: string; problem_title: string; problem_description: string; current_status: TicketStatus; customer_name: string; created_at: string; ended_at: string | null; end_reason: string }
const items = ref<HistoryItem[]>([])
const selected = ref<HistoryItem | null>(null)
const search = ref('')
const outcome = ref('')
const page = ref(1)
const count = ref(0)
const hasNext = ref(false)
const loading = ref(true)
const error = ref('')
const outcomes: Record<string, string> = { RESOLVED: 'Resolved', CANCELLED: 'Cancelled', REASSIGNED: 'Reassigned away', UNASSIGNED: 'Unassigned', '': 'Previous assignment' }
let generation = 0
async function load(reset = false) {
  if (reset) page.value = 1
  const request = ++generation
  loading.value = true; error.value = ''
  try {
    const { data } = await api.get<{ results: HistoryItem[]; count: number; next: string | null }>('assignments/history/', { params: { page: page.value, search: search.value.trim(), outcome: outcome.value } })
    if (request !== generation) return
    items.value = data.results; count.value = data.count; hasNext.value = Boolean(data.next)
  } catch (err) { if (request === generation) error.value = readableAuthError(err, 'Could not load your ticket history. Please try again.') }
  finally { if (request === generation) loading.value = false }
}
function clear() { search.value = outcome.value = ''; void load(true) }
function date(value: string | null) { return value ? new Date(value).toLocaleString() : 'Not recorded' }
onMounted(() => load())
</script>
<template>
  <section class="dashboard-view" aria-labelledby="history-heading">
    <div class="dashboard-view-heading"><div><p class="eyebrow">YOUR PAST WORK</p><h2 id="history-heading">Ticket History</h2><p>Review your previous assignments. History is read-only and shows how each assignment ended.</p></div></div>
    <form class="history-filters" @submit.prevent="load(true)">
      <label class="ticket-filter-control">Search history<input v-model="search" type="search" placeholder="Ticket number, issue or customer" /></label>
      <label class="ticket-filter-control">Assignment outcome<select v-model="outcome" @change="load(true)"><option value="">All outcomes</option><option value="RESOLVED">Resolved</option><option value="CANCELLED">Cancelled</option><option value="REASSIGNED">Reassigned away</option><option value="UNASSIGNED">Unassigned</option><option value="PREVIOUS">Previous assignment</option></select></label>
      <button type="submit" class="button button-primary" :disabled="loading">Search</button><button type="button" class="ticket-clear-filters" @click="clear">Clear filters</button>
    </form>
    <p class="history-note">Older records may show ?Previous assignment? when an outcome was not recorded. Ticket status reflects its current state.</p>
    <p v-if="loading" class="dashboard-message" role="status">Loading ticket history...</p>
    <p v-else-if="error" class="form-message form-error" role="alert">{{ error }} <button type="button" @click="load()">Retry</button></p>
    <div v-else-if="!items.length" class="ticket-empty-state"><h3>No matching history</h3><p>Past assignments will appear here after they leave your active workload.</p></div>
    <template v-else>
      <div class="history-table-wrap"><table class="ticket-table history-table"><thead><tr><th scope="col">Ticket Number</th><th scope="col">Issue / Customer</th><th scope="col">Assigned on</th><th scope="col">Assignment outcome</th><th scope="col">Current ticket status</th><th scope="col">Action</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><span class="ticket-table-id">{{ item.ticket_number }}</span></td><td><strong>{{ item.problem_title }}</strong><small>{{ item.customer_name }}</small></td><td>{{ date(item.created_at) }}</td><td>{{ outcomes[item.end_reason] || 'Previous assignment' }}<small v-if="item.ended_at">{{ date(item.ended_at) }}</small></td><td><TicketStatusBadge :status="item.current_status" /></td><td><button class="dashboard-text-link" type="button" @click="selected = item">View history</button></td></tr></tbody></table></div>
      <div class="history-pagination"><span>{{ count }} assignment records ? Page {{ page }}</span><div><button type="button" class="button button-secondary" :disabled="page === 1 || loading" @click="page--; load()">Previous</button><button type="button" class="button button-secondary" :disabled="!hasNext || loading" @click="page++; load()">Next</button></div></div>
    </template>
    <DirectoryDetailsModal v-if="selected" title="Assignment History" @close="selected = null"><article class="history-details"><span class="ticket-table-id">{{ selected.ticket_number }}</span><h3>{{ selected.problem_title }}</h3><p class="history-description">{{ selected.problem_description }}</p><dl><div><dt>Customer</dt><dd>{{ selected.customer_name }}</dd></div><div><dt>Assigned on</dt><dd>{{ date(selected.created_at) }}</dd></div><div><dt>Your assignment outcome</dt><dd>{{ outcomes[selected.end_reason] || 'Previous assignment' }}</dd></div><div><dt>Assignment ended</dt><dd>{{ date(selected.ended_at) }}</dd></div><div><dt>Current ticket status</dt><dd><TicketStatusBadge :status="selected.current_status" /></dd></div></dl><p class="history-note">Historical access only. Ticket editing and status actions are not available here.</p></article></DirectoryDetailsModal>
  </section>
</template>
<style scoped>
.history-filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 16px; margin-top: 24px; padding: 20px; background: var(--surface); border: 1px solid var(--border); border-radius: 13px; }
.history-filters > label:first-child { flex: 1 1 280px; min-width: 0; }
.history-filters > label:nth-child(2) { flex: 0 1 220px; }
.history-note { color: var(--muted); font-size: 11px; line-height: 1.8; margin: 16px 0; }
.history-table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 13px; background: var(--surface); }
.history-table { min-width: 850px; }
.history-table td { font-size: 12px; }
.history-table small { display: block; margin-top: 6px; color: var(--muted); font-size: 10px; }
.history-pagination { display: flex; justify-content: space-between; flex-wrap: wrap; align-items: center; gap: 16px; margin-top: 18px; color: var(--muted); font-size: 12px; }
.history-pagination > div { display: flex; gap: 10px; }
.history-details { padding: 24px; }
.history-description { white-space: pre-wrap; overflow-wrap: anywhere; color: var(--muted); font-size: 13px; line-height: 1.8; }
.history-details dl { display: grid; gap: 18px; }
.history-details dt { color: var(--muted); font-size: 11px; }
.history-details dd { margin: 7px 0 0; color: var(--text-primary); font-size: 13px; }
@media (max-width: 600px) { .history-filters > label:nth-child(2) { flex-basis: 100%; } }
</style>
