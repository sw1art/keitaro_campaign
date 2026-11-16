export type OperationStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface OperationError {
  code: string
  message: string
}

export interface Operation {
  operation_id: string
  type: string
  status: OperationStatus
  campaign_id: number | null
  error: OperationError | null
  created_at: string
  completed_at: string | null
}
