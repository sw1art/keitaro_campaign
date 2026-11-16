<script setup lang="ts">
import type { AnalyticsRange, RangeSelection } from '~/types/analytics'

const props = defineProps<{
  modelValue: RangeSelection
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: RangeSelection): void
}>()

const ranges: Array<{ value: AnalyticsRange; label: string }> = [
  { value: 'today', label: 'Сегодня' },
  { value: 'yesterday', label: 'Вчера' },
  { value: 'last_7_days', label: '7 дней' },
  { value: 'last_30_days', label: '30 дней' },
  { value: 'custom', label: 'Произвольный' },
]

const timezones = [
  'Europe/Moscow',
  'Europe/London',
  'Europe/Berlin',
  'UTC',
  'America/New_York',
  'Asia/Almaty',
]

function update(patch: Partial<RangeSelection>) {
  emit('update:modelValue', { ...props.modelValue, ...patch })
}
</script>

<template>
  <div class="flex flex-wrap items-end gap-3">
    <div>
      <span class="field-label">Период</span>
      <div class="mt-1 flex flex-wrap gap-1">
        <button
          v-for="r in ranges"
          :key="r.value"
          type="button"
          class="rounded-md px-3 py-1.5 text-sm font-medium ring-1 ring-inset transition"
          :class="
            modelValue.range === r.value
              ? 'bg-indigo-600 text-white ring-indigo-600'
              : 'bg-white text-slate-700 ring-slate-300 hover:bg-slate-50'
          "
          @click="update({ range: r.value })"
        >
          {{ r.label }}
        </button>
      </div>
    </div>

    <div v-if="modelValue.range === 'custom'" class="flex gap-3">
      <div>
        <label class="field-label" for="range-from">С</label>
        <input
          id="range-from"
          type="date"
          class="input mt-1 w-40"
          :value="modelValue.from"
          @input="update({ from: ($event.target as HTMLInputElement).value })"
        />
      </div>
      <div>
        <label class="field-label" for="range-to">По</label>
        <input
          id="range-to"
          type="date"
          class="input mt-1 w-40"
          :value="modelValue.to"
          @input="update({ to: ($event.target as HTMLInputElement).value })"
        />
      </div>
    </div>

    <div>
      <label class="field-label" for="range-tz">Часовой пояс</label>
      <select
        id="range-tz"
        class="input mt-1 w-48"
        :value="modelValue.timezone"
        @change="update({ timezone: ($event.target as HTMLSelectElement).value })"
      >
        <option v-for="tz in timezones" :key="tz" :value="tz">{{ tz }}</option>
      </select>
    </div>
  </div>
</template>
