<template>
  <div class="advice-page" v-loading="loading">
    <div class="header">
      <div class="title-section">
        <h3>智能投资策略建议</h3>
        <span class="desc">基于历史分位、{{ days >= 250 ? '250日' : days + '日' }}均线偏离度及持仓盈亏自动运算</span>
      </div>
      <div class="actions-section">
        <el-input v-model="newFundCode" placeholder="6位代码加自选" class="add-input" maxlength="6" :disabled="adding">
          <template #append>
            <el-button :loading="adding" @click="addFund" :icon="Plus"></el-button>
          </template>
        </el-input>
        <el-radio-group v-model="days" size="small" @change="load" class="days-radio">
          <el-radio-button :value="125">半年</el-radio-button>
          <el-radio-button :value="250">1年</el-radio-button>
          <el-radio-button :value="750">3年</el-radio-button>
        </el-radio-group>
        <el-button 
          size="small" 
          type="primary" 
          plain 
          :icon="Refresh" 
          :loading="loading" 
          @click="load"
        >
          刷新建议
        </el-button>
      </div>
    </div>
    <div class="filter-section" v-if="list.length > 0">
      <el-radio-group v-model="filterType" size="small" class="filter-radio">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="held">持仓</el-radio-button>
        <el-radio-button value="watchlist">自选</el-radio-button>
      </el-radio-group>
    </div>
    <el-empty v-if="!loading && filteredList.length === 0" description="暂无符合条件的基金" />
    
    <el-card v-for="item in filteredList" :key="item.fund_code" class="advice-card" shadow="hover">
      <div class="card-top">
        <div class="card-header" @click="$router.push(`/fund/${item.fund_code}`)">
          <span class="name">{{ item.fund_name }}</span>
          <span class="code font-number">{{ item.fund_code }}</span>
          <el-button v-if="item.profit_rate === null" class="delete-btn" link type="danger" @click.stop="removeFund(item.fund_code)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <div class="signals">
          <AdviceBadge v-for="(s, i) in item.signals" :key="i" :signal="s" />
        </div>
      </div>
      
      <div class="card-body">
        <div class="metrics-grid">
          <div class="metric-item-spec">
            <span class="label">历史百分位 ({{ days === 125 ? '半年' : days === 250 ? '1年' : '3年' }})</span>
            <span class="val font-number">{{ formatPercent(item.percentile) }}</span>
            <div v-if="item.percentile !== null" class="percentile-indicator">
              <div class="indicator-bar-bg"></div>
              <div class="indicator-pointer" :style="{ left: `${(item.percentile || 0) * 100}%` }"></div>
              <div class="indicator-labels">
                <span class="buy-label">低位 (买入机会)</span>
                <span>中位</span>
                <span class="sell-label">高位 (卖出风险)</span>
              </div>
            </div>
          </div>
          <div class="metric-box">
            <span class="label">{{ days >= 250 ? '250日' : days + '日' }}均线偏离</span>
            <span class="val" :class="getDeviationClass(item.ma_deviation)">
              {{ item.ma_deviation !== null ? (item.ma_deviation >= 0 ? '+' : '') + formatPercent(item.ma_deviation) : '-' }}
            </span>
          </div>
          <div class="metric-box">
            <span class="label">自高点最大回撤</span>
            <span class="val text-warning font-number">{{ formatPercent(item.max_drawdown) }}</span>
          </div>
          <div class="metric-box">
            <span class="label">持仓当前收益率</span>
            <span class="val" :class="item.profit_rate !== null ? (item.profit_rate >= 0 ? 'profit-glow-up' : 'profit-glow-down') : 'muted'">
              {{ item.profit_rate !== null ? (item.profit_rate >= 0 ? '+' : '') + formatPercent(item.profit_rate) : '未持仓' }}
            </span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { Refresh, Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adviceApi } from '@/api/advice'
import { fundsApi } from '@/api/funds'
import { formatPercent } from '@/utils/format'
import AdviceBadge from '@/components/AdviceBadge.vue'
import type { FundAdvice } from '@/types'

const list = ref<FundAdvice[]>([])
const loading = ref(false)
const days = ref(750)
const newFundCode = ref('')
const adding = ref(false)

