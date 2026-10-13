<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'

const menuOpen = ref(false)

const closeMenu = () => {
  menuOpen.value = false
}
</script>

<template>
  <header class="site-header">
    <div class="container nav-shell">
      <a class="brand" href="#home" aria-label="Tickarla home" @click="closeMenu">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M4.5 7.5h15v10a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-10Z" />
            <path d="M4.5 10h4a2 2 0 1 0 0-4h-4m15 4h-4a2 2 0 1 1 0-4h4M12 10v1m0 2v1m0 2v1" />
          </svg>
        </span>
        <span>Tickarla</span>
      </a>

      <button
        class="menu-toggle"
        type="button"
        :aria-expanded="menuOpen"
        aria-controls="primary-navigation"
        :aria-label="menuOpen ? 'Close navigation menu' : 'Open navigation menu'"
        @click="menuOpen = !menuOpen"
      >
        <svg v-if="!menuOpen" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" /></svg>
        <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
      </button>

      <nav id="primary-navigation" class="primary-nav" :class="{ 'is-open': menuOpen }" aria-label="Main navigation">
        <a href="#home" @click="closeMenu">Home</a>
        <a href="#features" @click="closeMenu">Features</a>
        <a href="#about" @click="closeMenu">About</a>
        <ThemeToggle />
        <RouterLink class="nav-login" to="/login" @click="closeMenu">Login</RouterLink>
      </nav>
    </div>
  </header>
</template>
