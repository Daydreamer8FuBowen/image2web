<script setup lang="ts">
defineProps<{
  currentImageUrl?: string
  imageCount: number
}>()
</script>

<template>
  <section class="revision-chain">
    <div class="panel-title">
      <span>编辑链路</span>
      <small>无多轮记忆</small>
    </div>
    <p>当前任务是一次新的独立编辑，可基于历史结果继续修改，但不会继承旧对话上下文。</p>
    <div class="revision-chain__stats">
      <span>当前输入图：{{ imageCount }} / 3</span>
      <span>{{ currentImageUrl ? '已有最新结果' : '暂无结果图' }}</span>
    </div>
  </section>
</template>
