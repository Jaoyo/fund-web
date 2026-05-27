<template>
  <el-container class="app-container">
    <el-header v-if="!$route.meta.public" class="app-header">
      <div class="brand">fund-web</div>
      <el-menu mode="horizontal" :router="true" :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/">总览</el-menu-item>
        <el-menu-item index="/transactions">交易</el-menu-item>
        <el-menu-item index="/advice">建议</el-menu-item>
      </el-menu>
      <el-button text size="small" class="logout-btn" @click="handleLogout">登出</el-button>
    </el-header>
    <el-main :class="{ 'no-padding': $route.meta.public }">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function handleLogout() {
  auth.clearToken()
  ElMessage.success('已登出')
  router.push('/login')
}
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
.app-container { height: 100%; }
.app-header {
  display: flex; align-items: center; gap: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(13, 18, 30, 0.8) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 0 32px !important;
}
.brand {
  font-weight: 800;
  font-size: 20px;
  background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 50%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}
.nav-menu {
  flex: 1;
  border-bottom: none !important;
  background: transparent !important;
}
.nav-menu .el-menu-item {
  font-weight: 500;
  color: var(--el-text-color-regular) !important;
}
.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  background: transparent !important;
  color: var(--el-color-primary-light-3) !important;
}
.logout-btn {
  color: var(--el-text-color-secondary) !important;
}
.logout-btn:hover {
  color: var(--el-color-primary-light-3) !important;
}
.el-main.no-padding {
  padding: 0 !important;
}

/* 路由平滑淡入淡出动效 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
