<template>
  <div class="advice-page">
    <div class="header">
      <h3>智能建议</h3>
      <el-button size="small" :loading="loading" @click="load">刷新</el-button>
    </div>
    <el-empty v-if="!loading && list.length === 0" description="暂无建议（先去录入持仓）" />
    <el-card v-for="item in list" :key="item.fund_code" class="advice-card">
      <div class="card-header" @click="$router.push(`/fund/${item.fund_code}`)">
        <span class="name">{{ item.fund_name }}</span>
        <span class="code">{{ item.fund_code }}</span>
      </div>
      <div class="metrics">
        <span v-if="item.percentile !== null">
          历史分位 <b>{{ formatPercent(item.percentile) }}</b>
        </span>
        <span v-if="item.ma_deviation !== null">
          均线偏离 <b>{{ formatPercent(item.ma_deviation) }}</b>
        </span>
        <span v-if="item.max_drawdown !== null">
          最大回撤 <b>{{ formatPercent(item.max_drawdown) }}</b>
        </span>
        <span v-if="item.profit_rate !== null">
          收益率 <b>{{ formatPercent(item.profit_rate) }}</b>
        </span>
      </div>
      <div class="signals">
        <AdviceBadge v-for="(s, i) in item.signals" :key="i" :signal="s" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { adviceApi } from '@/api/advice'
import { formatPercent } from '@/utils/format'
import AdviceBadge from '@/components/AdviceBadge.vue'
import type { FundAdvice } from '@/types'

const list = ref<FundAdvice[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    list.value = await adviceApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.advice-page { max-width: 960px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.advice-card { margin-bottom: 12px; }
.card-header {
  display: flex; gap: 12px; align-items: baseline; cursor: pointer; margin-bottom: 8px;
}
.name { font-weight: 600; font-size: 16px; }
.code { color: var(--el-text-color-secondary); font-size: 13px; }
.metrics {
  display: flex; gap: 24px; flex-wrap: wrap;
  font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 8px;
}
.metrics b { color: var(--el-text-color-primary); }
.signals { display: flex; flex-wrap: wrap; }
</style>
