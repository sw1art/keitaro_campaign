<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Campaign, Operation } from '~/types'
import { ApiError } from '~/utils/apiError'
import { formatDate } from '~/utils/format'

const api = useApi()

const campaignCount = ref(0)
const latestCampaigns = ref<Campaign[]>([])
const latestOperations = ref<Operation[]>([])
const operationsTotal = ref(0)
const successCount = ref(0)
const failedCount = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    const dashboard = await api.getDashboard()
    campaignCount.value = dashboard.campaigns_count
    latestCampaigns.value = dashboard.recent_campaigns
    latestOperations.value = dashboard.recent_operations
    operationsTotal.value = dashboard.operations_total
    successCount.value = dashboard.operations_completed
    failedCount.value = dashboard.operations_failed
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить данные'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">Дашборд</h1>
      <p class="mt-1 text-sm text-slate-500">Обзор кампаний и операций AdRobot</p>
    </div>

    <AppSpinner v-if="loading" label="Загрузка…" />
    <AppAlert v-else-if="error" type="error" title="Ошибка загрузки">{{ error }}</AppAlert>

    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="card p-5">
          <p class="text-sm text-slate-500">Кампании</p>
          <p class="mt-1 text-3xl font-semibold text-slate-900">{{ campaignCount }}</p>
        </div>
        <div class="card p-5">
          <p class="text-sm text-slate-500">Операции (всего)</p>
          <p class="mt-1 text-3xl font-semibold text-slate-900">{{ operationsTotal }}</p>
        </div>
        <div class="card p-5">
          <p class="text-sm text-slate-500">Успешные операции</p>
          <p class="mt-1 text-3xl font-semibold text-emerald-600">{{ successCount }}</p>
        </div>
        <div class="card p-5">
          <p class="text-sm text-slate-500">Неуспешные операции</p>
          <p class="mt-1 text-3xl font-semibold text-red-600">{{ failedCount }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section class="card p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-slate-900">Последние кампании</h2>
            <NuxtLink to="/campaigns" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">Все кампании →</NuxtLink>
          </div>
          <ul class="mt-3 divide-y divide-slate-100">
            <li v-for="campaign in latestCampaigns" :key="campaign.id" class="flex items-center justify-between py-2.5">
              <div class="min-w-0">
                <NuxtLink :to="`/campaigns/${campaign.id}`" class="truncate text-sm font-medium text-slate-900 hover:text-indigo-600">
                  {{ campaign.name }}
                </NuxtLink>
                <p class="text-xs text-slate-500">#{{ campaign.id }} · {{ campaign.domain }}</p>
              </div>
              <AppStatusBadge :status="campaign.state" />
            </li>
            <li v-if="latestCampaigns.length === 0" class="py-4 text-sm text-slate-500">Нет кампаний</li>
          </ul>
        </section>

        <section class="card p-5">
          <h2 class="text-base font-semibold text-slate-900">Последние операции</h2>
          <ul class="mt-3 divide-y divide-slate-100">
            <li v-for="operation in latestOperations" :key="operation.operation_id" class="flex items-center justify-between py-2.5">
              <div class="min-w-0">
                <NuxtLink :to="`/operations/${operation.operation_id}`" class="truncate text-sm font-medium text-slate-900 hover:text-indigo-600">
                  {{ operation.type }}
                </NuxtLink>
                <p class="text-xs text-slate-500">{{ formatDate(operation.created_at) }}</p>
              </div>
              <AppStatusBadge :status="operation.status" />
            </li>
            <li v-if="latestOperations.length === 0" class="py-4 text-sm text-slate-500">Нет операций</li>
          </ul>
        </section>
      </div>
    </template>
  </div>
</template>
