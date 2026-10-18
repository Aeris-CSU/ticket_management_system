import { defineStore } from 'pinia';
import api from '@/api/client';

export interface UserAccount {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    role: 'ADMIN' | 'TECHNICIAN' | 'CUSTOMER';
    customer_profile_id?: number;
    technician_profile_id?: number;
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: JSON.parse(localStorage.getItem('user_account') || 'null') as UserAccount | null,
        accessToken: localStorage.getItem('access_token') || '',
    }),
    getters: {
        isAuthenticated: (state) => !!state.accessToken,
        role: (state) => state.user?.role,
    },
    actions: {
        async login(credentials: { username: string; password: string }) {
            const response = await api.post('login/', credentials);
            const { tokens, account } = response.data;

            this.accessToken = tokens.access;
            this.user = account;

            localStorage.setItem('access_token', tokens.access);
            localStorage.setItem('refresh_token', tokens.refresh);
            localStorage.setItem('user_account', JSON.stringify(account));

            if (account.role === 'CUSTOMER') {
                try {
                    const res = await api.get('customers/');
                    const profile = res.data.find((c: any) => c.email === account.email);
                    if (profile) {
                        this.user!.customer_profile_id = profile.id;
                        localStorage.setItem('user_account', JSON.stringify(this.user));
                    }
                } catch (e) {
                    console.error('Failed to link customer profile', e);
                }
            } else if (account.role === 'TECHNICIAN') {
                try {
                    const res = await api.get('technicians/');
                    const profile = res.data.find((t: any) => t.email === account.email);
                    if (profile) {
                        this.user!.technician_profile_id = profile.id;
                        localStorage.setItem('user_account', JSON.stringify(this.user));
                    }
                } catch (e) {
                    console.error('Failed to link technician profile', e);
                }
            }

            return account.role;
        },
        logout() {
            this.user = null;
            this.accessToken = '';
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_account');
        },
        updateUserData(updatedData: Partial<UserAccount>) {
            if (this.user) {
                this.user = { ...this.user, ...updatedData };
                localStorage.setItem('user_account', JSON.stringify(this.user));
            }
        }
    },
});