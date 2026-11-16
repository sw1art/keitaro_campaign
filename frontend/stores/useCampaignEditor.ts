import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { computeDistribution, isValidShare, offersDiffer, type ShareEntry } from '~/utils/distribution'

interface EditorInit {
  id: number
  offers: Array<{ offer_id: number; share: number }>
  fingerprint?: string | null
}

/**
 * Local editing state for the Offer Flow of one campaign. The backend is the
 * source of truth; this store only tracks the working copy and exposes the
 * pure business rules (distribution, share validation, dirty detection).
 */
export const useCampaignEditorStore = defineStore('campaignEditor', () => {
  const streamId = ref<number | null>(null)
  const originalOffers = ref<ShareEntry[]>([])
  const workingOffers = ref<ShareEntry[]>([])
  const baseFingerprint = ref<string | null>(null)

  const distribution = computed(() => computeDistribution(workingOffers.value))
  const totalShare = computed(() => workingOffers.value.reduce((sum, offer) => sum + offer.share, 0))
  const isDirty = computed(() => offersDiffer(workingOffers.value, originalOffers.value))
  const hasOffers = computed(() => workingOffers.value.length > 0)
  const allSharesValid = computed(() => workingOffers.value.every((offer) => isValidShare(offer.share)))
  const canSave = computed(() => isDirty.value && hasOffers.value && allSharesValid.value)

  function initialize(init: EditorInit) {
    streamId.value = init.id
    const offers = init.offers.map((offer) => ({ offer_id: offer.offer_id, share: offer.share }))
    originalOffers.value = offers
    workingOffers.value = offers.map((offer) => ({ ...offer }))
    baseFingerprint.value = init.fingerprint ?? null
  }

  function applyServer(offers: Array<{ offer_id: number; share: number }>, fingerprint?: string | null) {
    const next = offers.map((offer) => ({ offer_id: offer.offer_id, share: offer.share }))
    originalOffers.value = next
    workingOffers.value = next.map((offer) => ({ ...offer }))
    if (fingerprint !== undefined) baseFingerprint.value = fingerprint
  }

  function addOffer(offerId: number) {
    if (workingOffers.value.some((offer) => offer.offer_id === offerId)) return
    workingOffers.value = [...workingOffers.value, { offer_id: offerId, share: 100 }]
  }

  function removeOffer(offerId: number) {
    workingOffers.value = workingOffers.value.filter((offer) => offer.offer_id !== offerId)
  }

  function setShare(offerId: number, value: number) {
    const safe = Number.isFinite(value) ? value : 0
    workingOffers.value = workingOffers.value.map((offer) =>
      offer.offer_id === offerId ? { ...offer, share: safe } : offer,
    )
  }

  function reset() {
    workingOffers.value = originalOffers.value.map((offer) => ({ ...offer }))
  }

  return {
    streamId,
    originalOffers,
    workingOffers,
    baseFingerprint,
    distribution,
    totalShare,
    isDirty,
    hasOffers,
    allSharesValid,
    canSave,
    initialize,
    applyServer,
    addOffer,
    removeOffer,
    setShare,
    reset,
  }
})
