import type {
  AnalyticsCampaign,
  AnalyticsDeltas,
  AnalyticsGeoItem,
  AnalyticsGeoResponse,
  AnalyticsMetricKey,
  AnalyticsMetrics,
  AnalyticsOfferItem,
  AnalyticsOffersItem,
  AnalyticsOffersResponse,
  AnalyticsOverview,
  AnalyticsRange,
  AnalyticsRangeInfo,
  AnalyticsStreamItem,
  AnalyticsTrendItem,
  AnalyticsTrends,
} from '~/types/analytics'
import { OFFERS } from './data'

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

function toDateStr(d: Date): string {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

function addDays(d: Date, n: number): Date {
  const copy = new Date(d)
  copy.setDate(copy.getDate() + n)
  return copy
}

/** Deterministic pseudo-random in [0, 1) keyed on a string. */
function seeded(seed: string): number {
  let h = 2166136261
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return (h >>> 0) / 4294967295
}

export function resolveRange(
  range: AnalyticsRange,
  from?: string,
  to?: string,
  timezone = 'Europe/Moscow',
): AnalyticsRangeInfo {
  const today = new Date()
  let start: Date
  let end: Date
  switch (range) {
    case 'today':
      start = today
      end = today
      break
    case 'yesterday':
      start = addDays(today, -1)
      end = start
      break
    case 'last_7_days':
      start = addDays(today, -6)
      end = today
      break
    case 'last_30_days':
      start = addDays(today, -29)
      end = today
      break
    case 'custom':
    default:
      start = from ? new Date(`${from}T00:00:00`) : addDays(today, -6)
      end = to ? new Date(`${to}T00:00:00`) : today
      break
  }
  if (start > end) [start, end] = [end, start]
  const length = Math.round((end.getTime() - start.getTime()) / 86400000) + 1
  const prevTo = addDays(start, -1)
  const prevFrom = addDays(prevTo, -(length - 1))
  return {
    from: toDateStr(start),
    to: toDateStr(end),
    prev_from: toDateStr(prevFrom),
    prev_to: toDateStr(prevTo),
    timezone,
  }
}

export function rangeDays(info: AnalyticsRangeInfo): string[] {
  const days: string[] = []
  const d = new Date(`${info.from}T00:00:00`)
  const end = new Date(`${info.to}T00:00:00`)
  while (d <= end && days.length <= 366) {
    days.push(toDateStr(d))
    d.setDate(d.getDate() + 1)
  }
  return days
}

interface DayMetrics {
  clicks: number
  conversions: number
  revenue: number
  cost: number
  profit: number
  roi: number
  cr: number
}

function dayMetrics(seed: string): DayMetrics {
  const clicks = Math.round(80 + seeded(`${seed}:clicks`) * 900)
  const cr = 0.02 + seeded(`${seed}:cr`) * 0.06
  const conversions = Math.round(clicks * cr)
  const cost = Math.round(clicks * (0.15 + seeded(`${seed}:cpc`) * 0.35) * 100) / 100
  const revenue = Math.round(conversions * (25 + seeded(`${seed}:rpc`) * 60) * 100) / 100
  const profit = Math.round((revenue - cost) * 100) / 100
  const roi = cost > 0 ? (profit / cost) * 100 : 0
  const crPct = clicks > 0 ? (conversions / clicks) * 100 : 0
  return { clicks, conversions, revenue, cost, profit, roi, cr: crPct }
}

function aggregate(items: DayMetrics[]): AnalyticsMetrics {
  let clicks = 0
  let conversions = 0
  let revenue = 0
  let cost = 0
  for (const item of items) {
    clicks += item.clicks
    conversions += item.conversions
    revenue += item.revenue
    cost += item.cost
  }
  const profit = revenue - cost
  const roi = cost > 0 ? (profit / cost) * 100 : 0
  const cr = clicks > 0 ? (conversions / clicks) * 100 : 0
  const epc = clicks > 0 ? revenue / clicks : 0
  const cpa = conversions > 0 ? cost / conversions : 0
  return {
    clicks,
    campaign_unique_clicks: Math.round(clicks * 0.7),
    conversions,
    leads: Math.round(conversions * 0.8),
    sales: Math.round(conversions * 0.5),
    rejected: Math.round(clicks * 0.04),
    cr,
    cost,
    revenue,
    profit,
    roi,
    epc,
    cpa,
  }
}

const METRIC_KEYS: AnalyticsMetricKey[] = [
  'clicks',
  'campaign_unique_clicks',
  'conversions',
  'leads',
  'sales',
  'rejected',
  'cr',
  'cost',
  'revenue',
  'profit',
  'roi',
  'epc',
  'cpa',
]

const NULL_DELTA_KEYS = new Set<AnalyticsMetricKey>(['cpa', 'rejected'])

export function makeTrends(range: AnalyticsRange, from?: string, to?: string, timezone?: string): AnalyticsTrends {
  const info = resolveRange(range, from, to, timezone)
  const items: AnalyticsTrendItem[] = rangeDays(info).map((day) => {
    const m = dayMetrics(day)
    return { day, ...m }
  })
  return { range: info, items }
}

export function makeOverview(range: AnalyticsRange, from?: string, to?: string, timezone?: string): AnalyticsOverview {
  const trends = makeTrends(range, from, to, timezone)
  const deltas: AnalyticsDeltas = {}
  for (const key of METRIC_KEYS) {
    deltas[key] = NULL_DELTA_KEYS.has(key)
      ? null
      : Math.round((seeded(`delta:${key}`) * 90 - 40) * 10) / 10
  }
  return { range: trends.range, metrics: aggregate(trends.items), deltas }
}

function streamMetrics(streamId: number, name: string, weight: number): AnalyticsStreamItem {
  const seed = `stream:${streamId}`
  const clicks = Math.round(weight * (200 + seeded(seed) * 1200))
  const conversions = Math.round(clicks * (0.02 + seeded(`${seed}:cr`) * 0.05))
  const cost = Math.round(clicks * (0.15 + seeded(`${seed}:cpc`) * 0.35) * 100) / 100
  const revenue = Math.round(conversions * (25 + seeded(`${seed}:rpc`) * 60) * 100) / 100
  const profit = Math.round((revenue - cost) * 100) / 100
  const roi = cost > 0 ? (profit / cost) * 100 : 0
  const cr = clicks > 0 ? (conversions / clicks) * 100 : 0
  return { stream_id: streamId, stream_name: name, clicks, conversions, revenue, cost, profit, roi, cr }
}

function offerMetrics(offerId: number): AnalyticsOfferItem {
  const offer = OFFERS.find((o) => o.id === offerId)
  const seed = `offer:${offerId}`
  const clicks = Math.round(100 + seeded(`${seed}:clicks`) * 800)
  const conversions = Math.round(clicks * (0.02 + seeded(`${seed}:cr`) * 0.05))
  const cost = Math.round(clicks * (0.1 + seeded(`${seed}:cpc`) * 0.3) * 100) / 100
  const revenue = Math.round(conversions * (25 + seeded(`${seed}:rpc`) * 55) * 100) / 100
  const profit = Math.round((revenue - cost) * 100) / 100
  const roi = cost > 0 ? (profit / cost) * 100 : 0
  const cr = clicks > 0 ? (conversions / clicks) * 100 : 0
  return {
    offer_id: offerId,
    offer_name: offer?.name ?? `Оффер #${offerId}`,
    offer_state: offer?.state ?? 'active',
    clicks,
    conversions,
    revenue,
    cost,
    profit,
    roi,
    cr,
  }
}

function geoMetrics(country: string): AnalyticsGeoItem {
  const seed = `geo:${country}`
  const clicks = Math.round(50 + seeded(`${seed}:clicks`) * 400)
  const conversions = Math.round(clicks * (0.02 + seeded(`${seed}:cr`) * 0.05))
  const cost = Math.round(clicks * (0.1 + seeded(`${seed}:cpc`) * 0.3) * 100) / 100
  const revenue = Math.round(conversions * (22 + seeded(`${seed}:rpc`) * 50) * 100) / 100
  const profit = Math.round((revenue - cost) * 100) / 100
  const roi = cost > 0 ? (profit / cost) * 100 : 0
  const cr = clicks > 0 ? (conversions / clicks) * 100 : 0
  const epc = clicks > 0 ? revenue / clicks : 0
  const cpa = conversions > 0 ? cost / conversions : 0
  return { country, clicks, conversions, cr, revenue, cost, profit, roi, epc, cpa }
}

export function makeCampaignAnalytics(
  campaignId: number,
  offerIds: number[],
  range: AnalyticsRange,
  from?: string,
  to?: string,
  timezone?: string,
): AnalyticsCampaign {
  const trends = makeTrends(range, from, to, timezone)
  const metrics = aggregate(trends.items)
  const streams = [streamMetrics(1, 'Google Redirect', 0.35), streamMetrics(2, 'Offer Flow', 0.65)]
  const offers = offerIds.map((id) => offerMetrics(id))
  const geo = ['RU', 'US', 'DE', 'PL', 'UA', 'KZ', 'BR'].map((country) => geoMetrics(country))
  return { range: trends.range, campaign_id: campaignId, metrics, streams, offers, geo }
}

export function makeOffersAnalytics(
  campaignId: number | null,
  offerIds: number[] | null,
  range: AnalyticsRange,
  from?: string,
  to?: string,
  timezone?: string,
): AnalyticsOffersResponse {
  const info = resolveRange(range, from, to, timezone)
  const ids = offerIds ?? OFFERS.filter((o) => o.state === 'active').slice(0, 8).map((o) => o.id)
  const items: AnalyticsOffersItem[] = ids.map((id) => {
    const base = offerMetrics(id)
    const withCampaign = campaignId !== null
    return {
      offer_id: id,
      offer_name: base.offer_name,
      offer_state: base.offer_state,
      clicks: base.clicks,
      campaign_unique_clicks: Math.round(base.clicks * 0.7),
      conversions: base.conversions,
      leads: Math.round(base.conversions * 0.8),
      sales: Math.round(base.conversions * 0.5),
      rejected: Math.round(base.clicks * 0.04),
      cr: base.cr,
      cost: base.cost,
      revenue: base.revenue,
      profit: base.profit,
      roi: base.roi,
      epc: base.clicks > 0 ? base.revenue / base.clicks : 0,
      cpa: base.conversions > 0 ? base.cost / base.conversions : 0,
      ...(withCampaign ? { planned_share: 100, actual_share: Math.round(50 + seeded(`actual:${id}`) * 160) } : {}),
    }
  })
  return { range: info, campaign_id: campaignId, items }
}

export function makeGeoAnalytics(
  range: AnalyticsRange,
  from?: string,
  to?: string,
  timezone?: string,
): AnalyticsGeoResponse {
  const info = resolveRange(range, from, to, timezone)
  const items = ['RU', 'US', 'DE', 'PL', 'UA', 'KZ', 'BR', 'TR'].map((country) => geoMetrics(country))
  return { range: info, items }
}

function csvEscape(value: string | number): string {
  const s = String(value)
  return s.includes(',') || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s
}

export function makeCsv(type: 'campaigns' | 'offers' | 'geo' | 'streams'): string {
  if (type === 'offers') {
    const rows = makeOffersAnalytics(null, null, 'last_7_days').items
    const header = ['offer_id', 'offer_name', 'offer_state', 'clicks', 'conversions', 'cr', 'revenue', 'cost', 'profit', 'roi', 'epc', 'cpa']
    const lines = [header.join(',')]
    for (const r of rows) {
      lines.push(
        [
          r.offer_id,
          csvEscape(r.offer_name),
          r.offer_state,
          r.clicks,
          r.conversions,
          r.cr.toFixed(2),
          r.revenue.toFixed(2),
          r.cost.toFixed(2),
          r.profit.toFixed(2),
          r.roi.toFixed(2),
          r.epc.toFixed(2),
          r.cpa.toFixed(2),
        ].join(','),
      )
    }
    return lines.join('\n')
  }
  if (type === 'geo') {
    const rows = makeGeoAnalytics('last_7_days').items
    const header = ['country', 'clicks', 'conversions', 'cr', 'revenue', 'cost', 'profit', 'roi', 'epc', 'cpa']
    const lines = [header.join(',')]
    for (const r of rows) {
      lines.push(
        [r.country, r.clicks, r.conversions, r.cr.toFixed(2), r.revenue.toFixed(2), r.cost.toFixed(2), r.profit.toFixed(2), r.roi.toFixed(2), r.epc.toFixed(2), r.cpa.toFixed(2)].join(','),
      )
    }
    return lines.join('\n')
  }
  const header = ['id', 'name', 'clicks', 'conversions', 'revenue', 'cost', 'profit', 'roi']
  return [
    header.join(','),
    ...Array.from({ length: 6 }, (_, i) =>
      [`${1000 + i}`, csvEscape(`Sample ${type} ${i + 1}`), 200 + i * 10, 8 + i, (300 + i * 50).toFixed(2), (120 + i * 15).toFixed(2), (180 + i * 35).toFixed(2), ((40 + i * 3).toFixed(2))].join(','),
    ),
  ].join('\n')
}
