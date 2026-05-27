<template>
  <el-card class="profit-chart-card" shadow="hover">
    <div class="chart-header">
      <span class="title">近 30 天每日收益走势</span>
    </div>
    <div class="chart-container">
      <v-chart class="chart" :option="chartOption" autoresize />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import type { HoldingHistory } from '@/types'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent
])

const props = defineProps<{
  data: HoldingHistory[]
}>()

const chartOption = computed(() => {
  const dates = props.data.map(item => item.date.slice(5)) // MM-DD
  const profits = props.data.map(item => item.profit)
  const cumulativeProfits = props.data.map(item => item.cumulative_profit)

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      textStyle: { color: '#333' },
      borderColor: '#e5e7eb',
      borderWidth: 1,
      formatter: (params: any) => {
        let res = `<div style="font-size: 13px; font-weight: 500; margin-bottom: 4px;">${props.data[params[0].dataIndex].date}</div>`
        params.forEach((item: any) => {
          const val = item.value
          const color = val >= 0 ? '#ef4444' : '#22c55e'
          const sign = val >= 0 ? '+' : ''
          res += `<div style="margin-top: 4px; color: #6b7280; font-size: 12px; display: flex; align-items: center;">
                    ${item.marker} <span style="margin-right: 8px;">${item.seriesName}:</span> 
                    <span style="color: ${color}; font-weight: bold; font-size: 13px;">${sign}${val.toFixed(2)}</span>
                  </div>`
        })
        return res
      }
    },
    legend: {
      data: ['每日收益', '累计收益'],
      textStyle: { color: 'var(--el-text-color-regular)' },
      top: 0
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '3%',
      top: '30px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: {
        lineStyle: {
          color: 'rgba(150, 150, 150, 0.3)'
        }
      },
      axisLabel: {
        color: 'rgba(150, 150, 150, 0.8)',
        fontSize: 10
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '每日',
        nameTextStyle: { color: 'rgba(150, 150, 150, 0.8)', fontSize: 10 },
        splitLine: {
          lineStyle: { color: 'rgba(150, 150, 150, 0.15)', type: 'dashed' }
        },
        axisLabel: { color: 'rgba(150, 150, 150, 0.8)', fontSize: 10 }
      },
      {
        type: 'value',
        name: '累计',
        nameTextStyle: { color: 'rgba(150, 150, 150, 0.8)', fontSize: 10 },
        splitLine: { show: false },
        axisLabel: { color: 'rgba(150, 150, 150, 0.8)', fontSize: 10 }
      }
    ],
    series: [
      {
        name: '每日收益',
        data: profits,
        type: 'bar',
        yAxisIndex: 0,
        barMaxWidth: 40, // 限制单根柱子的最大宽度，防止数据太少时过粗
        itemStyle: {
          color: (params: any) => {
            return params.value >= 0 ? '#ff4d4f' : '#52c41a'
          },
          borderRadius: [2, 2, 0, 0]
        }
      },
      {
        name: '累计收益',
        data: cumulativeProfits,
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#3b82f6' },
        itemStyle: { color: '#3b82f6' }
      }
    ]
  }
})
</script>

<style scoped>
.profit-chart-card {
  margin-bottom: 24px;
  border-radius: 12px;
  border: none;
}
.chart-header {
  margin-bottom: 12px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.chart-container {
  height: 250px;
  width: 100%;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
