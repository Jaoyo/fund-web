import axios, { type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types'
import { useAuthStore } from '@/stores/auth'

const AUTH_FAIL_CODE = 4011

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.set('Authorization', `Bearer ${auth.token}`)
  }
  return config
})

client.interceptors.response.use(
  (resp) => {
    const body = resp.data as ApiResponse<unknown>
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === AUTH_FAIL_CODE) {
        const cfg = resp.config as AuthAwareRequestConfig
        if (!cfg._skipAuthRedirect) {
          handleAuthFailure(body.message)
        }
        return Promise.reject(body)
      }
      if (body.code !== 0) {
        ElMessage.error(body.message || `业务错误 ${body.code}`)
        return Promise.reject(body)
      }
    }
    return resp
  },
  (err) => {
    const msg = err?.response?.data?.message || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  },
)

function handleAuthFailure(message?: string) {
  const auth = useAuthStore()
  auth.clearToken()
  ElMessage.error(message || '请重新登录')
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export interface AuthAwareRequestConfig extends InternalAxiosRequestConfig {
  _skipAuthRedirect?: boolean
}

export async function apiGet<T>(
  url: string,
  params?: Record<string, unknown>,
  options?: { skipAuthRedirect?: boolean },
): Promise<T> {
  const resp = await client.get<ApiResponse<T>>(url, {
    params,
    _skipAuthRedirect: options?.skipAuthRedirect,
  } as AuthAwareRequestConfig)
  return resp.data.data
}

export async function apiPost<T>(url: string, payload?: unknown): Promise<T> {
  const resp = await client.post<ApiResponse<T>>(url, payload)
  return resp.data.data
}

export async function apiDelete<T>(url: string): Promise<T> {
  const resp = await client.delete<ApiResponse<T>>(url)
  return resp.data.data
}

export async function apiPut<T>(url: string, payload?: unknown): Promise<T> {
  const resp = await client.put<ApiResponse<T>>(url, payload)
  return resp.data.data
}

export default client
