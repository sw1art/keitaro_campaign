<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()

const emit = defineEmits<{
  (e: 'update:page', page: number): void
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
</script>

<template>
  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <p class="text-sm text-slate-500">
      Всего: {{ total }} · Страница {{ page }} из {{ totalPages }}
    </p>
    <div class="flex gap-2">
      <button class="btn btn-secondary" :disabled="page <= 1" @click="emit('update:page', page - 1)">Назад</button>
      <button class="btn btn-secondary" :disabled="page >= totalPages" @click="emit('update:page', page + 1)">Вперёд</button>
    </div>
  </div>
</template>
