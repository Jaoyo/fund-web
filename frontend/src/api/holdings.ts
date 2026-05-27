import { apiGet, apiPost, apiDelete } from './client'
import type { HoldingsSummary, Transaction, TransactionIn, HoldingHistory } from '@/types'

export const holdingsApi = {
  summary: () => apiGet<HoldingsSummary>('/holdings'),
  history: (days = 30) => apiGet<HoldingHistory[]>('/holdings/history', { days }),
}

export const transactionsApi = {
  list: (fundCode?: string) =>
    apiGet<Transaction[]>('/transactions', fundCode ? { fund_code: fundCode } : undefined),
  create: (payload: TransactionIn) => apiPost<Transaction>('/transactions', payload),
  remove: (id: number) => apiDelete<{ deleted: number }>(`/transactions/${id}`),
  syncPending: () => apiPost<{ synced_count: number }>('/transactions/sync_pending'),
}
