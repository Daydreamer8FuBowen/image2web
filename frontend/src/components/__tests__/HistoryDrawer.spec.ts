import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import HistoryDrawer from '@/components/HistoryDrawer.vue'

describe('HistoryDrawer', () => {
  it('emits selected history item without navigation', async () => {
    const item = {
      id: 1,
      prompt: '测试历史',
      createdAt: new Date().toISOString(),
      status: 'success',
      imageUrl: null,
    }
    const wrapper = mount(HistoryDrawer, {
      props: { items: [item] },
    })

    await wrapper.find('.history-drawer__item').trigger('click')
    expect(wrapper.emitted('select')?.[0]?.[0]).toEqual(item)
  })
})
