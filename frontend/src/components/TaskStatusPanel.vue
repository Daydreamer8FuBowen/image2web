<script setup lang="ts">
defineProps<{
  status: string
  error?: string
}>()

const labels: Record<string, string> = {
  idle: '尚未开始',
  pending: '排队中',
  processing: '生成中',
  success: '已完成',
  failed: '失败',
}

const descriptions: Record<string, string> = {
  idle: '准备好提示词和参考图后即可开始一次新的独立生成。',
  pending: '任务已经提交，系统正在为这次生成分配处理资源。',
  processing: '图像正在生成中，当前已锁定重复提交，请稍候查看结果。',
  success: '本次生成已经完成，可以查看结果或基于结果继续编辑。',
  failed: '本次任务未成功完成，请检查提示词或稍后重新提交。',
}
</script>

<template>
  <section class="task-status">
    <div class="panel-title">
      <span>任务状态</span>
      <strong>{{ labels[status] || status }}</strong>
    </div>

    <div v-if="status === 'pending' || status === 'processing'" class="task-status__scene" :class="[`is-${status}`]">
      <div class="task-status__orbit">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
    <p>{{ descriptions[status] || descriptions.idle }}</p>
    <p v-if="status === 'failed'" class="task-status__error">{{ error || '本次任务执行失败' }}</p>
  </section>
</template>
