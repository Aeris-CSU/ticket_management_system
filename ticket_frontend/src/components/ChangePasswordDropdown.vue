<script setup lang="ts">
import ChangePasswordForm from './ChangePasswordForm.vue'
</script>
<template>
  <details class="change-password-dropdown">
    <summary>Change password <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></summary>
    <ChangePasswordForm />
  </details>
</template>
<style scoped>
.change-password-dropdown { max-width: 780px; margin-top: 0; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
summary { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; cursor: pointer; color: var(--text-primary); font-size: 14px; font-weight: 650; list-style: none; }
summary::-webkit-details-marker { display: none; }
summary:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; border-radius: 12px; }
summary svg { transition: transform 160ms ease; }
details[open] > summary svg { transform: rotate(180deg); }
:deep(form) { border: 0; margin: 0; padding: 0 24px 24px; box-shadow: none; }
@media (prefers-reduced-motion: reduce) { summary svg { transition: none; } }
</style>
