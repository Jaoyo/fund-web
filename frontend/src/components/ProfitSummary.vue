<template>
  <el-card>
    <div class="title">总资产</div>
    <div class="amount">¥{{ formatMoney(summary.total_market_value) }}</div>
    <div class="grid">
      <div>
        <div class="label">累计成本</div>
        <div class="val">¥{{ formatMoney(summary.total_cost) }}</div>
      </div>
      <div>
        <div class="label">累计收益</div>
        <div class="val" :style="{ color: profitColor(summary.total_profit) }">
          {{ summary.total_profit >= 0 ? '+' : '' }}¥{{ formatMoney(summary.total_profit) }}
          ({{ formatPercent(summary.total_profit_rate) }})
        </div>
      </div>
      <div>
        <div class="label">今日预估</div>
        <div class="val" :style="{ color: profitColor(summary.today_profit) }">
          {{ summary.today_profit >= 0 ? '+' : '' }}¥{{ formatMoney(summary.today_profit) }}
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { formatMoney, formatPercent, profitColor } from '@/utils/format'
import type { HoldingsSummary } from '@/types'

defineProps<{ summary: HoldingsSummary }>()
</script>

<style scoped>
.title { color: var(--el-text-color-secondary); font-size: 13px; }
.amount { font-size: 28px; font-weight: 600; margin: 8px 0 16px; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.label { font-size: 12px; color: var(--el-text-color-secondary); }
.val { font-size: 16px; font-weight: 500; margin-top: 4px; }
</style>
