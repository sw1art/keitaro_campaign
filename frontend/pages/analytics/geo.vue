<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { AnalyticsGeoResponse, Campaign, RangeSelection } from '~/types'
import { ApiError } from '~/utils/apiError'
import { buildAnalyticsQuery, defaultRangeSelection, formatCurrency, formatInt, formatPercent } from '~/utils/analytics'
import { downloadAnalyticsExport } from '~/utils/analyticsExport'

type SortKey = 'country' | 'clicks' | 'conversions' | 'cr' | 'revenue' | 'roi' | 'epc' | 'cpa'

const columns: Array<{ key: SortKey; label: string }> = [
  { key: 'country', label: 'GEO' },
  { key: 'clicks', label: 'Clicks' },
  { key: 'conversions', label: 'Conversions' },
  { key: 'cr', label: 'CR' },
  { key: 'revenue', label: 'Revenue' },
  { key: 'roi', label: 'ROI' },
  { key: 'epc', label: 'EPC' },
  { key: 'cpa', label: 'CPA' },
]

const api = useApi()

const selection = ref<RangeSelection>(defaultRangeSelection())
const campaignFilter = ref('')
const campaigns = ref<Campaign[]>([])
const data = ref<AnalyticsGeoResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const sortBy = ref<SortKey>('clicks')
const sortOrder = ref<'asc' | 'desc'>('desc')

const items = computed(() => data.value?.items ?? [])

const sortedItems = computed(() => {
  const arr = [...items.value]
  arr.sort((a, b) => {
    const av = a[sortBy.value]
    const bv = b[sortBy.value]
    const result = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv))
    return sortOrder.value === 'asc' ? result : -result
  })
  return arr
})

function toggleSort(key: SortKey) {
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortOrder.value = 'desc'
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const campaignId = campaignFilter.value ? Number(campaignFilter.value) : undefined
    data.value = await api.getAnalyticsGeo({
      ...buildAnalyticsQuery(selection.value),
      campaign_id: campaignId,
    })
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить аналитику GEO'
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  const campaignId = campaignFilter.value ? Number(campaignFilter.value) : undefined
  downloadAnalyticsExport(
    api,
    { type: 'geo', campaign_id: campaignId, ...buildAnalyticsQuery(selection.value) },
    'analytics-geo.csv',
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
      <h1 class="mt-1 text-2xl font-semibold text-slate-900">GEO аналитика</h1>
      <p class="mt-1 text-sm text-slate-500">Распределение трафика по странам</p>
    </div>

    <div class="flex flex-wrap items-end gap-3">
      <AnalyticsRangeSelector v-model="selection" />
      <div>
        <label class="field-label" for="geo-campaign">Кампания</label>
        <select id="geo-campaign" v-model="campaignFilter" class="input mt-1 w-64">
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
              <th v-for="column in columns" :key="column.key" class="px-4 py-3" :class="column.key !== 'country' ? 'text-right' : ''">
                <button
                  type="button"
                  class="inline-flex items-center gap-1 uppercase tracking-wide hover:text-slate-700"
                  @click="toggleSort(column.key)"
                >
                  {{ column.label }}
                  <span v-if="sortBy === column.key" class="text-indigo-600">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-for="item in sortedItems" :key="item.country">
              <td class="px-4 py-3 font-mono text-xs text-slate-700">{{ item.country }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(item.clicks) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(item.conversions) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(item.cr) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(item.revenue) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(item.roi) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(item.epc) }}</td>
              <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(item.cpa) }}</td>
            </tr>
            <tr v-if="sortedItems.length === 0">
              <td :colspan="columns.length" class="px-4 py-8 text-center text-slate-500">Нет данных</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
