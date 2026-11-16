export interface ListResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ListParams {
  page?: number
  page_size?: number
}

export interface CampaignListParams extends ListParams {
  search?: string
  state?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  domain_id?: number
  traffic_source_id?: number
  group_id?: number
}

export interface OfferListParams extends ListParams {
  search?: string
  state?: string
}

export interface OperationListParams extends ListParams {}
