<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Campaign, Offer, Stream } from '~/types'
import { ApiError } from '~/utils/apiError'
import { formatDate } from '~/utils/format'
import { useCampaignEditorStore } from '~/stores/useCampaignEditor'
import { useToastsStore } from '~/stores/useToasts'

const route = useRoute()
const api = useApi()
const toasts = useToastsStore()
const editor = useCampaignEditorStore()

const campaignId = computed(() => Number(route.params.id))

const campaign = ref<Campaign | null>(null)
const googleRedirect = ref<Stream | null>(null)
const offerFlow = ref<Stream | null>(null)
const offersById = ref<Record<number, Offer>>({})

const loading = ref(true)
const loadError = ref<string | null>(null)

const addOfferOpen = ref(false)
const confirmSaveOpen = ref(false)
const saving = ref(false)

const googleGeo = computed(() => {
  const filter = googleRedirect.value?.filters.find((item) => item.name === 'country')
  return filter?.payload ?? []
})

const saveSummary = computed(() => {
  const original = editor.originalOffers
  const working = editor.workingOffers
  const originalIds = new Set(original.map((offer) => offer.offer_id))
  const workingIds = new Set(working.map((offer) => offer.offer_id))
  const added = working.filter((offer) => !originalIds.has(offer.offer_id)).length
  const removed = original.filter((offer) => !workingIds.has(offer.offer_id)).length
  const changed = working.filter((offer) => {
    const before = original.find((item) => item.offer_id === offer.offer_id)
    return before !== undefined && before.share !== offer.share
  }).length
  return { added, removed, changed, total: working.length }
})

async function loadOfferDetails(stream: Stream | null) {
  const ids = [...new Set((stream?.offers ?? []).map((offer) => offer.offer_id))]
  if (ids.length === 0) return
  const results = await Promise.all(
    ids.map(async (id) => {
      try {
        const result = await api.listOffers({ search: String(id), page: 1, page_size: 5 })
        return result.items.find((offer) => offer.id === id) ?? null
      } catch {
        return null
      }
    }),
  )
  const map: Record<number, Offer> = { ...offersById.value }
  results.forEach((offer, index) => {
    if (offer) map[ids[index]] = offer
  })
  offersById.value = map
}

async function load() {
  loading.value = true
  loadError.value = null
  try {
    const [camp, streams] = await Promise.all([
      api.getCampaign(campaignId.value),
      api.getCampaignStreams(campaignId.value),
    ])
    campaign.value = camp

    const redirect = streams.find((stream) => stream.schema === 'redirect' || stream.name === 'Google Redirect') ?? null
    const flow = streams.find((stream) => stream.schema === 'landings' || stream.name === 'Offer Flow') ?? null
    googleRedirect.value = redirect
    offerFlow.value = flow ? await api.getStream(flow.id) : null

    await loadOfferDetails(offerFlow.value)
    editor.initialize(offerFlow.value ?? { id: 0, offers: [] })
  } catch (err) {
    loadError.value = err instanceof ApiError ? err.message : 'Не удалось загрузить кампанию'
  } finally {
    loading.value = false
  }
}

function onPickOffer(offer: Offer) {
  if (editor.workingOffers.some((item) => item.offer_id === offer.id)) {
    toasts.push('warning', `Оффер #${offer.id} уже добавлен в поток`)
    return
  }
  editor.addOffer(offer.id)
  offersById.value = { ...offersById.value, [offer.id]: offer }
  addOfferOpen.value = false
  toasts.push('success', `Оффер «${offer.name}» добавлен`)
}

function onCancelChanges() {
  editor.reset()
  toasts.push('info', 'Изменения отменены')
}

