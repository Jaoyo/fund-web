<template>
  <div class="tx-page">
    <el-card class="form-card">
      <div class="card-title">录入交易记录</div>
      <el-form :model="form" label-width="80px" @submit.prevent="submit" label-position="left">
        <el-row :gutter="16">
          <el-col :span="8" :xs="24">
            <el-form-item label="基金代码">
              <el-input v-model="form.fund_code" placeholder="6 位代码，如 001753" @blur="fetchQuote" />
            </el-form-item>
          </el-col>
          <el-col :span="8" :xs="24">
            <el-form-item label="交易日期">
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8" :xs="24">
            <el-form-item label="交易类型">
              <el-radio-group v-model="form.type" class="type-radio-group">
                <el-radio-button value="buy">买入</el-radio-button>
                <el-radio-button value="sell">卖出</el-radio-button>
                <el-radio-button value="import">导入持仓</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <template v-if="form.type !== 'import'">
            <el-col :span="8" :xs="24" v-if="form.type === 'buy'">
              <el-form-item label="交易金额">
                <el-input-number v-model="form.amount" :precision="2" :step="100" :min="0" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="8" :xs="24" v-if="form.type === 'sell'">
              <el-form-item label="确认份额">
                <el-input-number v-model="form.shares" :precision="2" :step="100" :min="0" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="8" :xs="24">
              <el-form-item label="手续费用">
                <el-input-number v-model="form.fee" :precision="2" :step="1" :min="0" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="8" :xs="24">
              <el-form-item label="交易确认">
                <el-radio-group v-model="form.settlement_days" class="type-radio-group">
                  <el-radio-button :value="1">T+1</el-radio-button>
                  <el-radio-button :value="2">T+2</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </template>
          <template v-else>
            <el-col :span="8" :xs="24">
              <el-form-item label="持有金额">
                <el-input-number v-model="form.amount" :precision="2" :step="100" :min="0" placeholder="当前持仓市值" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="8" :xs="24">
              <el-form-item label="累计收益">
                <el-input-number v-model="form.profit" :precision="2" :step="100" placeholder="持仓累计收益(亏损填负)" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="8" :xs="24">
              <el-form-item label="基金名称">
                <el-input v-model="form.fund_name" placeholder="可选，自定义基金名称" />
              </el-form-item>
            </el-col>
          </template>
        </el-row>
        
        <div v-if="fundInfo" class="quote-info">
          <div style="font-size: 14px; margin-bottom: 2px; color: #eaecef;">
            基金名称：<strong style="color: #ffffff;">{{ fundInfo.name }}</strong>
            <span style="margin-left: 8px; color: #707a8a; font-size: 12px;">({{ fundInfo.code }})</span>
          </div>
          <div v-if="quoteInfo && form.type !== 'import'" style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed #3b424c;">
            <span>实时预估净值：<strong :class="quoteInfo.estimated_growth && quoteInfo.estimated_growth > 0 ? 'text-red font-number' : 'text-green font-number'">{{ quoteInfo.estimated_nav?.toFixed(4) || '-' }}</strong></span>
            <span style="margin-left: 16px;">预估涨跌：<strong :class="quoteInfo.estimated_growth && quoteInfo.estimated_growth > 0 ? 'text-red font-number' : 'text-green font-number'">{{ quoteInfo.estimated_growth !== null && quoteInfo.estimated_growth !== undefined ? (quoteInfo.estimated_growth > 0 ? '+' : '') + quoteInfo.estimated_growth.toFixed(2) + '%' : '-' }}</strong></span>
            <span class="update-time">更新时间: {{ quoteInfo.estimated_time || '-' }}</span>
          </div>
        </div>
        <el-form-item label="交易备注">
          <el-input v-model="form.note" placeholder="选填，如：定投、止盈、低估买入等" />
        </el-form-item>
        <div class="form-actions">
          <el-button type="primary" :loading="submitting" @click="submit" class="save-btn">保存交易</el-button>
          <span class="hint">{{ form.type === 'import' ? '根据最新估值/净值自动换算持仓均价与剩余份额并导入旧持仓。' : '盘中录入自动列为待确认，晚间净值更新后自动计算补全。' }}</span>
        </div>
      </el-form>
    </el-card>

    <el-card class="list-card">
      <div class="card-title list-header">
        <span>交易历史流水</span>
        <el-button type="primary" link @click="syncPending" :loading="syncing">
          <el-icon style="margin-right: 4px;"><RefreshRight /></el-icon>
          同步待确认订单
        </el-button>
      </div>
      <el-table :data="list" stripe style="width: 100%">
        <el-table-column prop="date" label="交易日期" min-width="100" class-name="font-number" />
        <el-table-column prop="fund_code" label="基金代码" min-width="90" class-name="font-number" />
        <el-table-column label="交易类型" min-width="80">
          <template #default="{ row }">
            <span :class="row.type === 'sell' ? 'type-sell' : (row.type === 'import' ? 'type-import' : 'type-buy')">
              {{ row.type === 'import' ? '导入' : (row.type === 'buy' ? '买入' : '卖出') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="nav" label="成交净值" min-width="90" class-name="font-number">
          <template #default="{ row }">
            <span v-if="row.nav > 0">{{ row.nav.toFixed(4) }}</span>
            <el-tag v-else size="small" type="warning" effect="plain" style="border-color: rgba(245, 158, 11, 0.3); color: #fbbf24; background: rgba(245, 158, 11, 0.1);">待确认</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="shares" label="确认份额" min-width="100" class-name="font-number">
          <template #default="{ row }">
            {{ row.nav > 0 ? row.shares.toFixed(2) : (row.type in ['buy', 'import'] ? '-' : row.shares?.toFixed(2) || '-') }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="交易金额" min-width="100" class-name="font-number">
          <template #default="{ row }">
            {{ row.nav > 0 ? '¥' + row.amount.toFixed(2) : (row.type === 'sell' ? '-' : '¥' + (row.amount?.toFixed(2) || '-')) }}
          </template>
        </el-table-column>
        <el-table-column v-if="!isMobile" prop="fee" label="交易费用" min-width="80" class-name="font-number" />
        <el-table-column v-if="!isMobile" prop="note" label="备注" show-overflow-tooltip min-width="120" />
        <el-table-column label="操作" width="70" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="remove(row.id)" class="delete-btn">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { transactionsApi } from '@/api/holdings'
import { fundsApi } from '@/api/funds'
import { useHoldingsStore } from '@/stores/holdings'
import type { Transaction, TransactionIn, Quote, Fund } from '@/types'

const form = reactive<TransactionIn & { fee: number }>({
  fund_code: '',
  date: dayjs().format('YYYY-MM-DD'),
  type: 'buy',
  amount: undefined,
  shares: undefined,
  profit: undefined,
  fund_name: '',
  fee: 0,
  settlement_days: 1,
  note: '',
})

const list = ref<Transaction[]>([])
const submitting = ref(false)
const syncing = ref(false)
const fundInfo = ref<Fund | null>(null)
const quoteInfo = ref<Quote | null>(null)
const store = useHoldingsStore()

const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

async function fetchQuote() {
  if (!form.fund_code || form.fund_code.length !== 6) {
    fundInfo.value = null
    quoteInfo.value = null
    return
  }
  try {
    const detail = await fundsApi.detail(form.fund_code)
    fundInfo.value = detail.fund
    quoteInfo.value = detail.quote
    if (form.type === 'import' && detail.fund.name) {
      form.fund_name = detail.fund.name
    }
  } catch (e) {
    fundInfo.value = null
    quoteInfo.value = null
  }
}

watch(() => form.type, (newType) => {
  if (newType === 'import' && fundInfo.value) {
    form.fund_name = fundInfo.value.name
  }
})

async function loadList() {
  list.value = await transactionsApi.list()
}

async function submit() {
  if (!form.fund_code) { ElMessage.warning('请输入基金代码'); return }
  if (form.type === 'buy' && !form.amount) { ElMessage.warning('买入时必须提供交易金额'); return }
  if (form.type === 'sell' && !form.shares) { ElMessage.warning('卖出时必须提供确认份额'); return }
  if (form.type === 'import' && form.amount === undefined) { ElMessage.warning('导入持仓时必须提供持有金额（当前市值）'); return }
  if (form.type === 'import' && form.profit === undefined) { ElMessage.warning('导入持仓时必须提供持仓累计收益'); return }
  
  submitting.value = true
  try {
    await transactionsApi.create({
      fund_code: form.fund_code,
      date: form.date,
      type: form.type,
      amount: form.amount,
      shares: form.shares,
      profit: form.profit,
      fund_name: form.fund_name || undefined,
      fee: form.type === 'import' ? 0 : form.fee,
      settlement_days: form.type === 'import' ? 1 : form.settlement_days,
      note: form.note,
      client_id: `${form.fund_code}-${form.date}-${form.type}-${Date.now()}`,
    })
    ElMessage.success(form.type === 'import' ? '持仓导入成功' : '交易记录已保存')
    form.amount = undefined
    form.shares = undefined
    form.profit = undefined
    form.fund_name = ''
    form.settlement_days = 1
    form.note = ''
    fundInfo.value = null
    quoteInfo.value = null
    await loadList()
    await store.refresh()
  } finally {
    submitting.value = false
  }
}

async function syncPending() {
  syncing.value = true
  try {
    const res = await transactionsApi.syncPending()
    if (res.synced_count > 0) {
      ElMessage.success(`成功同步 ${res.synced_count} 笔订单`)
      await loadList()
      await store.refresh()
    } else {
      ElMessage.info('暂无可同步的订单或基金净值尚未更新')
    }
  } finally {
    syncing.value = false
  }
}

async function remove(id: number) {
  await ElMessageBox.confirm('确定要删除这笔交易记录吗？该操作不可撤销，并将重新计算持仓及收益！', '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
    boxType: 'confirm'
  })
  await transactionsApi.remove(id)
  ElMessage.success('记录已成功删除')
  await loadList()
  await store.refresh()
}

onMounted(() => {
  loadList()
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.tx-page { max-width: 1100px; margin: 16px auto 40px; padding: 0 16px; }
.form-card, .list-card { margin-bottom: 20px; padding: 16px 20px; background-color: #1e2329 !important; border: 1px solid #2b3139 !important; }
.card-title { font-weight: 700; font-size: 15px; margin-bottom: 20px; color: #ffffff; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.form-actions { display: flex; align-items: center; gap: 16px; margin-top: 16px; }
.hint { color: #707a8a; font-size: 12px; }
.quote-info { margin-bottom: 16px; padding: 12px 16px; background: #2b3139; border-radius: 10px; font-size: 13px; border: 1px solid #20262d; }
.update-time { margin-left: 16px; font-size: 12px; color: #707a8a; }

/* 红涨绿跌配色 */
.text-red { color: #f6465d; }
.text-green { color: #0ecb81; }

.type-buy {
  color: #f6465d;
  font-weight: 600;
  background: rgba(246, 70, 93, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.type-sell {
  color: #0ecb81;
  font-weight: 600;
  background: rgba(14, 203, 129, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.type-import {
  color: #3b82f6;
  font-weight: 600;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.delete-btn {
  font-weight: 500;
  color: #0ecb81 !important; /* 币安风格的红色/绿色做删除按钮 */
}
.delete-btn:hover {
  color: #f6465d !important;
  text-decoration: underline;
}

:deep(.el-radio-button__inner) {
  background-color: #2b3139 !important;
  border: 1px solid #2b3139 !important;
  color: #eaecef !important;
  transition: all 0.2s ease;
}
:deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner),
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: var(--el-color-primary) !important;
  color: #181a20 !important;
  border-color: var(--el-color-primary) !important;
  box-shadow: -1px 0 0 0 var(--el-color-primary) !important;
}
:deep(.el-input-number .el-input__inner) {
  text-align: left;
}

/* 手机端响应式适配 */
@media (max-width: 768px) {
  .tx-page {
    margin: 8px auto 24px;
    padding: 0 4px;
  }
  .form-card, .list-card {
    padding: 12px !important;
    margin-bottom: 16px;
  }
  .form-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    margin-top: 12px;
  }
  .save-btn {
    width: 100%;
    height: 40px;
  }
  .hint {
    text-align: center;
  }
  .update-time {
    display: block;
    margin-left: 0;
    margin-top: 6px;
  }
}
</style>
