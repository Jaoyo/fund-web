<template>
  <el-card class="profit-summary-card">
    <div class="header-section">
      <div class="title-row">
        <div class="title">总资产市值 (元)</div>
      </div>
      <div class="amount-row">
        <div class="amount font-number">¥{{ formatMoney(summary.total_market_value) }}</div>
        <!-- 移动端：成本内联在总资产右侧 -->
        <div class="cost-inline">
          <div class="cost-label">投入成本</div>
          <div class="cost-val font-number">¥{{ formatMoney(summary.total_cost) }}</div>
        </div>
      </div>
    </div>
    <!-- 桌面端：三列网格（成本 + 累计收益 + 今日收益） -->
    <div class="grid desktop-grid">
      <div class="card-panel">
        <div class="label">累计投入成本</div>
        <div class="val font-number">¥{{ formatMoney(summary.total_cost) }}</div>
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
    <!-- 移动端：两列网格（累计收益 + 今日收益） -->
    <div class="grid mobile-grid">
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
  </el-card>
</template>

<script setup lang="ts">
import { formatMoney, formatPercent } from '@/utils/format'
import type { HoldingsSummary } from '@/types'

defineProps<{ 
  summary: HoldingsSummary
}>()
</script>

<style scoped>
.profit-summary-card {
  padding: 20px 24px;
  margin-bottom: 24px;
  background-color: #1e2329 !important;
  border: 1px solid #2b3139 !important;
  position: relative;
}
.header-section {
  margin-bottom: 20px;
}
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title { color: #929aa5; font-size: 13px; font-weight: 500; }

/* 总资产行 */
.amount-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.amount {
  font-size: 36px;
  font-weight: 700;
  margin: 8px 0 0;
  color: #ffffff;
  letter-spacing: -0.5px;
}
/* 移动端内联成本 - 桌面端隐藏 */
.cost-inline {
  display: none;
}
.cost-label {
  font-size: 11px;
  color: #707a8a;
  font-weight: 500;
  text-align: right;
}
.cost-val {
  font-size: 15px;
  font-weight: 600;
  color: #929aa5;
  text-align: right;
}

/* 桌面端三列网格 */
.desktop-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
/* 移动端两列网格 - 桌面端隐藏 */
.mobile-grid { display: none; }

.card-panel {
  background: #2b3139;
  border: 1px solid #20262d;
  padding: 14px 16px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.2s ease;
}
/* 红涨绿跌背景微发光 */
.bg-glow-up {
  background: rgba(246, 70, 93, 0.03) !important;
  border-color: rgba(246, 70, 93, 0.15) !important;
}
.bg-glow-down {
  background: rgba(14, 203, 129, 0.03) !important;
  border-color: rgba(14, 203, 129, 0.15) !important;
}
.label { font-size: 12px; color: #929aa5; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.val { font-size: 16px; font-weight: 700; color: #eaecef; }
.rate { font-size: 10px; font-weight: 600; display: block; margin-top: 2px; margin-left: 0; }

/* 手机端响应式适配 */
@media (max-width: 768px) {
  .profit-summary-card {
    padding: 16px !important;
  }
  .amount {
    font-size: 28px;
  }
  /* 显示内联成本，隐藏桌面网格，显示移动网格 */
  .cost-inline {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: 8px;
  }
  .desktop-grid {
    display: none;
  }
  .mobile-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .card-panel {
    padding: 12px;
  }
  .val {
    font-size: 15px;
  }
}
</style>

