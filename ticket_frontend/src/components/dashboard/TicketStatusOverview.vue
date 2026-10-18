<script setup lang="ts">
import { computed } from 'vue'
import type { Ticket } from '@/types/ticket'
const props = defineProps<{ tickets: Ticket[] }>()
const groups = computed(() => [
  { label: 'Open', status: 'OPEN', color: '#d3a349' },
  { label: 'Assigned', status: 'ASSIGNED', color: '#5185dc' },
  { label: 'Ongoing', status: 'ONGOING', color: '#9a79d4' },
  { label: 'Resolved', status: 'RESOLVED', color: '#3e9b88' },
  { label: 'Cancelled', status: 'CANCELLED', color: '#91a0b7' },
].map(group => ({ ...group, count: props.tickets.filter(ticket => ticket.status === group.status).length })))
const chart = computed(() => {
  if (!props.tickets.length) return 'var(--border)'
  let start = 0
  return `conic-gradient(${groups.value.map(group => {
    const end = start + group.count / props.tickets.length * 100
    const segment = `${group.color} ${start}% ${end}%`
    start = end
    return segment
  }).join(',')})`
})
</script>
<template>
  <section class="status-overview" aria-labelledby="status-overview-title">
    <div class="status-panel-heading"><span>WORKLOAD SNAPSHOT</span><h3 id="status-overview-title">Every request, at a glance.</h3><p>Current status of the tickets in your workspace.</p></div>
    <div class="status-panel-body">
      <div class="status-chart" :style="{ background: chart }" aria-hidden="true"><div><b>{{ tickets.length }}</b><span>Total tickets</span></div></div>
      <ul class="status-legend" aria-label="Ticket counts by status"><li v-for="group in groups" :key="group.status"><i :style="{ background: group.color }" aria-hidden="true"></i><span>{{ group.label }}</span><b>{{ group.count }}</b></li></ul>
    </div>
    <p v-if="!tickets.length" class="status-empty">Your overview will fill in as tickets arrive.</p>
  </section>
</template>
<style scoped>
.status-overview { min-width: 0; padding: 26px 28px; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); box-shadow: 0 5px 22px rgb(20 44 80 / 3%); }
.status-panel-heading > span { font-size: 9px; font-weight: 750; letter-spacing: .14em; color: var(--muted); }
.status-panel-heading h3 { margin: 10px 0 7px; font-size: 20px; letter-spacing: -.035em; color: var(--text-primary); }
.status-panel-heading p, .status-empty { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.7; }
.status-panel-body { display: flex; align-items: center; gap: 32px; margin-top: 26px; }
.status-chart { display: grid; place-items: center; width: 150px; height: 150px; flex-shrink: 0; border-radius: 50%; }
.status-chart > div { display: flex; align-items: center; justify-content: center; flex-direction: column; width: 119px; height: 119px; border-radius: 50%; background: var(--surface); }
.status-chart b { font-size: 32px; letter-spacing: -.04em; color: var(--text-primary); }
.status-chart span { margin-top: 5px; font-size: 10px; color: var(--muted); }
.status-legend { display: grid; gap: 13px; flex: 1; margin: 0; padding: 0; list-style: none; }
.status-legend li { display: flex; align-items: center; gap: 9px; color: var(--muted); font-size: 12px; }
.status-legend i { width: 7px; height: 7px; border-radius: 50%; }
.status-legend b { margin-left: auto; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.status-empty { margin-top: 18px; }
@media (max-width: 420px) { .status-overview { padding: 22px; } .status-panel-body { gap: 20px; } .status-chart { width: 120px; height: 120px; } .status-chart > div { width: 94px; height: 94px; } }
</style>
