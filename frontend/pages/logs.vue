<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { AuditLogItem, Operation } from '~/types'
import { ApiError } from '~/utils/apiError'
import { formatDate } from '~/utils/format'

const api = useApi()

type Tab = 'operations' | 'audit'

const activeTab = ref<Tab>('operations')

const operations = ref<Operation[]>([])
const operationsTotal = ref(0)
const opsPage = ref(1)
const opsPageSize = ref(20)

const audit = ref<AuditLogItem[]>([])
const auditTotal = ref(0)
const auditPage = ref(1)
const auditPageSize = ref(20)

const loading = ref(false)
const error = ref<string | null>(null)

const stageLabels: Record<string, string> = {
  pending: 'Ожидание',
  creating_campaign: 'Создание кампании',
  creating_google_stream: 'Google Redirect',
  creating_offer_stream: 'Offer Flow',
  verifying: 'Проверка',
  completed: 'Завершено',
}

function stageLabel(stage: string | null | undefined): string {
  if (!stage) return '—'
  return stageLabels[stage] ?? stage
}

async function loadOperations() {
  try {
    const res = await api.listOperations({ page: opsPage.value, page_size: opsPageSize.value })
    operations.value = res.items
    operationsTotal.value = res.total
  } catch (err) {
    throw err
  }
}

async function loadAudit() {
  try {
    const res = await api.listAuditLogs({ page: auditPage.value, page_size: auditPageSize.value })
    audit.value = res.items
    auditTotal.value = res.total
  } catch (err) {
    throw err
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    if (activeTab.value === 'operations') await loadOperations()
    else await loadAudit()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить логи'
  } finally {
    loading.value = false
  }
}

watch(activeTab, load)
watch([opsPage, opsPageSize], loadOperations)
watch([auditPage, auditPageSize], loadAudit)

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">Логи</h1>
      <p class="mt-1 text-sm text-slate-500">История операций и аудит действий AdRobot</p>
    </div>

    <div class="flex gap-1 border-b border-slate-200">
      <button
        class="border-b-2 px-4 py-2 text-sm font-medium transition"
        :class="activeTab === 'operations' ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500 hover:text-slate-800'"
        @click="activeTab = 'operations'"
      >
        Операции
      </button>
      <button
        class="border-b-2 px-4 py-2 text-sm font-medium transition"
        :class="activeTab === 'audit' ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500 hover:text-slate-800'"
        @click="activeTab = 'audit'"
      >
        Аудит
      </button>
    </div>

    <AppSpinner v-if="loading" label="Загрузка…" />
    <AppAlert v-else-if="error" type="error" title="Ошибка загрузки">{{ error }}</AppAlert>

    <!-- Operations -->
    <template v-else-if="activeTab === 'operations'">
      <div class="card overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th class="px-4 py-3">ID операции</th>
              <th class="px-4 py-3">Тип</th>
              <th class="px-4 py-3">Статус</th>
              <th class="px-4 py-3">Этап</th>
              <th class="px-4 py-3">Кампания</th>
              <th class="px-4 py-3">Создана</th>
              <th class="px-4 py-3">Завершена</th>
              <th class="px-4 py-3 text-right">Действие</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-for="operation in operations" :key="operation.operation_id">
              <td class="px-4 py-3 font-mono text-xs text-slate-500">{{ operation.operation_id.slice(0, 8) }}…</td>
              <td class="px-4 py-3 text-slate-700">{{ operation.type }}</td>
              <td class="px-4 py-3"><AppStatusBadge :status="operation.status" /></td>
              <td class="px-4 py-3">
                <div class="text-slate-700">{{ stageLabel(operation.current_stage) }}</div>
                <div class="mt-1 h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
                  <div class="h-full rounded-full bg-indigo-500" :style="{ width: `${operation.progress}%` }"></div>
                </div>
              </td>
              <td class="px-4 py-3">
                <NuxtLink v-if="operation.campaign_id" :to="`/campaigns/${operation.campaign_id}`" class="font-mono text-sm text-indigo-600 hover:underline">
                  #{{ operation.campaign_id }}
                </NuxtLink>
                <span v-else class="text-slate-400">—</span>
              </td>
              <td class="px-4 py-3 text-slate-500">{{ formatDate(operation.created_at) }}</td>
              <td class="px-4 py-3 text-slate-500">{{ formatDate(operation.finished_at) }}</td>
              <td class="px-4 py-3 text-right">
                <NuxtLink :to="`/operations/${operation.operation_id}`" class="btn btn-secondary !px-2.5 !py-1.5">Открыть</NuxtLink>
              </td>
            </tr>
            <tr v-if="operations.length === 0">
              <td colspan="8" class="px-4 py-8 text-center text-slate-500">Операций нет</td>
            </tr>
          </tbody>
        </table>
      </div>
      <AppPaginator v-model:page="opsPage" v-model:page-size="opsPageSize" :total="operationsTotal" />
    </template>

    <!-- Audit -->
    <template v-else>
      <div class="card overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th class="px-4 py-3">Время</th>
              <th class="px-4 py-3">Действие</th>
              <th class="px-4 py-3">Тип сущности</th>
              <th class="px-4 py-3">ID сущности</th>
              <th class="px-4 py-3">Операция</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 bg-white">
            <tr v-for="entry in audit" :key="entry.id">
              <td class="px-4 py-3 text-slate-500">{{ formatDate(entry.created_at) }}</td>
              <td class="px-4 py-3 font-mono text-xs text-slate-700">{{ entry.action }}</td>
              <td class="px-4 py-3 text-slate-700">{{ entry.entity_type }}</td>
              <td class="px-4 py-3 font-mono text-xs text-slate-500">{{ entry.entity_id }}</td>
              <td class="px-4 py-3">
                <NuxtLink v-if="entry.operation_id" :to="`/operations/${entry.operation_id}`" class="font-mono text-xs text-indigo-600 hover:underline">
                  {{ entry.operation_id.slice(0, 8) }}…
                </NuxtLink>
                <span v-else class="text-slate-400">—</span>
              </td>
            </tr>
            <tr v-if="audit.length === 0">
              <td colspan="5" class="px-4 py-8 text-center text-slate-500">Записей аудита нет</td>
            </tr>
          </tbody>
        </table>
      </div>
      <AppPaginator v-model:page="auditPage" v-model:page-size="auditPageSize" :total="auditTotal" />
    </template>
  </div>
</template>
