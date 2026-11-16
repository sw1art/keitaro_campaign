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
const retrying = ref(false)

let timer: ReturnType<typeof setInterval> | undefined

const isActive = computed(() => {
  const status = operation.value?.status
  return status === 'pending' || status === 'processing'
})

const stageLabel = computed(() => {
  switch (operation.value?.current_stage) {
    case 'pending':
      return 'В очереди'
    case 'creating_campaign':
      return 'Создание кампании'
    case 'creating_google_stream':
      return 'Создание Google Redirect'
    case 'creating_offer_stream':
      return 'Создание Offer Flow'
    case 'verifying':
      return 'Проверка результата'
    case 'completed':
      return 'Завершено'
    default:
      return '—'
  }
})

const clampedProgress = computed(() => {
  const progress = operation.value?.progress ?? 0
  return Math.min(100, Math.max(0, progress))
})

const steps = ['Создание кампании', 'Google Redirect', 'Offer Flow', 'Проверка результата']

type StepState = 'pending' | 'current' | 'done' | 'failed'

function stageInfo(stage: string | null | undefined): { completedCount: number; currentIndex: number } {
  switch (stage) {
    case 'pending':
      return { completedCount: 0, currentIndex: -1 }
    case 'creating_campaign':
      return { completedCount: 0, currentIndex: 0 }
    case 'creating_google_stream':
      return { completedCount: 1, currentIndex: 1 }
    case 'creating_offer_stream':
      return { completedCount: 2, currentIndex: 2 }
    case 'verifying':
      return { completedCount: 3, currentIndex: 3 }
    case 'completed':
      return { completedCount: 4, currentIndex: -1 }
    default:
      return { completedCount: 0, currentIndex: -1 }
  }
}

const stepStates = computed<StepState[]>(() => {
  const status = operation.value?.status
  const stage = operation.value?.current_stage
  const info = stageInfo(stage)
  const isTerminalFailure =
    status === 'failed' || status === 'partially_failed' || status === 'needs_attention'
  return steps.map((_, index) => {
    if (index < info.completedCount) return 'done'
    if (index === info.currentIndex) {
      if (isTerminalFailure) return 'failed'
      if (status === 'processing') return 'current'
      return 'pending'
    }
    return 'pending'
  })
})

function stepCircleClass(state: StepState): string {
  switch (state) {
    case 'done':
      return 'border-emerald-500 bg-emerald-500 text-white'
    case 'failed':
      return 'border-red-500 bg-red-500 text-white'
    case 'current':
      return 'border-indigo-500 bg-indigo-50 text-indigo-600'
    default:
      return 'border-slate-300 bg-white text-slate-400'
  }
}

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

async function retry() {
  retrying.value = true
  try {
    operation.value = await api.retryOperation(operationId.value)
    error.value = null
    startPolling()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Не удалось повторить операцию'
  } finally {
    retrying.value = false
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
          <div v-if="operation.started_at">
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Начата</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ formatDate(operation.started_at) }}</dd>
          </div>
          <div v-if="operation.finished_at">
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">Завершена</dt>
            <dd class="mt-1 text-sm text-slate-800">{{ formatDate(operation.finished_at) }}</dd>
          </div>
        </dl>
      </div>

      <div class="card p-6">
        <div>
          <div class="flex items-center justify-between text-sm text-slate-500">
            <span>Прогресс</span>
            <span class="font-medium text-slate-800">{{ clampedProgress }}%</span>
          </div>
          <div class="mt-1.5 h-2 w-full rounded-full bg-slate-200">
            <div
              class="h-2 rounded-full bg-indigo-600 transition-all duration-500"
              :style="{ width: `${clampedProgress}%` }"
            ></div>
          </div>
        </div>

        <ol class="mt-6 flex items-start">
          <li v-for="(step, index) in steps" :key="step" class="flex flex-1 items-start">
            <div class="flex flex-col items-center text-center">
              <span
                class="flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-semibold"
                :class="stepCircleClass(stepStates[index])"
              >
                <svg
                  v-if="stepStates[index] === 'current'"
                  class="h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                <span v-else-if="stepStates[index] === 'done'">✓</span>
                <span v-else-if="stepStates[index] === 'failed'">✕</span>
                <span v-else>○</span>
              </span>
              <span class="mt-2 max-w-[7rem] text-xs leading-tight text-slate-600">{{ step }}</span>
            </div>
            <div v-if="index < steps.length - 1" class="mx-1 mt-4 h-0.5 flex-1 bg-slate-200"></div>
          </li>
        </ol>

        <div v-if="operation.status === 'failed'" class="mt-6">
          <AppAlert v-if="operation.error" type="error" title="Ошибка операции">
            <span class="font-mono">{{ operation.error?.code }}</span> — {{ operation.error?.message }}
          </AppAlert>
          <div class="mt-3">
            <button class="btn btn-primary" :disabled="retrying" @click="retry">
              <AppSpinner v-if="retrying" size="sm" label="Повтор…" />
              <span v-else>Повторить операцию</span>
            </button>
          </div>
        </div>

        <div v-else-if="operation.status === 'partially_failed'" class="mt-6">
          <AppAlert type="warning" title="Частично завершено">
            Частично завершено — часть объектов создана.
            <span v-if="operation.campaign_id"> Создана кампания #{{ operation.campaign_id }}.</span>
            <span v-if="operation.error"> {{ operation.error?.code }} — {{ operation.error?.message }}</span>
          </AppAlert>
        </div>

        <div v-else-if="operation.status === 'needs_attention'" class="mt-6">
          <AppAlert type="warning" title="Требуется вмешательство">
            Операция требует вмешательства.
            <span v-if="operation.error"> {{ operation.error?.code }} — {{ operation.error?.message }}</span>
          </AppAlert>
        </div>

        <div v-if="operation.status === 'completed' && operation.campaign_id" class="mt-6 flex flex-wrap items-center gap-3">
          <AppAlert type="success" title="Кампания создана">Кампания #{{ operation.campaign_id }} успешно создана</AppAlert>
          <NuxtLink :to="`/campaigns/${operation.campaign_id}`" class="btn btn-primary shrink-0">Открыть кампанию</NuxtLink>
        </div>

        <div v-if="isActive" class="mt-6 flex items-center gap-2 text-sm text-slate-500">
          <AppSpinner size="sm" label="Операция выполняется, статус обновляется автоматически…" />
        </div>
      </div>
    </template>
  </div>
</template>
