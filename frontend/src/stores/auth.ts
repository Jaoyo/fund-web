import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const STORAGE_KEY = 'fund_auth_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(STORAGE_KEY) || '')
  // 会话级标志：当前 token 是否已通过后端校验。刷新页面会重置，进而触发预校验。
  const validated = ref<boolean>(false)

  const isAuthed = computed(() => token.value.length > 0)

  function setToken(t: string) {
    token.value = t.trim()
    if (token.value) {
      localStorage.setItem(STORAGE_KEY, token.value)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  function markValidated() {
    validated.value = true
  }

  function clearToken() {
    token.value = ''
    validated.value = false
    localStorage.removeItem(STORAGE_KEY)
  }

  return { token, validated, isAuthed, setToken, markValidated, clearToken }
})
