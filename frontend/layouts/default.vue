<script setup lang="ts">
import { computed } from 'vue'

const route = useRoute()
const config = useRuntimeConfig()

const mockEnabled = computed(() => {
  const value: unknown = config.public.mock
  return value === true || value === 'true' || value === '1'
})

const nav = [
  { to: '/', label: 'Дашборд' },
  { to: '/campaigns', label: 'Кампании' },
  { to: '/analytics', label: 'Аналитика' },
  { to: '/campaigns/create', label: 'Создать кампанию' },
]

function isActive(to: string): boolean {
  if (to === '/') return route.path === '/'
  return route.path === to || route.path.startsWith(`${to}/`)
}
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <div class="flex items-center gap-3">
          <NuxtLink to="/" class="flex items-center gap-2">
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">A</span>
            <span class="text-base font-semibold text-slate-900">AdRobot</span>
          </NuxtLink>
          <span v-if="mockEnabled" class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
            Mock-режим
          </span>
        </div>
        <nav class="flex items-center gap-1">
          <NuxtLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="rounded-md px-3 py-2 text-sm font-medium transition"
            :class="isActive(item.to) ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
          >
            {{ item.label }}
          </NuxtLink>
        </nav>
      </div>
    </header>

    <main class="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
      <NuxtPage />
    </main>

    <footer class="border-t border-slate-200 bg-white">
      <div class="mx-auto max-w-7xl px-4 py-4 text-sm text-slate-400 sm:px-6">
        AdRobot · управление кампаниями Keitaro
      </div>
    </footer>

    <AppToasts />
  </div>
</template>
