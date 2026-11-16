<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { AnalyticsCampaign, Campaign, RangeSelection } from '~/types'
import { ApiError } from '~/utils/apiError'
import {
  buildAnalyticsQuery,
  defaultRangeSelection,
  formatCurrency,
  formatInt,
  formatMetricValue,
  formatPercent,
  METRIC_DEFS,
} from '~/utils/analytics'

const route = useRoute()
const api = useApi()

const campaignId = computed(() => Number(route.params.id))

const selection = ref<RangeSelection>(defaultRangeSelection())
const campaign = ref<Campaign | null>(null)
const analytics = ref<AnalyticsCampaign | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function loadAnalytics() {
  loading.value = true
  error.value = null
  try {
    analytics.value = await api.getAnalyticsCampaign(campaignId.value, buildAnalyticsQuery(selection.value))
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить аналитику кампании'
  } finally {
    loading.value = false
  }
}

async function loadCampaign() {
  try {
    campaign.value = await api.getCampaign(campaignId.value)
  } catch {
    campaign.value = null
  }
}

watch(selection, loadAnalytics, { deep: true })

onMounted(async () => {
  await Promise.all([loadCampaign(), loadAnalytics()])
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="min-w-0">
        <NuxtLink to="/analytics" class="text-sm text-indigo-600 hover:text-indigo-500">← К аналитике</NuxtLink>
        <h1 class="mt-1 truncate text-2xl font-semibold text-slate-900">
          {{ campaign?.name ?? `Кампания #${campaignId}` }}
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <AppStatusBadge v-if="campaign" :status="campaign.state" />
        <NuxtLink :to="`/campaigns/${campaignId}`" class="btn btn-secondary">Открыть кампанию</NuxtLink>
      </div>
    </div>

    <AnalyticsRangeSelector v-model="selection" />

    <AppSpinner v-if="loading" label="Загрузка аналитики…" />
    <AppAlert v-else-if="error" type="error" title="Ошибка загрузки">{{ error }}</AppAlert>

    <template v-else-if="analytics">
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        <AnalyticsMetricCard
          v-for="def in METRIC_DEFS"
          :key="def.key"
          :label="def.label"
          :value="formatMetricValue(analytics.metrics[def.key], def.kind)"
        />
      </div>

      <section class="card p-6">
        <h2 class="text-base font-semibold text-slate-900">Потоки</h2>
        <div class="mt-4 overflow-x-auto rounded-lg ring-1 ring-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th class="px-4 py-3">Поток</th>
                <th class="px-4 py-3 text-right">Clicks</th>
                <th class="px-4 py-3 text-right">Conversions</th>
                <th class="px-4 py-3 text-right">Revenue</th>
                <th class="px-4 py-3 text-right">Cost</th>
                <th class="px-4 py-3 text-right">Profit</th>
                <th class="px-4 py-3 text-right">ROI</th>
                <th class="px-4 py-3 text-right">CR</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-for="stream in analytics.streams" :key="stream.stream_id">
                <td class="px-4 py-3 text-slate-800">{{ stream.stream_name }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(stream.clicks) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(stream.conversions) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(stream.revenue) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(stream.cost) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(stream.profit) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(stream.roi) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(stream.cr) }}</td>
              </tr>
              <tr v-if="analytics.streams.length === 0">
                <td colspan="8" class="px-4 py-6 text-center text-slate-500">Нет данных</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card p-6">
        <h2 class="text-base font-semibold text-slate-900">Офферы</h2>
        <div class="mt-4 overflow-x-auto rounded-lg ring-1 ring-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th class="px-4 py-3">Оффер</th>
                <th class="px-4 py-3 text-right">Clicks</th>
                <th class="px-4 py-3 text-right">Conversions</th>
                <th class="px-4 py-3 text-right">Revenue</th>
                <th class="px-4 py-3 text-right">Cost</th>
                <th class="px-4 py-3 text-right">Profit</th>
                <th class="px-4 py-3 text-right">ROI</th>
                <th class="px-4 py-3 text-right">CR</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-for="offer in analytics.offers" :key="offer.offer_id">
                <td class="px-4 py-3">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="font-medium text-slate-900">{{ offer.offer_name }}</span>
                    <AppStatusBadge :status="offer.offer_state" />
                  </div>
                  <div class="font-mono text-xs text-slate-500">#{{ offer.offer_id }}</div>
                </td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(offer.clicks) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(offer.conversions) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(offer.revenue) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(offer.cost) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(offer.profit) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(offer.roi) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(offer.cr) }}</td>
              </tr>
              <tr v-if="analytics.offers.length === 0">
                <td colspan="8" class="px-4 py-6 text-center text-slate-500">Нет данных</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card p-6">
        <h2 class="text-base font-semibold text-slate-900">GEO</h2>
        <div class="mt-4 overflow-x-auto rounded-lg ring-1 ring-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th class="px-4 py-3">GEO</th>
                <th class="px-4 py-3 text-right">Clicks</th>
                <th class="px-4 py-3 text-right">Conversions</th>
                <th class="px-4 py-3 text-right">CR</th>
                <th class="px-4 py-3 text-right">Revenue</th>
                <th class="px-4 py-3 text-right">Cost</th>
                <th class="px-4 py-3 text-right">Profit</th>
                <th class="px-4 py-3 text-right">ROI</th>
                <th class="px-4 py-3 text-right">EPC</th>
                <th class="px-4 py-3 text-right">CPA</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr v-for="geo in analytics.geo" :key="geo.country">
                <td class="px-4 py-3 font-mono text-xs text-slate-700">{{ geo.country }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(geo.clicks) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatInt(geo.conversions) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(geo.cr) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(geo.revenue) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(geo.cost) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(geo.profit) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatPercent(geo.roi) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(geo.epc) }}</td>
                <td class="px-4 py-3 text-right text-slate-700">{{ formatCurrency(geo.cpa) }}</td>
              </tr>
              <tr v-if="analytics.geo.length === 0">
                <td colspan="10" class="px-4 py-6 text-center text-slate-500">Нет данных</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
