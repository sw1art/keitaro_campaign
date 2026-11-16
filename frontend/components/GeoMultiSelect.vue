<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { GeoCountry } from '~/types'

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>()

const api = useApi()

const countries = ref<GeoCountry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const open = ref(false)
const root = ref<HTMLElement | null>(null)

const selected = computed(() => props.modelValue)

const filtered = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return countries.value
  return countries.value.filter(
    (country) => country.name.toLowerCase().includes(query) || country.code.toLowerCase().includes(query),
  )
})

const selectedNames = computed(() => {
  const map = new Map(countries.value.map((country) => [country.code, country.name]))
  return selected.value.map((code) => map.get(code) ?? code)
})

function toggle(code: string) {
  if (selected.value.includes(code)) {
    emit('update:modelValue', selected.value.filter((item) => item !== code))
  } else {
    emit('update:modelValue', [...selected.value, code])
  }
}

function remove(code: string) {
  emit('update:modelValue', selected.value.filter((item) => item !== code))
}

function onClickOutside(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) {
    open.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', onClickOutside)
  loading.value = true
  try {
    countries.value = await api.listGeo()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Не удалось загрузить список стран'
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="input flex min-h-[42px] flex-wrap items-center gap-1.5 text-left"
      @click="open = !open"
    >
      <span v-if="selected.length === 0" class="text-slate-400">Выберите GEO…</span>
      <span
        v-for="code in selected"
        :key="code"
        class="inline-flex items-center gap-1 rounded bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700"
      >
        {{ code }}
        <button type="button" class="text-indigo-400 hover:text-indigo-700" @click.stop="remove(code)">×</button>
      </span>
    </button>

    <div
      v-if="open"
      class="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
    >
      <div class="border-b border-slate-200 p-2">
        <input v-model="search" type="text" placeholder="Поиск по названию или коду…" class="input py-1.5 text-sm" />
      </div>
      <div class="max-h-64 overflow-y-auto">
        <AppSpinner v-if="loading" class="p-3" label="Загрузка стран…" />
        <AppAlert v-else-if="error" type="error" class="m-3">{{ error }}</AppAlert>
        <p v-else-if="filtered.length === 0" class="p-3 text-sm text-slate-500">Ничего не найдено</p>
        <label
          v-for="country in filtered"
          :key="country.code"
          class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50"
        >
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            :checked="selected.includes(country.code)"
            @change="toggle(country.code)"
          />
          <span class="font-mono text-xs text-slate-500">{{ country.code }}</span>
          <span class="text-slate-800">{{ country.name }}</span>
        </label>
      </div>
    </div>

    <p v-if="selected.length > 0" class="mt-1.5 text-xs text-slate-500">
      {{ selectedNames.join(', ') }}
    </p>
  </div>
</template>
