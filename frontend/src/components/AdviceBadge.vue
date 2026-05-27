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
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  margin: 4px 8px 4px 0;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 8px;
  display: inline-block;
}

.title {
  font-weight: 700;
  margin-right: 6px;
}

.divider {
  width: 1px;
  height: 10px;
  background: rgba(255, 255, 255, 0.15);
  margin-right: 6px;
}

.message {
  opacity: 0.9;
}

/* buy (买入建议 - 翠绿) */
.buy {
  background: rgba(16, 185, 129, 0.1) !important;
  color: #34d399 !important;
  border-color: rgba(16, 185, 129, 0.25) !important;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.05);
}
.buy .indicator-dot {
  background-color: #10b981;
  box-shadow: 0 0 8px #10b981;
}

/* sell (卖出建议 - 珊瑚粉红) */
.sell {
  background: rgba(244, 63, 94, 0.1) !important;
  color: #fb7185 !important;
  border-color: rgba(244, 63, 94, 0.25) !important;
  box-shadow: 0 0 10px rgba(244, 63, 94, 0.05);
}
.sell .indicator-dot {
  background-color: #f43f5e;
  box-shadow: 0 0 8px #f43f5e;
}

/* watch (预警关注 - 琥珀黄) */
.watch {
  background: rgba(245, 158, 11, 0.1) !important;
  color: #fbbf24 !important;
  border-color: rgba(245, 158, 11, 0.25) !important;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.05);
}
.watch .indicator-dot {
  background-color: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
}

/* info (中性持有 - 灰蓝) */
.info {
  background: rgba(148, 163, 184, 0.08) !important;
  color: #cbd5e1 !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
}
.info .indicator-dot {
  background-color: #94a3b8;
}
</style>
