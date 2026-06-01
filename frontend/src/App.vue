<template>
  <el-config-provider :locale="zhCn">
    <el-container class="app-container">
      <!-- 顶部 header -->
      <el-header v-if="!$route.meta.public" class="app-header">
        <div class="brand">
          <el-icon class="brand-icon"><TrendCharts /></el-icon>
          <span class="brand-text">AlphaFi</span>
        </div>
        <!-- 桌面端菜单，在移动端通过 display: none 隐藏 -->
        <el-menu mode="horizontal" :router="true" :default-active="$route.path" class="nav-menu desktop-menu">
          <el-menu-item index="/">总览</el-menu-item>
          <el-menu-item index="/transactions">交易</el-menu-item>
          <el-menu-item index="/advice">建议</el-menu-item>
        </el-menu>
        <!-- 登出按钮 -->
        <el-button text size="small" class="logout-btn" @click="handleLogout">登出</el-button>
      </el-header>
      
      <el-main :class="{ 'no-padding': $route.meta.public }" class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>

      <!-- 移动端底部 TabBar，在桌面端通过 display: none 隐藏 -->
      <div v-if="!$route.meta.public" class="mobile-tabbar">
        <router-link to="/" class="tab-item" :class="{ active: $route.path === '/' }">
          <el-icon><PieChart /></el-icon>
          <span class="tab-label">总览</span>
        </router-link>
        <router-link to="/transactions" class="tab-item" :class="{ active: $route.path === '/transactions' }">
          <el-icon><List /></el-icon>
          <span class="tab-label">交易</span>
        </router-link>
        <router-link to="/advice" class="tab-item" :class="{ active: $route.path === '/advice' }">
          <el-icon><Opportunity /></el-icon>
          <span class="tab-label">建议</span>
        </router-link>
      </div>
    </el-container>
  </el-config-provider>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { PieChart, List, Opportunity, TrendCharts } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
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
html, body, #app { height: 100%; margin: 0; background-color: #0b0e11; }
.app-container { height: 100%; display: flex; flex-direction: column; }
.app-header {
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  border-bottom: 1px solid #2b3139;
  background: #0b0e11 !important;
  padding: 0 24px !important;
  height: 60px !important;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  font-size: 20px;
  color: #fcd535 !important; /* 币安黄 */
  letter-spacing: -0.5px;
}
.brand-icon {
  font-size: 22px;
}
.nav-menu {
  flex: 1;
  border-bottom: none !important;
  background: transparent !important;
  height: 100%;
}
.nav-menu .el-menu-item {
  font-weight: 500;
  color: #707a8a !important;
  height: 100%;
  border-bottom: 2px solid transparent !important;
}
.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  background: transparent !important;
  color: #fcd535 !important;
  border-bottom: 2px solid #fcd535 !important;
}
.logout-btn {
  color: #707a8a !important;
}
.logout-btn:hover {
  color: #fcd535 !important;
}
.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px 40px !important;
}
.app-main.no-padding {
  padding: 0 !important;
}

/* 移动端底部 TabBar 样式 */
.mobile-tabbar {
  display: none; /* 默认隐藏 */
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background-color: #1e2329;
  border-top: 1px solid #2b3139;
  z-index: 100;
  align-items: center;
  justify-content: space-around;
  padding-bottom: env(safe-area-inset-bottom); /* 适配刘海屏底部安全区 */
}
.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: #707a8a;
  flex: 1;
  height: 100%;
  transition: color 0.2s ease;
}
.tab-item .el-icon {
  font-size: 20px;
  margin-bottom: 2px;
}
.tab-label {
  font-size: 11px;
}
.tab-item.active {
  color: #fcd535;
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

/* 响应式媒体查询 */
@media (max-width: 768px) {
  .desktop-menu {
    display: none !important; /* 隐藏桌面端菜单 */
  }
  .app-header {
    padding: 0 16px !important;
    height: 50px !important;
  }
  .app-main {
    padding: 16px 12px 76px !important; /* 增加底部 padding 防止内容被 TabBar 遮挡 */
  }
  .mobile-tabbar {
    display: flex; /* 显示移动端 TabBar */
  }
}
</style>
