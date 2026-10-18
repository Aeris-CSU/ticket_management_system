<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import ProfileModal from './ProfileModal.vue';

const authStore = useAuthStore();
const router = useRouter();
const showProfileModal = ref(false);

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<template>
  <header class="bg-slate-900 border-b border-slate-800 px-6 py-3">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-xl font-black tracking-wider text-emerald-400">SUPPORT_DESK</span>
        <span class="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-bold uppercase text-slate-400">
          {{ authStore.role }}
        </span>
      </div>

      <div class="flex items-center gap-4">
        <button
            @click="showProfileModal = true"
            class="flex items-center gap-2 hover:bg-slate-800 px-3 py-1.5 rounded-lg border border-transparent hover:border-slate-700 transition"
        >
          <div class="w-7 h-7 rounded-full bg-emerald-500 text-slate-950 font-bold flex items-center justify-center text-xs">
            {{ authStore.user?.username.charAt(0).toUpperCase() }}
          </div>
          <span class="text-sm font-medium text-slate-200">{{ authStore.user?.username }}</span>
        </button>

        <button
            @click="handleLogout"
            class="text-xs bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 px-3 py-1.5 rounded transition font-bold"
        >
          Logout
        </button>
      </div>
    </div>

    <ProfileModal :is-open="showProfileModal" @close="showProfileModal = false" />
  </header>
</template>