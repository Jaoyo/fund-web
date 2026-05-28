import { defineStore } from 'pinia'
import { ref } from 'vue'
import { holdingsApi } from '@/api/holdings'
import type { HoldingsSummary, HoldingHistory } from '@/types'

export const useHoldingsStore = defineStore('holdings', () => {
  const summary = ref<HoldingsSummary | null>(null)
  const history = ref<HoldingHistory[]>([])
  const loading = ref(false)
  let timer: number | null = null

  async function refresh() {
    loading.value = true
    try {
      const [s, h] = await Promise.all([
        holdingsApi.summary(),
        holdingsApi.history(30)
      ])
      summary.value = s
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
      loading.value = false
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

  return { summary, history, loading, refresh, startPolling, stopPolling }
})
