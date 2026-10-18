<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue';
import Navbar from '@/components/Navbar.vue';
import api from '@/api/client';

interface Ticket {
  id: number;
  problem_title: string;
  problem_description: string;
  status: string;
  customer: number;
}

interface Technician {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  specialization: string;
  availability_status: string;
}

interface Customer {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  address: string;
}

interface Assignment {
  id: number;
  tickets: number;
  technicians: number;
}

// Active Tab ('tickets' | 'technicians' | 'customers')
const activeTab = ref<'tickets' | 'technicians' | 'customers'>('tickets');

const tickets = ref<Ticket[]>([]);
const technicians = ref<Technician[]>([]);
const customers = ref<Customer[]>([]);
const assignments = ref<Assignment[]>([]);
const loading = ref(true);

const selectedTechnicianForTicket = ref<{ [ticketId: number]: number }>({});

// --- Pagination States for each table view ---
const itemsPerPage = 10;
const pages = reactive({
  tickets: 1,
  technicians: 1,
  customers: 1,
});

// Staff Creation Modal
const staffModalOpen = ref(false);
const staffLoading = ref(false);
const staffError = ref('');
const staffForm = reactive({
  role: 'TECHNICIAN' as 'TECHNICIAN' | 'ADMIN',
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  specialization: '',
  availability_status: 'AVAILABLE',
});

