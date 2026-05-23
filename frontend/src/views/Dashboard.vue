<template>
  <div class="dashboard">
    <ProfitSummary v-if="store.summary" :summary="store.summary" />
    <el-empty v-else-if="!store.loading" description="还没有任何持仓，去交易页录入第一笔" />

    <div v-if="store.summary" class="holdings">
      <div class="section-title">
        <span>持仓 ({{ store.summary.positions.length }})</span>
        <el-button size="small" :loading="store.loading" @click="store.refresh()">刷新</el-button>
      </div>
      <HoldingCard
        v-for="p in store.summary.positions"
        :key="p.fund_code"
        :position="p"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue'
import { useHoldingsStore } from '@/stores/holdings'
import ProfitSummary from '@/components/ProfitSummary.vue'
import HoldingCard from '@/components/HoldingCard.vue'

const store = useHoldingsStore()

onMounted(() => store.startPolling())
onBeforeUnmount(() => store.stopPolling())
</script>

<style scoped>
.dashboard { max-width: 960px; margin: 0 auto; }
.holdings { margin-top: 24px; }
.section-title {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px; font-weight: 600;
}
</style>
