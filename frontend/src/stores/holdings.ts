import { defineStore } from 'pinia'
import { ref } from 'vue'
import { holdingsApi } from '@/api/holdings'
import type { HoldingsSummary, HoldingHistory } from '@/types'

export const useHoldingsStore = defineStore('holdings', () => {
  const summary = ref<HoldingsSummary | null>(null)
  const history = ref<HoldingHistory[]>([])
  const loading = ref(false)
  let timer: number | null = null

  const historyLoading = ref(false)
  const heavyStocks = ref<any[]>([])
  const heavyStocksLoading = ref(false)

  async function refresh() {
    loading.value = true
    try {
      const pSummary = holdingsApi.summary()
      let pHistory: Promise<any> | null = null

      if (history.value.length > 0) {
        pHistory = holdingsApi.history(30)
      }

      const [s, h] = await Promise.all([pSummary, pHistory])
      summary.value = s

      if (h) {
        if (s) {
          const combined = h.filter((item: any) => item.date < s.trade_date)
          combined.push({
            date: s.trade_date,
            profit: Number(s.today_profit.toFixed(2)),
            cumulative_profit: Number(s.total_profit.toFixed(2))
          })
          history.value = combined
        } else {
          history.value = h
        }
      }
    } finally {
      loading.value = false
    }
  }

  async function loadHistory() {
    if (history.value.length > 0 || historyLoading.value) return
    historyLoading.value = true
    try {
      const h = await holdingsApi.history(30)
      const s = summary.value
      if (s && h) {
        const combined = h.filter(item => item.date < s.trade_date)
        combined.push({
          date: s.trade_date,
          profit: Number(s.today_profit.toFixed(2)),
          cumulative_profit: Number(s.total_profit.toFixed(2))
        })
        history.value = combined
      } else {
        history.value = h
      }
    } finally {
      historyLoading.value = false
    }
  }

  async function loadHeavyStocks() {
    heavyStocksLoading.value = true
    try {
      heavyStocks.value = await holdingsApi.heavyWeightStocks()
    } finally {
      heavyStocksLoading.value = false
    }
  }

  function startPolling(intervalMs = 60_000) {
    stopPolling()
    refresh()
    timer = window.setInterval(refresh, intervalMs)
  }

  function stopPolling() {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
  }

  return { summary, history, loading, historyLoading, heavyStocks, heavyStocksLoading, refresh, loadHistory, loadHeavyStocks, startPolling, stopPolling }
})
