<template>
  <div class="detail-page" v-loading="loading">
    <div class="page-header">
      <el-button link @click="goBack" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>返回
      </el-button>
    </div>
    
    <el-card v-if="detail" class="head-card">
      <div class="head">
        <div class="title-container">
          <div class="name">{{ detail.fund.name }}</div>
          <div class="code font-number">{{ detail.fund.code }}</div>
        </div>
        <div v-if="detail.quote" class="quote">
          <div class="quote-row">最新净值 <b class="nav-val font-number">{{ detail.quote.nav.toFixed(4) }}</b> <span class="muted font-number">{{ detail.quote.nav_date }}</span></div>
          <div v-if="detail.quote.estimated_nav !== null" class="quote-row">
            实时估值 <b class="est-val font-number">{{ detail.quote.estimated_nav?.toFixed(4) }}</b>
            <span :class="(detail.quote.estimated_growth ?? 0) >= 0 ? 'profit-glow-up' : 'profit-glow-down'" class="growth-text">
              ({{ (detail.quote.estimated_growth ?? 0) >= 0 ? '+' : '' }}{{ (detail.quote.estimated_growth ?? 0).toFixed(2) }}%)
            </span>
            <span class="muted font-number">{{ detail.quote.estimated_time }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="chart-card">
      <div class="card-title select-header">
        <span>净值走势图</span>
        <el-radio-group v-model="days" size="small" @change="loadNav" class="time-selector">
          <el-radio-button :value="60">60天</el-radio-button>
          <el-radio-button :value="180">180天</el-radio-button>
          <el-radio-button :value="365">1年</el-radio-button>
          <el-radio-button :value="750">3年</el-radio-button>
        </el-radio-group>
      </div>
      <NavChart :records="navRecords" />
    </el-card>

    <el-card v-if="advice" class="advice-card">
      <div class="card-title">策略建议信号</div>
      <div class="advice-content">
        <div class="metrics-grid">
          <div class="metric-box" v-if="advice.percentile !== null">
            <span class="label">历史分位数</span>
            <span class="val font-number">{{ formatPercent(advice.percentile) }}</span>
          </div>
          <div class="metric-box" v-if="advice.ma_deviation !== null">
            <span class="label">250日均线偏离</span>
            <span class="val" :class="advice.ma_deviation >= 0.15 ? 'profit-glow-down' : (advice.ma_deviation <= -0.10 ? 'profit-glow-up' : '')">
              {{ (advice.ma_deviation >= 0 ? '+' : '') + formatPercent(advice.ma_deviation) }}
            </span>
          </div>
          <div class="metric-box" v-if="advice.max_drawdown !== null">
            <span class="label">历史最大回撤</span>
            <span class="val text-warning font-number">{{ formatPercent(advice.max_drawdown) }}</span>
          </div>
          <div class="metric-box" v-if="advice.profit_rate !== null">
            <span class="label">持仓收益率</span>
            <span class="val" :class="advice.profit_rate >= 0 ? 'profit-glow-up' : 'profit-glow-down'">
              {{ (advice.profit_rate >= 0 ? '+' : '') + formatPercent(advice.profit_rate) }}
            </span>
          </div>
        </div>
        <div class="signals">
          <AdviceBadge v-for="(s, i) in advice.signals" :key="i" :signal="s" />
        </div>
      </div>
    </el-card>

    <el-card class="tx-card">
      <div class="card-title">本只基金交易明细</div>
      <el-table :data="transactions" stripe style="width: 100%">
        <el-table-column prop="date" label="日期" min-width="100" class-name="font-number" />
        <el-table-column label="交易类型" min-width="80">
          <template #default="{ row }">
            <span :class="row.type === 'buy' ? 'type-buy' : 'type-sell'">
              {{ row.type === 'buy' ? '买入' : '卖出' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="nav" label="成交净值" min-width="85" class-name="font-number" />
        <el-table-column prop="shares" label="确认份额" min-width="95" class-name="font-number" />
        <el-table-column prop="amount" label="交易金额" min-width="95" class-name="font-number">
          <template #default="{ row }">
            ¥{{ row.amount.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column v-if="!isMobile" prop="fee" label="交易费用" min-width="80" class-name="font-number" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { fundsApi } from '@/api/funds'
import { transactionsApi } from '@/api/holdings'
import { adviceApi } from '@/api/advice'
import { formatPercent } from '@/utils/format'
import NavChart from '@/components/NavChart.vue'
import AdviceBadge from '@/components/AdviceBadge.vue'
import type { FundAdvice, FundDetail, NavRecord, Transaction } from '@/types'

const props = defineProps<{ code: string }>()
const router = useRouter()
const loading = ref(false)
const detail = ref<FundDetail | null>(null)
const navRecords = ref<NavRecord[]>([])
const advice = ref<FundAdvice | null>(null)
const transactions = ref<Transaction[]>([])
const days = ref(180)

const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

function goBack() {
  router.back()
}

async function loadAll() {
  loading.value = true
  try {
    const [d, txs, a] = await Promise.all([
      fundsApi.detail(props.code),
      transactionsApi.list(props.code),
      adviceApi.detail(props.code),
    ])
    detail.value = d
    transactions.value = txs
    advice.value = a
    await loadNav()
  } finally {
    loading.value = false
  }
}

async function loadNav() {
  navRecords.value = await fundsApi.nav(props.code, days.value)
}

watch(() => props.code, loadAll)

onMounted(() => {
  loadAll()
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.detail-page { max-width: 960px; margin: 16px auto 40px; padding: 0 16px; }
.page-header { margin-bottom: 16px; display: flex; align-items: center; }
.back-btn { font-size: 15px; font-weight: 600; color: #eaecef; }
.back-btn .el-icon { margin-right: 4px; font-size: 16px; }
.back-btn:hover { color: var(--el-color-primary); }
.head-card, .chart-card, .advice-card, .tx-card { margin-bottom: 16px; padding: 12px 16px; background-color: #1e2329 !important; border: 1px solid #2b3139 !important; }
.head { display: flex; justify-content: space-between; align-items: center; }
.title-container { display: flex; flex-direction: column; gap: 4px; }
.name { font-weight: 700; font-size: 18px; color: #ffffff; }
.code { color: #929aa5; font-size: 12px; }
.quote { text-align: right; font-size: 13px; line-height: 1.8; }
.quote-row { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
.nav-val { font-size: 15px; font-weight: 700; color: #ffffff; }
.est-val { font-size: 15px; font-weight: 700; color: #2dbdb6; } /* 采用碧蓝色实时估值 */
.growth-text { font-weight: 600; }
.muted { color: #707a8a; font-size: 11px; }

.card-title {
  display: flex; justify-content: space-between; align-items: center;
  font-weight: 700; margin-bottom: 18px;
  color: #ffffff;
  font-size: 14px;
}

.advice-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.metric-box {
  background: #2b3139;
  border: 1px solid #20262d;
  padding: 10px 14px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.label { font-size: 11px; color: #929aa5; font-weight: 500; }
.val { font-size: 15px; font-weight: 700; color: #eaecef; }
.signals { display: flex; flex-wrap: wrap; margin-top: 4px; }
.text-warning { color: #fbbf24 !important; }

.type-buy {
  color: #f6465d;
  font-weight: 600;
  background: rgba(246, 70, 93, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.type-sell {
  color: #0ecb81;
  font-weight: 600;
  background: rgba(14, 203, 129, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

:deep(.el-radio-button__inner) {
  background-color: #2b3139 !important;
  border: 1px solid #2b3139 !important;
  color: #eaecef !important;
  transition: all 0.2s ease;
}
:deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner),
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: var(--el-color-primary) !important;
  color: #181a20 !important;
  border-color: var(--el-color-primary) !important;
  box-shadow: -1px 0 0 0 var(--el-color-primary) !important;
}

/* 手机端响应式适配 */
@media (max-width: 768px) {
  .detail-page {
    margin: 8px auto 24px;
    padding: 0 4px;
  }
  .head-card, .chart-card, .advice-card, .tx-card {
    padding: 12px !important;
    margin-bottom: 12px;
  }
  .head {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .quote {
    text-align: left;
    width: 100%;
  }
  .quote-row {
    justify-content: flex-start;
  }
  .select-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .time-selector {
    width: 100%;
    display: flex;
  }
  :deep(.time-selector .el-radio-button) {
    flex: 1;
  }
  :deep(.time-selector .el-radio-button__inner) {
    width: 100%;
    padding: 8px 0;
    text-align: center;
  }
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>
