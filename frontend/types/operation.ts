export type OperationStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'partially_failed'
  | 'needs_attention'

export type OperationStage =
  | 'pending'
  | 'creating_campaign'
  | 'creating_google_stream'
  | 'creating_offer_stream'
  | 'verifying'
  | 'completed'

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
  current_stage: OperationStage | null
  progress: number
  started_at: string | null
  finished_at: string | null
  created_at: string
  completed_at: string | null
}
