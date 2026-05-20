<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getAuthErrorMessage, validateAdminKey, validateUserKey } from '@/api/auth'
import { useAdminSessionStore } from '@/stores/admin-session'
import { useSessionStore } from '@/stores/session'

const router = useRouter()
const session = useSessionStore()
const admin = useAdminSessionStore()

const loginKey = ref(admin.apiKey || session.apiKey)
const isSubmitting = ref(false)
const errorMessage = ref('')

const loginHint = computed(() => {
  if (isSubmitting.value) {
    return '正在识别 Key 对应权限并准备工作台...'
  }

  return '系统会优先校验管理员权限，成功后自动进入对应页面。'
})

async function handleLogin() {
  const value = loginKey.value.trim()
  if (!value || isSubmitting.value) {
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    await validateAdminKey(value)
    admin.updateApiKey(value)
    session.clearApiKey()
    await router.replace('/admin')
    return
  }
  catch {
    admin.clearApiKey()
  }

  try {
    const userInfo = await validateUserKey(value)
    session.updateApiKey(value)
    session.remainingCount = userInfo.remaining_count
    admin.clearApiKey()
    await router.replace('/')
  }
  catch (error) {
    session.clearApiKey()
    errorMessage.value = getAuthErrorMessage(error, 'Key 无效或已失效，请联系管理员确认可用次数。')
  }
  finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="login-screen">
    <section class="login-screen__story">
      <p class="eyebrow">Image2web Access</p>
      <h1>一把 Key，进入你的图像工作台。</h1>
      <p class="login-screen__lead">
        统一从一个入口登录。普通用户进入图像编辑工作区，管理员 Key 会直接切换到后台管理页。
      </p>

      <div class="login-screen__metrics">
        <article>
          <span>01</span>
          <strong>单 Key 登录</strong>
          <p>不区分账号密码，输入现有 Key 即可校验身份。</p>
        </article>
        <article>
          <span>02</span>
          <strong>自动识别角色</strong>
          <p>优先识别管理员权限，避免重复选择登录类型。</p>
        </article>
        <article>
          <span>03</span>
          <strong>延续现有会话</strong>
          <p>基于当前仓库既有本地存储与请求头约定接入。</p>
        </article>
      </div>
    </section>

    <section class="login-card">
      <div class="login-card__header">
        <p class="eyebrow">Sign In</p>
        <h2>输入登录 Key</h2>
        <p>{{ loginHint }}</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <label class="login-form__field">
          <span>登录 Key</span>
          <input
            v-model="loginKey"
            type="password"
            placeholder="请输入用户 Key 或管理员 Key"
            autocomplete="current-password"
          />
        </label>

        <button class="login-form__submit" type="submit" :disabled="!loginKey.trim() || isSubmitting">
          {{ isSubmitting ? '正在登录...' : '进入系统' }}
        </button>
      </form>

      <p v-if="errorMessage" class="login-card__error">{{ errorMessage }}</p>

      <div class="login-card__footer">
        <div>
          <strong>登录规则</strong>
          <p>管理员 Key 直达后台，普通 Key 进入前台工作区。</p>
        </div>
        <div>
          <strong>当前模式</strong>
          <p>沿用现有 `X-API-Key` 与管理员请求头校验。</p>
        </div>
      </div>
    </section>
  </main>
</template>
