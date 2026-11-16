<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Domain } from '~/types'
import { ApiError } from '~/utils/apiError'
import { useToastsStore } from '~/stores/useToasts'

const api = useApi()
const toasts = useToastsStore()

const name = ref('')
const geo = ref<string[]>([])
const offerIds = ref<number[]>([])
const domainId = ref<number | null>(null)

const domains = ref<Domain[]>([])
const domainsLoading = ref(true)
const domainsError = ref<string | null>(null)

const errors = ref<{ name?: string; geo?: string; offers?: string; domain?: string }>({})
const confirmOpen = ref(false)
const submitting = ref(false)

const activeDomains = computed(() => domains.value.filter((domain) => domain.state === 'active'))
const trimmedName = computed(() => name.value.trim())
const selectedDomain = computed(() => activeDomains.value.find((domain) => domain.id === domainId.value) ?? null)
const geoCodes = computed(() => geo.value.join(', '))

function validate(): boolean {
  const next: { name?: string; geo?: string; offers?: string; domain?: string } = {}
  if (trimmedName.value.length === 0) {
    next.name = 'Введите название кампании'
  } else if (trimmedName.value.length > 255) {
    next.name = 'Название не должно превышать 255 символов'
  }
  if (geo.value.length === 0) next.geo = 'Выберите хотя бы одно GEO'
  if (offerIds.value.length === 0) next.offers = 'Выберите хотя бы один оффер'
  if (domainId.value === null) next.domain = 'Выберите домен'
  errors.value = next
  return Object.keys(next).length === 0
}

function submit() {
  if (!validate()) return
  confirmOpen.value = true
}

async function confirmSubmit() {
  confirmOpen.value = false
  submitting.value = true
  try {
    const result = await api.createCampaign({
      name: trimmedName.value,
      geo: geo.value,
      offer_ids: offerIds.value,
      domain_id: domainId.value as number,
    })
    await navigateTo(`/operations/${result.operation_id}`)
  } catch (err) {
    toasts.push('error', err instanceof ApiError ? err.message : 'Не удалось запустить создание кампании')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    domains.value = await api.listDomains()
    if (activeDomains.value.length === 1) {
      domainId.value = activeDomains.value[0].id
    }
  } catch (err) {
    domainsError.value = err instanceof ApiError ? err.message : 'Не удалось загрузить домены'
  } finally {
    domainsLoading.value = false
  }
})
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">Создание кампании</h1>
      <p class="mt-1 text-sm text-slate-500">
        Кампания будет создана с потоками «Google Redirect» и «Offer Flow»
      </p>
    </div>

    <div class="card space-y-5 p-6">
      <div>
        <label class="field-label" for="campaign-name">Название кампании <span class="text-red-500">*</span></label>
        <input
          id="campaign-name"
          v-model="name"
          type="text"
          maxlength="255"
          placeholder="Например: AdRobot Flexacil PE"
          class="input mt-1.5"
        />
        <p v-if="errors.name" class="mt-1 text-sm text-red-600">{{ errors.name }}</p>
      </div>

      <div>
        <label class="field-label">GEO <span class="text-red-500">*</span></label>
        <div class="mt-1.5">
          <GeoMultiSelect v-model="geo" />
        </div>
        <p v-if="errors.geo" class="mt-1 text-sm text-red-600">{{ errors.geo }}</p>
      </div>

      <div>
        <label class="field-label">Офферы <span class="text-red-500">*</span></label>
        <div class="mt-1.5">
          <OfferMultiSelect v-model="offerIds" />
        </div>
        <p v-if="errors.offers" class="mt-1 text-sm text-red-600">{{ errors.offers }}</p>
      </div>

      <div>
        <label class="field-label" for="campaign-domain">Домен <span class="text-red-500">*</span></label>
        <div class="mt-1.5">
          <AppSpinner v-if="domainsLoading" size="sm" label="Загрузка доменов…" />
          <AppAlert v-else-if="domainsError" type="error">{{ domainsError }}</AppAlert>
          <select v-else id="campaign-domain" v-model="domainId" class="input">
            <option :value="null" disabled>Выберите домен…</option>
            <option v-for="domain in activeDomains" :key="domain.id" :value="domain.id">
              {{ domain.name }} (ID {{ domain.id }}){{ domain.is_ssl ? ' · SSL' : '' }}
            </option>
          </select>
        </div>
        <p v-if="errors.domain" class="mt-1 text-sm text-red-600">{{ errors.domain }}</p>
      </div>

      <div class="flex justify-end">
        <button class="btn btn-primary" @click="submit">Создать кампанию</button>
      </div>
    </div>

    <AppModal :open="confirmOpen" title="Подтверждение создания кампании" @close="confirmOpen = false">
      <div class="space-y-2 text-sm text-slate-700">
        <div class="flex justify-between"><span class="text-slate-500">Название:</span><span class="font-medium">{{ trimmedName }}</span></div>
        <div class="flex justify-between"><span class="text-slate-500">GEO:</span><span class="font-medium">{{ geoCodes }}</span></div>
        <div class="flex justify-between"><span class="text-slate-500">Домен:</span><span class="font-medium">{{ selectedDomain?.name ?? '—' }}</span></div>
        <div class="flex justify-between"><span class="text-slate-500">Офферы:</span><span class="font-medium">{{ offerIds.length }}</span></div>
        <div class="my-2 border-t border-slate-100"></div>
        <div class="flex justify-between"><span class="text-slate-500">Google Redirect:</span><span class="font-medium text-emerald-600">enabled</span></div>
        <div class="flex justify-between"><span class="text-slate-500">Offer Flow:</span><span class="font-medium text-emerald-600">enabled</span></div>
        <div class="flex justify-between"><span class="text-slate-500">Начальный share:</span><span class="font-medium">100 на каждый оффер</span></div>
        <div class="flex justify-between"><span class="text-slate-500">Распределение:</span><span class="font-medium">равномерное</span></div>
      </div>
      <template #footer>
        <button class="btn btn-secondary" :disabled="submitting" @click="confirmOpen = false">Назад</button>
        <button class="btn btn-primary" :disabled="submitting" @click="confirmSubmit">
          <AppSpinner v-if="submitting" size="sm" label="Создание…" />
          <span v-else>Подтвердить</span>
        </button>
      </template>
    </AppModal>
  </div>
</template>
