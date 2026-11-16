<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    page: number
    pageSize: number
    total: number
    pageSizeOptions?: number[]
  }>(),
  { pageSizeOptions: () => [10, 20, 50] },
)

const emit = defineEmits<{
  (e: 'update:page', page: number): void
  (e: 'update:pageSize', size: number): void
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

function go(page: number) {
  if (page < 1 || page > totalPages.value) return
  emit('update:page', page)
}

function onPageSizeChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:pageSize', Number(target.value))
}
</script>

<template>
  <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
    <div class="flex items-center gap-2 text-sm text-slate-500">
      <span>Строк на странице:</span>
      <select :value="pageSize" class="input w-20 py-1.5" @change="onPageSizeChange">
        <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}</option>
      </select>
    </div>

    <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
      <p class="text-sm text-slate-500">Всего: {{ total }} · Страница {{ page }} из {{ totalPages }}</p>
      <div class="flex gap-1">
        <button class="btn btn-secondary !px-2.5" :disabled="page <= 1" aria-label="Первая страница" @click="go(1)">«</button>
        <button class="btn btn-secondary !px-2.5" :disabled="page <= 1" aria-label="Предыдущая страница" @click="go(page - 1)">‹</button>
        <button class="btn btn-secondary !px-2.5" :disabled="page >= totalPages" aria-label="Следующая страница" @click="go(page + 1)">›</button>
        <button class="btn btn-secondary !px-2.5" :disabled="page >= totalPages" aria-label="Последняя страница" @click="go(totalPages)">»</button>
      </div>
    </div>
  </div>
</template>
