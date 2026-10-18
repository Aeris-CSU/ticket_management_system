import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import Login from '@/views/Login.vue';
import AdminDashboard from '@/views/AdminDashboard.vue';
import TechnicianDashboard from '@/views/TechnicianDashboard.vue';
import CustomerDashboard from '@/views/CustomerDashboard.vue';

const routes = [
    { path: '/login', name: 'Login', component: Login },
    {
        path: '/admin',
        name: 'AdminDashboard',
        component: AdminDashboard,
        meta: { requiresAuth: true, role: 'ADMIN' }
    },
    {
        path: '/technician',
        name: 'TechnicianDashboard',
        component: TechnicianDashboard,
        meta: { requiresAuth: true, role: 'TECHNICIAN' }
    },
    {
        path: '/customer',
        name: 'CustomerDashboard',
        component: CustomerDashboard,
        meta: { requiresAuth: true, role: 'CUSTOMER' }
    },
    { path: '/:pathMatch(.*)*', redirect: '/login' },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        return next('/login');
    }

    if (to.meta.role && authStore.role !== to.meta.role) {
        if (authStore.role === 'ADMIN') return next('/admin');
        if (authStore.role === 'TECHNICIAN') return next('/technician');
        if (authStore.role === 'CUSTOMER') return next('/customer');
        return next('/login');
    }

    next();
});

export default router;