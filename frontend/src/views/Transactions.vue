<template>
  <div class="tx-page">
    <el-card class="form-card">
      <div class="card-title">录入交易记录</div>
      <el-form :model="form" label-width="80px" @submit.prevent="submit" label-position="left">
        <el-row :gutter="24">
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
        <el-row :gutter="24">
          <template v-if="form.type !== 'import'">
            <el-col :span="8" :xs="12" v-if="form.type === 'buy'">
              <el-form-item label="交易金额">
                <el-input-number v-model="form.amount" :precision="2" :step="100" :min="0" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="8" :xs="12" v-if="form.type === 'sell'">
              <el-form-item label="确认份额">
                <el-input-number v-model="form.shares" :precision="2" :step="100" :min="0" style="width: 100%;" />
              </el-form-item>
            </el-col>
            <el-col :span="8" :xs="12">
              <el-form-item label="手续费用">
                <el-input-number v-model="form.fee" :precision="2" :step="1" :min="0" style="width: 100%;" />
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
        
        <div v-if="quoteInfo && form.type !== 'import'" class="quote-info">
          <span>实时预估净值：<strong :class="quoteInfo.estimated_growth && quoteInfo.estimated_growth > 0 ? 'text-red' : 'text-green'">{{ quoteInfo.estimated_nav?.toFixed(4) || '-' }}</strong></span>
          <span style="margin-left: 16px;">预估涨跌：<strong :class="quoteInfo.estimated_growth && quoteInfo.estimated_growth > 0 ? 'text-red' : 'text-green'">{{ quoteInfo.estimated_growth !== null && quoteInfo.estimated_growth !== undefined ? quoteInfo.estimated_growth.toFixed(2) + '%' : '-' }}</strong></span>
          <span style="margin-left: 16px; font-size: 12px; color: var(--el-text-color-secondary);">更新时间: {{ quoteInfo.estimated_time || '-' }}</span>
        </div>
        <el-form-item label="交易备注">
          <el-input v-model="form.note" placeholder="选填，如：定投、止盈、低估买入等" />
        </el-form-item>
        <div class="form-actions">
          <el-button type="primary" :loading="submitting" @click="submit">保存交易</el-button>
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
      <el-table :data="list" stripe>
        <el-table-column prop="date" label="交易日期" width="115" />
        <el-table-column prop="fund_code" label="基金代码" width="105" />
        <el-table-column label="交易类型" width="90">
          <template #default="{ row }">
            <span :class="row.type === 'buy' ? 'type-buy' : 'type-sell'">
              {{ row.type === 'buy' ? '买入' : '卖出' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="nav" label="成交净值" width="100">
          <template #default="{ row }">
            <span v-if="row.nav > 0">{{ row.nav }}</span>
            <el-tag v-else size="small" type="warning" effect="plain">待确认</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="shares" label="确认份额" width="120">
          <template #default="{ row }">
            {{ row.nav > 0 ? row.shares : (row.type === 'buy' ? '-' : row.shares) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="交易金额" width="120">
          <template #default="{ row }">
            {{ row.nav > 0 ? row.amount : (row.type === 'sell' ? '-' : row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="fee" label="交易费用" width="80" />
        <el-table-column prop="note" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="remove(row.id)" class="delete-btn">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { transactionsApi } from '@/api/holdings'
import { fundsApi } from '@/api/funds'
import { useHoldingsStore } from '@/stores/holdings'
import type { Transaction, TransactionIn, Quote } from '@/types'

const form = reactive<TransactionIn & { fee: number }>({
  fund_code: '',
  date: dayjs().format('YYYY-MM-DD'),
  type: 'buy',
  amount: undefined,
  shares: undefined,
  profit: undefined,
  fund_name: '',
  fee: 0,
  note: '',
})

const list = ref<Transaction[]>([])
const submitting = ref(false)
const syncing = ref(false)
const quoteInfo = ref<Quote | null>(null)
const store = useHoldingsStore()

async function fetchQuote() {
  if (!form.fund_code || form.fund_code.length !== 6) {
    quoteInfo.value = null
    return
  }
  try {
    quoteInfo.value = await fundsApi.quote(form.fund_code)
  } catch (e) {
    quoteInfo.value = null
  }
}

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
      note: form.note,
      client_id: `${form.fund_code}-${form.date}-${form.type}-${Date.now()}`,
    })
    ElMessage.success(form.type === 'import' ? '持仓导入成功，已转为买入记录' : '交易记录已保存')
    form.amount = undefined
    form.shares = undefined
    form.profit = undefined
    form.fund_name = ''
    form.note = ''
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

onMounted(loadList)
</script>

<style scoped>
.tx-page { max-width: 1100px; margin: 16px auto 40px; padding: 0 16px; }
.form-card, .list-card { margin-bottom: 20px; padding: 8px 12px; }
.card-title { font-weight: 700; font-size: 15px; margin-bottom: 20px; color: var(--el-text-color-primary); }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.form-actions { display: flex; align-items: center; gap: 16px; margin-top: 12px; }
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
.quote-info { margin-bottom: 16px; padding: 8px 16px; background: rgba(255,255,255,0.03); border-radius: 4px; font-size: 13px; }
.text-red { color: #f56c6c; }
.text-green { color: #67c23a; }

.type-buy {
  color: var(--el-color-success-light-3);
  font-weight: 600;
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.type-sell {
  color: var(--el-color-danger-light-3);
  font-weight: 600;
  background: rgba(244, 63, 94, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.delete-btn {
  font-weight: 500;
  color: var(--el-color-danger-light-3) !important;
}
.delete-btn:hover {
  color: var(--el-color-danger) !important;
  text-decoration: underline;
}

:deep(.el-radio-button__inner) {
  background-color: rgba(13, 18, 30, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: var(--el-text-color-regular) !important;
  transition: all 0.3s ease;
}
:deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner),
:deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: var(--el-color-primary) !important;
  color: #ffffff !important;
  border-color: var(--el-color-primary) !important;
  box-shadow: -1px 0 0 0 var(--el-color-primary) !important;
}
:deep(.el-input-number .el-input__inner) {
  text-align: left;
}
</style>
