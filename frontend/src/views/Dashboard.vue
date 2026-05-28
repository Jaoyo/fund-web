<template>
  <div class="dashboard">
    <div class="page-title-bar">
      <h2>资产账户总览</h2>
      <span class="subtitle">跟踪持仓明细与今日预估收益</span>
    </div>
    
    <ProfitSummary v-if="store.summary" :summary="store.summary" @toggle-chart="showChart = !showChart" />
    
    <ProfitChart v-if="store.history && store.history.length > 0 && showChart" :data="store.history" />
    
    <div v-else-if="!store.summary && !store.loading" class="empty-container">
      <el-empty description="当前账户暂无基金持仓" />
      <el-button type="primary" @click="$router.push('/transactions')">去录入首笔交易</el-button>
    </div>

    <div v-if="store.summary" class="holdings">
      <div class="section-title">
        <span class="title-text">持仓明细 <span class="count">({{ store.summary.positions.length }})</span></span>
        <div class="actions" style="display: flex; gap: 8px;">
          <el-button 
            v-if="!isSorting"
            size="small" 
            plain 
            :icon="Rank" 
            @click="enableSort"
          >
            排序
          </el-button>
          <template v-else>
            <el-button size="small" @click="cancelSort">取消</el-button>
            <el-button size="small" type="primary" :loading="savingSort" @click="saveSort">保存排序</el-button>
          </template>
          <el-button 
            size="small" 
            type="primary" 
            plain 
            :icon="Refresh" 
            :loading="store.loading" 
            @click="store.refresh()"
            :disabled="isSorting"
          >
            刷新数据
          </el-button>
        </div>
      </div>
      <div ref="listRef" class="sortable-list">
        <HoldingCard
          v-for="p in store.summary.positions"
          :key="p.fund_code"
          :position="p"
          :is-sorting="isSorting"
          :data-code="p.fund_code"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue'
import { Refresh, Rank } from '@element-plus/icons-vue'
import { useHoldingsStore } from '@/stores/holdings'
import { fundsApi } from '@/api/funds'
import { ElMessage } from 'element-plus'
import Sortable from 'sortablejs'
import ProfitSummary from '@/components/ProfitSummary.vue'
import ProfitChart from '@/components/ProfitChart.vue'
import HoldingCard from '@/components/HoldingCard.vue'

const store = useHoldingsStore()

const showChart = ref(false)
const isSorting = ref(false)
const savingSort = ref(false)
const listRef = ref<HTMLElement | null>(null)
let sortableInst: Sortable | null = null
let originalPositions: any[] = []

function enableSort() {
  isSorting.value = true
  originalPositions = JSON.parse(JSON.stringify(store.summary?.positions || []))
  nextTick(() => {
    if (listRef.value) {
      sortableInst = new Sortable(listRef.value, {
        animation: 150,
        handle: '.holding-card',
        ghostClass: 'sortable-ghost',
        onEnd: (evt) => {
          if (store.summary && evt.oldIndex !== undefined && evt.newIndex !== undefined) {
            const item = store.summary.positions.splice(evt.oldIndex, 1)[0]
            store.summary.positions.splice(evt.newIndex, 0, item)
          }
        }
      })
    }
  })
}

function cancelSort() {
  isSorting.value = false
  if (sortableInst) {
    sortableInst.destroy()
    sortableInst = null
  }
  if (store.summary) {
    store.summary.positions = originalPositions
  }
}

async function saveSort() {
  if (!store.summary) return
  savingSort.value = true
  try {
    const codes = store.summary.positions.map(p => p.fund_code)
    await fundsApi.sort(codes)
    ElMessage.success('排序保存成功')
    isSorting.value = false
    if (sortableInst) {
      sortableInst.destroy()
      sortableInst = null
    }
  } catch (e) {
    // 错误由 client 拦截
  } finally {
    savingSort.value = false
  }
}

onMounted(() => store.startPolling())
onBeforeUnmount(() => store.stopPolling())
</script>

<style scoped>
.dashboard { max-width: 960px; margin: 16px auto 40px; padding: 0 16px; }
.page-title-bar {
  margin-bottom: 24px;
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
.holdings { margin-top: 32px; }
.section-title {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.title-text {
  font-weight: 700;
  font-size: 20px;
  color: #ffffff;
}
.title-text .count {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-weight: normal;
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
.sortable-ghost {
  opacity: 0.4;
  background-color: var(--el-fill-color-light);
  border: 1px dashed var(--el-color-primary) !important;
}

/* 移动端响应式适配 */
@media (max-width: 768px) {
  .dashboard {
    margin: 8px auto 24px;
    padding: 0 4px;
  }
  .page-title-bar {
    margin-bottom: 16px;
  }
  .page-title-bar h2 {
    font-size: 20px;
  }
  .section-title {
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }
  .actions {
    justify-content: flex-end;
  }
  .holdings {
    margin-top: 24px;
  }
}
</style>
