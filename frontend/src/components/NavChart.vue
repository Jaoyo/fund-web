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
    backgroundColor: 'transparent',
    grid: { top: 20, right: 10, bottom: 25, left: 45 },
    xAxis: {
      type: 'category',
      data: asc.map((r) => r.date),
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', fontSize: 10, fontFamily: 'Inter' },
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.04)' } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', fontSize: 10, fontFamily: 'Inter' },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 22, 40, 0.85)',
      borderColor: 'rgba(255, 255, 255, 0.08)',
      borderWidth: 1,
      padding: [10, 14],
      textStyle: { color: '#cbd5e1', fontSize: 12, fontFamily: 'Inter' },
      extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5)',
      formatter: (params: any) => {
        const item = params[0]
        return `
          <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">${item.name}</div>
          <div style="font-weight: 700; color: #f8fafc; font-size: 14px;">
            净值: <span style="color: #60a5fa;">${parseFloat(item.value).toFixed(4)}</span>
          </div>
        `
      }
    },
    series: [
      {
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: asc.map((r) => r.nav),
        lineStyle: {
          width: 3,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#6366f1' },
            { offset: 1, color: '#3b82f6' },
          ]),
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.22)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.0)' },
          ]),
        },
        itemStyle: {
          color: '#3b82f6',
        },
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
