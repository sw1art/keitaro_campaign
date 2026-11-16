<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { Offer } from '~/types'

const props = defineProps<{
  modelValue: number[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: number[]): void
}>()

const api = useApi()

const offers = ref<Offer[]>([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const open = ref(false)
const root = ref<HTMLElement | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | undefined

const selected = computed(() => props.modelValue)
const hasMore = computed(() => offers.value.length < total.value)

const selectedOffers = computed(() =>
  offers.value.filter((offer) => selected.value.includes(offer.id)),
)

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

function toggle(id: number) {
  if (selected.value.includes(id)) {
    emit('update:modelValue', selected.value.filter((item) => item !== id))
  } else {
    emit('update:modelValue', [...selected.value, id])
  }
}

function remove(id: number) {
  emit('update:modelValue', selected.value.filter((item) => item !== id))
}

function onClickOutside(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  load(true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
  clearTimeout(debounceTimer)
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="input flex min-h-[42px] flex-wrap items-center gap-1.5 text-left"
      @click="open = !open"
    >
      <span v-if="selected.length === 0" class="text-slate-400">Выберите офферы…</span>
      <span
        v-for="id in selected"
        :key="id"
        class="inline-flex items-center gap-1 rounded bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700"
      >
        #{{ id }}
        <button type="button" class="text-indigo-400 hover:text-indigo-700" @click.stop="remove(id)">×</button>
      </span>
    </button>

    <div
      v-if="open"
      class="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
    >
      <div class="border-b border-slate-200 p-2">
        <input
          v-model="search"
          type="text"
          placeholder="Поиск по ID или названию…"
          class="input py-1.5 text-sm"
          @input="onSearchInput"
        />
      </div>
      <div class="max-h-72 overflow-y-auto">
        <AppSpinner v-if="loading && offers.length === 0" class="p-3" label="Загрузка офферов…" />
        <AppAlert v-else-if="error" type="error" class="m-3">{{ error }}</AppAlert>
        <p v-else-if="offers.length === 0" class="p-3 text-sm text-slate-500">Ничего не найдено</p>
        <template v-else>
          <label
            v-for="offer in offers"
            :key="offer.id"
            class="flex cursor-pointer items-start gap-2 px-3 py-2 text-sm hover:bg-slate-50"
          >
            <input
              type="checkbox"
              class="mt-0.5 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              :checked="selected.includes(offer.id)"
              @change="toggle(offer.id)"
            />
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
          </label>
          <div class="border-t border-slate-100 p-2 text-center">
            <button v-if="hasMore" type="button" class="btn btn-secondary w-full" :disabled="loading" @click="loadMore">
              {{ loading ? 'Загрузка…' : 'Показать ещё' }}
            </button>
            <span v-else class="text-xs text-slate-400">Показаны все активные офферы ({{ total }})</span>
          </div>
        </template>
      </div>
    </div>

    <p v-if="selectedOffers.length > 0" class="mt-1.5 text-xs text-slate-500">
      {{ selectedOffers.map((offer) => offer.name).join(', ') }}
    </p>
  </div>
</template>
