<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import Navbar from '@/components/Navbar.vue';
import { useAuthStore } from '@/stores/auth';
import api from '@/api/client';

const authStore = useAuthStore();

interface Ticket {
  id: number;
  problem_title: string;
  problem_description: string;
  status: string;
  customer: number;
}

const myTickets = ref<Ticket[]>([]);
const loading = ref(true);
const modalOpen = ref(false);
const isEditing = ref(false);
const activeTicketId = ref<number | null>(null);

const form = reactive({
  problem_title: '',
  problem_description: '',
  status: 'OPEN',
});

const fetchCustomerTickets = async () => {
  loading.value = true;
  try {
    // 1. Resolve Customer ID if not already cached in store
    if (!authStore.user?.customer_profile_id) {
      const custRes = await api.get('customers/');
      const current = custRes.data.find((c: any) => c.email === authStore.user?.email);
      if (current) authStore.user!.customer_profile_id = current.id;
    }

    // 2. Fetch all tickets and filter customer's own tickets
    const res = await api.get('tickets/');
    myTickets.value = res.data.filter((t: Ticket) => t.customer === authStore.user?.customer_profile_id);
  } catch (err) {
    console.error('Failed to load tickets', err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchCustomerTickets);

const openCreateModal = () => {
  isEditing.value = false;
  activeTicketId.value = null;
  form.problem_title = '';
  form.problem_description = '';
  form.status = 'OPEN';
  modalOpen.value = true;
};

const openEditModal = (ticket: Ticket) => {
  isEditing.value = true;
  activeTicketId.value = ticket.id;
  form.problem_title = ticket.problem_title;
  form.problem_description = ticket.problem_description;
  form.status = ticket.status;
  modalOpen.value = true;
};

const saveTicket = async () => {
  try {
    if (isEditing.value && activeTicketId.value) {
      // Customer PUT on tickets/pk
      await api.put(`tickets/${activeTicketId.value}`, {
        problem_title: form.problem_title,
        problem_description: form.problem_description,
      });
    } else {
      // Customer POST on tickets/create/
      await api.post('tickets/create/', {
        problem_title: form.problem_title,
        problem_description: form.problem_description,
        status: 'PENDING',
        customer: authStore.user?.customer_profile_id,
      });
    }
    modalOpen.value = false;
    await fetchCustomerTickets();
  } catch (err: any) {
    alert(err.response?.data?.message || 'Failed to submit ticket');
  }
};

const deleteTicket = async (ticketId: number) => {
  if (!confirm('Are you sure you want to delete this ticket?')) return;
  try {
    // Backend CustomerPermission returns 403: "Customers are not allowed to delete tickets."
    await api.delete(`tickets/${ticketId}`);
    await fetchCustomerTickets();
  } catch (err: any) {
    alert(err.response?.data?.message || 'Access Denied: Customers cannot delete tickets per backend rules.');
  }
};
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <Navbar />

    <main class="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-xl font-black text-white">My Support Tickets</h2>
          <p class="text-xs text-slate-400 mt-1">Submit inquiries and track assignment status</p>
        </div>
        <button
            @click="openCreateModal"
            class="bg-emerald-500 hover:bg-emerald-600 text-black font-bold px-4 py-2 rounded-lg text-xs transition"
        >
          + New Ticket
        </button>
      </div>

      <!-- Ticket Cards -->
      <div v-if="myTickets.length === 0" class="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-sm">
        No support tickets filed yet. Click "+ New Ticket" to create one.
      </div>

      <div class="grid grid-cols-1 gap-4">
        <div
            v-for="t in myTickets"
            :key="t.id"
            class="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition"
        >
          <div class="flex justify-between items-start gap-4">
            <div>
              <span class="text-xs font-mono text-emerald-400">#{{ t.id }}</span>
              <h3 class="text-base font-bold text-white mt-0.5">{{ t.problem_title }}</h3>
              <p class="text-xs text-slate-400 mt-2 leading-relaxed">{{ t.problem_description }}</p>
            </div>
            <span class="text-xs font-bold px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300">
              {{ t.status }}
            </span>
          </div>

          <div class="flex justify-end gap-2 mt-4 pt-3 border-t border-slate-800/80">
            <button
                @click="openEditModal(t)"
                class="text-xs text-slate-300 hover:text-white bg-slate-800 px-3 py-1 rounded"
            >
              Edit
            </button>
            <button
                @click="deleteTicket(t.id)"
                class="text-xs text-rose-400 hover:text-rose-300 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Create/Edit Modal -->
    <div v-if="modalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 text-white shadow-2xl">
        <h3 class="text-base font-bold text-emerald-400 mb-4">
          {{ isEditing ? 'Edit Ticket' : 'Create New Ticket' }}
        </h3>

        <form @submit.prevent="saveTicket" class="space-y-4">
          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Problem Title</label>
            <input
                v-model="form.problem_title"
                type="text"
                required
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Problem Description</label>
            <textarea
                v-model="form.problem_description"
                rows="4"
                required
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            ></textarea>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button
                type="button"
                @click="modalOpen = false"
                class="px-4 py-2 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              Cancel
            </button>
            <button
                type="submit"
                class="px-4 py-2 text-xs rounded bg-emerald-500 hover:bg-emerald-600 text-black font-bold"
            >
              {{ isEditing ? 'Update Ticket' : 'Submit Ticket' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>