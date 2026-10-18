<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import api from '@/api/client';

const router = useRouter();
const authStore = useAuthStore();

const isRegistering = ref(false);
const loading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

// Login Form State
const credentials = reactive({
  username: '',
  password: '',
});

// Customer-Only Registration State
const registerForm = reactive({
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  address: '',
});

// Forgot Password State
const forgotModalOpen = ref(false);
const resetEmail = ref('');
const resetStatus = ref('');

const handleLogin = async () => {
  loading.value = true;
  errorMsg.value = '';

  try {
    const role = await authStore.login(credentials);
    if (role === 'ADMIN') router.push('/admin');
    else if (role === 'TECHNICIAN') router.push('/technician');
    else if (role === 'CUSTOMER') router.push('/customer');
  } catch (err: any) {
    errorMsg.value = err.response?.data?.message || 'Invalid username or password.';
  } finally {
    loading.value = false;
  }
};

const handleCustomerRegister = async () => {
  loading.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  try {
    await api.post('register-customers/', {
      username: registerForm.username,
      password: registerForm.password,
      first_name: registerForm.first_name,
      last_name: registerForm.last_name,
      email: registerForm.email,
      address: registerForm.address || 'Not specified',
    });

    successMsg.value = 'Account created successfully! Please sign in.';
    isRegistering.value = false;
    credentials.username = registerForm.username;
    credentials.password = '';
  } catch (err: any) {
    const data = err.response?.data;
    if (typeof data === 'object') {
      const firstError = Object.values(data).flat()[0];
      errorMsg.value = String(firstError || 'Registration failed.');
    } else {
      errorMsg.value = 'Failed to create customer account.';
    }
  } finally {
    loading.value = false;
  }
};

const handleForgotPassword = () => {
  if (!resetEmail.value) {
    resetStatus.value = 'Please provide an email address.';
    return;
  }
  resetStatus.value = `A password reset link has been dispatched to ${resetEmail.value}`;
  setTimeout(() => {
    forgotModalOpen.value = false;
    resetEmail.value = '';
    resetStatus.value = '';
  }, 2500);
};
</script>

<template>
  <div class="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 font-sans text-white">
    <div class="max-w-md w-full bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-xl">
      <div class="mb-6 text-center">
        <h1 class="text-2xl font-black text-emerald-400 tracking-wider uppercase">Helpdesk Portal</h1>
        <p class="text-xs text-slate-400 mt-1">
          {{ isRegistering ? 'Create your Customer account' : 'Sign in with your configured role credentials' }}
        </p>
      </div>

      <!-- Feedback Alerts -->
      <div v-if="errorMsg" class="mb-4 bg-rose-500/10 border border-rose-500/40 text-rose-400 text-xs p-3 rounded">
        {{ errorMsg }}
      </div>
      <div v-if="successMsg" class="mb-4 bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 text-xs p-3 rounded">
        {{ successMsg }}
      </div>

      <!-- Sign In Form -->
      <form v-if="!isRegistering" @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Username</label>
          <input
              v-model="credentials.username"
              type="text"
              required
              class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Password</label>
          <input
              v-model="credentials.password"
              type="password"
              required
              class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        <div class="flex justify-end">
          <button
              type="button"
              @click="forgotModalOpen = true"
              class="text-xs text-emerald-400 hover:underline"
          >
            Forgot Password?
          </button>
        </div>

        <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold rounded-lg text-sm transition"
        >
          {{ loading ? 'Authenticating...' : 'Sign In' }}
        </button>

        <div class="pt-4 text-center border-t border-slate-800 text-xs text-slate-400">
          New customer?
          <button type="button" @click="isRegistering = true; errorMsg = ''" class="text-emerald-400 hover:underline font-bold ml-1">
            Create an Account
          </button>
        </div>
      </form>

      <!-- Customer Registration Form -->
      <form v-else @submit.prevent="handleCustomerRegister" class="space-y-3">
        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Username</label>
          <input
              v-model="registerForm.username"
              type="text"
              required
              class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">First Name</label>
            <input
                v-model="registerForm.first_name"
                type="text"
                required
                class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
            />
          </div>
          <div>
            <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Last Name</label>
            <input
                v-model="registerForm.last_name"
                type="text"
                required
                class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Email</label>
          <input
              v-model="registerForm.email"
              type="email"
              required
              class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Password</label>
          <input
              v-model="registerForm.password"
              type="password"
              required
              class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400 mb-1">Address</label>
          <input
              v-model="registerForm.address"
              type="text"
              placeholder="e.g. 123 Main St"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        <button
            type="submit"
            :disabled="loading"
            class="w-full mt-2 py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold rounded-lg text-sm transition"
        >
          {{ loading ? 'Creating Account...' : 'Complete Registration' }}
        </button>

        <div class="pt-4 text-center border-t border-slate-800 text-xs text-slate-400">
          Already have an account?
          <button type="button" @click="isRegistering = false; errorMsg = ''" class="text-emerald-400 hover:underline font-bold ml-1">
            Back to Sign In
          </button>
        </div>
      </form>
    </div>

    <!-- Forgot Password Modal -->
    <div v-if="forgotModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-xl max-w-sm w-full p-6 text-white shadow-2xl">
        <h3 class="text-base font-bold text-emerald-400 mb-2">Reset Password</h3>
        <p class="text-xs text-slate-400 mb-4">Enter the email associated with your account.</p>

        <div v-if="resetStatus" class="mb-3 text-xs bg-emerald-500/10 border border-emerald-500 text-emerald-400 p-2 rounded">
          {{ resetStatus }}
        </div>

        <input
            v-model="resetEmail"
            type="email"
            placeholder="your.email@domain.com"
            class="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none mb-4"
        />

        <div class="flex justify-end gap-2">
          <button @click="forgotModalOpen = false" class="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 rounded text-slate-300">
            Cancel
          </button>
          <button @click="handleForgotPassword" class="px-3 py-1.5 text-xs bg-emerald-500 hover:bg-emerald-600 text-black font-bold rounded">
            Send Reset Link
          </button>
        </div>
      </div>
    </div>
  </div>
</template>