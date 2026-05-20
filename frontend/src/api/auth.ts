import axios from 'axios'

import { apiClient } from '@/api/client'

export type UserAuthInfo = {
  key_name: string
  remaining_count: number
  status: string
  is_admin: boolean
}

export type AdminAuthInfo = {
  is_admin: true
}

type ApiErrorPayload = {
  detail?: string
}

export async function validateUserKey(apiKey: string) {
  const response = await apiClient.get<UserAuthInfo>('/api/auth/me', {
    headers: { 'X-API-Key': apiKey },
  })
  return response.data
}

export async function validateAdminKey(apiKey: string) {
  const response = await apiClient.get<AdminAuthInfo>('/api/admin/me', {
    headers: {
      'X-API-Key': apiKey,
      'X-Admin-Mode': '1',
    },
  })
  return response.data
}

export function getAuthErrorMessage(error: unknown, fallback = 'Key 校验失败，请确认后重试') {
  if (!axios.isAxiosError<ApiErrorPayload>(error)) {
    return fallback
  }

  return error.response?.data?.detail || fallback
}
