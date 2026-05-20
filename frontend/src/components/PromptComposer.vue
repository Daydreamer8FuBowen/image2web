<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  prompt: string
  disabled?: boolean
  imageCount: number
}>()

const emit = defineEmits<{
  'update:prompt': [value: string]
  submit: []
}>()

const helperText = computed(() =>
  props.disabled
    ? '当前任务生成中，工作台已临时锁定提交入口'
    : `每次生成独立计算，可上传 ${props.imageCount}/3 张参考图`,
)
</script>

<template>
  <section class="prompt-composer">
    <div class="prompt-composer__heading">
      <div>
        <span class="eyebrow">Image Studio</span>
        <h2>把图片编辑当作一段专注对话</h2>
      </div>
      <p>{{ helperText }}</p>
    </div>
    <textarea
      class="prompt-composer__main"
      :value="prompt"
      placeholder="描述你想对图片做的修改，例如：把背景换成暖色木纹桌面，主体保留真实材质与阴影。"
      @input="emit('update:prompt', ($event.target as HTMLTextAreaElement).value)"
    />
    <button class="prompt-composer__submit" type="button" :disabled="disabled" @click="emit('submit')">
      {{ disabled ? '生成中...' : '开始生成' }}
    </button>
  </section>
</template>
