<template>
  <div class="detail-page" v-loading="loading">
    <el-card v-if="detail" class="head-card">
      <div class="head">
        <div>
          <div class="name">{{ detail.fund.name }}</div>
          <div class="code">{{ detail.fund.code }}</div>
        </div>
        <div v-if="detail.quote" class="quote">
          <div>净值 <b>{{ detail.quote.nav.toFixed(4) }}</b> <span class="muted">{{ detail.quote.nav_date }}</span></div>
          <div v-if="detail.quote.estimated_nav !== null">
            估值 <b>{{ detail.quote.estimated_nav?.toFixed(4) }}</b>
            <span :style="{ color: profitColor(detail.quote.estimated_growth) }">
              ({{ (detail.quote.estimated_growth ?? 0).toFixed(2) }}%)
            </span>
            <span class="muted">{{ detail.quote.estimated_time }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="chart-card">
      <div class="card-title">
        <span>净值走势</span>
        <el-radio-group v-model="days" size="small" @change="loadNav">
          <el-radio-button :label="60">60D</el-radio-button>
          <el-radio-button :label="180">180D</el-radio-button>
          <el-radio-button :label="365">1Y</el-radio-button>
          <el-radio-button :label="750">3Y</el-radio-button>
        </el-radio-group>
      </div>
      <NavChart :records="navRecords" />
    </el-card>

    <el-card v-if="advice" class="advice-card">
      <div class="card-title">建议</div>
      <div class="metrics">
        <span v-if="advice.percentile !== null">历史分位 <b>{{ formatPercent(advice.percentile) }}</b></span>
        <span v-if="advice.ma_deviation !== null">均线偏离 <b>{{ formatPercent(advice.ma_deviation) }}</b></span>
        <span v-if="advice.max_drawdown !== null">最大回撤 <b>{{ formatPercent(advice.max_drawdown) }}</b></span>
      </div>
      <div class="signals">
        <AdviceBadge v-for="(s, i) in advice.signals" :key="i" :signal="s" />
      </div>
    </el-card>

    <el-card class="tx-card">
      <div class="card-title">该基金交易记录</div>
      <el-table :data="transactions" stripe>
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.type === 'buy' ? 'success' : 'danger'" size="small">
              {{ row.type === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="nav" label="净值" width="100" />
        <el-table-column prop="shares" label="份额" />
        <el-table-column prop="amount" label="金额" />
        <el-table-column prop="fee" label="费用" width="80" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { fundsApi } from '@/api/funds'
import { transactionsApi } from '@/api/holdings'
import { adviceApi } from '@/api/advice'
import { formatPercent, profitColor } from '@/utils/format'
import NavChart from '@/components/NavChart.vue'
import AdviceBadge from '@/components/AdviceBadge.vue'
import type { FundAdvice, FundDetail, NavRecord, Transaction } from '@/types'

const props = defineProps<{ code: string }>()
const loading = ref(false)
const detail = ref<FundDetail | null>(null)
const navRecords = ref<NavRecord[]>([])
const advice = ref<FundAdvice | null>(null)
const transactions = ref<Transaction[]>([])
const days = ref(180)

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
.detail-page { max-width: 960px; margin: 0 auto; }
.head-card, .chart-card, .advice-card, .tx-card { margin-bottom: 16px; }
.head { display: flex; justify-content: space-between; align-items: flex-start; }
.name { font-weight: 600; font-size: 18px; }
.code { color: var(--el-text-color-secondary); font-size: 13px; }
.quote { text-align: right; font-size: 14px; line-height: 1.8; }
.muted { color: var(--el-text-color-secondary); margin-left: 8px; font-size: 12px; }
.card-title {
  display: flex; justify-content: space-between; align-items: center;
  font-weight: 600; margin-bottom: 12px;
}
.metrics {
  display: flex; gap: 24px; flex-wrap: wrap;
  font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 8px;
}
.metrics b { color: var(--el-text-color-primary); }
.signals { display: flex; flex-wrap: wrap; }
</style>
