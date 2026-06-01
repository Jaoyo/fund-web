import { createRouter, createWebHistory } from 'vue-router'
import { apiGet } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
    { path: '/transactions', name: 'transactions', component: () => import('@/views/Transactions.vue') },
    { path: '/analysis', name: 'analysis', component: () => import('@/views/Analysis.vue') },
    { path: '/advice', name: 'advice', component: () => import('@/views/Advice.vue') },
    { path: '/fund/:code', name: 'fund-detail', component: () => import('@/views/FundDetail.vue'), props: true },
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const auth = useAuthStore()
  if (!auth.isAuthed) {
    return { name: 'login' }
  }
  if (auth.validated) return true

  // 静默预校验：避免持过期 token 进入主页面后才弹错
  try {
    await apiGet('/transactions', undefined, { skipAuthRedirect: true })
    auth.markValidated()
    return true
  } catch (e: unknown) {
    const code = (e as { code?: number })?.code
    if (code === 4011) {
      auth.clearToken()
      return { name: 'login' }
    }
    // 其它错误（网络、5xx）不阻断进入，让页面自己处理
    auth.markValidated()
    return true
  }
})

export default router
