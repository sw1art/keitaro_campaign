<script setup lang="ts">
import { computed } from 'vue'
import { formatDelta } from '~/utils/analytics'

const props = defineProps<{
  label: string
  value: string
  delta?: number | null
}>()

const badge = computed(() => formatDelta(props.delta))
</script>

<template>
  <div class="card p-4">
    <p class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ label }}</p>
    <p class="mt-1 text-xl font-semibold text-slate-900">{{ value }}</p>
    <span
      v-if="delta !== undefined"
      class="mt-1 inline-flex items-center text-xs font-medium"
      :class="badge.kind === 'up' ? 'text-emerald-600' : badge.kind === 'down' ? 'text-red-600' : 'text-slate-400'"
    >
      {{ badge.text }}
    </span>
  </div>
</template>
