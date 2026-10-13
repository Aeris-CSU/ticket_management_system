<script setup lang="ts">
import { RouterLink } from 'vue-router'
import TicketPreview from './TicketPreview.vue'
</script>

<template>
  <section id="home" class="hero-section">
    <div class="container hero-grid">
      <div class="hero-copy">
        <div class="welcome-label"><span class="welcome-spark" aria-hidden="true">✦</span> Welcome to Tickarla</div>
        <h1>Support <span>Made Simple.</span></h1>
        <p class="hero-description">
          Submit support requests, track ticket progress, and stay connected with technicians—all in one simple platform.
        </p>
        <div class="hero-actions">
          <RouterLink class="button button-primary" to="/login">Get started <span aria-hidden="true">→</span></RouterLink>
          <a class="button button-secondary" href="#features">Explore features</a>
        </div>
        <div class="hero-note"><span class="note-check" aria-hidden="true">✓</span> A clearer way to get the help you need</div>
      </div>
      <div class="hero-visual">
        <TicketPreview />
      </div>
    </div>
  </section>
</template>
