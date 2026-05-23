import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
    { path: '/transactions', name: 'transactions', component: () => import('@/views/Transactions.vue') },
    { path: '/advice', name: 'advice', component: () => import('@/views/Advice.vue') },
    { path: '/fund/:code', name: 'fund-detail', component: () => import('@/views/FundDetail.vue'), props: true },
  ],
})

export default router
