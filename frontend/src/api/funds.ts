import { apiGet, apiPut } from './client'
import type { FundDetail, NavRecord, Quote } from '@/types'

export const fundsApi = {
  detail: (code: string) => apiGet<FundDetail>(`/funds/${code}`),
  nav: (code: string, days = 60) => apiGet<NavRecord[]>(`/funds/${code}/nav`, { days }),
  quote: (code: string) => apiGet<Quote | null>(`/quotes/${code}`),
  sort: (codes: string[]) => apiPut<{ sorted: number }>('/funds/sort', { codes }),
}