const fetchData = async () => {
  loading.value = true;
  try {
    const [ticketsRes, techsRes, custsRes, assignsRes] = await Promise.all([
      api.get('tickets/'),
      api.get('technicians/'),
      api.get('customers/'),
      api.get('assignments/'),
    ]);
    tickets.value = ticketsRes.data;
    technicians.value = techsRes.data;
    customers.value = custsRes.data;
    assignments.value = assignsRes.data;
  } catch (err) {
    console.error('Failed to load dashboard data', err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);

// Stats Calculation
const assignedTicketIds = computed(() => new Set(assignments.value.map(a => a.tickets)));

const unassignedCount = computed(() =>
    tickets.value.filter(t => !assignedTicketIds.value.has(t.id)).length
);

const availableTechCount = computed(() =>
    technicians.value.filter(t => t.availability_status?.toUpperCase() === 'AVAILABLE').length
);

const busyTechCount = computed(() =>
    technicians.value.filter(t => t.availability_status?.toUpperCase() === 'BUSY').length
);

const availableTechnicians = computed(() =>
    technicians.value.filter(t => t.availability_status?.toUpperCase() === 'AVAILABLE')
);

// --- Active Dataset & Pagination Helpers ---
const currentDataset = computed(() => {
  if (activeTab.value === 'tickets') return tickets.value;
  if (activeTab.value === 'technicians') return technicians.value;
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

const switchTab = (tab: 'tickets' | 'technicians' | 'customers') => {
  activeTab.value = tab;
};

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
  }
};

const getAssignedTechName = (ticketId: number) => {
  const match = assignments.value.find(a => a.tickets === ticketId);
  if (!match) return 'Unassigned';
  const tech = technicians.value.find(t => t.id === match.technicians);
  return tech ? `${tech.first_name} ${tech.last_name}` : `Assigned (Tech #${match.technicians})`;
};

const assignTechnician = async (ticketId: number) => {
  const techId = selectedTechnicianForTicket.value[ticketId];
  if (!techId) return;

  try {
    await api.post('assignments/create/', {
      tickets: ticketId,
      technicians: techId,
    });
    await fetchData();
  } catch (err) {
    alert('Failed to assign technician');
  }
};

const createStaff = async () => {
  staffLoading.value = true;
  staffError.value = '';

  try {
    if (staffForm.role === 'TECHNICIAN') {
      await api.post('register-technicians/', {
        username: staffForm.username,
        password: staffForm.password,
        first_name: staffForm.first_name,
        last_name: staffForm.last_name,
        email: staffForm.email,
        specialization: staffForm.specialization || 'General Technical Support',
        availability_status: staffForm.availability_status,
      });
    } else {
      await api.post('register/', {
        username: staffForm.username,
        password: staffForm.password,
        first_name: staffForm.first_name,
        last_name: staffForm.last_name,
        email: staffForm.email,
      });
    }

    staffModalOpen.value = false;
    staffForm.username = '';
    staffForm.password = '';
    staffForm.first_name = '';
    staffForm.last_name = '';
    staffForm.email = '';
    staffForm.specialization = '';
    await fetchData();
  } catch (err: any) {
    const data = err.response?.data;
    staffError.value = typeof data === 'object' ? Object.values(data).flat()[0] as string : 'Failed to create staff account';
  } finally {
    staffLoading.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <Navbar />

    <main class="max-w-7xl mx-auto px-6 py-8 space-y-8">
      <!-- General Stats Cards -->
      <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <span class="text-xs uppercase text-slate-400 font-bold">Unassigned Tickets</span>
          <div class="text-3xl font-black text-rose-400 mt-2">{{ unassignedCount }}</div>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <span class="text-xs uppercase text-slate-400 font-bold">Available Technicians</span>
          <div class="text-3xl font-black text-emerald-400 mt-2">{{ availableTechCount }}</div>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <span class="text-xs uppercase text-slate-400 font-bold">Busy Technicians</span>
          <div class="text-3xl font-black text-amber-400 mt-2">{{ busyTechCount }}</div>
        </div>
      </section>

      <!-- Unified Table Container -->
      <section class="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <!-- Header with Tab Navigation & Action Button -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 border-b border-slate-800 pb-4">
          <!-- Switcher Tabs -->
          <div class="flex items-center gap-2 bg-slate-950 p-1.5 rounded-lg border border-slate-800">
            <button
                @click="switchTab('tickets')"
                :class="activeTab === 'tickets' ? 'bg-emerald-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'"
                class="px-4 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer"
            >
              Master Tickets ({{ tickets.length }})
            </button>
            <button
                @click="switchTab('technicians')"
                :class="activeTab === 'technicians' ? 'bg-emerald-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'"
                class="px-4 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer"
            >
              Technicians & Staff ({{ technicians.length }})
            </button>
            <button
                @click="switchTab('customers')"
                :class="activeTab === 'customers' ? 'bg-emerald-500 text-black font-bold shadow' : 'text-slate-400 hover:text-white'"
                class="px-4 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer"
            >
              Customers ({{ customers.length }})
            </button>
          </div>

          <!-- Actions & Counter -->
          <div class="flex items-center gap-4">
            <span class="text-xs text-slate-400">
              Showing <span class="text-white font-semibold">{{ startItemIndex }}</span>–<span class="text-white font-semibold">{{ endItemIndex }}</span> of <span class="text-emerald-400 font-semibold">{{ currentDataset.length }}</span>
            </span>

            <button
                v-if="activeTab === 'technicians'"
                @click="staffModalOpen = true; staffError = ''"
                class="bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-xs px-3 py-1.5 rounded-lg transition cursor-pointer"
            >
              + Add Staff
            </button>
          </div>
        </div>

        <!-- 1. Master Tickets Table -->
        <div v-if="activeTab === 'tickets'" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400">
            <tr>
              <th class="p-3">ID</th>
              <th class="p-3">Title</th>
              <th class="p-3">Status</th>
              <th class="p-3">Assigned To</th>
              <th class="p-3">Assign Action</th>
            </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
            <tr v-for="ticket in (paginatedItems as Ticket[])" :key="ticket.id" class="hover:bg-slate-800/40">
              <td class="p-3 font-mono text-slate-400">#{{ ticket.id }}</td>
              <td class="p-3 font-semibold text-white">{{ ticket.problem_title }}</td>
              <td class="p-3">
                  <span class="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-emerald-300">
                    {{ ticket.status }}
                  </span>
              </td>
              <td class="p-3 text-slate-300">{{ getAssignedTechName(ticket.id) }}</td>
              <td class="p-3">
                <div v-if="!assignedTicketIds.has(ticket.id)" class="flex gap-2">
                  <select
                      v-model="selectedTechnicianForTicket[ticket.id]"
                      class="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                  >
                    <option :value="undefined" disabled>Select available tech</option>
                    <option v-for="t in availableTechnicians" :key="t.id" :value="t.id">
                      {{ t.first_name }} {{ t.last_name }} ({{ t.specialization }})
                    </option>
                  </select>
                  <button
                      @click="assignTechnician(ticket.id)"
                      :disabled="!selectedTechnicianForTicket[ticket.id]"
                      class="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-black font-bold px-3 py-1 rounded text-xs transition cursor-pointer"
                  >
                    Assign
                  </button>
                </div>
                <span v-else class="text-xs text-slate-500">Already Assigned</span>
              </td>
            </tr>
            <tr v-if="tickets.length === 0">
              <td colspan="5" class="p-6 text-center text-xs text-slate-500">No tickets found.</td>
            </tr>
            </tbody>
          </table>
        </div>

        <!-- 2. Technicians & Staff Table -->
        <div v-else-if="activeTab === 'technicians'" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400">
            <tr>
              <th class="p-3">ID</th>
              <th class="p-3">Name</th>
              <th class="p-3">Email</th>
              <th class="p-3">Specialization</th>
              <th class="p-3">Availability</th>
            </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
            <tr v-for="tech in (paginatedItems as Technician[])" :key="tech.id" class="hover:bg-slate-800/40">
              <td class="p-3 font-mono text-slate-400">#{{ tech.id }}</td>
              <td class="p-3 font-semibold text-white">{{ tech.first_name }} {{ tech.last_name }}</td>
              <td class="p-3 text-slate-400">{{ tech.email }}</td>
              <td class="p-3 text-slate-300">{{ tech.specialization || 'General Support' }}</td>
              <td class="p-3">
                  <span
                      class="text-xs font-bold px-2 py-0.5 rounded"
                      :class="tech.availability_status?.toUpperCase() === 'AVAILABLE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'"
                  >
                    {{ tech.availability_status }}
                  </span>
              </td>
            </tr>
            <tr v-if="technicians.length === 0">
              <td colspan="5" class="p-6 text-center text-xs text-slate-500">No technicians registered.</td>
            </tr>
            </tbody>
          </table>
        </div>

        <!-- 3. Customers Table -->
        <div v-else-if="activeTab === 'customers'" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400">
            <tr>
              <th class="p-3">ID</th>
              <th class="p-3">Name</th>
              <th class="p-3">Email</th>
              <th class="p-3">Address</th>
            </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
            <tr v-for="cust in (paginatedItems as Customer[])" :key="cust.id" class="hover:bg-slate-800/40">
              <td class="p-3 font-mono text-slate-400">#{{ cust.id }}</td>
              <td class="p-3 font-semibold text-white">{{ cust.first_name }} {{ cust.last_name }}</td>
              <td class="p-3 text-slate-400">{{ cust.email }}</td>
              <td class="p-3 text-slate-300">📍 {{ cust.address }}</td>
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

    <!-- Admin Add Staff Modal -->
    <div v-if="staffModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 text-white shadow-2xl">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-base font-bold text-emerald-400">Create Staff Account</h3>
          <button @click="staffModalOpen = false" class="text-slate-400 hover:text-white">✕</button>
        </div>

        <div v-if="staffError" class="mb-3 text-xs bg-rose-500/10 border border-rose-500 text-rose-400 p-2 rounded">
          {{ staffError }}
        </div>

        <form @submit.prevent="createStaff" class="space-y-3">
          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Staff Role</label>
            <select
                v-model="staffForm.role"
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="TECHNICIAN">Technician</option>
              <option value="ADMIN">Administrator</option>
            </select>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Username</label>
            <input
                v-model="staffForm.username"
                type="text"
                required
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">First Name</label>
              <input
                  v-model="staffForm.first_name"
                  type="text"
                  required
                  class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Last Name</label>
              <input
                  v-model="staffForm.last_name"
                  type="text"
                  required
                  class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Email</label>
            <input
                v-model="staffForm.email"
                type="email"
                required
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Password</label>
            <input
                v-model="staffForm.password"
                type="password"
                required
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div v-if="staffForm.role === 'TECHNICIAN'">
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Specialization</label>
            <input
                v-model="staffForm.specialization"
                type="text"
                placeholder="e.g. Hardware, Network, Database"
                class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button
                type="button"
                @click="staffModalOpen = false"
                class="px-4 py-2 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              Cancel
            </button>
            <button
                type="submit"
                :disabled="staffLoading"
                class="px-4 py-2 text-xs rounded bg-emerald-500 hover:bg-emerald-600 text-black font-bold"
            >
              {{ staffLoading ? 'Creating...' : 'Create Account' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>