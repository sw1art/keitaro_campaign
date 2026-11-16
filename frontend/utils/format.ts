function parseDate(value: string): Date | null {
  // Campaign timestamps arrive as "YYYY-MM-DD HH:MM:SS" (local time); operation
  // timestamps arrive as ISO 8601 with a "Z" suffix. Normalize the space form.
  const normalized = value.includes('T') ? value : value.replace(' ', 'T')
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = parseDate(value)
  if (!date) return value
  return new Intl.DateTimeFormat('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
