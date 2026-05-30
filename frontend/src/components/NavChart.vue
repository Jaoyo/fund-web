<template>
  <div ref="chartRef" class="nav-chart"></div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import * as echarts from 'echarts/core'
import type { NavRecord } from '@/types'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps<{ records: NavRecord[] }>()
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!chart) return
  const asc = [...props.records].sort((a, b) => a.date.localeCompare(b.date))
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { top: 15, right: 5, bottom: 20, left: 40 },
    xAxis: {
      type: 'category',
      data: asc.map((r) => r.date),
      axisLine: { lineStyle: { color: '#2b3139' } },
      axisTick: { show: false },
      axisLabel: { color: '#707a8a', fontSize: 9, fontFamily: 'var(--font-sans)' },
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#20262d' } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#707a8a', fontSize: 9, fontFamily: 'var(--font-number)' },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e2329',
      borderColor: '#2b3139',
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: '#eaecef', fontSize: 12, fontFamily: 'var(--font-sans)' },
      extraCssText: 'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); border-radius: 4px;',
      formatter: (params: any) => {
        const item = params[0]
        return `
          <div style="font-size: 11px; color: #929aa5; margin-bottom: 4px;">${item.name}</div>
          <div style="font-weight: 700; color: #ffffff; font-size: 13px; display: flex; align-items: center; justify-content: space-between; gap: 8px;">
            <span>净值:</span> <span style="color: #2dbdb6; font-family: monospace;">${parseFloat(item.value).toFixed(4)}</span>
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
          width: 2.5,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#2dbdb6' },
            { offset: 1, color: '#3b82f6' },
          ]),
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(45, 189, 182, 0.15)' },
            { offset: 1, color: 'rgba(45, 189, 182, 0.0)' },
          ]),
        },
        itemStyle: {
          color: '#2dbdb6',
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
.nav-chart { width: 100%; height: 300px; }

@media (max-width: 768px) {
  .nav-chart {
    height: 200px; /* 移动端高度调整为 200px 更加精致 */
  }
}
</style>
