import axios from 'axios'

import { env } from '@/config/env'

const USER_KEY_STORAGE = 'image2web-user-key'
const ADMIN_KEY_STORAGE = 'image2web-admin-key'

export const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 30000,
})

apiClient.interceptors.request.use((config) => {
  config.headers = config.headers ?? {}
  const isAdmin = config.headers?.['X-Admin-Mode'] === '1'
  const storageKey = isAdmin ? ADMIN_KEY_STORAGE : USER_KEY_STORAGE
  const token = window.localStorage.getItem(storageKey)
  if (token && !config.headers['X-API-Key']) {
    config.headers['X-API-Key'] = token
  }
  delete config.headers['X-Admin-Mode']
  return config
})

export function setUserKey(key: string) {
  window.localStorage.setItem(USER_KEY_STORAGE, key)
}

export function setAdminKey(key: string) {
  window.localStorage.setItem(ADMIN_KEY_STORAGE, key)
}

export function clearUserKey() {
  window.localStorage.removeItem(USER_KEY_STORAGE)
}

export function clearAdminKey() {
  window.localStorage.removeItem(ADMIN_KEY_STORAGE)
}

export function getUserKey() {
  return window.localStorage.getItem(USER_KEY_STORAGE) || ''
}

export function getAdminKey() {
  return window.localStorage.getItem(ADMIN_KEY_STORAGE) || ''
}

export function resolveAssetUrl(url?: string | null) {
  if (!url) {
    return ''
  }

  if (/^(https?:)?\/\//i.test(url) || url.startsWith('blob:') || url.startsWith('data:')) {
    return url
  }

  return new URL(url, env.apiBaseUrl).toString()
}
