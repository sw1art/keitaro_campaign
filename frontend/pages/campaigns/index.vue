<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { Campaign, Domain, Group, TrafficSource } from '~/types'
import { ApiError } from '~/utils/apiError'
import { formatDate } from '~/utils/format'

const route = useRoute()
const router = useRouter()
const api = useApi()

const search = ref('')
const stateFilter = ref('')
const domainFilter = ref('')
const trafficSourceFilter = ref('')
const groupFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const sortBy = ref('created_at')
const sortOrder = ref<'asc' | 'desc'>('desc')

const items = ref<Campaign[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

const domains = ref<Domain[]>([])
const trafficSources = ref<TrafficSource[]>([])
const groups = ref<Group[]>([])

let debounceTimer: ReturnType<typeof setTimeout> | undefined
let syncing = false

const stateOptions = [
  { value: '', label: 'Все статусы' },
  { value: 'active', label: 'Активные' },
  { value: 'disabled', label: 'Отключенные' },
]

const columns: Array<{ key: string; label: string }> = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Название' },
  { key: 'state', label: 'Статус' },
  { key: 'domain', label: 'Домен' },
  { key: 'traffic_source', label: 'Источник трафика' },
  { key: 'group', label: 'Группа' },
  { key: 'created_at', label: 'Создана' },
  { key: 'updated_at', label: 'Обновлена' },
]

const validSortBy = new Set(['id', 'name', 'state', 'domain', 'traffic_source', 'group', 'created_at', 'updated_at'])

function parsePositiveInt(value: unknown, fallback: number): number {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback
}

function readQuery() {
  const query = route.query
  page.value = parsePositiveInt(query.page, 1)
  pageSize.value = parsePositiveInt(query.page_size, 20)
  search.value = typeof query.search === 'string' ? query.search : ''
  stateFilter.value = typeof query.state === 'string' ? query.state : ''
  domainFilter.value = typeof query.domain_id === 'string' ? query.domain_id : ''
  trafficSourceFilter.value = typeof query.traffic_source_id === 'string' ? query.traffic_source_id : ''
  groupFilter.value = typeof query.group_id === 'string' ? query.group_id : ''
  sortBy.value = typeof query.sort_by === 'string' && validSortBy.has(query.sort_by) ? query.sort_by : 'created_at'
  sortOrder.value = query.sort_order === 'asc' ? 'asc' : 'desc'
}

function buildQuery(): Record<string, string> {
  const query: Record<string, string> = {
    page: String(page.value),
    page_size: String(pageSize.value),
    sort_by: sortBy.value,
    sort_order: sortOrder.value,
  }
  if (search.value) query.search = search.value
  if (stateFilter.value) query.state = stateFilter.value
  if (domainFilter.value) query.domain_id = domainFilter.value
  if (trafficSourceFilter.value) query.traffic_source_id = trafficSourceFilter.value
  if (groupFilter.value) query.group_id = groupFilter.value
  return query
}

async function syncQuery() {
  syncing = true
  try {
    await router.replace({ query: buildQuery() })
  } finally {
    syncing = false
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const result = await api.listCampaigns({
      search: search.value.trim() || undefined,
      state: stateFilter.value || undefined,
      domain_id: domainFilter.value ? Number(domainFilter.value) : undefined,
      traffic_source_id: trafficSourceFilter.value ? Number(trafficSourceFilter.value) : undefined,
      group_id: groupFilter.value ? Number(groupFilter.value) : undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
      page: page.value,
      page_size: pageSize.value,
    })
    items.value = result.items
    total.value = result.total
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить кампании'
  } finally {
    loading.value = false
  }
}

function toggleSort(key: string) {
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortOrder.value = 'desc'
  }
  page.value = 1
  syncQuery()
  load()
}

function onSearchInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    syncQuery()
    load()
  }, 300)
}

function onFilterChange() {
  page.value = 1
  syncQuery()
  load()
}

function onPageChange(next: number) {
  page.value = next
  syncQuery()
  load()
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  syncQuery()
  load()
}

watch(
  () => route.query,
  () => {
    if (syncing) return
    readQuery()
    load()
  },
)

onMounted(async () => {
  readQuery()
  await load()

  // Populate filter dropdowns (best effort).
  try {
    const [domainList, sourceList, groupList] = await Promise.all([
      api.listDomains(),
      api.listTrafficSources(),
      api.listGroups(),
    ])
    domains.value = domainList
    trafficSources.value = sourceList
    groups.value = groupList
  } catch {
    /* filters stay empty if dictionaries fail */
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">Кампании</h1>
        <p class="mt-1 text-sm text-slate-500">Список кампаний Keitaro</p>
      </div>
      <NuxtLink to="/campaigns/create" class="btn btn-primary">Создать кампанию</NuxtLink>
    </div>

    <div class="flex flex-wrap items-end gap-3">
      <input
        v-model="search"
        type="text"
        placeholder="Поиск по ID или названию…"
        class="input sm:max-w-xs"
        @input="onSearchInput"
      />
      <select v-model="stateFilter" class="input sm:w-44" @change="onFilterChange">
        <option v-for="option in stateOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <select v-model="domainFilter" class="input sm:w-48" @change="onFilterChange">
        <option value="">Все домены</option>
        <option v-for="domain in domains" :key="domain.id" :value="String(domain.id)">
          {{ domain.name }}
        </option>
      </select>
      <select v-model="trafficSourceFilter" class="input sm:w-48" @change="onFilterChange">
        <option value="">Все источники</option>
        <option v-for="source in trafficSources" :key="source.id" :value="String(source.id)">
          {{ source.name }}
        </option>
      </select>
      <select v-model="groupFilter" class="input sm:w-48" @change="onFilterChange">
        <option value="">Все группы</option>
        <option v-for="group in groups" :key="group.id" :value="String(group.id)">
          {{ group.name }}
        </option>
      </select>
    </div>

    <AppSpinner v-if="loading && items.length === 0" label="Загрузка кампаний…" />
    <AppAlert v-else-if="error" type="error" title="Ошибка загрузки">{{ error }}</AppAlert>

    <template v-else>
      <div class="card overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th v-for="column in columns" :key="column.key" class="px-4 py-3">
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
            <tr v-for="campaign in items" :key="campaign.id" class="hover:bg-slate-50">
              <td class="px-4 py-3 font-mono text-xs text-slate-500">{{ campaign.id }}</td>
              <td class="px-4 py-3">
                <NuxtLink :to="`/campaigns/${campaign.id}`" class="font-medium text-indigo-600 hover:text-indigo-500">
                  {{ campaign.name }}
                </NuxtLink>
              </td>
              <td class="px-4 py-3"><AppStatusBadge :status="campaign.state" /></td>
              <td class="px-4 py-3 text-slate-700">{{ campaign.domain }}</td>
              <td class="px-4 py-3 text-slate-700">{{ campaign.traffic_source }}</td>
              <td class="px-4 py-3 text-slate-700">{{ campaign.group }}</td>
              <td class="px-4 py-3 text-slate-500">{{ formatDate(campaign.created_at) }}</td>
              <td class="px-4 py-3 text-slate-500">{{ formatDate(campaign.updated_at) }}</td>
            </tr>
            <tr v-if="items.length === 0">
              <td :colspan="columns.length" class="px-4 py-8 text-center text-slate-500">Кампании не найдены</td>
            </tr>
          </tbody>
        </table>
      </div>

      <AppPaginator
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="onPageChange"
        @update:pageSize="onPageSizeChange"
      />
    </template>
  </div>
</template>
