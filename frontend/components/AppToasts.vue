<script setup lang="ts">
import { computed } from 'vue'
import { useToastsStore } from '~/stores/useToasts'

const store = useToastsStore()

const kindClasses: Record<string, string> = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  error: 'border-red-200 bg-red-50 text-red-800',
  info: 'border-sky-200 bg-sky-50 text-sky-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
}

const visible = computed(() => store.toasts)
</script>

<template>
  <div class="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-80 flex-col gap-2">
    <TransitionGroup name="toast">
      <div
        v-for="toast in visible"
        :key="toast.id"
        class="pointer-events-auto flex items-start justify-between gap-2 rounded-lg border px-3 py-2.5 text-sm shadow-lg"
        :class="kindClasses[toast.kind] ?? kindClasses.info"
      >
        <span>{{ toast.message }}</span>
        <button
          type="button"
          class="ml-2 shrink-0 rounded p-0.5 text-current opacity-60 hover:opacity-100"
          aria-label="Закрыть"
          @click="store.dismiss(toast.id)"
        >
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
            />
          </svg>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}
</style>
