import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastKind = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: number
  kind: ToastKind
  message: string
}

let nextId = 1

export const useToastsStore = defineStore('toasts', () => {
  const toasts = ref<Toast[]>([])

  function push(kind: ToastKind, message: string) {
    const id = nextId++
    toasts.value = [...toasts.value, { id, kind, message }]
    setTimeout(() => dismiss(id), 5000)
  }

  function dismiss(id: number) {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }

  return { toasts, push, dismiss }
})
