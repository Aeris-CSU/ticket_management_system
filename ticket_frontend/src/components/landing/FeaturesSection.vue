<script setup lang="ts">
const features = [
  {
    number: '1',
    title: 'Easy Ticket Submission',
    description: 'Create and submit support tickets quickly with a simple and organized process.',
    icon: 'ticket',
  },
  {
    number: '2',
    title: 'Ticket Progress Tracking',
    description: 'Monitor the progress of your support requests from submission to resolution.',
    icon: 'progress',
  },
  {
    number: '3',
    title: 'Organized Ticket Assignment',
    description: 'Keep support requests organized by assigning tickets to the right technicians.',
    icon: 'team',
  },
] as const
</script>

<template>
  <section id="features" class="features-section section-pad">
    <div class="container">
      <div class="section-heading">
        <span class="eyebrow">BUILT FOR EVERYDAY SUPPORT</span>
        <h2>Simple Tools for <span>Better Support</span></h2>
        <p>Everything you need to manage technical concerns and support requests efficiently.</p>
      </div>

      <div class="feature-grid">
        <article v-for="feature in features" :key="feature.number" class="feature-card">
          <div class="feature-card-top"><span class="feature-icon" aria-hidden="true">
            <svg v-if="feature.icon === 'ticket'" viewBox="0 0 24 24" fill="none"><path d="M4 7.5h16v3a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4v-3Z"/><path d="M12 8v1.5m0 2v1.5m0 2v1"/></svg>
            <svg v-else-if="feature.icon === 'progress'" viewBox="0 0 24 24" fill="none"><path d="M8 6h12M8 12h12M8 18h12M3.5 6h.01M3.5 12h.01M3.5 18h.01"/><path d="m2.8 11.7.7.7 1.3-1.5m-2 6.9.7.7 1.3-1.5"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="none"><path d="M16 20v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 18.5V20m6-9a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm9-3a3.5 3.5 0 0 1 0 6.8m1 8v-1.3a3.5 3.5 0 0 0-2.7-3.4"/></svg>
          </span><span class="feature-number">{{ feature.number }}</span></div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
          <span class="feature-rule" aria-hidden="true"></span>
        </article>
      </div>
    </div>
  </section>
</template>
