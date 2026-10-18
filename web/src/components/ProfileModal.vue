<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useAuthStore } from '@/stores/auth';
import api from '@/api/client';

const props = defineProps<{ isOpen: boolean }>();
const emit = defineEmits(['close']);
const authStore = useAuthStore();

const form = reactive({
  first_name: authStore.user?.first_name || '',
  last_name: authStore.user?.last_name || '',
  email: authStore.user?.email || '',
  password: '',
});

const loading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

const updateProfile = async () => {
  loading.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  try {
    const payload: any = {
      user: {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
      }
    };
    if (form.password) {
      payload.user.password = form.password;
    }

    if (authStore.user?.role === 'CUSTOMER' && authStore.user.customer_profile_id) {
      await api.put(`customers/update/${authStore.user.customer_profile_id}/`, payload);
    } else if (authStore.user?.role === 'TECHNICIAN' && authStore.user.technician_profile_id) {
      await api.put(`technicians/update/${authStore.user.technician_profile_id}/`, payload);
    }

    authStore.updateUserData({
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email,
    });

    successMsg.value = 'Profile updated successfully!';
    setTimeout(() => emit('close'), 1000);
  } catch (err: any) {
    errorMsg.value = 'Failed to update profile details.';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
    <div class="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 text-white shadow-2xl">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-bold text-emerald-400">Edit Profile</h3>
        <button @click="$emit('close')" class="text-slate-400 hover:text-white">✕</button>
      </div>

      <div v-if="errorMsg" class="mb-3 text-sm bg-rose-500/10 border border-rose-500 text-rose-400 p-2 rounded">
        {{ errorMsg }}
      </div>
      <div v-if="successMsg" class="mb-3 text-sm bg-emerald-500/10 border border-emerald-500 text-emerald-400 p-2 rounded">
        {{ successMsg }}
      </div>

      <form @submit.prevent="updateProfile" class="space-y-4">
        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">First Name</label>
          <input v-model="form.first_name" type="text" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Last Name</label>
          <input v-model="form.last_name" type="text" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Email</label>
          <input v-model="form.email" type="email" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>
        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">New Password (leave blank to keep)</label>
          <input v-model="form.password" type="password" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none" />
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <button type="button" @click="$emit('close')" class="px-4 py-2 text-sm rounded bg-slate-800 hover:bg-slate-700 text-slate-300">
            Cancel
          </button>
          <button type="submit" :disabled="loading" class="px-4 py-2 text-sm rounded bg-emerald-500 hover:bg-emerald-600 text-black font-semibold">
            {{ loading ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>