const filterType = ref('all')

const filteredList = computed(() => {
  if (filterType.value === 'held') {
    return list.value.filter(item => item.profit_rate !== null)
  } else if (filterType.value === 'watchlist') {
    return list.value.filter(item => item.profit_rate === null)
  }
  return list.value
})

async function load() {
  loading.value = true
  try {
    list.value = await adviceApi.list(days.value)
  } finally {
    loading.value = false
  }
}

function getDeviationClass(dev: number | null) {
  if (dev === null) return 'muted'
  // 低位绿，高位红
  return dev >= 0.15 ? 'profit-glow-up' : (dev <= -0.10 ? 'profit-glow-down' : '')
}

async function addFund() {
  if (!newFundCode.value || newFundCode.value.length !== 6) {
    ElMessage.warning('请输入6位基金代码')
    return
  }
  adding.value = true
  try {
    await fundsApi.addWatchlist(newFundCode.value)
    ElMessage.success('已添加到自选')
    newFundCode.value = ''
    await load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '添加失败')
  } finally {
    adding.value = false
  }
}

async function removeFund(code: string) {
  try {
    await ElMessageBox.confirm('确认删除该自选基金吗？', '提示', { type: 'warning' })
    await fundsApi.removeWatchlist(code)
    ElMessage.success('已删除')
    await load()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.message || '删除失败')
    }
  }
}

onMounted(load)
</script>

<style scoped>
.advice-page { max-width: 960px; margin: 16px auto 40px; padding: 0 16px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.title-section h3 {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
  color: #ffffff;
  letter-spacing: -0.5px;
}
.title-section .desc {
  font-size: 13px;
  color: #707a8a;
}
.filter-section {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}
.actions-section {
  display: flex;
  gap: 12px;
  align-items: center;
}
.add-input {
  width: 200px;
}
.advice-card { margin-bottom: 16px; padding: 12px 16px; background-color: #1e2329 !important; border: 1px solid #2b3139 !important; }
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #2b3139;
  padding-bottom: 14px;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 12px;
}
.card-header {
  display: flex; gap: 8px; align-items: baseline; cursor: pointer;
}
.card-header:hover .name {
  color: var(--el-color-primary);
}
.name { font-weight: 700; font-size: 16px; color: #ffffff; transition: color 0.2s ease; }
.code { color: #929aa5; font-size: 12px; }
.delete-btn { margin-left: auto; padding-left: 8px; }
.signals { display: flex; flex-wrap: wrap; }

.metrics-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1fr;
  gap: 20px;
}
.metric-item-spec {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.metric-box {
  background: #2b3139;
  border: 1px solid #20262d;
  padding: 10px 14px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}
.label { font-size: 11px; color: #929aa5; font-weight: 500; }
.val { font-size: 15px; font-weight: 700; color: #eaecef; }
.muted { color: #707a8a !important; font-weight: normal; }
.text-warning { color: #fbbf24 !important; }

.percentile-indicator {
  position: relative;
  height: 28px;
  margin-top: 8px;
  width: 100%;
}
/* 低位买为绿(#0ecb81)，高位卖为红(#f6465d) */
.indicator-bar-bg {
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, #0ecb81 0%, rgba(255,255,255,0.12) 50%, #f6465d 100%);
  width: 100%;
}
.indicator-pointer {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid var(--el-color-primary);
  top: -2px;
  transform: translateX(-50%);
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
}
.indicator-labels {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  color: #707a8a;
  margin-top: 6px;
  font-weight: 500;
}
.buy-label { color: #0ecb81; }
.sell-label { color: #f6465d; }

/* 手机端响应式适配 */
@media (max-width: 768px) {
  .advice-page {
    margin: 8px auto 24px;
    padding: 0 4px;
  }
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 16px;
  }
  .actions-section {
    width: 100%;
    justify-content: space-between;
  }
  .advice-card {
    padding: 12px !important;
    margin-bottom: 12px;
  }
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .metric-item-spec {
    grid-column: span 2;
  }
  .metric-box:last-child {
    grid-column: span 2;
  }
  .metric-box {
    padding: 8px 10px;
  }
  .val {
    font-size: 14px;
  }
}
</style>
