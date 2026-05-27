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
          <div class="code">{{ detail.fund.code }}</div>
        </div>
        <div v-if="detail.quote" class="quote">
          <div class="quote-row">最新净值 <b class="nav-val">{{ detail.quote.nav.toFixed(4) }}</b> <span class="muted">{{ detail.quote.nav_date }}</span></div>
          <div v-if="detail.quote.estimated_nav !== null" class="quote-row">
            实时估值 <b class="est-val">{{ detail.quote.estimated_nav?.toFixed(4) }}</b>
            <span :class="(detail.quote.estimated_growth ?? 0) >= 0 ? 'profit-glow-up' : 'profit-glow-down'" class="growth-text">
              ({{ (detail.quote.estimated_growth ?? 0) >= 0 ? '+' : '' }}{{ (detail.quote.estimated_growth ?? 0).toFixed(2) }}%)
            </span>
            <span class="muted font-sans">{{ detail.quote.estimated_time }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="chart-card">
      <div class="card-title">
        <span>净值走势图</span>
        <el-radio-group v-model="days" size="small" @change="loadNav">
          <el-radio-button :label="60">60天</el-radio-button>
          <el-radio-button :label="180">180天</el-radio-button>
          <el-radio-button :label="365">1年</el-radio-button>
          <el-radio-button :label="750">3年</el-radio-button>
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
            <span class="val">{{ formatPercent(advice.percentile) }}</span>
          </div>
          <div class="metric-box" v-if="advice.ma_deviation !== null">
            <span class="label">250日均线偏离</span>
            <span class="val" :class="advice.ma_deviation >= 0.15 ? 'profit-glow-down' : (advice.ma_deviation <= -0.10 ? 'profit-glow-up' : '')">
              {{ (advice.ma_deviation >= 0 ? '+' : '') + formatPercent(advice.ma_deviation) }}
            </span>
          </div>
          <div class="metric-box" v-if="advice.max_drawdown !== null">
            <span class="label">历史最大回撤</span>
            <span class="val text-warning">{{ formatPercent(advice.max_drawdown) }}</span>
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
      <el-table :data="transactions" stripe>
        <el-table-column prop="date" label="日期" width="115" />
        <el-table-column label="交易类型" width="90">
          <template #default="{ row }">
            <span :class="row.type === 'buy' ? 'type-buy' : 'type-sell'">
              {{ row.type === 'buy' ? '买入' : '卖出' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="nav" label="成交净值" width="100" />
        <el-table-column prop="shares" label="确认份额" />
        <el-table-column prop="amount" label="交易金额" />
        <el-table-column prop="fee" label="交易费用" width="90" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
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
onMounted(loadAll)
</script>

<style scoped>
.detail-page { max-width: 960px; margin: 16px auto 40px; padding: 0 16px; }
.page-header { margin-bottom: 16px; display: flex; align-items: center; }
.back-btn { font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); }
.back-btn .el-icon { margin-right: 4px; font-size: 16px; }
.back-btn:hover { color: var(--el-color-primary); }
.head-card, .chart-card, .advice-card, .tx-card { margin-bottom: 16px; padding: 8px 12px; }
.head { display: flex; justify-content: space-between; align-items: center; }
.title-container { display: flex; flex-direction: column; gap: 4px; }
.name { font-weight: 800; font-size: 20px; color: var(--el-text-color-primary); }
.code { color: var(--el-text-color-secondary); font-size: 13px; font-family: var(--font-sans); }
.quote { text-align: right; font-size: 13px; line-height: 1.8; }
.quote-row { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
.nav-val { font-size: 16px; font-weight: 700; color: var(--el-text-color-primary); font-family: var(--font-sans); }
.est-val { font-size: 16px; font-weight: 700; color: #60a5fa; font-family: var(--font-sans); }
.growth-text { font-weight: 600; font-family: var(--font-sans); }
.muted { color: var(--el-text-color-secondary); font-size: 11px; }

.card-title {
  display: flex; justify-content: space-between; align-items: center;
  font-weight: 700; margin-bottom: 18px;
  color: var(--el-text-color-primary);
  font-size: 15px;
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
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.03);
  padding: 10px 14px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.label { font-size: 11px; color: var(--el-text-color-secondary); font-weight: 500; }
.val { font-size: 16px; font-weight: 700; font-family: var(--font-sans); color: var(--el-text-color-primary); }
.signals { display: flex; flex-wrap: wrap; margin-top: 4px; }

.type-buy {
  color: var(--el-color-success-light-3);
  font-weight: 600;
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.type-sell {
  color: var(--el-color-danger-light-3);
  font-weight: 600;
  background: rgba(244, 63, 94, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
