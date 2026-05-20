<script setup lang="ts">
import type { HistoryItem } from '@/stores/session'

defineProps<{
  items: HistoryItem[]
}>()

const emit = defineEmits<{
  select: [item: HistoryItem]
}>()
</script>

<template>
  <aside class="history-drawer">
    <div class="panel-title">
      <span>历史回顾</span>
      <small>独立会话</small>
    </div>
    <button
      v-for="item in items"
      :key="item.id"
      class="history-drawer__item"
      type="button"
      @click="emit('select', item)"
    >
      <img v-if="item.imageUrl" :src="item.imageUrl" alt="" />
      <div>
        <strong>{{ item.prompt }}</strong>
        <p>{{ item.status }} · {{ new Date(item.createdAt).toLocaleString() }}</p>
      </div>
    </button>
  </aside>
</template>
