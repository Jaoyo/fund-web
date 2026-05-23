<template>
  <div class="tx-page">
    <el-card class="form-card">
      <div class="card-title">录入交易</div>
      <el-form :model="form" label-width="80px" @submit.prevent="submit">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="基金代码">
              <el-input v-model="form.fund_code" placeholder="6 位代码，如 001753" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="日期">
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="5">
            <el-form-item label="类型">
              <el-radio-group v-model="form.type">
                <el-radio-button label="buy">买入</el-radio-button>
                <el-radio-button label="sell">卖出</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="成交净值">
              <el-input-number v-model="form.nav" :precision="4" :step="0.0001" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="金额">
              <el-input-number v-model="form.amount" :precision="2" :step="100" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="份额">
              <el-input-number v-model="form.shares" :precision="2" :step="100" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="费用">
              <el-input-number v-model="form.fee" :precision="2" :step="1" :min="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.note" />
        </el-form-item>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
        <span class="hint">金额和份额至少填一个，缺的那个用净值反推</span>
      </el-form>
    </el-card>

    <el-card class="list-card">
      <div class="card-title">交易流水</div>
      <el-table :data="list" stripe>
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="fund_code" label="代码" width="100" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.type === 'buy' ? 'success' : 'danger'" size="small">
              {{ row.type === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="nav" label="净值" width="100" />
        <el-table-column prop="shares" label="份额" width="120" />
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column prop="fee" label="费用" width="80" />
        <el-table-column prop="note" label="备注" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button link type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { transactionsApi } from '@/api/holdings'
import { useHoldingsStore } from '@/stores/holdings'
import type { Transaction, TransactionIn } from '@/types'

const form = reactive<TransactionIn & { fee: number }>({
  fund_code: '',
  date: dayjs().format('YYYY-MM-DD'),
  type: 'buy',
  nav: 1.0,
  amount: undefined,
  shares: undefined,
  fee: 0,
  note: '',
})

const list = ref<Transaction[]>([])
const submitting = ref(false)
const store = useHoldingsStore()

async function loadList() {
  list.value = await transactionsApi.list()
}

async function submit() {
  if (!form.fund_code) { ElMessage.warning('请输入基金代码'); return }
  if (!form.amount && !form.shares) { ElMessage.warning('金额和份额至少填一个'); return }
  submitting.value = true
  try {
    await transactionsApi.create({
      fund_code: form.fund_code,
      date: form.date,
      type: form.type,
      nav: form.nav,
      amount: form.amount,
      shares: form.shares,
      fee: form.fee,
      note: form.note,
      client_id: `${form.fund_code}-${form.date}-${form.type}-${Date.now()}`,
    })
    ElMessage.success('已保存')
    form.amount = undefined
    form.shares = undefined
    form.note = ''
    await loadList()
    await store.refresh()
  } finally {
    submitting.value = false
  }
}

async function remove(id: number) {
  await ElMessageBox.confirm('确认删除这笔交易？', '提示', { type: 'warning' })
  await transactionsApi.remove(id)
  ElMessage.success('已删除')
  await loadList()
  await store.refresh()
}

onMounted(loadList)
</script>

<style scoped>
.tx-page { max-width: 1100px; margin: 0 auto; }
.form-card { margin-bottom: 16px; }
.card-title { font-weight: 600; margin-bottom: 16px; }
.hint { color: var(--el-text-color-secondary); font-size: 12px; margin-left: 12px; }
</style>
