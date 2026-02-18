import { createRouter, createWebHistory } from 'vue-router'
import { authService } from '@/services/auth'
import Dashboard from '@/views/Dashboard.vue'
import InvoiceDetail from '@/views/InvoiceDetail.vue'
import Login from '@/views/Login.vue'
import Admin from '@/views/Admin.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/invoices/pending',
    name: 'PendingInvoices',
    component: Dashboard,
    props: { statusFilter: 'pending' },
  },
  {
    path: '/invoices/approved',
    name: 'ApprovedInvoices',
    component: Dashboard,
    props: { statusFilter: 'approved' },
  },
  {
    path: '/invoices/rejected',
    name: 'RejectedInvoices',
    component: Dashboard,
    props: { statusFilter: 'rejected' },
  },
  {
    path: '/invoices/:id',
    name: 'InvoiceDetail',
    component: InvoiceDetail,
    props: true,
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresSuperuser: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.public) return true

  if (!authService.isAuthenticated()) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresSuperuser && !authService.isSuperuser()) {
    return { name: 'Dashboard' }
  }

  return true
})

export default router
