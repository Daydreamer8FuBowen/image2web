import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient } from '@/api/client'
import { useGenerationTask } from '@/composables/useGenerationTask'
import { useSessionStore } from '@/stores/session'

describe('useGenerationTask', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('blocks submit when image count exceeds three', async () => {
    const session = useSessionStore()
    session.selectedImages = [
      { id: '1', name: '1', preview: 'a', sourceType: 'upload' },
      { id: '2', name: '2', preview: 'b', sourceType: 'upload' },
      { id: '3', name: '3', preview: 'c', sourceType: 'upload' },
      { id: '4', name: '4', preview: 'd', sourceType: 'upload' },
    ]
    const postSpy = vi.spyOn(apiClient, 'post')
    const { submitTask } = useGenerationTask()

    await submitTask()

    expect(postSpy).not.toHaveBeenCalled()
    expect(session.currentError).toContain('最多上传 3 张图片')
  })

  it('blocks repeated submit while task is processing', async () => {
    const session = useSessionStore()
    session.currentTaskStatus = 'processing'
    const postSpy = vi.spyOn(apiClient, 'post')
    const { submitTask } = useGenerationTask()

    await submitTask()

    expect(postSpy).not.toHaveBeenCalled()
  })

  it('maps history response fields for prompt, time and image display', async () => {
    const session = useSessionStore()
    vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
      data: [
        {
          id: 7,
          prompt: '生成豆包大战gpt的现代3d动画风格图片',
          status: 'success',
          created_at: '2026-05-20T06:39:30Z',
          image_url: '/static/images/2026/05/20/demo.png',
        },
      ],
    })
    const { loadHistory } = useGenerationTask()

    await loadHistory()

    expect(session.historyItems[0]).toMatchObject({
      id: 7,
      prompt: '生成豆包大战gpt的现代3d动画风格图片',
      status: 'success',
      createdAt: '2026-05-20T06:39:30Z',
      imageUrl: expect.stringContaining('/static/images/2026/05/20/demo.png'),
    })
  })
})
