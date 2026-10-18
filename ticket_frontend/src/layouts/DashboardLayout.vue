<script setup lang="ts">
import { ref } from 'vue'
import { RouterView } from 'vue-router'
import DashboardHeader from '@/components/dashboard/DashboardHeader.vue'
import DashboardSidebar from '@/components/dashboard/DashboardSidebar.vue'

const sidebarOpen = ref(false)
const desktopCollapsed = ref(false)

function toggleMenu() {
  if (window.innerWidth > 700) desktopCollapsed.value = !desktopCollapsed.value
  else sidebarOpen.value = !sidebarOpen.value
}
</script>

<template>
  <div class="dashboard-shell" :class="{ 'sidebar-collapsed': desktopCollapsed }" @keydown.esc="sidebarOpen = false">
    <DashboardSidebar :open="sidebarOpen" @close="sidebarOpen = false" />
    <button
      v-if="sidebarOpen"
      class="dashboard-overlay"
      type="button"
      aria-label="Close navigation menu"
      @click="sidebarOpen = false"
    />
    <div class="dashboard-main">
      <DashboardHeader :menu-open="sidebarOpen" :desktop-collapsed="desktopCollapsed" @open-menu="toggleMenu" />
      <main class="dashboard-content" id="dashboard-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
