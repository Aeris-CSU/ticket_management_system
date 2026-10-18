<script setup lang="ts">
import NotificationBell from './NotificationBell.vue'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'

const emit = defineEmits<{ openMenu: [] }>()
const props = defineProps<{ menuOpen: boolean; desktopCollapsed?: boolean }>()
const isDesktop = ref(window.innerWidth > 700)
const menuExpanded = computed(() => isDesktop.value ? !props.desktopCollapsed : props.menuOpen)
function updateViewport() { isDesktop.value = window.innerWidth > 700 }
onMounted(() => window.addEventListener('resize', updateViewport))
onUnmounted(() => window.removeEventListener('resize', updateViewport))
const route = useRoute()
const title = computed(() => String(route.meta.title || 'Dashboard'))

</script>

<template>
  <header class="dashboard-header">
    <button
      class="dashboard-menu-button"
      type="button"
      :aria-label="menuExpanded ? 'Hide navigation menu' : 'Show navigation menu'"
      aria-controls="dashboard-sidebar"
      :aria-expanded="menuExpanded"
      @click="emit('openMenu')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
    </button>
    <h1>{{ title }}</h1>
    <div class="dashboard-account">
      <NotificationBell />
      <ThemeToggle />
    </div>
  </header>
</template>
