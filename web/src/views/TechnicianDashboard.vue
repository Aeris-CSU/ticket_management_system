<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue';
import Navbar from '@/components/Navbar.vue';
import { useAuthStore } from '@/stores/auth';
import api from '@/api/client';

const authStore = useAuthStore();

interface Ticket {
  id: number;
  problem_title: string;
  problem_description: string;
  status: string;
  remarks?: string;
  customer?: number;
}

interface CustomerBasic {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

interface Assignment {
  id: number;
  tickets: number;
  technicians: number;
}

// Active Tab ('claimed' | 'unassigned' | 'customers')
const activeTab = ref<'claimed' | 'unassigned' | 'customers'>('claimed');

const tickets = ref<Ticket[]>([]);
const customers = ref<CustomerBasic[]>([]);
const assignments = ref<Assignment[]>([]);
const myStatus = ref('AVAILABLE');
const loading = ref(true);

const techId = computed(() => authStore.user?.technician_profile_id);

// --- Pagination State ---
const itemsPerPage = 10;
const pages = reactive({
  claimed: 1,
  unassigned: 1,
  customers: 1,
});

// --- Ticket Management Modal State ---
const isDetailModalOpen = ref(false);
const selectedTicket = ref<Ticket | null>(null);
const ticketUpdateLoading = ref(false);
const ticketUpdateForm = reactive({
  status: 'IN_PROGRESS' as 'IN_PROGRESS' | 'RESOLVED' | 'CANCELLED',
  remarks: '',
});

const fetchData = async () => {
  loading.value = true;
  try {
    const [ticketsRes, custsRes, assignsRes, techListRes] = await Promise.all([
      api.get('tickets/'),
      api.get('customers/'),
      api.get('assignments/'),
      api.get('technicians/'),
    ]);
    tickets.value = ticketsRes.data;
    customers.value = custsRes.data;
    assignments.value = assignsRes.data;

    // Resolve current technician profile and availability status
    const currentTech = techListRes.data.find((t: any) => t.email === authStore.user?.email);
    if (currentTech) {
      myStatus.value = currentTech.availability_status;
      authStore.user!.technician_profile_id = currentTech.id;
    }
  } catch (err) {
    console.error('Error loading technician dashboard', err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);

// Assignments and ticket filters
const assignedTicketIds = computed(() => new Set(assignments.value.map(a => a.tickets)));

const unassignedTickets = computed(() =>
    tickets.value.filter(t => !assignedTicketIds.value.has(t.id))
);

const myAssignedTickets = computed(() => {
  if (!techId.value) return [];
  const myTicketIds = new Set(
      assignments.value.filter(a => a.technicians === techId.value).map(a => a.tickets)
  );
  return tickets.value.filter(t => myTicketIds.has(t.id));
});

// --- Tab Datasets & Pagination ---
const currentDataset = computed(() => {
  if (activeTab.value === 'claimed') return myAssignedTickets.value;
  if (activeTab.value === 'unassigned') return unassignedTickets.value;
  return customers.value;
});

const currentPage = computed({
  get: () => pages[activeTab.value],
  set: (val: number) => { pages[activeTab.value] = val; }
});

const totalPages = computed(() =>
    Math.max(1, Math.ceil(currentDataset.value.length / itemsPerPage))
);

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  return currentDataset.value.slice(start, start + itemsPerPage);
});

const startItemIndex = computed(() => {
  if (currentDataset.value.length === 0) return 0;
  return (currentPage.value - 1) * itemsPerPage + 1;
});

const endItemIndex = computed(() => {
  return Math.min(currentPage.value * itemsPerPage, currentDataset.value.length);
});

const switchTab = (tab: 'claimed' | 'unassigned' | 'customers') => {
  activeTab.value = tab;
};

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
  }
};

const toggleStatus = async (statusChoice: 'AVAILABLE' | 'BUSY') => {
  if (!techId.value) return;
  try {
    await api.put(`technicians/update/${techId.value}/`, {
      availability_status: statusChoice
    });
    myStatus.value = statusChoice;
  } catch (err) {
    alert('Failed to update status.');
  }
};

const claimTicket = async (ticketId: number) => {
  if (!techId.value) {
    alert('Technician profile ID not located.');
    return;
  }
  try {
    await api.post('assignments/create/', {
      tickets: ticketId,
      technicians: techId.value,
    });
    await fetchData();
  } catch (err) {
    alert('Failed to claim ticket.');
  }
};

// Open Ticket Details Modal
const openTicketDetails = (ticket: Ticket) => {
  selectedTicket.value = ticket;
  // Fallback to IN_PROGRESS if the initial ticket status was PENDING or other
  const validStatus = (ticket.status === 'RESOLVED' || ticket.status === 'CANCELLED')
      ? ticket.status
      : 'IN_PROGRESS';
  ticketUpdateForm.status = validStatus;
  ticketUpdateForm.remarks = ticket.remarks || '';
  isDetailModalOpen.value = true;
};

