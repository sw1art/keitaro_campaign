export interface AuditLogItem {
  id: string
  operation_id: string | null
  action: string
  entity_type: string
  entity_id: string
  details: Record<string, unknown> | null
  created_at: string | null
}
