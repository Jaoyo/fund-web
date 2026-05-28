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
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e2329',
      textStyle: { color: '#eaecef', fontSize: 12 },
      borderColor: '#2b3139',
      borderWidth: 1,
      extraCssText: 'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); border-radius: 4px;',
      formatter: (params: any) => {
        let res = `<div style="font-size: 12px; color: #929aa5; margin-bottom: 4px; font-family: monospace;">${props.data[params[0].dataIndex].date}</div>`
        params.forEach((item: any) => {
          const val = item.value
          const color = val >= 0 ? '#f6465d' : '#0ecb81' // 红涨绿跌
          const sign = val >= 0 ? '+' : ''
          res += `<div style="margin-top: 4px; font-size: 12px; display: flex; align-items: center; justify-content: space-between; gap: 12px;">
                    <span style="color: #929aa5; display: flex; align-items: center; gap: 4px;">${item.marker} ${item.seriesName}:</span> 
                    <span style="color: ${color}; font-weight: bold; font-family: monospace;">${sign}${val.toFixed(2)}</span>
                  </div>`
        })
        return res
      }
    },
    legend: {
      data: ['每日收益', '累计收益'],
      textStyle: { color: '#929aa5', fontSize: 11 },
      top: 0,
      right: 'center'
    },
    grid: {
      left: '2%',
      right: '2%',
      bottom: '2%',
      top: '35px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: {
        lineStyle: {
          color: '#2b3139'
        }
      },
      axisLabel: {
        color: '#707a8a',
        fontSize: 10
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '每日',
        nameTextStyle: { color: '#707a8a', fontSize: 9 },
        splitLine: {
          lineStyle: { color: '#20262d', type: 'dashed' }
        },
        axisLabel: { color: '#707a8a', fontSize: 9 }
      },
      {
        type: 'value',
        name: '累计',
        nameTextStyle: { color: '#707a8a', fontSize: 9 },
        splitLine: { show: false },
        axisLabel: { color: '#707a8a', fontSize: 9 }
      }
    ],
    series: [
      {
        name: '每日收益',
        data: profits,
        type: 'bar',
        yAxisIndex: 0,
        barMaxWidth: 16, 
        itemStyle: {
          color: (params: any) => {
            return params.value >= 0 ? '#f6465d' : '#0ecb81' // 红涨绿跌
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
        lineStyle: { width: 2.5, color: '#fcd535' }, // 币安黄折线
        itemStyle: { color: '#fcd535' }
      }
    ]
  }
})
</script>

<style scoped>
.profit-chart-card {
  margin-bottom: 24px;
  border-radius: 8px;
  border: 1px solid #2b3139 !important;
  background-color: #1e2329 !important;
  box-shadow: none !important;
}
.chart-header {
  margin-bottom: 16px;
}
.title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}
.chart-container {
  height: 240px;
  width: 100%;
}
.chart {
  height: 100%;
  width: 100%;
}

@media (max-width: 768px) {
  .profit-chart-card {
    padding: 12px 8px !important;
    margin-bottom: 16px;
  }
  .chart-container {
    height: 200px;
  }
}
</style>
