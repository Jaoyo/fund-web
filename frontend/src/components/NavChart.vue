<template>
  <div ref="chartRef" class="nav-chart"></div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { NavRecord } from '@/types'

const props = defineProps<{ records: NavRecord[] }>()
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!chart) return
  const asc = [...props.records].sort((a, b) => a.date.localeCompare(b.date))
  chart.setOption({
    grid: { top: 20, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: asc.map((r) => r.date) },
    yAxis: { type: 'value', scale: true },
    tooltip: { trigger: 'axis' },
    series: [
      {
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: asc.map((r) => r.nav),
        lineStyle: { width: 2 },
      },
    ],
  })
}

function handleResize() { chart?.resize() }

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    render()
    window.addEventListener('resize', handleResize)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

watch(() => props.records, render, { deep: true })
</script>

<style scoped>
.nav-chart { width: 100%; height: 320px; }
</style>
