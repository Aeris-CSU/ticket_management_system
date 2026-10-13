import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '@/views/LandingView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import RoleDashboardPlaceholder from '@/views/RoleDashboardPlaceholder.vue'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { pinia } from '@/stores/pinia'
import type { UserRole } from '@/types/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: LandingView },
    { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
    { path: '/register', name: 'register', component: RegisterView, meta: { guestOnly: true } },
    {
      path: '/admin',
      component: DashboardLayout,
      meta: { requiresAuth: true, role: 'ADMIN', title: 'Admin Dashboard' },
      children: [
        { path: '', name: 'admin', component: RoleDashboardPlaceholder },
        { path: 'tickets', name: 'admin-tickets', component: () => import('@/views/TicketsListView.vue'), meta: { title: 'All Tickets', audience: 'admin' } },
        { path: 'tickets/:id', name: 'admin-ticket-detail', component: () => import('@/views/TicketDetailsView.vue'), meta: { title: 'Ticket Details' } },
        { path: 'assignments', name: 'admin-assignments', component: () => import('@/views/AdminAssignmentsView.vue'), meta: { title: 'Assignments' } },
        { path: 'customers', name: 'admin-customers', component: () => import('@/views/AdminDirectoryView.vue'), meta: { title: 'Customers', directory: 'customers' } },
        { path: 'technicians', name: 'admin-technicians', component: () => import('@/views/AdminDirectoryView.vue'), meta: { title: 'Technicians', directory: 'technicians' } },
      ],
    },
    {
      path: '/technician',
      component: DashboardLayout,
      meta: { requiresAuth: true, role: 'TECHNICIAN', title: 'Technician Dashboard' },
      children: [
        { path: '', name: 'technician', component: RoleDashboardPlaceholder },
        { path: 'tickets', name: 'technician-tickets', component: () => import('@/views/TicketsListView.vue'), meta: { title: 'Assigned Tickets', audience: 'technician' } },
        { path: 'tickets/:id', name: 'technician-ticket-detail', component: () => import('@/views/TicketDetailsView.vue'), meta: { title: 'Ticket Details', audience: 'technician' } },
      ],
    },
    {
      path: '/customer',
      component: DashboardLayout,
      meta: { requiresAuth: true, role: 'CUSTOMER', title: 'Customer Dashboard' },
      children: [
        { path: '', name: 'customer', component: RoleDashboardPlaceholder },
        { path: 'tickets', name: 'customer-tickets', component: () => import('@/views/TicketsListView.vue'), meta: { title: 'My Tickets' } },
        { path: 'tickets/new', name: 'customer-ticket-create', component: () => import('@/views/CreateTicketView.vue'), meta: { title: 'Create Ticket' } },
        { path: 'tickets/:id', name: 'customer-ticket-detail', component: () => import('@/views/TicketDetailsView.vue'), meta: { title: 'Ticket Details' } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore(pinia)
  if (auth.status === 'unknown') await auth.restoreSession()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }

  const requiredRole = to.meta.role as UserRole | undefined
  if (requiredRole && auth.user?.role !== requiredRole) {
    return auth.dashboardPath()
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return auth.dashboardPath()
  }

  return true
})

export default router
