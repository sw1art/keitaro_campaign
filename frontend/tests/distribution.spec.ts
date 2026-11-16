import { describe, expect, it } from 'vitest'
import { computeDistribution, formatPercentage, isValidShare, offersDiffer } from '../utils/distribution'

describe('computeDistribution', () => {
  it('computes percentages from the task example', () => {
    const result = computeDistribution([
      { offer_id: 1, share: 100 },
      { offer_id: 2, share: 50 },
      { offer_id: 3, share: 50 },
    ])
    expect(result.map((entry) => entry.percentage)).toEqual([50, 25, 25])
  })

  it('returns zero percentages when the total share is zero', () => {
    const result = computeDistribution([
      { offer_id: 1, share: 0 },
      { offer_id: 2, share: 0 },
    ])
    expect(result.every((entry) => entry.percentage === 0)).toBe(true)
  })

  it('keeps the stored share untouched (rounding affects display only)', () => {
    const result = computeDistribution([
      { offer_id: 1, share: 1 },
      { offer_id: 2, share: 3 },
    ])
    expect(result[0].share).toBe(1)
    expect(result[1].share).toBe(3)
    expect(formatPercentage(result[0].percentage)).toBe('25.00%')
    expect(formatPercentage(result[1].percentage)).toBe('75.00%')
  })

  it('formats percentages with exactly two decimals', () => {
    expect(formatPercentage(50)).toBe('50.00%')
    expect(formatPercentage(33.3333333)).toBe('33.33%')
  })
})

describe('isValidShare', () => {
  it('rejects zero, negatives, fractions, out-of-range, NaN, null and undefined', () => {
    expect(isValidShare(0)).toBe(false)
    expect(isValidShare(-5)).toBe(false)
    expect(isValidShare(101)).toBe(false)
    expect(isValidShare(0.5)).toBe(false)
    expect(isValidShare(100.5)).toBe(false)
    expect(isValidShare(Number.NaN)).toBe(false)
    expect(isValidShare(null)).toBe(false)
    expect(isValidShare(undefined)).toBe(false)
  })

  it('accepts integers in the range 1..100', () => {
    expect(isValidShare(1)).toBe(true)
    expect(isValidShare(50)).toBe(true)
    expect(isValidShare(100)).toBe(true)
  })
})

describe('offersDiffer', () => {
  it('detects changed shares, added offers and removed offers', () => {
    expect(offersDiffer([{ offer_id: 1, share: 100 }], [{ offer_id: 1, share: 200 }])).toBe(true)
    expect(
      offersDiffer(
        [{ offer_id: 1, share: 100 }],
        [
          { offer_id: 1, share: 100 },
          { offer_id: 2, share: 100 },
        ],
      ),
    ).toBe(true)
    expect(offersDiffer([{ offer_id: 1, share: 100 }], [{ offer_id: 2, share: 100 }])).toBe(true)
  })

  it('returns false for identical configurations', () => {
    expect(offersDiffer([{ offer_id: 1, share: 100 }], [{ offer_id: 1, share: 100 }])).toBe(false)
  })
})
