<template>
  <el-card shadow="hover" class="holding-card" @click="goDetail">
    <div class="row top">
      <div class="name">{{ position.fund_name }}</div>
      <div class="code">{{ position.fund_code }}</div>
    </div>
    <div class="row metrics">
      <div>
        <div class="label">市值</div>
        <div class="value">¥{{ formatMoney(position.market_value) }}</div>
      </div>
      <div>
        <div class="label">累计收益</div>
        <div class="value" :style="{ color: profitColor(position.profit) }">
          {{ position.profit >= 0 ? '+' : '' }}{{ formatMoney(position.profit) }}
          <span class="rate">({{ formatPercent(position.profit_rate) }})</span>
        </div>
      </div>
      <div>
        <div class="label">今日预估</div>
        <div class="value" :style="{ color: profitColor(position.today_profit) }">
          <template v-if="position.today_profit !== null">
            {{ position.today_profit >= 0 ? '+' : '' }}{{ formatMoney(position.today_profit) }}
            <span class="rate">({{ formatPercent(position.today_profit_rate) }})</span>
          </template>
          <template v-else>盘后</template>
        </div>
      </div>
    </div>
    <div class="row footer">
      <span>份额 {{ formatMoney(position.shares, 2) }}</span>
      <span>成本 {{ formatMoney(position.avg_cost, 4) }}</span>
      <span>净值 {{ formatMoney(position.latest_nav, 4) }}</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { formatMoney, formatPercent, profitColor } from '@/utils/format'
import type { Position } from '@/types'

const props = defineProps<{ position: Position }>()
const router = useRouter()

function goDetail() {
  router.push(`/fund/${props.position.fund_code}`)
}
</script>

<style scoped>
.holding-card { cursor: pointer; margin-bottom: 12px; }
.row { display: flex; align-items: baseline; }
.top { justify-content: space-between; margin-bottom: 12px; }
.name { font-weight: 600; font-size: 16px; }
.code { color: var(--el-text-color-secondary); font-size: 13px; }
.metrics { gap: 32px; }
.metrics .label { font-size: 12px; color: var(--el-text-color-secondary); }
.metrics .value { font-size: 16px; font-weight: 500; }
.rate { font-size: 12px; margin-left: 4px; }
.footer {
  margin-top: 12px; gap: 16px;
  font-size: 12px; color: var(--el-text-color-secondary);
}
</style>
