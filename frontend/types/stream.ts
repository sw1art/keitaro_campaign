export interface StreamFilter {
  name: string
  mode: string
  payload: string[]
}

export interface StreamOffer {
  offer_id: number
  state: string
  share: number
}

export interface Stream {
  id: number
  type: string
  name: string
  campaign_id: number
  position: number
  state: string
  schema: string
  action_type: string
  action_payload: string
  collect_clicks: boolean
  filter_or: boolean
  weight: number
  offer_selection: string
  filters: StreamFilter[]
  offers: StreamOffer[]
  landings: unknown[]
}

export interface StreamOfferUpdate {
  offer_id: number
  share: number
}

export interface UpdateStreamOffersRequest {
  offers: StreamOfferUpdate[]
}
