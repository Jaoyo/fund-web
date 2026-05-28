<template>
  <el-card shadow="hover" class="holding-card" :class="{ 'is-clickable': !isSorting, 'is-sorting': isSorting }" @click="goDetail">
    <div class="row top">
      <div class="name-container">
        <span class="name">{{ position.fund_name }}</span>
        <span class="code font-number">{{ position.fund_code }}</span>
        <el-tag 
          v-if="!position.is_estimated" 
          size="small" 
          type="success" 
          effect="plain" 
          round 
          style="margin-left: 6px; padding: 0 4px; height: 18px; line-height: 16px; font-size: 10px; border-color: rgba(14, 203, 129, 0.3); color: #0ecb81; background: rgba(14, 203, 129, 0.1);"
        >
          已更新
        </el-tag>
      </div>
      <el-icon v-if="isSorting" class="drag-handle"><Rank /></el-icon>
      <el-icon v-else class="arrow-icon"><ArrowRight /></el-icon>
    </div>
    <div class="row metrics">
      <div class="metric-item">
        <div class="label">当前市值</div>
        <div class="value market-val font-number">¥{{ formatMoney(position.market_value) }}</div>
      </div>
      <div class="metric-item">
        <div class="label">累计收益</div>
        <div class="value" :class="position.profit >= 0 ? 'profit-glow-up' : 'profit-glow-down'">
          {{ position.profit >= 0 ? '+' : '' }}{{ formatMoney(position.profit) }}
          <span class="rate">({{ formatPercent(position.profit_rate) }})</span>
        </div>
      </div>
      <div class="metric-item">
        <div class="label">{{ position.is_estimated ? '今日预估' : '今日收益' }}</div>
        <div v-if="position.today_profit !== null" class="value" :class="position.today_profit >= 0 ? 'profit-glow-up' : 'profit-glow-down'">
          {{ position.today_profit >= 0 ? '+' : '' }}{{ formatMoney(position.today_profit) }}
          <span class="rate">({{ formatPercent(position.today_profit_rate) }})</span>
        </div>
        <div v-else class="value muted">--</div>
      </div>
    </div>
    <div class="row footer">
      <span class="badge">份额: {{ formatMoney(position.shares, 2) }}</span>
      <span class="badge">均价: {{ formatMoney(position.avg_cost, 4) }}</span>
      <span class="badge">净值: {{ formatMoney(position.latest_nav, 4) }} ({{ position.latest_nav_date }})</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowRight, Rank } from '@element-plus/icons-vue'
import { formatMoney, formatPercent } from '@/utils/format'
import type { Position } from '@/types'

const props = defineProps<{ position: Position, isSorting?: boolean }>()
const router = useRouter()

function goDetail() {
  if (props.isSorting) return
  router.push(`/fund/${props.position.fund_code}`)
}
</script>

<style scoped>
.holding-card {
  margin-bottom: 16px;
  padding: 12px 16px;
  background-color: #1e2329 !important;
  border: 1px solid #2b3139 !important;
  transition: all 0.2s ease;
}
.holding-card.is-clickable {
  cursor: pointer;
}
.holding-card.is-clickable:hover {
  border-color: #707a8a !important;
}
.holding-card.is-sorting {
  cursor: grab;
  border-color: var(--el-color-primary) !important;
}
.holding-card.is-sorting:active {
  cursor: grabbing;
}
.row { display: flex; align-items: center; }
.top { justify-content: space-between; margin-bottom: 14px; }
.name-container { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.name { font-weight: 700; font-size: 18px; color: #ffffff; }
.code { color: #929aa5; font-size: 13px; }
.arrow-icon { color: #707a8a; opacity: 0.5; transition: transform 0.2s ease; }
.holding-card.is-clickable:hover .arrow-icon { transform: translateX(3px); opacity: 1; color: var(--el-color-primary); }
.drag-handle { color: #929aa5; font-size: 18px; cursor: grab; }

.metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.metric-item { display: flex; flex-direction: column; gap: 4px; }
.metrics .label { font-size: 13px; color: #707a8a; font-weight: 500; }
.metrics .value { font-size: 18px; font-weight: 700; }
.market-val { color: #ffffff; }
.rate { font-size: 12px; margin-left: 2px; font-weight: 600; }
.muted { color: #707a8a; font-weight: normal !important; }

.footer {
  margin-top: 16px; gap: 8px;
  border-top: 1px solid #20262d;
  padding-top: 12px;
  flex-wrap: wrap;
}
.badge {
  font-size: 12px;
  color: #eaecef;
  background: #2b3139;
  padding: 3px 8px;
  border-radius: 6px;
  font-family: var(--font-number);
  border: 1px solid #20262d;
}

/* 手机端响应式适配 */
@media (max-width: 768px) {
  .holding-card {
    padding: 8px 12px !important;
  }
  .name {
    font-size: 15px;
  }
  .metrics {
    gap: 8px;
  }
  .metrics .value {
    font-size: 14px;
  }
  .rate {
    font-size: 10px;
    margin-left: 1px;
  }
  .badge {
    font-size: 10px;
    padding: 2px 6px;
  }
  .footer {
    margin-top: 12px;
    padding-top: 10px;
    gap: 6px;
  }
}
</style>
