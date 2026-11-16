<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Offer } from '~/types'
import { useCampaignEditorStore } from '~/stores/useCampaignEditor'
import { formatPercentage, isValidShare } from '~/utils/distribution'

const props = defineProps<{
  offersById: Record<number, Offer>
}>()

const emit = defineEmits<{
  (e: 'add-offer'): void
  (e: 'save'): void
  (e: 'cancel'): void
}>()

const store = useCampaignEditorStore()
const pendingRemoveId = ref<number | null>(null)

const distributionByOffer = computed(() => {
  const map = new Map<number, number>()
  for (const entry of store.distribution) map.set(entry.offer_id, entry.percentage)
  return map
})

function offerName(id: number): string {
  return props.offersById[id]?.name ?? `Оффер #${id}`
}

function onShareInput(id: number, event: Event) {
  const target = event.target as HTMLInputElement
  const value = target.value === '' ? 0 : Number(target.value)
  store.setShare(id, value)
}

function shareText(id: number): string {
  const offer = store.workingOffers.find((item) => item.offer_id === id)
  return offer === undefined ? '' : String(offer.share)
}

function percentageText(id: number): string {
  if (store.totalShare <= 0) return '—'
  const offer = store.workingOffers.find((item) => item.offer_id === id)
  if (!offer || offer.share <= 0) return '—'
  const percentage = distributionByOffer.value.get(id)
  return percentage === undefined ? '—' : formatPercentage(percentage)
}

function confirmRemove(id: number) {
  pendingRemoveId.value = id
}

function doRemove() {
  if (pendingRemoveId.value !== null) {
    store.removeOffer(pendingRemoveId.value)
    pendingRemoveId.value = null
  }
}

function cancelRemove() {
  pendingRemoveId.value = null
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-2">
        <h3 class="text-base font-semibold text-slate-900">Офферы</h3>
        <span
          v-if="store.isDirty"
          class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700"
        >
          <span class="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
          Есть несохранённые изменения
        </span>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button class="btn btn-secondary" @click="emit('add-offer')">Добавить оффер</button>
        <button class="btn btn-secondary" :disabled="!store.isDirty" @click="emit('cancel')">Отменить изменения</button>
        <button class="btn btn-primary" :disabled="!store.canSave" @click="emit('save')">Сохранить изменения</button>
      </div>
    </div>

    <div
      v-if="store.workingOffers.length === 0"
      class="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500"
    >
      В потоке нет офферов. Добавьте хотя бы один оффер.
    </div>

    <div v-else class="overflow-x-auto rounded-lg ring-1 ring-slate-200">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-4 py-3">Оффер</th>
            <th class="px-4 py-3">ID</th>
            <th class="w-32 px-4 py-3">Share</th>
            <th class="px-4 py-3">Доля трафика</th>
            <th class="px-4 py-3 text-right">Действие</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 bg-white">
          <tr v-for="offer in store.workingOffers" :key="offer.offer_id">
            <td class="px-4 py-3">
              <div class="font-medium text-slate-900">{{ offerName(offer.offer_id) }}</div>
              <div v-if="offersById[offer.offer_id]?.group" class="text-xs text-slate-500">
                {{ offersById[offer.offer_id].group }}
              </div>
            </td>
            <td class="px-4 py-3 text-slate-500">{{ offer.offer_id }}</td>
            <td class="px-4 py-3">
              <input
                type="number"
                min="1"
                max="100"
                step="1"
                :value="shareText(offer.offer_id)"
                class="input w-24 py-1.5"
                @input="onShareInput(offer.offer_id, $event)"
              />
              <p v-if="!isValidShare(offer.share)" class="mt-1 text-xs text-red-600">
                Share — целое число от 1 до 100
              </p>
            </td>
            <td class="px-4 py-3 font-semibold text-slate-900">{{ percentageText(offer.offer_id) }}</td>
            <td class="px-4 py-3 text-right">
              <button
                class="btn btn-secondary !px-2.5 !py-1.5 text-red-600 ring-red-200 hover:bg-red-50"
                @click="confirmRemove(offer.offer_id)"
              >
                Удалить
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AppModal :open="pendingRemoveId !== null" title="Удалить оффер?" @close="cancelRemove">
      <p class="text-sm text-slate-600">
        Оффер «{{ pendingRemoveId !== null ? offerName(pendingRemoveId) : '' }}» будет удалён из потока Offer Flow.
        Это действие не удаляет оффер из Keitaro.
      </p>
      <template #footer>
        <button class="btn btn-secondary" @click="cancelRemove">Отмена</button>
        <button class="btn btn-danger" @click="doRemove">Удалить</button>
      </template>
    </AppModal>
  </div>
</template>
