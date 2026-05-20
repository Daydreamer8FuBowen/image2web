import { defineStore } from 'pinia'
import { ref } from 'vue'

import { clearAdminKey, getAdminKey, setAdminKey } from '@/api/client'

export const useAdminSessionStore = defineStore('admin-session', () => {
  const apiKey = ref(getAdminKey())
  const totalKeys = ref(0)
  const totalTasks = ref(0)
  const successRecords = ref(0)
  const failedTasks = ref(0)

  function updateApiKey(value: string) {
    apiKey.value = value
    setAdminKey(value)
  }

  function clearApiKey() {
    apiKey.value = ''
    clearAdminKey()
  }

  return {
    apiKey,
    totalKeys,
    totalTasks,
    successRecords,
    failedTasks,
    updateApiKey,
    clearApiKey,
  }
})
