<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Campaign } from '~/types'
import { ApiError } from '~/utils/apiError'
import { formatDate } from '~/utils/format'

const api = useApi()

const search = ref('')
const stateFilter = ref('')
const page = ref(1)
const pageSize = 20

const items = ref<Campaign[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | undefined

const stateOptions = [
  { value: '', label: 'Все статусы' },
  { value: 'active', label: 'Активные' },
  { value: 'disabled', label: 'Отключенные' },
  { value: 'paused', label: 'Приостановленные' },
]

async function load() {
  loading.value = true
  error.value = null
  try {
    const result = await api.listCampaigns({
      search: search.value.trim() || undefined,
      state: stateFilter.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    items.value = result.items
    total.value = result.total
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить кампании'
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    load()
  }, 300)
}

function onStateChange() {
  page.value = 1
  load()
}

function setPage(next: number) {
  page.value = next
  load()
}

onMounted(load)
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

    <div class="flex flex-col gap-3 sm:flex-row">
      <input
        v-model="search"
        type="text"
        placeholder="Поиск по ID или названию…"
        class="input sm:max-w-xs"
        @input="onSearchInput"
      />
      <select v-model="stateFilter" class="input sm:w-56" @change="onStateChange">
        <option v-for="option in stateOptions" :key="option.value" :value="option.value">
          {{ option.label }}
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
              <th class="px-4 py-3">ID</th>
              <th class="px-4 py-3">Название</th>
              <th class="px-4 py-3">Статус</th>
              <th class="px-4 py-3">Домен</th>
              <th class="px-4 py-3">Источник трафика</th>
              <th class="px-4 py-3">Создана</th>
              <th class="px-4 py-3">Обновлена</th>
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
              <td class="px-4 py-3 text-slate-500">{{ formatDate(campaign.created_at) }}</td>
              <td class="px-4 py-3 text-slate-500">{{ formatDate(campaign.updated_at) }}</td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-slate-500">Кампании не найдены</td>
            </tr>
          </tbody>
        </table>
      </div>

      <AppPaginator :page="page" :page-size="pageSize" :total="total" @update:page="setPage" />
    </template>
  </div>
</template>
