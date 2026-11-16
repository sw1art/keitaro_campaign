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
}

export interface OfferListParams extends ListParams {
  search?: string
  state?: string
}

export interface OperationListParams extends ListParams {}
