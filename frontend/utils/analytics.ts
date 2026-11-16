import type { AnalyticsMetricKey, AnalyticsMetrics, AnalyticsQuery, RangeSelection } from '~/types/analytics'

export type MetricKind = 'int' | 'currency' | 'percent'

export interface MetricDef {
  key: AnalyticsMetricKey
  label: string
  kind: MetricKind
}

/** All metrics in display order. */
export const METRIC_DEFS: MetricDef[] = [
  { key: 'clicks', label: 'Клики', kind: 'int' },
  { key: 'campaign_unique_clicks', label: 'Уник. клики', kind: 'int' },
  { key: 'conversions', label: 'Конверсии', kind: 'int' },
  { key: 'leads', label: 'Лиды', kind: 'int' },
  { key: 'sales', label: 'Продажи', kind: 'int' },
  { key: 'rejected', label: 'Отклонённые', kind: 'int' },
  { key: 'cr', label: 'CR', kind: 'percent' },
  { key: 'cost', label: 'Расход', kind: 'currency' },
  { key: 'revenue', label: 'Доход', kind: 'currency' },
  { key: 'profit', label: 'Прибыль', kind: 'currency' },
  { key: 'roi', label: 'ROI', kind: 'percent' },
  { key: 'epc', label: 'EPC', kind: 'currency' },
  { key: 'cpa', label: 'CPA', kind: 'currency' },
]

export function formatInt(value: number): string {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(value)
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`
}

export function formatMetricValue(value: number, kind: MetricKind): string {
  if (kind === 'currency') return formatCurrency(value)
  if (kind === 'percent') return formatPercent(value)
  return formatInt(value)
}

export interface DeltaBadge {
  text: string
  kind: 'up' | 'down' | 'flat'
}

export function formatDelta(delta: number | null | undefined): DeltaBadge {
  if (delta === null || delta === undefined) return { text: '—', kind: 'flat' }
  if (delta > 0) return { text: `▲ +${delta.toFixed(1)}%`, kind: 'up' }
  if (delta < 0) return { text: `▼ ${Math.abs(delta).toFixed(1)}%`, kind: 'down' }
  return { text: '0%', kind: 'flat' }
}

/** "YYYY-MM-DD" -> "DD.MM" for compact chart axis labels. */
export function shortDay(day: string): string {
  const parts = day.split('-')
  if (parts.length !== 3) return day
  return `${parts[2]}.${parts[1]}`
}

export function metricOf(metrics: AnalyticsMetrics, key: AnalyticsMetricKey): number {
  return metrics[key] ?? 0
}

export function toDateInput(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function defaultRangeSelection(): RangeSelection {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - 6)
  return {
    range: 'last_7_days',
    from: toDateInput(from),
    to: toDateInput(to),
    timezone: 'Europe/Moscow',
  }
}

export function buildAnalyticsQuery(selection: RangeSelection): AnalyticsQuery {
  const query: AnalyticsQuery = { range: selection.range, timezone: selection.timezone }
  if (selection.range === 'custom') {
    if (selection.from) query.from = selection.from
    if (selection.to) query.to = selection.to
  }
  return query
}
