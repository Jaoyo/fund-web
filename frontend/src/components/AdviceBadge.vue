<template>
  <div class="advice-chip" :class="signal.level">
    <span class="indicator-dot"></span>
    <span class="title">{{ signal.name }}</span>
    <span class="divider"></span>
    <span class="message">{{ signal.message }}</span>
  </div>
</template>

<script setup lang="ts">
import type { AdviceSignal } from '@/types'

defineProps<{ signal: AdviceSignal }>()
</script>

<style scoped>
.advice-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 500;
  margin: 4px 8px 4px 0;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  display: inline-block;
}

.title {
  font-weight: 700;
  margin-right: 4px;
}

.divider {
  width: 1px;
  height: 10px;
  background: rgba(255, 255, 255, 0.12);
  margin-right: 6px;
}

.message {
  opacity: 0.9;
}

/* buy (买入建议 - 变更为绿色) */
.buy {
  background: rgba(14, 203, 129, 0.08) !important;
  color: #0ecb81 !important;
  border-color: rgba(14, 203, 129, 0.2) !important;
}
.buy .indicator-dot {
  background-color: #0ecb81;
  box-shadow: 0 0 6px #0ecb81;
}

/* sell (卖出建议 - 变更为红色) */
.sell {
  background: rgba(246, 70, 93, 0.08) !important;
  color: #f6465d !important;
  border-color: rgba(246, 70, 93, 0.2) !important;
}
.sell .indicator-dot {
  background-color: #f6465d;
  box-shadow: 0 0 6px #f6465d;
}

/* watch (预警关注 - 琥珀黄) */
.watch {
  background: rgba(245, 158, 11, 0.08) !important;
  color: #fbbf24 !important;
  border-color: rgba(245, 158, 11, 0.2) !important;
}
.watch .indicator-dot {
  background-color: #f59e0b;
  box-shadow: 0 0 6px #f59e0b;
}

/* info (中性持有 - 灰蓝) */
.info {
  background: rgba(148, 163, 184, 0.08) !important;
  color: #eaecef !important;
  border-color: rgba(148, 163, 184, 0.15) !important;
}
.info .indicator-dot {
  background-color: #929aa5;
}
</style>
