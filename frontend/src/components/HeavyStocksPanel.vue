<template>
  <el-card class="heavy-stocks-panel" shadow="hover">
    <template #header>
      <div class="header">
        <span class="title">穿透重仓股</span>
        <el-button 
          v-if="!store.heavyStocksLoading && store.heavyStocks.length > 0" 
          type="primary" 
          link 
          @click="store.loadHeavyStocks()"
        >
          刷新
        </el-button>
      </div>
    </template>
    
    <div v-if="store.heavyStocksLoading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>
    <div v-else-if="store.heavyStocks.length === 0" class="empty-container">
      <el-empty description="暂无重仓股数据" :image-size="80">
        <el-button type="primary" size="small" @click="store.loadHeavyStocks()">获取数据</el-button>
      </el-empty>
    </div>
    <div v-else class="stocks-list">
      <div class="list-header">
        <span class="col-name">股票名称</span>
        <span class="col-value">等效市值</span>
        <span class="col-prop">持仓占比</span>
      </div>
      <div v-for="(stock, index) in store.heavyStocks" :key="stock.stock_code" class="stock-item">
        <div class="col-name">
          <span class="index" :class="{'top-3': index < 3}">{{ index + 1 }}</span>
          <div class="name-info">
            <div class="name-row">
              <span class="name" :title="stock.stock_name">{{ stock.stock_name }}</span>
              <el-popover placement="right" :width="300" trigger="hover" v-if="stock.contributing_funds?.length > 0">
                <template #reference>
                  <span class="source-badge pc-only" :class="{'single-fund': stock.contributing_funds.length === 1}">
                    {{ stock.contributing_funds.length === 1 ? stock.contributing_funds[0].fund_name : `${stock.contributing_funds.length}只基金` }}
                  </span>
                </template>
                <div class="contrib-list">
                  <div class="contrib-title">资金来源明细</div>
                  <div v-for="f in stock.contributing_funds" :key="f.fund_code" class="contrib-item">
                    <span class="c-name" :title="f.fund_name">{{ f.fund_name }}</span>
                    <span class="c-val">¥{{ f.market_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</span>
                  </div>
                </div>
              </el-popover>
            </div>
            <div class="code-row">
              <span class="code">{{ stock.stock_code }}</span>
              <el-popover placement="bottom-start" :width="280" trigger="click" v-if="stock.contributing_funds?.length > 0">
                <template #reference>
                  <span class="source-badge mobile-only">
                    {{ stock.contributing_funds.length }}只
                  </span>
                </template>
                <div class="contrib-list">
                  <div class="contrib-title">资金来源明细</div>
                  <div v-for="f in stock.contributing_funds" :key="f.fund_code" class="contrib-item">
                    <span class="c-name" :title="f.fund_name">{{ f.fund_name }}</span>
                    <span class="c-val">¥{{ f.market_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</span>
                  </div>
                </div>
              </el-popover>
            </div>
          </div>
        </div>
        <div class="col-value">¥{{ stock.total_market_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</div>
        <div class="col-prop">
          <span class="prop-text">{{ stock.proportion.toFixed(2) }}%</span>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: Math.min(stock.proportion, 100) + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useHoldingsStore } from '@/stores/holdings'

const store = useHoldingsStore()

onMounted(() => {
  if (store.heavyStocks.length === 0 && !store.heavyStocksLoading) {
    store.loadHeavyStocks()
  }
})
</script>

<style scoped>
.heavy-stocks-panel {
  margin-top: 16px;
  background-color: var(--el-bg-color-overlay);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-weight: 600;
  font-size: 16px;
}

.loading-container {
  padding: 20px;
}

.empty-container {
  padding: 20px 0;
}

.stocks-list {
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  padding: 8px 16px;
  background-color: var(--el-fill-color-light);
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.stock-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background-color 0.2s;
}

.stock-item:last-child {
  border-bottom: none;
}

.stock-item:hover {
  background-color: var(--el-fill-color-light);
}

.col-name {
  flex: 2;
  display: flex;
  align-items: center;
  min-width: 0;
}

.col-value {
  flex: 1.5;
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 14px;
  font-weight: 500;
}

.col-prop {
  flex: 1.5;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  background-color: var(--el-fill-color-darker);
  color: var(--el-text-color-regular);
  font-size: 12px;
  font-weight: 600;
  margin-right: 12px;
  flex-shrink: 0;
}

.index.top-3 {
  background-color: var(--el-color-primary-light-3);
  color: #fff;
}

.name-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.name-row, .code-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.code {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.source-badge {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  background-color: var(--el-fill-color);
  padding: 1px 6px;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  border: 1px solid var(--el-border-color-lighter);
  line-height: 1.4;
}

.source-badge.single-fund {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-badge:hover {
  background-color: var(--el-fill-color-dark);
  color: var(--el-text-color-regular);
}

.pc-only {
  display: inline-flex;
}

.mobile-only {
  display: none;
}

.contrib-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--el-text-color-regular);
  padding-bottom: 6px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.contrib-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.contrib-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  gap: 12px;
}

.c-name {
  flex: 1;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.c-val {
  font-weight: 600;
  color: var(--el-text-color-regular);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.prop-text {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  width: 48px;
  text-align: right;
}

.progress-bar-bg {
  width: 60px;
  height: 6px;
  background-color: var(--el-fill-color-dark);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: var(--el-color-primary);
  border-radius: 3px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .pc-only {
    display: none;
  }
  .mobile-only {
    display: inline-flex;
  }
  .name-row, .code-row {
    gap: 4px;
  }
  .source-badge {
    font-size: 10px;
    padding: 0 4px;
    border-radius: 4px;
  }
  .col-prop {
    flex-direction: column;
    align-items: flex-end;
    justify-content: center;
    gap: 4px;
  }
  .prop-text {
    width: auto;
    font-size: 12px;
  }
  .progress-bar-bg {
    width: 48px;
  }
}
</style>
