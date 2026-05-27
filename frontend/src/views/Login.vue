<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand-block">
        <div class="brand">fund-web</div>
        <div class="subtitle">输入访问令牌以继续</div>
      </div>
      <el-input
        v-model="tokenInput"
        type="password"
        placeholder="访问令牌"
        size="large"
        show-password
        clearable
        @keyup.enter="handleLogin"
      />
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        class="login-btn"
        @click="handleLogin"
      >
        登录
      </el-button>
      <div class="hint">令牌由服务器管理员通过 FUND_AUTH_TOKEN 配置</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiGet } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const tokenInput = ref('')
const loading = ref(false)

async function handleLogin() {
  const value = tokenInput.value.trim()
  if (!value) {
    ElMessage.warning('请输入令牌')
    return
  }
  loading.value = true
  auth.setToken(value)
  try {
    await apiGet('/transactions', undefined, { skipAuthRedirect: true })
    auth.markValidated()
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e: unknown) {
    auth.clearToken()
    const code = (e as { code?: number })?.code
    const msg = (e as { message?: string })?.message
    if (code === 4011) {
      ElMessage.error('令牌错误')
    } else {
      ElMessage.error(msg || '登录失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at top, rgba(99, 102, 241, 0.08), transparent 60%),
    var(--el-bg-color-page);
}
.login-card {
  width: 360px;
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: rgba(13, 18, 30, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}
.brand-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 6px;
}
.brand {
  font-weight: 800;
  font-size: 28px;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 50%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.login-btn {
  width: 100%;
}
.hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}
</style>
