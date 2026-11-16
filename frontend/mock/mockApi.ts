import type { ListResponse } from '~/types/api'
import type { AdRobotApi } from '~/types/api-client'
import type { AuditLogItem } from '~/types/audit'
import type { Campaign, CreateCampaignRequest, CreateCampaignResponse } from '~/types/campaign'
import type { Dashboard } from '~/types/dashboard'
import type { Operation } from '~/types/operation'
import type { Stream } from '~/types/stream'
import { ApiError } from '~/utils/apiError'
import { dbDate, DOMAINS, GEO, isoDate, makeCampaigns, makeOperations, makeStreams, OFFERS, TRAFFIC_SOURCES } from './data'

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function uuid(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `op-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function paginate<T>(items: T[], page: number, pageSize: number): ListResponse<T> {
  const start = (page - 1) * pageSize
  return { items: items.slice(start, start + pageSize), total: items.length, page, page_size: pageSize }
}

function mockFingerprint(offers: Array<{ offer_id: number; share: number }>): string {
  return offers
    .map((offer) => `${offer.offer_id}:${offer.share}`)
    .sort()
    .join('|')
}

/**
 * In-browser mock implementing the exact AdRobotApi contract. Keeps a mutable
 * in-memory state so pages render and buttons/percentages can be exercised
 * without the FastAPI backend. Enabled via NUXT_PUBLIC_MOCK=true.
 */
export function createMockApi(): AdRobotApi {
  const campaigns: Campaign[] = makeCampaigns()
  const operations: Operation[] = makeOperations()
  const streamsByCampaign = new Map<number, Stream[]>()
  let nextStreamId = 1311444
  let nextCampaignId = 212162

  for (const campaign of campaigns) {
    const index = campaigns.indexOf(campaign)
    const offerIds = OFFERS.slice((index * 2) % OFFERS.length, ((index * 2) % OFFERS.length) + 3).map((o) => o.id)
    const result = makeStreams(campaign, offerIds, nextStreamId)
    nextStreamId = result.nextStreamId
    streamsByCampaign.set(campaign.id, result.streams)
  }

  function findStream(id: number): Stream | null {
    for (const streams of streamsByCampaign.values()) {
      const found = streams.find((stream) => stream.id === id)
      if (found) return found
    }
    return null
  }

  return {
    async listCampaigns(params) {
      await delay(250)
      let items = [...campaigns]
      if (params?.search) {
        const query = params.search.toLowerCase()
        items = items.filter((c) => String(c.id).includes(query) || c.name.toLowerCase().includes(query))
      }
      if (params?.state) items = items.filter((c) => c.state === params.state)
      const sortBy = params?.sort_by ?? 'created_at'
      const sortOrder = params?.sort_order ?? 'desc'
      items.sort((a, b) => {
        const av = (a as unknown as Record<string, unknown>)[sortBy]
        const bv = (b as unknown as Record<string, unknown>)[sortBy]
        const result =
          typeof av === 'number' && typeof bv === 'number'
            ? av - bv
            : String(av ?? '').localeCompare(String(bv ?? ''))
        return sortOrder === 'asc' ? result : -result
      })
      return paginate(items, params?.page ?? 1, params?.page_size ?? 20)
    },

    async getCampaign(id) {
      await delay(200)
      const campaign = campaigns.find((c) => c.id === id)
      if (!campaign) throw new ApiError('NOT_FOUND', `Campaign ${id} not found`, 404)
      return clone(campaign)
    },

    async getCampaignStreams(id) {
      await delay(200)
      const streams = streamsByCampaign.get(id)
      if (!streams) throw new ApiError('NOT_FOUND', `Campaign ${id} not found`, 404)
      return clone(streams)
    },

    async createCampaign(body: CreateCampaignRequest) {
      await delay(300)
      const operationId = uuid()
      const operation: Operation = {
        operation_id: operationId,
        type: 'campaign.create',
        status: 'pending',
        campaign_id: null,
        error: null,
        current_stage: 'pending',
        progress: 0,
        started_at: null,
        finished_at: null,
        created_at: isoDate(new Date()),
        completed_at: null,
      }
      operations.unshift(operation)

      setTimeout(() => {
        operation.status = 'processing'
        operation.current_stage = 'creating_campaign'
        operation.progress = 15
        operation.started_at = isoDate(new Date())
      }, 600)

      setTimeout(() => {
        operation.current_stage = 'creating_google_stream'
        operation.progress = 40
      }, 1200)

      setTimeout(() => {
        operation.current_stage = 'creating_offer_stream'
        operation.progress = 65
      }, 1800)

      setTimeout(() => {
        operation.current_stage = 'verifying'
        operation.progress = 90
      }, 2400)

      setTimeout(() => {
        const campaignId = nextCampaignId++
        const domain = DOMAINS.find((d) => d.id === body.domain_id)
        const now = new Date()
        const campaign: Campaign = {
          id: campaignId,
          name: body.name,
          state: 'active',
          alias: `alias-${campaignId}`,
          domain: domain ? `https://${domain.name}/` : 'https://unknown/',
          domain_id: body.domain_id,
          traffic_source_id: 836,
          traffic_source: 'FORTESTS',
          group_id: 10332,
          group: 'FORTESTS',
          cost_type: 'CPC',
          cost_value: 0,
          cost_currency: 'USD',
          created_at: dbDate(now),
          updated_at: dbDate(now),
        }
        campaigns.unshift(campaign)
        const result = makeStreams(campaign, body.offer_ids, nextStreamId)
        nextStreamId = result.nextStreamId
        streamsByCampaign.set(campaign.id, result.streams)
        operation.status = 'completed'
        operation.current_stage = 'completed'
        operation.progress = 100
        operation.campaign_id = campaignId
        operation.finished_at = isoDate(new Date())
        operation.completed_at = isoDate(new Date())
      }, 3000)

      const response: CreateCampaignResponse = {
        operation_id: operationId,
        status: 'pending',
        message: 'Campaign creation started',
        warnings: [],
      }
      return response
    },

    async getStream(id) {
      await delay(200)
      const stream = findStream(id)
      if (!stream) throw new ApiError('NOT_FOUND', `Stream ${id} not found`, 404)
      return clone(stream)
    },

    async updateStreamOffers(id, body) {
      await delay(300)
      const stream = findStream(id)
      if (!stream) throw new ApiError('NOT_FOUND', `Stream ${id} not found`, 404)
      const current = mockFingerprint(stream.offers)
      if (body.base_fingerprint && body.base_fingerprint !== current) {
        throw new ApiError('CONFLICT', 'The stream was modified by someone else. Reload the campaign and retry.', 409)
      }
      stream.offers = body.offers.map((offer) => ({ offer_id: offer.offer_id, state: 'active', share: offer.share }))
      stream.fingerprint = mockFingerprint(stream.offers)
      return clone(stream)
    },

    async listOperations(params) {
      await delay(250)
      const items = [...operations].sort((a, b) => b.created_at.localeCompare(a.created_at))
      return paginate(items, params?.page ?? 1, params?.page_size ?? 20)
    },

    async getOperation(id) {
      await delay(200)
      const operation = operations.find((o) => o.operation_id === id)
      if (!operation) throw new ApiError('NOT_FOUND', `Operation ${id} not found`, 404)
      return clone(operation)
    },

    async retryOperation(id) {
      await delay(250)
      const operation = operations.find((o) => o.operation_id === id)
      if (!operation) throw new ApiError('NOT_FOUND', `Operation ${id} not found`, 404)
      if (operation.status !== 'failed') {
        throw new ApiError('CONFLICT', 'Only failed operations can be retried.', 409)
      }
      operation.status = 'pending'
      operation.error = null
      operation.current_stage = 'pending'
      operation.progress = 0
      operation.started_at = null
      operation.finished_at = null
      operation.completed_at = null
      return clone(operation)
    },

    async getOperationAudit(id) {
      await delay(200)
      const entries: AuditLogItem[] = [
        {
          id: uuid(),
          operation_id: id,
          action: 'campaign.create',
          entity_type: 'campaign',
          entity_id: '212150',
          details: { keitaro_id: 212150 },
          created_at: isoDate(new Date()),
        },
      ]
      return entries
    },

    async getDashboard() {
      await delay(250)
      const recentCampaigns = [...campaigns].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5)
      const recentOperations = [...operations].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 5)
      const dashboard: Dashboard = {
        campaigns_count: campaigns.length,
        recent_campaigns: recentCampaigns,
        operations_total: operations.length,
        operations_completed: operations.filter((o) => o.status === 'completed').length,
        operations_failed: operations.filter((o) => o.status === 'failed').length,
        recent_operations: recentOperations,
      }
      return dashboard
    },

    async listGeo() {
      await delay(150)
      return clone(GEO)
    },

    async listOffers(params = {}) {
      await delay(250)
      const stateFilter = params.state ?? 'active'
      let items = OFFERS.filter((o) => o.state === stateFilter)
      if (params.search) {
        const query = params.search.toLowerCase()
        items = items.filter((o) => String(o.id).includes(query) || o.name.toLowerCase().includes(query))
      }
      return paginate(items, params.page ?? 1, params.page_size ?? 20)
    },

    async listDomains() {
      await delay(200)
      return clone(DOMAINS)
    },

    async listTrafficSources() {
      await delay(200)
      return clone(TRAFFIC_SOURCES)
    },
  }
}
