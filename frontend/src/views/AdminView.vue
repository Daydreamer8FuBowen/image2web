<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { apiClient, resolveAssetUrl } from '@/api/client'
import { useAdminSessionStore } from '@/stores/admin-session'

type AdminKeyItem = {
  id: number
  name: string
  key_value: string
  remaining_count: number
  status: string
}

type AdminStatsResponse = {
  total_keys: number
  total_tasks: number
  success_records: number
  failed_tasks: number
}

type AdminRecordInputImageItem = {
  id: number
  url: string
  source_type: string
  original_name: string
}

type AdminRecordItem = {
  id: number
  prompt: string
  negative_prompt: string | null
  status: string
  image_url: string | null
  created_at: string
  parent_record_id: number | null
  input_images: AdminRecordInputImageItem[]
}

const router = useRouter()
const admin = useAdminSessionStore()
const keyList = ref<AdminKeyItem[]>([])
const recordItems = ref<AdminRecordItem[]>([])
const activeRecordKeyId = ref<number | null>(null)
const activeRecordKeyName = ref('')
const remainingDrafts = ref<Record<number, number>>({})
const rowFeedback = ref<Record<number, string>>({})

function generateUserKey() {
  const cryptoApi = window.crypto
  const bytes = new Uint8Array(18)
  cryptoApi.getRandomValues(bytes)
  const token = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('')
  return `sk-${token}`
}

const form = ref({
  name: '',
  key_value: generateUserKey(),
  remaining_count: 10,
})
const isRefreshing = ref(false)
const isCreating = ref(false)
const isLoadingRecords = ref(false)
const isUpdatingKeyId = ref<number | null>(null)
const isDeletingKeyId = ref<number | null>(null)
const loadError = ref('')
const recordsError = ref('')

const activeKeyCount = computed(() => keyList.value.filter((item) => item.status === 'active').length)
const totalRemainingQuota = computed(() => keyList.value.reduce((sum, item) => sum + item.remaining_count, 0))
const successRate = computed(() => {
  if (!admin.totalTasks) {
    return '0%'
  }

  return `${Math.round((admin.successRecords / admin.totalTasks) * 100)}%`
})
const metricCards = computed(() => [
  {
    label: '用户 Key',
    value: admin.totalKeys,
    detail: `${activeKeyCount.value} 个处于启用状态`,
    tone: 'amber',
  },
  {
    label: '总任务数',
    value: admin.totalTasks,
    detail: `成功率 ${successRate.value}`,
    tone: 'violet',
  },
  {
    label: '成功结果',
    value: admin.successRecords,
    detail: `失败 ${admin.failedTasks} 次`,
    tone: 'emerald',
  },
  {
    label: '剩余次数池',
    value: totalRemainingQuota.value,
    detail: '用于快速判断账号资源储备',
    tone: 'sky',
  },
])

function normalizeError(error: unknown) {
  if (error instanceof Error) {
    return error.message
  }

  return '后台数据加载失败，请检查管理员 Key 和服务状态。'
}

function maskKey(value: string) {
  if (value.length <= 10) {
    return value
  }

  return `${value.slice(0, 6)}...${value.slice(-4)}`
}

function regenerateUserKey() {
  form.value.key_value = generateUserKey()
}

