import type { Campaign } from './campaign'
import type { Operation } from './operation'

export interface Dashboard {
  campaigns_count: number
  recent_campaigns: Campaign[]
  operations_total: number
  operations_completed: number
  operations_failed: number
  recent_operations: Operation[]
}
