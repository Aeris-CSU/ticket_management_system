<script setup lang="ts">
const workspaces = [
  { role: 'For customers', title: 'Your request. A clear next step.', description: 'Report a concern, keep your details in one place, and follow your ticket status.', icon: 'customer', tag: 'MY SUPPORT', rows: ['Describe the issue', 'Submit your request', 'Follow its progress'] },
  { role: 'For technicians', title: 'Know what needs your attention.', description: 'See your assigned tickets, review the problem, and update work as it progresses.', icon: 'technician', tag: 'ASSIGNED WORK', rows: ['Review assigned tickets', 'Start working', 'Mark as resolved'] },
  { role: 'For administrators', title: 'Bring order to every request.', description: 'Review incoming concerns, assign technicians, and manage your support workspace.', icon: 'admin', tag: 'SUPPORT OPERATIONS', rows: ['Review the ticket queue', 'Assign a technician', 'Manage your workspace'] },
]
</script>
<template>
  <section class="workspace-section section-pad" aria-labelledby="workspace-heading">
    <div class="container">
      <div class="workspace-heading"><span class="eyebrow">THREE ROLES. ONE CONNECTED WORKFLOW.</span><h2 id="workspace-heading">Built around the people<br />behind every ticket.</h2><p>A dedicated workspace for everyone involved in getting things done.</p></div>
      <div class="workspace-grid">
        <article v-for="(workspace, index) in workspaces" :key="workspace.icon" class="workspace-card" :class="`workspace-${workspace.icon}`">
          <div class="workspace-art" aria-hidden="true">
            <div class="workspace-mini-header"><span class="workspace-mini-logo">T</span><span>{{ workspace.tag }}</span><i></i></div>
            <div class="workspace-mini-body"><div class="workspace-mini-avatar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="8" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/></svg></div><div class="workspace-mini-lines"><i></i><i></i></div></div>
            <div v-for="(row, rowIndex) in workspace.rows" :key="row" class="workspace-mini-row"><span>{{ String(rowIndex + 1).padStart(2, '0') }}</span>{{ row }}<b>{{ rowIndex === index ? '+' : '' }}</b></div>
          </div>
          <div class="workspace-card-copy"><span>{{ workspace.role }}</span><h3>{{ workspace.title }}</h3><p>{{ workspace.description }}</p></div>
        </article>
      </div>
    </div>
  </section>
</template>
