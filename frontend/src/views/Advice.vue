<template>
  <div class="advice-page" v-loading="loading">
    <div class="header">
      <div class="title-section">
        <h3>智能投资策略建议</h3>
        <span class="desc">基于历史分位、{{ days >= 250 ? '250日' : days + '日' }}均线偏离度及持仓盈亏自动运算</span>
      </div>
      <div class="actions-section">
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
    <el-empty v-if="!loading && list.length === 0" description="暂无策略建议，请先录入基金交易流水" />
    
    <el-card v-for="item in list" :key="item.fund_code" class="advice-card" shadow="hover">
      <div class="card-top">
        <div class="card-header" @click="$router.push(`/fund/${item.fund_code}`)">
          <span class="name">{{ item.fund_name }}</span>
          <span class="code font-number">{{ item.fund_code }}</span>
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
import { onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { adviceApi } from '@/api/advice'
import { formatPercent } from '@/utils/format'
import AdviceBadge from '@/components/AdviceBadge.vue'
import type { FundAdvice } from '@/types'

const list = ref<FundAdvice[]>([])
const loading = ref(false)
const days = ref(750)

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
  // 红涨绿跌偏离度颜色
  return dev >= 0.15 ? 'profit-glow-down' : (dev <= -0.10 ? 'profit-glow-up' : '')
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
.actions-section {
  display: flex;
  gap: 12px;
  align-items: center;
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
/* 红涨绿跌渐变条：低位买为红(#f6465d)，高位卖为绿(#0ecb81) */
.indicator-bar-bg {
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, #f6465d 0%, rgba(255,255,255,0.12) 50%, #0ecb81 100%);
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
.buy-label { color: #f6465d; }
.sell-label { color: #0ecb81; }

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
