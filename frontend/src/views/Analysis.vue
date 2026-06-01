<template>
  <div class="analysis-page">
    <div class="page-title-bar">
      <h2>深度分析</h2>
      <span class="subtitle">历史走势与穿透重仓股剖析</span>
    </div>

    <!-- 近30天走势图 -->
    <ProfitChart 
      v-if="store.history && store.history.length > 0" 
      :data="store.history" 
    />
    <div v-else-if="store.historyLoading" class="loading-placeholder">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 今日贡献度 -->
    <DailyContributionChart 
      v-if="store.summary && store.summary.positions.length > 0" 
      :positions="store.summary.positions" 
    />
    <div v-else-if="store.loading" class="loading-placeholder">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 穿透重仓股 -->
    <HeavyStocksPanel v-if="store.summary && store.summary.positions.length > 0" />
    
    <div v-if="!store.loading && (!store.summary || store.summary.positions.length === 0)" class="empty-container">
      <el-empty description="当前账户暂无基金持仓，无法进行分析" />
      <el-button type="primary" @click="$router.push('/transactions')">去录入首笔交易</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useHoldingsStore } from '@/stores/holdings'
import HeavyStocksPanel from '@/components/HeavyStocksPanel.vue'
import ProfitChart from '@/components/ProfitChart.vue'
import DailyContributionChart from '@/components/DailyContributionChart.vue'

const store = useHoldingsStore()

onMounted(async () => {
  // 确保 summary 数据已加载
  if (!store.summary && !store.loading) {
    store.refresh()
  }
  // 加载走势图数据
  if (store.history.length === 0 && !store.historyLoading) {
    store.loadHistory()
  }
})
</script>

<style scoped>
.analysis-page {
  max-width: 960px;
  margin: 16px auto 40px;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-title-bar {
  margin-bottom: 8px;
}

.page-title-bar h2 {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
  color: #ffffff;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.loading-placeholder {
  background-color: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 24px;
}

.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 60px;
  gap: 16px;
}

:deep(.el-empty__description p) {
  color: var(--el-text-color-secondary) !important;
}

/* 移动端响应式适配 */
@media (max-width: 768px) {
  .analysis-page {
    margin: 8px auto 24px;
    padding: 0 4px;
    gap: 16px;
  }
  .page-title-bar h2 {
    font-size: 20px;
  }
}
</style>
