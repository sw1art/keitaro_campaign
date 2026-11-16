<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { Operation } from '~/types'
import { ApiError } from '~/utils/apiError'
import { formatDate } from '~/utils/format'

const route = useRoute()
const api = useApi()

const operationId = computed(() => String(route.params.id))

const operation = ref<Operation | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

let timer: ReturnType<typeof setInterval> | undefined

const isActive = computed(() => {
  const status = operation.value?.status
  return status === 'pending' || status === 'processing'
})

const stageLabel = computed(() => {
  switch (operation.value?.status) {
    case 'pending':
      return 'В очереди'
    case 'processing':
      return 'Выполняется'
    case 'completed':
      return 'Завершено'
    case 'failed':
      return 'Ошибка'
    default:
      return '—'
  }
})

const stageIndex = computed(() => {
  switch (operation.value?.status) {
    case 'pending':
      return 0
    case 'processing':
      return 1
    case 'completed':
      return 2
    default:
      return 0
  }
})

const steps = ['В очереди', 'Выполняется', 'Завершено']

function startPolling() {
  if (timer) return
  timer = setInterval(() => {
    load()
  }, 2000)
}

function stopPolling() {
  if (timer) {
    clearInterval(timer)
    timer = undefined
  }
}

async function load() {
  try {
    operation.value = await api.getOperation(operationId.value)
    error.value = null
    if (isActive.value) startPolling()
    else stopPolling()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось загрузить операцию'
    stopPolling()
  } finally {
    loading.value = false
  }
}

onMounted(load)
onBeforeUnmount(stopPolling)
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <div class="flex items-center justify-between gap-3">
      <div class="min-w-0">
        <NuxtLink to="/" class="text-sm text-indigo-600 hover:text-indigo-500">← На дашборд</NuxtLink>
        <h1 class="mt-1 text-2xl font-semibold text-slate-900">Статус операции</h1>
      </div>
      <AppStatusBadge v-if="operation" :status="operation.status" />
    </div>

    <AppSpinner v-if="loading" label="Загрузка операции…" />
    <AppAlert v-else-if="error" type="error" title="Ошибка">{{ error }}</AppAlert>

    <template v-else-if="operation">
      <div class="card p-6">
        <dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">ID операции</dt>
            <dd class="mt-1 break-all font-mono text-sm text-slate-800">{{ operation.operation_id }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Тип</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ operation.type }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Текущий этап</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ stageLabel }}</dd>
          </div>
          <div>
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Создана</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ formatDate(operation.created_at) }}</dd>
          </div>
        </dl>
      </div>

      <div class="card p-6">
        <ol class="flex items-center">
          <li v-for="(step, index) in steps" :key="step" class="flex flex-1 items-center">
            <div class="flex flex-col items-center">
              <span
                class="flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold"
                :class="index < stageIndex || operation.status === 'completed' ? 'bg-emerald-500 text-white' : index === stageIndex ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-500'"
              >
                {{ index + 1 }}
              </span>
              <span class="mt-1.5 text-xs text-slate-600">{{ step }}</span>
            </div>
            <div v-if="index < steps.length - 1" class="mx-2 h-0.5 flex-1 bg-slate-200"></div>
          </li>
        </ol>

        <div v-if="operation.status === 'failed' && operation.error" class="mt-5">
          <AppAlert type="error" title="Ошибка операции">
            <span class="font-mono">{{ operation.error.code }}</span> — {{ operation.error.message }}
          </AppAlert>
        </div>

        <div v-if="operation.status === 'completed' && operation.campaign_id" class="mt-5 flex items-center gap-3">
          <AppAlert type="success" title="Кампания создана">Кампания #{{ operation.campaign_id }} успешно создана</AppAlert>
          <NuxtLink :to="`/campaigns/${operation.campaign_id}`" class="btn btn-primary shrink-0">Открыть кампанию</NuxtLink>
        </div>

        <div v-if="isActive" class="mt-5 flex items-center gap-2 text-sm text-slate-500">
          <AppSpinner size="sm" label="Операция выполняется, статус обновляется автоматически…" />
        </div>
      </div>
    </template>
  </div>
</template>
