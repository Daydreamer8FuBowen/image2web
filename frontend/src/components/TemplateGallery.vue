<script setup lang="ts">
import type { StyleTemplate } from '@/data/style-templates'

defineProps<{
  items: StyleTemplate[]
}>()

const emit = defineEmits<{
  select: [item: StyleTemplate]
}>()
</script>

<template>
  <section class="template-gallery">
    <div class="panel-title">
      <span>风格模板</span>
      <small>点击即填充提示词</small>
    </div>
    <article v-for="item in items" :key="item.id" class="template-gallery__card" @click="emit('select', item)">
      <img :src="item.preview" :alt="item.name" />
      <div>
        <h3>{{ item.name }}</h3>
        <p>{{ item.description }}</p>
      </div>
    </article>
  </section>
</template>
