<script setup lang="ts">
defineProps<{
  imageUrl?: string
  status: string
  prompt: string
}>()

const emit = defineEmits<{
  reuse: [url: string]
}>()

async function copyPrompt(prompt: string) {
  await navigator.clipboard.writeText(prompt)
}
</script>

<template>
  <section class="generation-result">
    <div class="panel-title">
      <span>结果画布</span>
      <small>每次生成都是独立任务</small>
    </div>
    <div v-if="imageUrl" class="generation-result__card">
      <img :src="imageUrl" alt="生成结果" />
      <div class="generation-result__actions">
        <button type="button" @click="emit('reuse', imageUrl)">设为输入图</button>
        <button type="button" @click="copyPrompt(prompt)">复制提示词</button>
      </div>
    </div>
    <div v-else class="generation-result__empty">
      <p>{{ status === 'processing' ? '正在等待图像返回...' : '生成后的图片会显示在这里。' }}</p>
    </div>
  </section>
</template>
