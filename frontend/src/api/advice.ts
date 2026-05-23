import { apiGet } from './client'
import type { FundAdvice } from '@/types'

export const adviceApi = {
  list: () => apiGet<FundAdvice[]>('/advice'),
  detail: (code: string) => apiGet<FundAdvice | null>(`/advice/${code}`),
}
