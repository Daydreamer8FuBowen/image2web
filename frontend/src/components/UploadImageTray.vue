<script setup lang="ts">
import type { WorkspaceImage } from '@/stores/session'

defineProps<{
  items: WorkspaceImage[]
}>()

const emit = defineEmits<{
  remove: [id: string]
  pick: [event: Event]
}>()
</script>

<template>
  <section class="upload-tray">
    <div class="upload-tray__header">
      <span>输入图片</span>
      <strong>{{ items.length }}/3</strong>
    </div>
    <div class="upload-tray__list">
      <label class="upload-tray__dropzone" :class="{ 'is-disabled': items.length >= 3 }">
        <input
          class="sr-only"
          type="file"
          accept=".png,.jpg,.jpeg,.webp"
          multiple
          :disabled="items.length >= 3"
          @change="emit('pick', $event)"
        />
        <span>{{ items.length >= 3 ? '已达上限' : '拖拽或选择图片' }}</span>
      </label>
      <article v-for="item in items" :key="item.id" class="upload-tray__card">
        <img :src="item.preview" :alt="item.name" />
        <div>
          <p>{{ item.name }}</p>
          <small>{{ item.sourceType === 'history' ? '来自历史结果' : '本地上传' }}</small>
        </div>
        <button type="button" @click="emit('remove', item.id)">移除</button>
      </article>
    </div>
  </section>
</template>
