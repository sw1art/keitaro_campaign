import type { AdRobotApi } from '~/types/api-client'
import { createRealApi } from '~/utils/apiClient'
import { createMockApi } from '~/mock/mockApi'

let client: AdRobotApi | null = null

/**
 * Returns the single API client for the app. Chooses the in-browser mock when
 * NUXT_PUBLIC_MOCK=true, otherwise the real HTTP client pointed at
 * runtimeConfig.public.apiBase.
 */
export function useApi(): AdRobotApi {
  if (client) return client

  const config = useRuntimeConfig()
  const mockValue: unknown = config.public.mock
  const mock = mockValue === true || mockValue === 'true' || mockValue === '1'
  const base = typeof config.public.apiBase === 'string' ? config.public.apiBase : 'http://localhost:8000/api/v1'

  client = mock ? createMockApi() : createRealApi(base)
  return client
}

export function isMockMode(): boolean {
  const config = useRuntimeConfig()
  const mockValue: unknown = config.public.mock
  return mockValue === true || mockValue === 'true' || mockValue === '1'
}
