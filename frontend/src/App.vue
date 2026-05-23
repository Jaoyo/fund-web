<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="brand">fund-web</div>
      <el-menu mode="horizontal" :router="true" :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/">总览</el-menu-item>
        <el-menu-item index="/transactions">交易</el-menu-item>
        <el-menu-item index="/advice">建议</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts"></script>

<style>
html, body, #app { height: 100%; margin: 0; }
.app-container { height: 100%; }
.app-header {
  display: flex; align-items: center; gap: 24px;
  border-bottom: 1px solid var(--el-border-color-light);
  background: #fff;
}
.brand { font-weight: 600; font-size: 18px; }
.nav-menu { flex: 1; border-bottom: none; }
</style>
