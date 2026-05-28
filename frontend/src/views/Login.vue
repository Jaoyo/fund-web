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
        class="login-input"
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
  background: radial-gradient(ellipse at top, rgba(252, 213, 53, 0.03), transparent 60%), #0b0e11;
}
.login-card {
  width: 90%;
  max-width: 360px;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background-color: #1e2329;
  border: 1px solid #2b3139;
  border-radius: 16px;
  box-sizing: border-box;
}
.brand-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 6px;
}
.brand {
  font-weight: 800;
  font-size: 26px;
  letter-spacing: -0.5px;
  color: #fcd535;
}
.subtitle {
  font-size: 13px;
  color: #929aa5;
}
.login-btn {
  width: 100%;
}
.hint {
  font-size: 11px;
  color: #707a8a;
  text-align: center;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .login-card {
    padding: 24px 20px;
    gap: 16px;
  }
  .brand {
    font-size: 24px;
  }
}
</style>
