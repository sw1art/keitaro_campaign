<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { AnalyticsOffersItem, AnalyticsOffersResponse, Campaign, RangeSelection } from '~/types'
import { ApiError } from '~/utils/apiError'
import { buildAnalyticsQuery, defaultRangeSelection, formatInt, formatPercent } from '~/utils/analytics'
import { downloadAnalyticsExport } from '~/utils/analyticsExport'

const api = useApi()

const selection = ref<RangeSelection>(defaultRangeSelection())
const campaignFilter = ref('')
const campaigns = ref<Campaign[]>([])
const data = ref<AnalyticsOffersResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const items = computed(() => data.value?.items ?? [])

async function load() {
  loading.value = true
  error.value = null
  try {
    const campaignId = campaignFilter.value ? Number(campaignFilter.value) : undefined
    data.value = await api.getAnalyticsOffers({
      ...buildAnalyticsQuery(selection.value),
      campaign_id: campaignId,
    })
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить аналитику офферов'
  } finally {
    loading.value = false
  }
}

function shareMismatch(item: AnalyticsOffersItem): boolean {
  return item.planned_share !== undefined && item.actual_share !== undefined && item.planned_share !== item.actual_share
}

function exportCsv() {
  const campaignId = campaignFilter.value ? Number(campaignFilter.value) : undefined
  downloadAnalyticsExport(
    api,
    { type: 'offers', campaign_id: campaignId, ...buildAnalyticsQuery(selection.value) },
    'analytics-offers.csv',
  )
}

onMounted(async () => {
  try {
    const result = await api.listCampaigns({ page_size: 100, sort_by: 'created_at', sort_order: 'desc' })
    campaigns.value = result.items
  } catch {
    campaigns.value = []
  }
  await load()
})

watch(selection, load, { deep: true })
watch(campaignFilter, load)
</script>

<template>
  <div class="space-y-6">
    <div>
      <NuxtLink to="/analytics" class="text-sm text-indigo-600 hover:text-indigo-500">← К аналитике</NuxtLink>
      <h1 class="mt-1 text-2xl font-semibold text-slate-900">Эффективность офферов</h1>
      <p class="mt-1 text-sm text-slate-500">Сравнение заданного и фактического распределения трафика</p>
    </div>

    <div class="flex flex-wrap items-end gap-3">
      <AnalyticsRangeSelector v-model="selection" />
      <div>
        <label class="field-label" for="offers-campaign">Кампания</label>
        <select id="offers-campaign" v-model="campaignFilter" class="input mt-1 w-64">
          <option value="">Все кампании</option>
          <option v-for="campaign in campaigns" :key="campaign.id" :value="String(campaign.id)">
            #{{ campaign.id }} · {{ campaign.name }}
          </option>
        </select>
      </div>
      <button class="btn btn-secondary" @click="exportCsv">Экспорт CSV</button>
    </div>

    <AppSpinner v-if="loading" label="Загрузка…" />
    <AppAlert v-else-if="error" type="error" title="Ошибка загрузки">{{ error }}</AppAlert>

    <template v-else>
      <div class="card overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th class="px-4 py-3">Оффер</th>
              <th class="px-4 py-3">Заданный Share</th>
              <th class="px-4 py-3">Факт. трафик</th>
              <th class="px-4 py-3 text-right">Clicks</th>
              <th class="px-4 py-3 text-right">CR</th>
              <th class="px-4 py-3 text-right">ROI</th>
              <th class="px-4 py-3 text-right">EPC</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-for="item in items" :key="item.offer_id" :class="shareMismatch(item) ? 'bg-amber-50/50' : ''">
              <td class="px-4 py-3">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="font-medium text-slate-900">{{ item.offer_name }}</span>
                  <AppStatusBadge :status="item.offer_state" />
                </div>
                <div class="font-mono text-xs text-slate-500">#{{ item.offer_id }}</div>
              </td>
              <td class="px-4 py-3 text-slate-700">
                {{ item.planned_share !== undefined ? item.planned_share : '—' }}
              </td>
              <td class="px-4 py-3">
                <span :class="shareMismatch(item) ? 'font-semibold text-amber-600' : 'text-slate-700'">
                  {{ item.actual_share !== undefined ? `${item.actual_share}%` : '—' }}
                </span>
                <span v-if="shareMismatch(item)" class="ml-1 text-xs text-amber-600" title="Расхождение с заданным share">⚠</span>
              </td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(item.clicks) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(item.cr) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(item.roi) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">${{ item.epc.toFixed(2) }}</td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-slate-500">Нет данных</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
