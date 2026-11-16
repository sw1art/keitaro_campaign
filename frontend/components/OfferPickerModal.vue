<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Offer } from '~/types'

const props = defineProps<{
  open: boolean
  excludeIds: number[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'pick', offer: Offer): void
}>()

const api = useApi()

const offers = ref<Offer[]>([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | undefined

const excluded = computed(() => new Set(props.excludeIds))
const hasMore = computed(() => offers.value.length < total.value)

async function load(reset: boolean) {
  if (reset) {
    page.value = 1
    offers.value = []
  }
  loading.value = true
  error.value = null
  try {
    const result = await api.listOffers({
      search: search.value.trim() || undefined,
      state: 'active',
      page: page.value,
      page_size: 20,
    })
    offers.value = reset ? result.items : [...offers.value, ...result.items]
    total.value = result.total
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Не удалось загрузить офферы'
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => load(true), 300)
}

function loadMore() {
  page.value += 1
  load(false)
}

function pick(offer: Offer) {
  emit('pick', offer)
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      search.value = ''
      load(true)
    }
  },
)
</script>

<template>
  <AppModal :open="open" title="Добавить оффер" @close="emit('close')">
    <div class="space-y-3">
      <input
        v-model="search"
        type="text"
        placeholder="Поиск по ID или названию…"
        class="input text-sm"
        @input="onSearchInput"
      />

      <div class="max-h-80 overflow-y-auto rounded-lg ring-1 ring-slate-200">
        <AppSpinner v-if="loading && offers.length === 0" class="p-3" label="Загрузка офферов…" />
        <AppAlert v-else-if="error" type="error" class="m-3">{{ error }}</AppAlert>
        <p v-else-if="offers.length === 0" class="p-4 text-sm text-slate-500">Ничего не найдено</p>
        <template v-else>
          <button
            v-for="offer in offers"
            :key="offer.id"
            type="button"
            class="flex w-full items-start justify-between gap-2 px-3 py-2.5 text-left text-sm hover:bg-slate-50"
            :disabled="excluded.has(offer.id)"
            :class="excluded.has(offer.id) ? 'opacity-40' : ''"
            @click="pick(offer)"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium text-slate-900">{{ offer.name }}</span>
                <AppStatusBadge :status="offer.state" />
              </div>
              <div class="truncate text-xs text-slate-500">
                <span class="font-mono">#{{ offer.id }}</span>
                <span v-if="offer.group"> · {{ offer.group }}</span>
                <span v-if="offer.country?.length"> · {{ offer.country.join(', ') }}</span>
              </div>
            </div>
            <span v-if="excluded.has(offer.id)" class="shrink-0 text-xs font-medium text-slate-400">уже добавлен</span>
            <span v-else class="shrink-0 text-xs font-medium text-indigo-600">Добавить</span>
          </button>
          <div class="border-t border-slate-100 p-2 text-center">
            <button v-if="hasMore" type="button" class="btn btn-secondary w-full" :disabled="loading" @click="loadMore">
              {{ loading ? 'Загрузка…' : 'Показать ещё' }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </AppModal>
</template>
