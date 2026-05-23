import { defineStore } from 'pinia'
import { ref } from 'vue'
import { holdingsApi } from '@/api/holdings'
import type { HoldingsSummary } from '@/types'

export const useHoldingsStore = defineStore('holdings', () => {
  const summary = ref<HoldingsSummary | null>(null)
  const loading = ref(false)
  let timer: number | null = null

  async function refresh() {
    loading.value = true
    try {
      summary.value = await holdingsApi.summary()
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

  return { summary, loading, refresh, startPolling, stopPolling }
})
