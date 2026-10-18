<script setup lang="ts">
defineProps<{ registration?: boolean }>()
</script>
<template>
  <aside class="auth-brand-panel" aria-labelledby="auth-panel-heading">
    <span class="auth-panel-kicker">THE TICKARLA WORKSPACE</span>
    <h2 id="auth-panel-heading">{{ registration ? 'Good support starts with a simple request.' : 'Every request deserves a clear next step.' }}</h2>
    <p>{{ registration ? 'Create your customer account and bring your support requests into one organized place.' : 'Your tickets, your updates, and your support team. Together in one place.' }}</p>
    <div class="auth-ticket-art" aria-hidden="true">
      <div class="auth-art-bar"><span>T</span><b>SUPPORT REQUEST</b><i></i></div>
      <div class="auth-art-title">A little clarity goes a long way.</div>
      <div class="auth-art-lines"><i></i><i></i></div>
      <div class="auth-art-progress"><span class="done"></span><i></i><span class="current"></span><i></i><span></span></div>
      <div class="auth-art-labels"><span>Submitted</span><span>In progress</span><span>Resolved</span></div>
    </div>
    <div class="auth-panel-footer"><span class="auth-panel-dot"></span> Support Made Simple.</div>
  </aside>
</template>