// Update Ticket Status & Remarks
const updateTicketDetails = async () => {
  if (!selectedTicket.value) return;
  ticketUpdateLoading.value = true;

  try {
    await api.put(`tickets/${selectedTicket.value.id}/`, {
      status: ticketUpdateForm.status,
      remarks: ticketUpdateForm.remarks,
    });

    isDetailModalOpen.value = false;
    await fetchData();
  } catch (err: any) {
    alert('Failed to update ticket: ' + JSON.stringify(err.response?.data || err.message));
  } finally {
    ticketUpdateLoading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <Navbar />

    <main class="max-w-7xl mx-auto px-6 py-8 space-y-8">
      <!-- Status & Availability Banner -->
      <section class="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 class="text-xl font-black text-white">Technician Workspace</h2>
          <p class="text-xs text-slate-400 mt-1">Claim unassigned tickets, manage active tasks, and set your status</p>
        </div>

        <div class="flex items-center gap-3">
          <span class="text-xs text-slate-400 uppercase font-bold">My Status:</span>
          <button
              @click="toggleStatus('AVAILABLE')"
              :class="myStatus.toUpperCase() === 'AVAILABLE' ? 'bg-emerald-500 text-black font-bold' : 'bg-slate-800 text-slate-400 hover:text-white'"
              class="px-4 py-1.5 rounded-lg text-xs font-semibold border border-slate-700 transition cursor-pointer"
          >
            AVAILABLE
          </button>
          <button
              @click="toggleStatus('BUSY')"
              :class="myStatus.toUpperCase() === 'BUSY' ? 'bg-amber-500 text-black font-bold' : 'bg-slate-800 text-slate-400 hover:text-white'"
              class="px-4 py-1.5 rounded-lg text-xs font-semibold border border-slate-700 transition cursor-pointer"
          >
            BUSY
          </button>
        </div>
      </section>

      <!-- Unified Table Container -->
      <section class="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <!-- Tab Navigation & Counter -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 border-b border-slate-800 pb-4">
          <!-- Switcher Tabs -->
          <div class="flex items-center gap-2 bg-slate-950 p-1.5 rounded-lg border border-slate-800">
            <button
                @click="switchTab('claimed')"
                :class="activeTab === 'claimed' ? 'bg-emerald-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'"
                class="px-4 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer"
            >
              My Claimed Tickets ({{ myAssignedTickets.length }})
            </button>
            <button
                @click="switchTab('unassigned')"
                :class="activeTab === 'unassigned' ? 'bg-emerald-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'"
                class="px-4 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer"
            >
              Unassigned Queue ({{ unassignedTickets.length }})
            </button>
            <button
                @click="switchTab('customers')"
                :class="activeTab === 'customers' ? 'bg-emerald-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'"
                class="px-4 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer"
            >
              Customer Directory ({{ customers.length }})
            </button>
          </div>

          <!-- Counter Indicator -->
          <span class="text-xs text-slate-400">
            Showing <span class="text-white font-semibold">{{ startItemIndex }}</span>–<span class="text-white font-semibold">{{ endItemIndex }}</span> of <span class="text-emerald-400 font-semibold">{{ currentDataset.length }}</span>
          </span>
        </div>

        <!-- 1. My Claimed Tickets Table -->
        <div v-if="activeTab === 'claimed'" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400">
            <tr>
              <th class="p-3">ID</th>
              <th class="p-3">Problem Title</th>
              <th class="p-3">Description</th>
              <th class="p-3">Status</th>
              <th class="p-3">Remarks</th>
            </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
            <tr
                v-for="ticket in (paginatedItems as Ticket[])"
                :key="ticket.id"
                @click="openTicketDetails(ticket)"
                class="hover:bg-slate-800/60 cursor-pointer transition"
            >
              <td class="p-3 font-mono text-slate-400">#{{ ticket.id }}</td>
              <td class="p-3 font-semibold text-white">{{ ticket.problem_title }}</td>
              <td class="p-3 text-slate-300 max-w-xs truncate">{{ ticket.problem_description }}</td>
              <td class="p-3">
                  <span
                      class="text-xs px-2.5 py-1 rounded font-bold border"
                      :class="{
                      'bg-emerald-500/10 text-emerald-400 border-emerald-500/30': ticket.status === 'RESOLVED',
                      'bg-rose-500/10 text-rose-400 border-rose-500/30': ticket.status === 'CANCELLED',
                      'bg-blue-500/10 text-blue-400 border-blue-500/30': ticket.status === 'IN_PROGRESS',
                      'bg-slate-800 text-slate-400 border-slate-700': ticket.status !== 'RESOLVED' && ticket.status !== 'CANCELLED' && ticket.status !== 'IN_PROGRESS'
                    }"
                  >
                    {{ ticket.status }}
                  </span>
              </td>
              <td class="p-3 text-xs text-slate-400 max-w-xs truncate">
                {{ ticket.remarks || 'No remarks recorded' }}
              </td>
            </tr>
            <tr v-if="myAssignedTickets.length === 0">
              <td colspan="5" class="p-6 text-center text-xs text-slate-500">You have no claimed tickets.</td>
            </tr>
            </tbody>
          </table>
        </div>

        <!-- 2. Unassigned Queue Table -->
        <div v-else-if="activeTab === 'unassigned'" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400">
            <tr>
              <th class="p-3">ID</th>
              <th class="p-3">Problem Title</th>
              <th class="p-3">Description</th>
              <th class="p-3">Status</th>
              <th class="p-3">Action</th>
            </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
            <tr v-for="ticket in (paginatedItems as Ticket[])" :key="ticket.id" class="hover:bg-slate-800/40">
              <td class="p-3 font-mono text-slate-400">#{{ ticket.id }}</td>
              <td class="p-3 font-semibold text-white">{{ ticket.problem_title }}</td>
              <td class="p-3 text-slate-300 max-w-md truncate">{{ ticket.problem_description }}</td>
              <td class="p-3">
                  <span class="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
                    {{ ticket.status }}
                  </span>
              </td>
              <td class="p-3">
                <button
                    @click="claimTicket(ticket.id)"
                    class="bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-xs px-3 py-1.5 rounded transition cursor-pointer"
                >
                  Claim Ticket
                </button>
              </td>
            </tr>
            <tr v-if="unassignedTickets.length === 0">
              <td colspan="5" class="p-6 text-center text-xs text-slate-500">No unassigned tickets available in queue.</td>
            </tr>
            </tbody>
          </table>
        </div>

        <!-- 3. Customer Directory Table (first name, last name, email only) -->
        <div v-else-if="activeTab === 'customers'" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400">
            <tr>
              <th class="p-3">ID</th>
              <th class="p-3">First Name</th>
              <th class="p-3">Last Name</th>
              <th class="p-3">Email Address</th>
            </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
            <tr v-for="cust in (paginatedItems as CustomerBasic[])" :key="cust.id" class="hover:bg-slate-800/40">
              <td class="p-3 font-mono text-slate-400">#{{ cust.id }}</td>
              <td class="p-3 font-semibold text-white">{{ cust.first_name }}</td>
              <td class="p-3 font-semibold text-white">{{ cust.last_name }}</td>
              <td class="p-3 text-slate-300">{{ cust.email }}</td>
            </tr>
            <tr v-if="customers.length === 0">
              <td colspan="4" class="p-6 text-center text-xs text-slate-500">No customers registered.</td>
            </tr>
            </tbody>
          </table>
        </div>

        <!-- Shared Pagination Controls -->
        <div v-if="totalPages > 1" class="flex items-center justify-between border-t border-slate-800 px-2 py-3 mt-4">
          <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage === 1"
              class="px-3 py-1 text-xs font-semibold rounded bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800 cursor-pointer disabled:cursor-not-allowed transition"
          >
            &larr; Previous
          </button>

          <div class="flex items-center gap-1">
            <button
                v-for="page in totalPages"
                :key="page"
                @click="goToPage(page)"
                :class="currentPage === page ? 'bg-emerald-500 text-black font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'"
                class="w-7 h-7 text-xs rounded transition flex items-center justify-center cursor-pointer"
            >
              {{ page }}
            </button>
          </div>

          <button
              @click="goToPage(currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="px-3 py-1 text-xs font-semibold rounded bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800 cursor-pointer disabled:cursor-not-allowed transition"
          >
            Next &rarr;
          </button>
        </div>
      </section>
    </main>

    <!-- Ticket Management Modal (Restricted to IN_PROGRESS, RESOLVED, CANCELLED) -->
    <div v-if="isDetailModalOpen && selectedTicket" class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 text-white shadow-2xl">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-base font-bold text-emerald-400">Manage Ticket #{{ selectedTicket.id }}</h3>
          <button @click="isDetailModalOpen = false" class="text-slate-400 hover:text-white cursor-pointer">✕</button>
        </div>

        <div class="mb-4 space-y-1 bg-slate-950 p-3 rounded-lg border border-slate-800">
          <p class="text-xs font-bold text-white">{{ selectedTicket.problem_title }}</p>
          <p class="text-xs text-slate-400 leading-relaxed">{{ selectedTicket.problem_description }}</p>
        </div>

        <form @submit.prevent="updateTicketDetails" class="space-y-4">
          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Status</label>
            <select
                v-model="ticketUpdateForm.status"
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Technician Remarks / Notes</label>
            <textarea
                v-model="ticketUpdateForm.remarks"
                rows="3"
                placeholder="Add diagnostic notes or resolution steps..."
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            ></textarea>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button
                type="button"
                @click="isDetailModalOpen = false"
                class="px-4 py-2 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
            >
              Cancel
            </button>
            <button
                type="submit"
                :disabled="ticketUpdateLoading"
                class="px-4 py-2 text-xs rounded bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black font-bold cursor-pointer"
            >
              {{ ticketUpdateLoading ? 'Saving...' : 'Save Updates' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>