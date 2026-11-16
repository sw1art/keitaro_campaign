<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { AnalyticsOverview, AnalyticsTrends, RangeSelection } from '~/types/analytics'
import { ApiError } from '~/utils/apiError'
import {
  buildAnalyticsQuery,
  defaultRangeSelection,
  formatMetricValue,
  METRIC_DEFS,
  shortDay,
} from '~/utils/analytics'

const api = useApi()

const selection = ref<RangeSelection>(defaultRangeSelection())
const overview = ref<AnalyticsOverview | null>(null)
const trends = ref<AnalyticsTrends | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const items = computed(() => trends.value?.items ?? [])
const hasData = computed(() => items.value.length > 0)

const chartLabels = computed(() => items.value.map((item) => shortDay(item.day)))

const clicksConversions = computed(() => [
  { label: 'Клики', data: items.value.map((item) => item.clicks), borderColor: '#6366f1', yAxisID: 'y' as const },
  { label: 'Конверсии', data: items.value.map((item) => item.conversions), borderColor: '#10b981', yAxisID: 'y1' as const },
])

const money = computed(() => [
  { label: 'Доход', data: items.value.map((item) => item.revenue), borderColor: '#10b981' },
  { label: 'Расход', data: items.value.map((item) => item.cost), borderColor: '#ef4444' },
  { label: 'Прибыль', data: items.value.map((item) => item.profit), borderColor: '#6366f1' },
])

const roiSeries = computed(() => [
  { label: 'ROI', data: items.value.map((item) => item.roi), borderColor: '#8b5cf6' },
])

const crSeries = computed(() => [
  { label: 'CR', data: items.value.map((item) => item.cr), borderColor: '#0ea5e9' },
])

async function load() {
  loading.value = true
  error.value = null
  try {
    const query = buildAnalyticsQuery(selection.value)
    const [overviewData, trendsData] = await Promise.all([
      api.getAnalyticsOverview(query),
      api.getAnalyticsTrends(query),
    ])
    overview.value = overviewData
    trends.value = trendsData
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить аналитику'
  } finally {
    loading.value = false
  }
}

watch(selection, load, { deep: true })
onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">Аналитика</h1>
        <p class="mt-1 text-sm text-slate-500">Сводные показатели по всем кампаниям</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/analytics/offers" class="btn btn-secondary">Офферы</NuxtLink>
        <NuxtLink to="/analytics/geo" class="btn btn-secondary">GEO</NuxtLink>
      </div>
    </div>

    <AnalyticsRangeSelector v-model="selection" />

    <AppSpinner v-if="loading" label="Загрузка аналитики…" />
    <AppAlert v-else-if="error" type="error" title="Ошибка загрузки">{{ error }}</AppAlert>

    <template v-else-if="overview">
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        <AnalyticsMetricCard
          v-for="def in METRIC_DEFS"
          :key="def.key"
          :label="def.label"
          :value="formatMetricValue(overview.metrics[def.key], def.kind)"
          :delta="overview.deltas[def.key] ?? null"
        />
      </div>

      <div v-if="!hasData" class="card p-8 text-center text-sm text-slate-500">
        Нет данных за выбранный период
      </div>

      <template v-else>
        <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section class="card p-5">
            <h2 class="text-sm font-semibold text-slate-900">Клики и конверсии</h2>
            <div class="mt-3"><AppLineChart :labels="chartLabels" :datasets="clicksConversions" :height="240" /></div>
          </section>
          <section class="card p-5">
            <h2 class="text-sm font-semibold text-slate-900">Доход, расход и прибыль</h2>
            <div class="mt-3"><AppLineChart :labels="chartLabels" :datasets="money" :height="240" /></div>
          </section>
          <section class="card p-5">
            <h2 class="text-sm font-semibold text-slate-900">ROI по дням</h2>
            <div class="mt-3"><AppLineChart :labels="chartLabels" :datasets="roiSeries" :height="240" /></div>
          </section>
          <section class="card p-5">
            <h2 class="text-sm font-semibold text-slate-900">CR по дням</h2>
            <div class="mt-3"><AppLineChart :labels="chartLabels" :datasets="crSeries" :height="240" /></div>
          </section>
        </div>
      </template>
    </template>
  </div>
</template>
