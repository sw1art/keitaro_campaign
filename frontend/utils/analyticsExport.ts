import type { AdRobotApi } from '~/types/api-client'
import type { AnalyticsExportQuery } from '~/types/analytics'

/** Triggers a browser download of a CSV export (works for both real URLs and mock data URLs). */
export function downloadAnalyticsExport(api: AdRobotApi, params: AnalyticsExportQuery, filename: string): void {
  const url = api.getAnalyticsExportUrl(params)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}
