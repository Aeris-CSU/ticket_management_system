<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="cta-section">
    <div class="container cta-card">
      <span class="cta-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none"><path d="M4.5 7.5h15v10a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-10Z"/><path d="M4.5 10h4a2 2 0 1 0 0-4h-4m15 4h-4a2 2 0 1 1 0-4h4M12 10v1m0 2v1"/></svg>
      </span>
      <h2>Ready to Get Started?</h2>
      <p>Start managing your support requests with Tickarla.</p>
      <RouterLink class="button button-primary" to="/login">Get started <span aria-hidden="true">→</span></RouterLink>
    </div>
  </section>
</template>
