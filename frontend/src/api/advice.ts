import { apiGet } from './client'
import type { FundAdvice } from '@/types'

export const adviceApi = {
  list: (days: number = 750) => apiGet<FundAdvice[]>(`/advice?days=${days}`),
  detail: (code: string, days: number = 750) => apiGet<FundAdvice | null>(`/advice/${code}?days=${days}`),
}
