<template>
  <el-card class="profit-summary-card">
    <div class="header-section">
      <div class="title">总资产市值 (元)</div>
      <div class="amount">¥{{ formatMoney(summary.total_market_value) }}</div>
    </div>
    <div class="grid">
      <div class="card-panel">
        <div class="label">累计投入成本</div>
        <div class="val">¥{{ formatMoney(summary.total_cost) }}</div>
      </div>
      <div class="card-panel" :class="summary.total_profit >= 0 ? 'bg-glow-up' : 'bg-glow-down'">
        <div class="label">累计总收益</div>
        <div class="val" :class="summary.total_profit >= 0 ? 'profit-glow-up' : 'profit-glow-down'">
          {{ summary.total_profit >= 0 ? '+' : '' }}¥{{ formatMoney(summary.total_profit) }}
          <span class="rate">({{ formatPercent(summary.total_profit_rate) }})</span>
        </div>
      </div>
      <div class="card-panel" :class="summary.today_profit >= 0 ? 'bg-glow-up' : 'bg-glow-down'">
        <div class="label" style="display: flex; align-items: center; gap: 6px;">
          {{ summary.update_status === 'updated' ? '今日收益' : '今日估算收益' }}
          <el-tag 
            v-if="summary.update_status === 'updating'" 
            size="small" 
            type="warning" 
            effect="dark" 
            round 
            style="transform: scale(0.85); transform-origin: left center;"
          >
            更新中
          </el-tag>
        </div>
        <div class="val" :class="summary.today_profit >= 0 ? 'profit-glow-up' : 'profit-glow-down'">
          {{ summary.today_profit >= 0 ? '+' : '' }}¥{{ formatMoney(summary.today_profit) }}
          <span class="rate">({{ formatPercent(summary.today_profit_rate) }})</span>
        </div>
      </div>
    </div>
    <div class="toggle-chart-btn" @click="$emit('toggleChart')">
      <span>近30天走势</span>
      <el-icon><DataLine /></el-icon>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { formatMoney, formatPercent } from '@/utils/format'
import { DataLine } from '@element-plus/icons-vue'
import type { HoldingsSummary } from '@/types'

defineProps<{ summary: HoldingsSummary }>()
defineEmits<{ (e: 'toggleChart'): void }>()
</script>

<style scoped>
.profit-summary-card {
  padding: 16px;
  background: linear-gradient(135deg, rgba(20, 26, 42, 0.8) 0%, rgba(13, 18, 30, 0.8) 100%) !important;
  position: relative;
}
.toggle-chart-btn {
  position: absolute;
  right: 16px;
  bottom: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: color 0.2s;
}
.toggle-chart-btn:hover {
  color: var(--el-color-primary);
}
.header-section {
  margin-bottom: 24px;
}
.title { color: var(--el-text-color-secondary); font-size: 13px; font-weight: 500; }
.amount {
  font-size: 36px;
  font-weight: 800;
  margin: 10px 0 0;
  background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-family: var(--font-sans);
  letter-spacing: -1px;
}
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.card-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
  padding: 12px 16px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.3s ease;
}
.bg-glow-up {
  background: linear-gradient(135deg, rgba(244, 63, 94, 0.03) 0%, rgba(255, 255, 255, 0.02) 100%);
  border-color: rgba(244, 63, 94, 0.08);
}
.bg-glow-down {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.03) 0%, rgba(255, 255, 255, 0.02) 100%);
  border-color: rgba(16, 185, 129, 0.08);
}
.label { font-size: 12px; color: var(--el-text-color-secondary); font-weight: 500; }
.val { font-size: 18px; font-weight: 700; font-family: var(--font-sans); color: var(--el-text-color-primary); }
.rate { font-size: 12px; font-weight: 600; margin-left: 2px; }
</style>
