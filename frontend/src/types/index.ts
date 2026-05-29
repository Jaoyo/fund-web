export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface Fund {
  code: string
  name: string
  type?: string | null
  updated_at?: string | null
}

export interface Quote {
  code: string
  name: string
  nav_date: string
  nav: number
  estimated_nav?: number | null
  estimated_growth?: number | null
  estimated_time?: string | null
}

export interface FundDetail {
  fund: Fund
  quote: Quote | null
}

export interface NavRecord {
  date: string
  nav: number
  accumulated_nav?: number | null
  growth_rate?: number | null
}

export interface Position {
  fund_code: string
  fund_name: string
  shares: number
  cost_amount: number
  avg_cost: number
  market_value: number
  profit: number
  profit_rate: number
  today_profit: number | null
  today_profit_rate: number | null
  latest_nav: number
  latest_nav_date: string
  estimated_nav: number | null
  estimated_growth: number | null
  is_estimated: boolean
}

export interface HoldingsSummary {
  total_market_value: number
  total_cost: number
  total_profit: number
  total_profit_rate: number
  today_profit: number
  today_profit_rate: number
  is_estimated: boolean
  update_status: 'estimated' | 'updating' | 'updated'
  positions: Position[]
  trade_date: string
}

export interface HoldingHistory {
  date: string
  profit: number
  cumulative_profit: number
}

export interface Transaction {
  id: number
  client_id: string | null
  fund_code: string
  date: string
  type: 'buy' | 'sell' | 'import'
  nav: number
  shares: number
  amount: number
  fee: number
  note: string | null
  created_at: string
}

export interface TransactionIn {
  client_id?: string
  fund_code: string
  date: string
  type: 'buy' | 'sell' | 'import'
  nav?: number | null
  shares?: number | null
  amount?: number | null
  profit?: number
  fund_name?: string
  fee?: number
  note?: string
}

export type SignalLevel = 'info' | 'watch' | 'buy' | 'sell'

export interface AdviceSignal {
  name: string
  level: SignalLevel
  message: string
  value: number | null
}

export interface FundAdvice {
  fund_code: string
  fund_name: string
  signals: AdviceSignal[]
  percentile: number | null
  ma_deviation: number | null
  max_drawdown: number | null
  profit_rate: number | null
}
