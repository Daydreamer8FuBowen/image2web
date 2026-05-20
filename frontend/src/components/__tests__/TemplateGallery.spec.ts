import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import TemplateGallery from '@/components/TemplateGallery.vue'
import { styleTemplates } from '@/data/style-templates'

describe('TemplateGallery', () => {
  it('emits selected template', async () => {
    const wrapper = mount(TemplateGallery, {
      props: { items: styleTemplates.slice(0, 1) },
    })

    await wrapper.find('.template-gallery__card').trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
  })
})
