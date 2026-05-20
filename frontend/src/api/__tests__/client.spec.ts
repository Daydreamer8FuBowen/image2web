import { describe, expect, it } from 'vitest'

import { apiClient, resolveAssetUrl } from '@/api/client'
import { env } from '@/config/env'

describe('apiClient', () => {
  it('uses env api base url', () => {
    expect(apiClient.defaults.baseURL).toBe(env.apiBaseUrl)
  })

  it('resolves relative asset urls to backend origin', () => {
    expect(resolveAssetUrl('/static/images/demo.png')).toBe(`${env.apiBaseUrl}/static/images/demo.png`)
  })
})