function syncRemainingDrafts(items: AdminKeyItem[]) {
  remainingDrafts.value = Object.fromEntries(items.map((item) => [item.id, item.remaining_count]))
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadStats() {
  const response = await apiClient.get<AdminStatsResponse>('/api/admin/stats', {
    headers: { 'X-Admin-Mode': '1' },
  })
  admin.totalKeys = response.data.total_keys
  admin.totalTasks = response.data.total_tasks
  admin.successRecords = response.data.success_records
  admin.failedTasks = response.data.failed_tasks
}

async function loadKeys() {
  const response = await apiClient.get<AdminKeyItem[]>('/api/admin/keys', {
    headers: { 'X-Admin-Mode': '1' },
  })
  keyList.value = response.data
  syncRemainingDrafts(response.data)
}

async function createKey() {
  isCreating.value = true
  loadError.value = ''
  try {
    await apiClient.post('/api/admin/keys', form.value, {
      headers: { 'X-Admin-Mode': '1' },
    })
    form.value = {
      name: '',
      key_value: generateUserKey(),
      remaining_count: 10,
    }
    await refreshAdmin()
  }
  catch (error) {
    loadError.value = normalizeError(error)
  }
  finally {
    isCreating.value = false
  }
}

async function copyKey(item: AdminKeyItem) {
  await navigator.clipboard.writeText(item.key_value)
  rowFeedback.value = {
    ...rowFeedback.value,
    [item.id]: '已复制',
  }
}

async function updateRemainingCount(item: AdminKeyItem) {
  const nextValue = Number(remainingDrafts.value[item.id] ?? item.remaining_count)
  const delta = nextValue - item.remaining_count
  if (!Number.isFinite(nextValue) || nextValue < 0 || delta === 0) {
    rowFeedback.value = {
      ...rowFeedback.value,
      [item.id]: delta === 0 ? '无变化' : '次数需大于等于 0',
    }
    return
  }

  isUpdatingKeyId.value = item.id
  rowFeedback.value = {
    ...rowFeedback.value,
    [item.id]: '',
  }
  try {
    await apiClient.patch(
      `/api/admin/keys/${item.id}/recharge`,
      { delta },
      { headers: { 'X-Admin-Mode': '1' } },
    )
    rowFeedback.value = {
      ...rowFeedback.value,
      [item.id]: '已更新',
    }
    await refreshAdmin()
  }
  catch (error) {
    rowFeedback.value = {
      ...rowFeedback.value,
      [item.id]: normalizeError(error),
    }
  }
  finally {
    isUpdatingKeyId.value = null
  }
}

async function deleteKey(item: AdminKeyItem) {
  const confirmed = window.confirm(`确认删除用户 Key「${item.name}」吗？相关记录也会一起删除。`)
  if (!confirmed) {
    return
  }

  isDeletingKeyId.value = item.id
  rowFeedback.value = {
    ...rowFeedback.value,
    [item.id]: '',
  }
  try {
    await apiClient.delete(`/api/admin/keys/${item.id}`, {
      headers: { 'X-Admin-Mode': '1' },
    })
    if (activeRecordKeyId.value === item.id) {
      activeRecordKeyId.value = null
      activeRecordKeyName.value = ''
      recordItems.value = []
      recordsError.value = ''
    }
    await refreshAdmin()
  }
  catch (error) {
    rowFeedback.value = {
      ...rowFeedback.value,
      [item.id]: normalizeError(error),
    }
  }
  finally {
    isDeletingKeyId.value = null
  }
}

async function loadKeyRecords(item: AdminKeyItem) {
  activeRecordKeyId.value = item.id
  activeRecordKeyName.value = item.name
  isLoadingRecords.value = true
  recordsError.value = ''
  try {
    const response = await apiClient.get<AdminRecordItem[]>(`/api/admin/keys/${item.id}/records`, {
      headers: { 'X-Admin-Mode': '1' },
    })
    recordItems.value = response.data.map((record) => ({
      ...record,
      image_url: resolveAssetUrl(record.image_url),
      input_images: record.input_images.map((image) => ({
        ...image,
        url: resolveAssetUrl(image.url),
      })),
    }))
  }
  catch (error) {
    recordItems.value = []
    recordsError.value = normalizeError(error)
  }
  finally {
    isLoadingRecords.value = false
  }
}

async function refreshAdmin() {
  isRefreshing.value = true
  loadError.value = ''
  try {
    await Promise.all([loadStats(), loadKeys()])
    if (activeRecordKeyId.value) {
      const currentKey = keyList.value.find((item) => item.id === activeRecordKeyId.value)
      if (currentKey) {
        await loadKeyRecords(currentKey)
      }
    }
  }
  catch (error) {
    loadError.value = normalizeError(error)
  }
  finally {
    isRefreshing.value = false
  }
}

async function handleLogout() {
  admin.clearApiKey()
  await router.replace('/login')
}

onMounted(() => {
  if (admin.apiKey) {
    void refreshAdmin()
  }
})
</script>

<template>
  <main class="admin-screen">
    <section class="admin-screen__hero">
      <div>
        <p class="eyebrow">Operations Console</p>
        <h1>为图像工作台准备一套更像控制中枢的后台界面。</h1>
        <p class="admin-screen__lead">
          统一查看密钥资源、任务表现与配额储备，并在同一页面完成管理员校验、统计刷新和用户 Key 创建。
        </p>
      </div>

      <div class="admin-screen__hero-actions">
        <button class="admin-screen__ghost-button" type="button" @click="handleLogout">退出后台</button>
        <button class="prompt-composer__submit" type="button" :disabled="isRefreshing" @click="refreshAdmin">
          {{ isRefreshing ? '正在同步...' : '同步后台数据' }}
        </button>
      </div>
    </section>

    <section class="admin-screen__metrics">
      <article
        v-for="card in metricCards"
        :key="card.label"
        class="admin-screen__metric-card"
        :data-tone="card.tone"
      >
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.detail }}</p>
      </article>
    </section>

    <section class="admin-screen__layout">
      <section class="admin-screen__create">
        <div class="admin-screen__section-head">
          <div>
            <p class="eyebrow">Key Provisioning</p>
            <h2>创建新的用户 Key</h2>
          </div>
          <div class="admin-screen__section-meta">
            <small>写入数据库后立即参与鉴权</small>
            <span class="admin-screen__status-pill" :class="{ 'is-live': Boolean(admin.apiKey) }">
              {{ admin.apiKey ? '已连接' : '未连接' }}
            </span>
          </div>
        </div>

        <div class="admin-screen__session-inline">
          <div class="admin-screen__session-grid">
            <article>
              <span>当前模式</span>
              <strong>已通过登录页完成管理员鉴权</strong>
            </article>
            <article>
              <span>列表规模</span>
              <strong>{{ keyList.length }} 个用户 Key</strong>
            </article>
          </div>
        </div>

        <div class="admin-screen__form">
          <label>
            <span>用户名称</span>
            <input v-model="form.name" placeholder="例如：运营团队 A" />
          </label>
          <label>
            <span>用户 Key</span>
            <div class="admin-screen__generated-key">
              <input :value="form.key_value" readonly />
              <button class="admin-screen__ghost-button" type="button" @click="regenerateUserKey">重新生成</button>
            </div>
          </label>
          <label>
            <span>剩余次数</span>
            <input v-model.number="form.remaining_count" type="number" min="0" placeholder="默认 10" />
          </label>
        </div>

        <div class="admin-screen__create-bar">
          <p>建议为同一业务主体统一命名，便于后续统计和排查。</p>
          <button class="prompt-composer__submit" type="button" :disabled="isCreating" @click="createKey">
            {{ isCreating ? '正在创建...' : '创建用户 Key' }}
          </button>
        </div>

        <p v-if="loadError" class="admin-screen__error">{{ loadError }}</p>
      </section>
    </section>

    <section class="admin-screen__list">
      <div class="admin-screen__section-head">
        <div>
          <p class="eyebrow">Key Registry</p>
          <h2>用户 Key 列表</h2>
        </div>
        <small>{{ keyList.length }} 个记录</small>
      </div>

      <div class="admin-screen__table-head">
        <span>用户</span>
        <span>Key 标识</span>
        <span>剩余次数</span>
        <span>状态</span>
        <span>操作</span>
      </div>

      <article v-for="item in keyList" :key="item.id" class="admin-screen__row">
        <div class="admin-screen__row-user">
          <strong>{{ item.name }}</strong>
          <p>ID #{{ item.id }}</p>
        </div>
        <div class="admin-screen__row-key">{{ maskKey(item.key_value) }}</div>
        <div class="admin-screen__row-count">
          <div class="admin-screen__remaining-editor">
            <input v-model.number="remainingDrafts[item.id]" type="number" min="0" />
            <button
              class="admin-screen__mini-button"
              type="button"
              :disabled="isUpdatingKeyId === item.id"
              @click="updateRemainingCount(item)"
            >
              {{ isUpdatingKeyId === item.id ? '更新中' : '调整' }}
            </button>
          </div>
        </div>
        <div>
          <span class="admin-screen__status-pill" :class="{ 'is-live': item.status === 'active' }">
            {{ item.status === 'active' ? '启用中' : item.status }}
          </span>
        </div>
        <div class="admin-screen__row-actions">
          <button class="admin-screen__mini-button" type="button" @click="copyKey(item)">复制 Key</button>
          <button
            class="admin-screen__mini-button"
            type="button"
            :disabled="isLoadingRecords && activeRecordKeyId === item.id"
            @click="loadKeyRecords(item)"
          >
            {{ activeRecordKeyId === item.id ? '查看中' : '查看记录' }}
          </button>
          <button
            class="admin-screen__mini-button is-danger"
            type="button"
            :disabled="isDeletingKeyId === item.id"
            @click="deleteKey(item)"
          >
            {{ isDeletingKeyId === item.id ? '删除中' : '删除 Key' }}
          </button>
          <p v-if="rowFeedback[item.id]" class="admin-screen__row-feedback">{{ rowFeedback[item.id] }}</p>
        </div>
      </article>
    </section>

    <section v-if="activeRecordKeyId" class="admin-screen__records">
      <div class="admin-screen__section-head">
        <div>
          <p class="eyebrow">Conversation Records</p>
          <h2>{{ activeRecordKeyName }} 的记录与图片</h2>
        </div>
        <small>{{ recordItems.length }} 条记录</small>
      </div>

      <p v-if="recordsError" class="admin-screen__error">{{ recordsError }}</p>
      <p v-else-if="isLoadingRecords" class="admin-screen__records-tip">正在加载该用户的历史记录与图片...</p>
      <p v-else-if="!recordItems.length" class="admin-screen__records-tip">该用户暂时还没有生成记录。</p>

      <article v-for="record in recordItems" :key="record.id" class="admin-screen__record-card">
        <div class="admin-screen__record-head">
          <div>
            <span class="admin-screen__record-time">{{ formatDate(record.created_at) }}</span>
            <h3>{{ record.prompt }}</h3>
          </div>
          <span class="admin-screen__status-pill" :class="{ 'is-live': record.status === 'success' }">
            {{ record.status === 'success' ? '成功' : record.status }}
          </span>
        </div>

        <p v-if="record.negative_prompt" class="admin-screen__record-negative">
          反向提示词：{{ record.negative_prompt }}
        </p>

        <div class="admin-screen__record-images">
          <section class="admin-screen__record-panel">
            <div class="admin-screen__record-panel-head">
              <span>输入图</span>
              <small>{{ record.input_images.length }} 张</small>
            </div>
            <div v-if="record.input_images.length" class="admin-screen__input-grid">
              <figure v-for="image in record.input_images" :key="image.id" class="admin-screen__thumb-card">
                <img :src="image.url" :alt="image.original_name" />
                <figcaption>{{ image.original_name }}</figcaption>
              </figure>
            </div>
            <p v-else class="admin-screen__records-tip">该记录没有输入图。</p>
          </section>

          <section class="admin-screen__record-panel">
            <div class="admin-screen__record-panel-head">
              <span>结果图</span>
              <small v-if="record.parent_record_id">来源记录 #{{ record.parent_record_id }}</small>
            </div>
            <figure v-if="record.image_url" class="admin-screen__result-card">
              <img :src="record.image_url" :alt="record.prompt" />
            </figure>
            <p v-else class="admin-screen__records-tip">该记录当前没有结果图。</p>
          </section>
        </div>
      </article>
    </section>
  </main>
</template>
