import { defineStore } from 'pinia'
import { ref } from 'vue'

import { clearUserKey, getUserKey, setUserKey } from '@/api/client'

export type WorkspaceImage = {
  id: string
  name: string
  preview: string
  sourceType: 'upload' | 'history'
  file?: File
}

export type HistoryItem = {
  id: number
  prompt: string
  imageUrl?: string | null
  createdAt: string
  status: string
}

export const useSessionStore = defineStore('session', () => {
  const apiKey = ref(getUserKey())
  const remainingCount = ref<number | null>(null)
  const prompt = ref('')
  const negativePrompt = ref('')
  const selectedImages = ref<WorkspaceImage[]>([])
  const currentTaskId = ref<number | null>(null)
  const currentTaskStatus = ref<'idle' | 'pending' | 'processing' | 'success' | 'failed'>('idle')
  const currentImageUrl = ref('')
  const currentError = ref('')
  const historyItems = ref<HistoryItem[]>([])

  function updateApiKey(value: string) {
    apiKey.value = value
    setUserKey(value)
  }

  function clearApiKey() {
    apiKey.value = ''
    remainingCount.value = null
    clearUserKey()
  }

  return {
    apiKey,
    remainingCount,
    prompt,
    negativePrompt,
    selectedImages,
    currentTaskId,
    currentTaskStatus,
    currentImageUrl,
    currentError,
    historyItems,
    updateApiKey,
    clearApiKey,
  }
})
