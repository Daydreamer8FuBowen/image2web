import { getCurrentInstance, onBeforeUnmount } from 'vue'

import { apiClient, resolveAssetUrl } from '@/api/client'
import { useSessionStore } from '@/stores/session'

let pollTimer: number | null = null

export function useGenerationTask() {
  const session = useSessionStore()

  async function submitTask() {
    if (session.currentTaskStatus === 'pending' || session.currentTaskStatus === 'processing') {
      return
    }

    if (session.selectedImages.length > 3) {
      session.currentError = '最多上传 3 张图片'
      return
    }

    const formData = new FormData()
    formData.append('prompt', session.prompt)
    formData.append('negativePrompt', session.negativePrompt || '')
    session.selectedImages.forEach((item: { file?: File }) => {
      if (item.file) {
        formData.append('images', item.file)
      }
    })

    session.currentError = ''
    session.currentImageUrl = ''
    session.currentTaskStatus = 'pending'
    const response = await apiClient.post('/api/generations', formData)
    session.currentTaskId = response.data.task_id
    startPolling()
  }

  async function loadHistory() {
    const response = await apiClient.get('/api/generations/history')
    session.historyItems = response.data.map((item: Record<string, unknown>) => ({
      id: Number(item.id),
      prompt: String(item.prompt ?? ''),
      status: String(item.status ?? 'idle'),
      createdAt: String(item.created_at ?? ''),
      imageUrl: resolveAssetUrl((item.image_url as string | null | undefined) ?? null),
    }))
  }

  async function pollTask() {
    if (!session.currentTaskId) return
    const response = await apiClient.get(`/api/generations/tasks/${session.currentTaskId}`)
    const data = response.data
    session.currentTaskStatus = data.status
    session.currentImageUrl = resolveAssetUrl(data.image_url)
    session.currentError = data.error_message || ''
    session.remainingCount = data.remaining_count
    if (data.status === 'success' || data.status === 'failed') {
      stopPolling()
      await loadHistory()
    }
  }

  function startPolling() {
    stopPolling()
    pollTimer = window.setInterval(() => {
      void pollTask()
    }, 2500)
    void pollTask()
  }

  function stopPolling() {
    if (pollTimer !== null) {
      window.clearInterval(pollTimer)
      pollTimer = null
    }
  }

  if (getCurrentInstance()) {
    onBeforeUnmount(stopPolling)
  }

  return {
    submitTask,
    loadHistory,
    pollTask,
    startPolling,
    stopPolling,
  }
}
