import type { OperationStatus } from './operation'

export interface Campaign {
  id: number
  name: string
  state: string
  alias: string
  domain: string
  domain_id: number
  traffic_source_id: number
  traffic_source: string
  group_id: number
  group: string
  cost_type: string
  cost_value: number
  cost_currency: string
  created_at: string
  updated_at: string
}

export interface CreateCampaignRequest {
  name: string
  geo: string[]
  offer_ids: number[]
  domain_id: number
}

export interface CreateCampaignResponse {
  operation_id: string
  status: OperationStatus
  message: string
}
