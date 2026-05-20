import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import PromptComposer from '@/components/PromptComposer.vue'

describe('PromptComposer', () => {
  it('shows current image count helper', () => {
    const wrapper = mount(PromptComposer, {
      props: {
        prompt: '',
        imageCount: 3,
      },
    })

    expect(wrapper.text()).toContain('3/3')
  })
})
