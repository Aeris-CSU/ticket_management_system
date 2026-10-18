<script setup lang="ts">
const steps = [
  { number: '01', label: 'Report the issue', role: 'CUSTOMER', description: 'Describe your concern and share the details your support team needs.' },
  { number: '02', label: 'Connect with support', role: 'ADMIN & TECHNICIAN', description: 'An administrator assigns your ticket so a technician can begin working on it.' },
  { number: '03', label: 'Follow the progress', role: 'ONE SHARED RECORD', description: 'Check your ticket details and status as your request moves toward resolution.' },
]
</script>
<template>
  <section class="support-workflow section-pad" aria-labelledby="workflow-title">
    <div class="container">
      <div class="workflow-heading"><div><span class="eyebrow">HOW IT WORKS</span><h2 id="workflow-title">A clear path from<br />issue to resolution.</h2></div><p>Less guesswork. More clarity.<br />Everyone knows the next step.</p></div>
      <div class="workflow-steps">
        <article v-for="step in steps" :key="step.number" class="workflow-step">
          <div class="workflow-step-top"><span class="workflow-number">{{ step.number }}</span><span class="workflow-role">{{ step.role }}</span></div>
          <h3>{{ step.label }}</h3><p>{{ step.description }}</p>
        </article>
      </div>
    </div>
  </section>
</template>
