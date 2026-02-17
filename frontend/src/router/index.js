import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import InvoiceDetail from '@/views/InvoiceDetail.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/invoices/pending',
    name: 'PendingInvoices',
    component: Dashboard,
    props: { statusFilter: 'pending' }
  },
  {
    path: '/invoices/approved',
    name: 'ApprovedInvoices',
    component: Dashboard,
    props: { statusFilter: 'approved' }
  },
  {
    path: '/invoices/rejected',
    name: 'RejectedInvoices',
    component: Dashboard,
    props: { statusFilter: 'rejected' }
  },
  {
    path: '/invoices/:id',
    name: 'InvoiceDetail',
    component: InvoiceDetail,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