async function onSave() {
  confirmSaveOpen.value = false
  if (!offerFlow.value || !editor.canSave) return
  saving.value = true
  try {
    const updated = await api.updateStreamOffers(offerFlow.value.id, {
      offers: editor.workingOffers.map((offer) => ({ offer_id: offer.offer_id, share: offer.share })),
    })
    offerFlow.value = updated
    editor.applyServer(updated.offers.map((offer) => ({ offer_id: offer.offer_id, share: offer.share })))
    await loadOfferDetails(updated)
    toasts.push('success', 'Изменения сохранены')
  } catch (err) {
    toasts.push('error', err instanceof ApiError ? err.message : 'Не удалось сохранить изменения')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between gap-3">
      <div class="min-w-0">
        <NuxtLink to="/campaigns" class="text-sm text-indigo-600 hover:text-indigo-500">← К списку кампаний</NuxtLink>
        <h1 class="mt-1 truncate text-2xl font-semibold text-slate-900">
          {{ campaign?.name ?? `Кампания #${campaignId}` }}
        </h1>
      </div>
      <AppStatusBadge v-if="campaign" :status="campaign.state" />
    </div>

    <AppSpinner v-if="loading" label="Загрузка кампании…" />
    <AppAlert v-else-if="loadError" type="error" title="Ошибка загрузки">{{ loadError }}</AppAlert>

    <template v-else-if="campaign">
      <section class="card p-6">
        <h2 class="text-base font-semibold text-slate-900">Общая информация</h2>
        <dl class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">ID</dt>
            <dd class="mt-1 text-sm font-mono text-slate-800">{{ campaign.id }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Домен</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ campaign.domain }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Источник трафика</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ campaign.traffic_source }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Группа</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ campaign.group }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Тип стоимости</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ campaign.cost_type }} · {{ campaign.cost_currency }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Создана / обновлена</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ formatDate(campaign.created_at) }} / {{ formatDate(campaign.updated_at) }}</dd>
          </div>
        </dl>
      </section>

      <section class="card p-6">
        <h2 class="text-base font-semibold text-slate-900">Google Redirect</h2>
        <div v-if="googleRedirect" class="mt-4 space-y-2 text-sm">
          <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
            <div><span class="text-slate-500">Поток:</span> {{ googleRedirect.name }}</div>
            <div class="flex items-center gap-2"><span class="text-slate-500">Статус:</span> <AppStatusBadge :status="googleRedirect.state" /></div>
            <div><span class="text-slate-500">Тип действия:</span> {{ googleRedirect.action_type }}</div>
            <div class="truncate"><span class="text-slate-500">URL:</span> {{ googleRedirect.action_payload }}</div>
          </div>
          <div>
            <span class="text-slate-500">GEO:</span>
            <span class="mt-1 flex flex-wrap gap-1.5">
              <span v-for="code in googleGeo" :key="code" class="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-700">{{ code }}</span>
              <span v-if="googleGeo.length === 0" class="text-slate-400">не заданы</span>
            </span>
          </div>
        </div>
        <p v-else class="mt-4 text-sm text-slate-500">Поток Google Redirect не найден</p>
      </section>

      <section class="card p-6">
        <h2 class="text-base font-semibold text-slate-900">Offer Flow</h2>
        <p v-if="offerFlow" class="mt-1 flex items-center gap-2 text-sm text-slate-500">
          Поток: {{ offerFlow.name }}
          <AppStatusBadge :status="offerFlow.state" />
        </p>
        <div class="mt-4">
          <OfferEditor :offers-by-id="offersById" @add-offer="addOfferOpen = true" @save="confirmSaveOpen = true" @cancel="onCancelChanges" />
        </div>
      </section>
    </template>

    <OfferPickerModal :open="addOfferOpen" :exclude-ids="editor.workingOffers.map((o) => o.offer_id)" @close="addOfferOpen = false" @pick="onPickOffer" />

    <AppModal :open="confirmSaveOpen" title="Сохранить изменения?" @close="confirmSaveOpen = false">
      <p class="text-sm text-slate-600">
        Текущая конфигурация офферов отличается от сохранённой. Проверьте изменения перед сохранением.
      </p>
      <ul class="mt-3 space-y-1 text-sm text-slate-700">
        <li>Добавлено офферов: <span class="font-semibold text-emerald-600">{{ saveSummary.added }}</span></li>
        <li>Удалено офферов: <span class="font-semibold text-red-600">{{ saveSummary.removed }}</span></li>
        <li>Изменено share: <span class="font-semibold text-amber-600">{{ saveSummary.changed }}</span></li>
        <li>Всего офферов после сохранения: <span class="font-semibold">{{ saveSummary.total }}</span></li>
      </ul>
      <template #footer>
        <button class="btn btn-secondary" :disabled="saving" @click="confirmSaveOpen = false">Отмена</button>
        <button class="btn btn-primary" :disabled="saving" @click="onSave">
          <AppSpinner v-if="saving" size="sm" label="Сохранение…" />
          <span v-else>Сохранить</span>
        </button>
      </template>
    </AppModal>
  </div>
</template>
