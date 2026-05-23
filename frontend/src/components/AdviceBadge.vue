<template>
  <el-tag :type="tagType" size="small" class="advice-badge">
    {{ signal.name }}
    <span class="msg">· {{ signal.message }}</span>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AdviceSignal } from '@/types'

const props = defineProps<{ signal: AdviceSignal }>()

const tagType = computed(() => {
  switch (props.signal.level) {
    case 'buy': return 'success'
    case 'sell': return 'danger'
    case 'watch': return 'warning'
    default: return 'info'
  }
})
</script>

<style scoped>
.advice-badge { margin: 2px 4px 2px 0; }
.msg { color: inherit; font-weight: normal; margin-left: 4px; }
</style>
