<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    status: string
    label?: string
  }>(),
  {},
)

interface BadgeStyle {
  classes: string
  dot: string
  text: string
}

const style = computed<BadgeStyle>(() => {
  const value = (props.status ?? '').toLowerCase()
  switch (value) {
    case 'active':
      return { classes: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', dot: 'bg-emerald-500', text: 'Активен' }
    case 'completed':
      return { classes: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', dot: 'bg-emerald-500', text: 'Завершено' }
    case 'paused':
      return { classes: 'bg-amber-50 text-amber-700 ring-amber-600/20', dot: 'bg-amber-500', text: 'Приостановлен' }
    case 'disabled':
      return { classes: 'bg-amber-50 text-amber-700 ring-amber-600/20', dot: 'bg-amber-500', text: 'Отключен' }
    case 'pending':
      return { classes: 'bg-sky-50 text-sky-700 ring-sky-600/20', dot: 'bg-sky-500', text: 'Ожидание' }
    case 'processing':
      return { classes: 'bg-indigo-50 text-indigo-700 ring-indigo-600/20', dot: 'bg-indigo-500 animate-pulse', text: 'Выполняется' }
    case 'failed':
      return { classes: 'bg-red-50 text-red-700 ring-red-600/20', dot: 'bg-red-500', text: 'Ошибка' }
    case 'deleted':
      return { classes: 'bg-slate-100 text-slate-500 ring-slate-500/20', dot: 'bg-slate-400', text: 'Удалена' }
    default:
      return { classes: 'bg-slate-100 text-slate-600 ring-slate-500/20', dot: 'bg-slate-400', text: props.label ?? props.status }
  }
})
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset"
    :class="style.classes"
  >
    <span class="h-1.5 w-1.5 rounded-full" :class="style.dot"></span>
    {{ style.text }}
  </span>
</template>
