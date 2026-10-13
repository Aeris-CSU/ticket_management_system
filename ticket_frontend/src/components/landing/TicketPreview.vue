<script setup lang="ts">
const stats = [
  { label: 'Total tickets', value: '24', tone: 'blue', icon: '▤' },
  { label: 'Open', value: '8', tone: 'amber', icon: '◷' },
  { label: 'In progress', value: '10', tone: 'violet', icon: '↗' },
  { label: 'Resolved', value: '6', tone: 'green', icon: '✓' },
]

const recentTickets = [
  { id: 'TK-1024', title: 'Unable to connect to Wi-Fi', team: 'Network support', status: 'Open', tone: 'amber' },
  { id: 'TK-1023', title: 'Printer not responding', team: 'Hardware support', status: 'In progress', tone: 'blue' },
  { id: 'TK-1022', title: 'Reset account password', team: 'Account support', status: 'Resolved', tone: 'green' },
]
</script>

<template>
  <div class="preview-wrap" aria-label="Illustrative ticket dashboard preview">
    <div class="preview-float float-top" aria-hidden="true">
      <span class="float-icon"><svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></svg></span>
      <span><strong>Ticket resolved</strong><small>Just a moment ago</small></span>
    </div>

    <section class="dashboard-preview" aria-label="Sample support dashboard">
      <div class="preview-topbar">
        <div class="preview-brand"><span class="preview-brand-mark">T</span><span>Tickarla</span></div>
        <div class="preview-profile"><span class="profile-dot">JD</span><span>Jordan Davis</span><span class="chevron">⌄</span></div>
      </div>

      <div class="preview-body">
        <aside class="preview-sidebar" aria-hidden="true">
          <span class="sidebar-line active"><i>▦</i> Overview</span>
          <span class="sidebar-line"><i>▤</i> My tickets</span>
          <span class="sidebar-line"><i>◷</i> Activity</span>
          <span class="sidebar-line"><i>⚙</i> Settings</span>
        </aside>

        <div class="preview-content">
          <div class="preview-heading">
            <div><p class="preview-eyebrow">MONDAY, OCTOBER 12, 2026</p><h2>Your support overview</h2></div>
            <button type="button" class="preview-add" aria-label="Illustrative new ticket button">＋ New ticket</button>
          </div>

          <div class="stat-grid">
            <article v-for="stat in stats" :key="stat.label" class="stat-card">
              <span class="stat-icon" :class="`tone-${stat.tone}`">{{ stat.icon }}</span>
              <span class="stat-value">{{ stat.value }}</span>
              <span class="stat-label">{{ stat.label }}</span>
            </article>
          </div>

          <div class="recent-panel">
            <div class="recent-heading"><div><h3>Recent tickets</h3><p>A quick look at your latest requests</p></div><a href="#features">View all <span aria-hidden="true">→</span></a></div>
            <div class="ticket-list">
              <article v-for="ticket in recentTickets" :key="ticket.id" class="ticket-row">
                <span class="ticket-file" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M7 3.75h7l4 4v12.5H7a2 2 0 0 1-2-2v-12.5a2 2 0 0 1 2-2Z"/><path d="M14 3.75v4h4M9 12h6m-6 3.5h6"/></svg></span>
                <span class="ticket-copy"><strong>{{ ticket.title }}</strong><small>{{ ticket.id }} <span>·</span> {{ ticket.team }}</small></span>
                <span class="ticket-status" :class="`status-${ticket.tone}`"><i></i>{{ ticket.status }}</span>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="preview-float float-bottom" aria-hidden="true">
      <span class="avatar-stack"><i>AM</i><i>LC</i><i>+2</i></span>
      <span><strong>Support team</strong><small>Ready to help</small></span>
      <span class="online-indicator"></span>
    </div>
  </div>
</template>
