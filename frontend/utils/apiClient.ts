import type { AdRobotApi } from '~/types/api-client'
import type {
  AnalyticsCampaign,
  AnalyticsExportQuery,
  AnalyticsFilterQuery,
  AnalyticsGeoResponse,
  AnalyticsOffersResponse,
  AnalyticsOverview,
  AnalyticsQuery,
  AnalyticsTrends,
} from '~/types/analytics'
import type { AuditLogItem } from '~/types/audit'
import type { Campaign, CreateCampaignRequest, CreateCampaignResponse } from '~/types/campaign'
import type { Dashboard } from '~/types/dashboard'
import type { Domain } from '~/types/domain'
import type { GeoCountry } from '~/types/geo'
import type { Group } from '~/types/group'
import type { Offer } from '~/types/offer'
import type { Operation } from '~/types/operation'
import type { Stream, UpdateStreamOffersRequest } from '~/types/stream'
import type { TrafficSource } from '~/types/traffic-source'
import type { ListResponse } from '~/types/api'
import { ApiError } from './apiError'

const DEFAULT_TIMEOUT_MS = 15_000

// Shared API token, set once when the client is created.
let apiToken: string | undefined

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  query?: Record<string, unknown>
  body?: unknown
}

function toQuery(params: object | undefined): Record<string, unknown> | undefined {
  if (!params) return undefined
  const out: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    out[key] = value
  }
  return out
}

function buildUrl(base: string, path: string, query?: Record<string, unknown>): string {
  const url = new URL(base.replace(/\/+$/, '') + (path.startsWith('/') ? path : `/${path}`))
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      url.searchParams.set(key, String(value))
    }
  }
  return url.toString()
}

async function request<T>(base: string, path: string, options: RequestOptions = {}): Promise<T> {
  const url = buildUrl(base, path, options.query)
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS)

  const headers: Record<string, string> = {}
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (apiToken) headers['X-Api-Key'] = apiToken

  try {
    const response = await fetch(url, {
      method: options.method ?? 'GET',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    })

    const text = await response.text()
    let data: unknown = null
    if (text) {
      try {
        data = JSON.parse(text)
      } catch {
        data = null
      }
    }

    if (!response.ok) {
      const body = data as { error?: { code?: string; message?: string } } | null
      throw new ApiError(
        body?.error?.code ?? 'HTTP_ERROR',
        body?.error?.message ?? `Request failed with status ${response.status}`,
        response.status,
      )
    }

    return data as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (typeof error === 'object' && error !== null && (error as { name?: string }).name === 'AbortError') {
      throw new ApiError('TIMEOUT', 'Request timed out', 0)
    }
    throw new ApiError('NETWORK_ERROR', 'Не удалось подключиться к API серверу', 0)
  } finally {
    clearTimeout(timer)
  }
}

export function createRealApi(base: string, token?: string): AdRobotApi {
  apiToken = token
  return {
    listCampaigns: (params) =>
      request<ListResponse<Campaign>>(base, '/campaigns', {
        query: toQuery(params),
      }),

    getCampaign: (id) => request<Campaign>(base, `/campaigns/${id}`),

    getCampaignStreams: async (id) => {
      const data = await request<{ items: Stream[] }>(base, `/campaigns/${id}/streams`)
      return data.items
    },

    createCampaign: (body: CreateCampaignRequest) =>
      request<CreateCampaignResponse>(base, '/campaigns', { method: 'POST', body }),

    getStream: (id) => request<Stream>(base, `/streams/${id}`),

    updateStreamOffers: (id, body: UpdateStreamOffersRequest) =>
      request<Stream>(base, `/streams/${id}/offers`, { method: 'PUT', body }),

    listOperations: (params) =>
      request<ListResponse<Operation>>(base, '/operations', { query: toQuery(params) }),

    getOperation: (id) => request<Operation>(base, `/operations/${id}`),

    retryOperation: (id) => request<Operation>(base, `/operations/${id}/retry`, { method: 'POST' }),

    getOperationAudit: async (id) => {
      const data = await request<{ items: AuditLogItem[] }>(base, `/operations/${id}/audit`)
      return data.items
    },

    getDashboard: () => request<Dashboard>(base, '/dashboard'),

    listGeo: async () => {
      const data = await request<{ items: GeoCountry[] }>(base, '/dictionaries/geo')
      return data.items
    },

    listOffers: (params) =>
      request<ListResponse<Offer>>(base, '/offers', { query: toQuery(params) }),

    listDomains: async () => {
      const data = await request<{ items: Domain[] }>(base, '/domains')
      return data.items
    },

    listTrafficSources: async () => {
      const data = await request<{ items: TrafficSource[] }>(base, '/traffic-sources')
      return data.items
    },

    listGroups: async () => {
      const data = await request<{ items: Group[] }>(base, '/groups')
      return data.items
    },

    getAnalyticsOverview: (params) =>
      request<AnalyticsOverview>(base, '/analytics/overview', { query: toQuery(params) }),

    getAnalyticsTrends: (params) =>
      request<AnalyticsTrends>(base, '/analytics/trends', { query: toQuery(params) }),

    getAnalyticsCampaign: (id, params) =>
      request<AnalyticsCampaign>(base, `/analytics/campaigns/${id}`, { query: toQuery(params) }),

    getAnalyticsOffers: (params) =>
      request<AnalyticsOffersResponse>(base, '/analytics/offers', { query: toQuery(params) }),

    getAnalyticsGeo: (params) =>
      request<AnalyticsGeoResponse>(base, '/analytics/geo', { query: toQuery(params) }),

    getAnalyticsExportUrl: (params: AnalyticsExportQuery) => buildUrl(base, '/analytics/export', toQuery(params)),
  }
}
