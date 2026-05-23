import { apiGet, apiPost, apiDelete } from './client'
import type { HoldingsSummary, Transaction, TransactionIn } from '@/types'

export const holdingsApi = {
  summary: () => apiGet<HoldingsSummary>('/holdings'),
}

export const transactionsApi = {
  list: (fundCode?: string) =>
    apiGet<Transaction[]>('/transactions', fundCode ? { fund_code: fundCode } : undefined),
  create: (payload: TransactionIn) => apiPost<Transaction>('/transactions', payload),
  remove: (id: number) => apiDelete<{ deleted: number }>(`/transactions/${id}`),
}
