<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import GenerationResult from '@/components/GenerationResult.vue'
import HistoryDrawer from '@/components/HistoryDrawer.vue'
import PromptComposer from '@/components/PromptComposer.vue'
import RevisionChainPanel from '@/components/RevisionChainPanel.vue'
import TaskStatusPanel from '@/components/TaskStatusPanel.vue'
import TemplateGallery from '@/components/TemplateGallery.vue'
import UploadImageTray from '@/components/UploadImageTray.vue'
import { useGenerationTask } from '@/composables/useGenerationTask'
import { styleTemplates, type StyleTemplate } from '@/data/style-templates'
import { useSessionStore, type HistoryItem } from '@/stores/session'

const session = useSessionStore()
const router = useRouter()
const { loadHistory, submitTask } = useGenerationTask()

function handleTemplateSelect(item: StyleTemplate) {
  session.prompt = item.prompt
  session.negativePrompt = item.negativePrompt
}

function handleImagePick(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  const available = 3 - session.selectedImages.length
  files.slice(0, available).forEach((file) => {
    session.selectedImages.push({
      id: `${file.name}-${file.size}-${Date.now()}`,
      name: file.name,
      preview: URL.createObjectURL(file),
      sourceType: 'upload',
      file,
    })
  })
  input.value = ''
}

function removeImage(id: string) {
  session.selectedImages = session.selectedImages.filter((item: (typeof session.selectedImages)[number]) => item.id !== id)
}

function reuseImage(url: string) {
  if (session.selectedImages.length >= 3) return
  session.selectedImages.push({
    id: `history-${Date.now()}`,
    name: '历史结果图',
    preview: url,
    sourceType: 'history',
  })
}

function handleHistorySelect(item: HistoryItem) {
  session.prompt = item.prompt
  if (item.imageUrl) {
    session.currentImageUrl = item.imageUrl
    session.currentTaskStatus = item.status === 'failed' ? 'failed' : 'success'
    session.currentError = ''
    session.currentTaskId = null
  }
}

async function handleLogout() {
  session.clearApiKey()
  await router.replace('/login')
}

onMounted(() => {
  void loadHistory()
})
</script>

<template>
  <main class="workspace">
    <HistoryDrawer :items="session.historyItems" @select="handleHistorySelect" />

    <section class="workspace__center">
      <header class="workspace__hero">
        <div>
          <p class="eyebrow">Image2web</p>
          <h1>像对话一样编辑图片，但每次生成都独立完成</h1>
          <p class="workspace__lead">
            登录鉴权已在入口完成。这里保留专注编辑体验，只处理图片、提示词与生成过程。
          </p>
        </div>
        <div class="workspace__hero-actions">
          <button class="admin-screen__ghost-button" type="button" @click="handleLogout">退出登录</button>
        </div>
      </header>

      <UploadImageTray :items="session.selectedImages" @pick="handleImagePick" @remove="removeImage" />

      <PromptComposer
        :prompt="session.prompt"
        :disabled="session.currentTaskStatus === 'pending' || session.currentTaskStatus === 'processing'"
        :image-count="session.selectedImages.length"
        @update:prompt="session.prompt = $event"
        @submit="submitTask"
      />

      <TaskStatusPanel :status="session.currentTaskStatus" :error="session.currentError" />
      <GenerationResult :image-url="session.currentImageUrl" :status="session.currentTaskStatus" :prompt="session.prompt" @reuse="reuseImage" />
    </section>

    <section class="workspace__right">
      <RevisionChainPanel :current-image-url="session.currentImageUrl" :image-count="session.selectedImages.length" />
      <TemplateGallery :items="styleTemplates" @select="handleTemplateSelect" />
    </section>
  </main>
</template>
