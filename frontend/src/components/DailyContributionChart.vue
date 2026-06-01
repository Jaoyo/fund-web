<template>
  <el-card class="daily-contribution-chart-card" shadow="hover">
    <div class="chart-header">
      <span class="title">今日收益贡献度</span>
    </div>
    <div class="chart-container" :style="{ height: chartHeight + 'px' }">
      <v-chart class="chart" :option="chartOption" autoresize />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import type { Position } from '@/types'

use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  TooltipComponent,
  TitleComponent
])

const props = defineProps<{
  positions: Position[]
}>()

// Filter and sort the positions
const chartData = computed(() => {
  // 过滤掉没有 today_profit 或者 today_profit 为 0 的记录（如果有需要的话，0 也可以保留）
  // 这里为了展示所有的有收益数据的基金，只过滤掉 null
  const validPositions = props.positions.filter(p => p.today_profit !== null && p.today_profit !== 0)
  
  // 按今日收益降序排序（从大到小）
  // 因为 ECharts 横向柱状图默认是从下往上画，所以为了让盈利最多的在最上面，
  // 我们可以通过设置 yAxis.inverse = true 来实现，这里保持降序。
  return [...validPositions].sort((a, b) => (b.today_profit || 0) - (a.today_profit || 0))
})

const chartHeight = computed(() => {
  const minHeight = 240
  const itemHeight = 35 // 每条柱子的高度空间
  const calculated = chartData.value.length * itemHeight + 60 // 基础高度
  return Math.max(minHeight, calculated)
})

const chartOption = computed(() => {
  const data = chartData.value
  const names = data.map(p => p.fund_name)
  const profits = data.map(p => ({
    value: p.today_profit,
    label: {
      position: (p.today_profit || 0) >= 0 ? 'right' : 'left'
    }
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e2329',
      textStyle: { color: '#eaecef', fontSize: 12 },
      borderColor: '#2b3139',
      borderWidth: 1,
      extraCssText: 'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); border-radius: 4px;',
      formatter: (params: any) => {
        const item = params[0]
        const val = item.value
        const color = val >= 0 ? '#f6465d' : '#0ecb81' // 红涨绿跌
        const sign = val > 0 ? '+' : ''
        return `
          <div style="font-size: 12px; color: #929aa5; margin-bottom: 4px;">${item.name}</div>
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
            <span style="color: #929aa5; display: flex; align-items: center; gap: 4px;">
              ${item.marker} 今日收益:
            </span>
            <span style="color: ${color}; font-weight: bold; font-family: monospace;">
              ${sign}${val.toFixed(2)}
            </span>
          </div>
        `
      }
    },
    grid: {
      left: '2%',
      right: '10%',
      bottom: '2%',
      top: '15px',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: { color: '#20262d', type: 'dashed' }
      },
      axisLabel: { color: '#707a8a', fontSize: 10 }
    },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true, // 让最大的在上面
      axisLine: {
        lineStyle: { color: '#2b3139' }
      },
      axisTick: { show: false },
      axisLabel: {
        color: '#929aa5',
        fontSize: 11,
        margin: 12,
        formatter: (value: string) => {
          return value.length > 8 ? value.slice(0, 8) + '...' : value
        }
      }
    },
    series: [
      {
        name: '今日收益',
        type: 'bar',
        data: profits,
        barMaxWidth: 16,
        label: {
          show: true,
          formatter: (params: any) => {
            const val = params.value
            return val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)
          },
          fontSize: 10,
          color: '#eaecef',
          distance: 5
        },
        itemStyle: {
          color: (params: any) => {
            return params.value >= 0 ? '#f6465d' : '#0ecb81' // 红涨绿跌
          },
          borderRadius: (params: any) => {
            return params.value >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4]
          }
        }
      }
    ]
  }
})
</script>

<style scoped>
.daily-contribution-chart-card {
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
  width: 100%;
}
.chart {
  height: 100%;
  width: 100%;
}

@media (max-width: 768px) {
  .daily-contribution-chart-card {
    padding: 12px 8px !important;
    margin-bottom: 16px;
  }
}
</style>
