export type AnalyticsRange = 'today' | 'yesterday' | 'last_7_days' | 'last_30_days' | 'custom'

export interface RangeSelection {
  range: AnalyticsRange
  from: string
  to: string
  timezone: string
}

export interface AnalyticsRangeInfo {
  from: string
  to: string
  prev_from: string | null
  prev_to: string | null
  timezone: string
}

/** Metric keys — use these exactly. */
export interface AnalyticsMetrics {
  clicks: number
  campaign_unique_clicks: number
  conversions: number
  leads: number
  sales: number
  rejected: number
  cr: number
  cost: number
  revenue: number
  profit: number
  roi: number
  epc: number
  cpa: number
}

export type AnalyticsMetricKey = keyof AnalyticsMetrics

/** Deltas are % change vs the previous period and may be null. */
export type AnalyticsDeltas = Partial<Record<AnalyticsMetricKey, number | null>>

export interface AnalyticsOverview {
  range: AnalyticsRangeInfo
  metrics: AnalyticsMetrics
  deltas: AnalyticsDeltas
}

export interface AnalyticsTrendItem {
  day: string
  clicks: number
  conversions: number
  revenue: number
  cost: number
  profit: number
  roi: number
  cr: number
}

export interface AnalyticsTrends {
  range: AnalyticsRangeInfo
  items: AnalyticsTrendItem[]
}

export interface AnalyticsStreamItem {
  stream_id: number
  stream_name: string
  clicks: number
  conversions: number
  revenue: number
  cost: number
  profit: number
  roi: number
  cr: number
}

export interface AnalyticsOfferItem {
  offer_id: number
  offer_name: string
  offer_state: string
  clicks: number
  conversions: number
  revenue: number
  cost: number
  profit: number
  roi: number
  cr: number
}

export interface AnalyticsGeoItem {
  country: string
  clicks: number
  conversions: number
  cr: number
  revenue: number
  cost: number
  profit: number
  roi: number
  epc: number
  cpa: number
}

export interface AnalyticsCampaign {
  range: AnalyticsRangeInfo
  campaign_id: number
  metrics: AnalyticsMetrics
  streams: AnalyticsStreamItem[]
  offers: AnalyticsOfferItem[]
  geo: AnalyticsGeoItem[]
}

export interface AnalyticsOffersItem {
  offer_id: number
  offer_name: string
  offer_state: string
  clicks: number
  campaign_unique_clicks: number
  conversions: number
  leads: number
  sales: number
  rejected: number
  cr: number
  cost: number
  revenue: number
  profit: number
  roi: number
  epc: number
  cpa: number
  planned_share?: number
  actual_share?: number
}

export interface AnalyticsOffersResponse {
  range: AnalyticsRangeInfo
  campaign_id: number | null
  items: AnalyticsOffersItem[]
}

export interface AnalyticsGeoResponse {
  range: AnalyticsRangeInfo
  items: AnalyticsGeoItem[]
}

export interface AnalyticsQuery {
  range: AnalyticsRange
  from?: string
  to?: string
  timezone?: string
}

export interface AnalyticsFilterQuery extends AnalyticsQuery {
  campaign_id?: number
}

export interface AnalyticsExportQuery {
  type: 'campaigns' | 'offers' | 'geo' | 'streams'
  campaign_id?: number
  range?: AnalyticsRange
  from?: string
  to?: string
  timezone?: string
}
