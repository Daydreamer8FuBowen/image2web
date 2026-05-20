import { createRouter, createWebHistory } from 'vue-router'

import { validateAdminKey, validateUserKey } from '@/api/auth'
import { useAdminSessionStore } from '@/stores/admin-session'
import { useSessionStore } from '@/stores/session'
import AdminView from '@/views/AdminView.vue'
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
    },
  ],
})

async function ensureUserAccess() {
  const session = useSessionStore()
  const apiKey = session.apiKey.trim()

  if (!apiKey) {
    return false
  }

  try {
    const userInfo = await validateUserKey(apiKey)
    session.remainingCount = userInfo.remaining_count
    return true
  }
  catch {
    session.clearApiKey()
    return false
  }
}

async function ensureAdminAccess() {
  const admin = useAdminSessionStore()
  const apiKey = admin.apiKey.trim()

  if (!apiKey) {
    return false
  }

  try {
    await validateAdminKey(apiKey)
    return true
  }
  catch {
    admin.clearApiKey()
    return false
  }
}

router.beforeEach(async (to) => {
  if (to.name === 'login') {
    if (await ensureAdminAccess()) {
      return { name: 'admin' }
    }

    if (await ensureUserAccess()) {
      return { name: 'home' }
    }

    return true
  }

  if (to.name === 'admin') {
    if (await ensureAdminAccess()) {
      return true
    }

    return { name: 'login' }
  }

  if (await ensureUserAccess()) {
    return true
  }

  if (await ensureAdminAccess()) {
    return { name: 'admin' }
  }

  return { name: 'login' }
})
