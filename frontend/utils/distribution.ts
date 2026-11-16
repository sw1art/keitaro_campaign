/**
 * Pure, unit-testable business rules for offer traffic distribution.
 *
 * Percentage = share / sum(all shares) * 100, displayed with exactly 2 decimals.
 * Rounding affects the DISPLAY only; the stored `share` is never modified.
 */

export interface ShareEntry {
  offer_id: number
  share: number
}

export interface DistributionEntry extends ShareEntry {
  /** Raw percentage (e.g. 50), not yet rounded for display. */
  percentage: number
}

export function computeDistribution(offers: ShareEntry[]): DistributionEntry[] {
  const total = offers.reduce((sum, offer) => sum + offer.share, 0)
  if (total <= 0) {
    return offers.map((offer) => ({ ...offer, percentage: 0 }))
  }
  return offers.map((offer) => ({
    ...offer,
    percentage: (offer.share / total) * 100,
  }))
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(2)}%`
}

/**
 * A share is valid only when it is a finite integer in the range 1..100.
 * (Verified against the live Keitaro: values >100 and fractional values are rejected.)
 */
export function isValidShare(value: number | null | undefined): boolean {
  return (
    typeof value === 'number' &&
    Number.isFinite(value) &&
    Number.isInteger(value) &&
    value >= 1 &&
    value <= 100
  )
}

/** Compares two offer/share configurations (order-insensitive, ids are unique). */
export function offersDiffer(a: ShareEntry[], b: ShareEntry[]): boolean {
  if (a.length !== b.length) return true
  const map = new Map<number, number>(b.map((offer) => [offer.offer_id, offer.share]))
  return a.some((offer) => map.get(offer.offer_id) !== offer.share)
}
