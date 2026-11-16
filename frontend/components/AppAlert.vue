<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'error' | 'warning' | 'info' | 'success'
    title?: string
  }>(),
  { type: 'error' },
)

const classes = computed(() => {
  switch (props.type) {
    case 'warning':
      return 'border-amber-200 bg-amber-50 text-amber-800'
    case 'info':
      return 'border-sky-200 bg-sky-50 text-sky-800'
    case 'success':
      return 'border-emerald-200 bg-emerald-50 text-emerald-800'
    default:
      return 'border-red-200 bg-red-50 text-red-800'
  }
})
</script>

<template>
  <div class="rounded-lg border px-4 py-3 text-sm" :class="classes">
    <p v-if="title" class="font-semibold">{{ title }}</p>
    <div class="mt-0.5">
      <slot />
    </div>
  </div>
</template>
