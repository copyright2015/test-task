<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const streams = ref([])
const offers = ref([])
const loading = ref(false)
const error = ref('')
const campaignName = ref('')
const selectedOffer = ref({})
const initialStreams = ref(null)
const removedStreamIds = ref([])
const leaveDialog = ref(false)
let pendingNavigation = null
let resolveNavigation = null
let loadVersion = 0

const hasChanges = computed(() =>
  initialStreams.value !== null &&
  (removedStreamIds.value.length > 0 || JSON.stringify(streams.value) !== initialStreams.value),
)

const activeOfferCount = computed(() =>
  streams.value.reduce((sum, stream) =>
    sum + (isRemoved(stream) ? 0 : (stream.offers || []).filter((offer) => !offer.deleted).length), 0),
)

const originalStreams = computed(() =>
  initialStreams.value === null ? [] : JSON.parse(initialStreams.value),
)

function isRemoved(stream) {
  return stream.id != null && removedStreamIds.value.includes(String(stream.id))
}

function isStreamChanged(stream) {
  if (isRemoved(stream) || stream.id == null) return true
  const original = originalStreams.value.find((item) => String(item.id) === String(stream.id))
  return !original || JSON.stringify(stream) !== JSON.stringify(original)
}

function showOffers(stream) {
  return !isRemoved(stream) && (stream.id == null || stream.offers.length > 0)
}

function removeStream(stream, index) {
  if (stream.id == null) {
    streams.value.splice(index, 1)
  } else {
    removedStreamIds.value.push(String(stream.id))
  }
}

function restoreStream(stream) {
  removedStreamIds.value = removedStreamIds.value.filter((id) => id !== String(stream.id))
}

function beforeUnload(event) {
  if (hasChanges.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}

function finishNavigation(allow) {
  leaveDialog.value = false
  const resolve = resolveNavigation
  pendingNavigation = null
  resolveNavigation = null
  if (resolve) resolve(allow)
}

function confirmNavigation() {
  if (!hasChanges.value) return true
  if (loading.value) return false
  if (!pendingNavigation) {
    leaveDialog.value = true
    pendingNavigation = new Promise((resolve) => { resolveNavigation = resolve })
  }
  return pendingNavigation
}

onBeforeRouteLeave(confirmNavigation)
onBeforeRouteUpdate((to, from) => to.params.id === from.params.id || confirmNavigation())

onMounted(() => {
  window.addEventListener('beforeunload', beforeUnload)
})

watch(() => route.params.id, async (id) => {
  const version = ++loadVersion
  initialStreams.value = null
  streams.value = []
  removedStreamIds.value = []
  selectedOffer.value = {}
  campaignName.value = ''
  error.value = ''
  loading.value = true
  try {
    const [editor, catalog] = await Promise.all([api.campaignEditor(id), api.catalog()])
    if (version !== loadVersion) return
    campaignName.value = editor.campaign.name
    streams.value = editor.streams.map((stream) => ({
      ...stream,
      offers: (stream.offers || []).map((offer) => ({
        ...offer,
        deleted: !!offer.deleted,
        fixed: !!offer.fixed,
      })),
    }))
    initialStreams.value = JSON.stringify(streams.value)
    offers.value = catalog.offers
  } catch (reason) {
    if (version === loadVersion) error.value = reason.message
  } finally {
    if (version === loadVersion) loading.value = false
  }
}, { immediate: true })

onBeforeUnmount(() => {
  loadVersion++
  window.removeEventListener('beforeunload', beforeUnload)
  finishNavigation(false)
})

function addStream() {
  streams.value.push({
    name: `${t('stream')} ${streams.value.length + 1}`,
    position: streams.value.length + 1,
    type: 'regular',
    schema: 'landings',
    filters: [],
    offers: [],
    action_type: 'http',
  })
}

function addOffer(stream, index) {
  const offerId = selectedOffer.value[index]
  if (!offerId) return
  const existing = (stream.offers || []).find((item) => String(item.offer_id ?? item.id) === String(offerId))
  if (existing) {
    existing.deleted = false
  } else {
    stream.offers = [...(stream.offers || []), { offer_id: offerId, share: 0, deleted: false, fixed: false }]
  }
  stream.schema = 'landings'
  stream.action_options = {}
  selectedOffer.value[index] = null
  distribute(stream)
}

function distribute(stream) {
  const active = (stream.offers || []).filter((offer) => !offer.deleted && !offer.fixed)
  const fixedTotal = (stream.offers || []).filter((offer) => !offer.deleted && offer.fixed)
    .reduce((sum, offer) => sum + Number(offer.share || 0), 0)
  const remaining = Math.max(0, 100 - fixedTotal)
  const baseShare = active.length ? Math.floor(remaining / active.length) : 0
  const remainder = active.length ? remaining - baseShare * active.length : 0
  active.forEach((offer, index) => { offer.share = baseShare + (index < remainder ? 1 : 0) })
  ;(stream.offers || []).filter((offer) => offer.deleted).forEach((offer) => { offer.share = 0 })
}

function updateFixed(stream, offer) {
  offer.fixed = !offer.fixed
  distribute(stream)
}

async function saveChanges() {
  if (!hasChanges.value || loading.value) return false
  loading.value = true
  error.value = ''
  try {
    await api.updateCampaignEditor(route.params.id, streams.value.filter((stream) => !isRemoved(stream)))
    initialStreams.value = JSON.stringify(streams.value)
    removedStreamIds.value = []
    return true
  } catch (reason) {
    error.value = reason.message
    return false
  } finally {
    loading.value = false
  }
}

async function save() {
  if (await saveChanges()) await router.push('/')
}

async function saveAndLeave() {
  if (await saveChanges()) finishNavigation(true)
}
</script>

<template>
  <div class="page-heading">
    <div><h1>{{ t('editCampaign') }}</h1><div class="text-medium-emphasis">{{ campaignName }}</div></div>
    <v-btn color="primary" :loading="loading" :disabled="!hasChanges || loading" @click="save">{{ t('save') }}</v-btn>
  </div>
  <v-alert v-if="error" type="error" class="mb-4">{{ t('error') }}: {{ error }}</v-alert>
  <div v-if="loading && !streams.length" class="text-center pa-8">{{ t('loading') }}</div>
  <v-card
    v-for="(stream, index) in streams" :key="stream.id == null ? `new-${index}` : `stream-${stream.id}`"
    class="mb-4 pa-4" :class="{ 'changed-stream': isStreamChanged(stream) }">
    <div class="d-flex align-center ga-3" :class="{ 'mb-4': showOffers(stream) }">
      <v-text-field v-if="showOffers(stream)" v-model="stream.name" :label="t('stream')" :disabled="loading" hide-details />
      <v-card-title v-else class="flex-grow-1 pa-0">{{ stream.name }}</v-card-title>
      <v-chip v-if="isStreamChanged(stream)" color="primary" size="small">
        {{ isRemoved(stream) ? t('streamRemoved') : t('changed') }}
      </v-chip>
      <v-btn v-if="isRemoved(stream)" icon="mdi-restore" color="primary" variant="text" :disabled="loading" :aria-label="t('restoreStream')" @click="restoreStream(stream)" />
      <v-btn v-else icon="mdi-delete" color="error" variant="text" :disabled="loading" :aria-label="t('removeStream')" @click="removeStream(stream, index)" />
    </div>
    <v-table v-if="showOffers(stream)">
      <thead><tr><th>{{ t('offer') }}</th><th>{{ t('share') }}</th><th>{{ t('fixed') }}</th><th>{{ t('actions') }}</th></tr></thead>
      <tbody>
        <tr v-for="offer in (stream.offers || [])" :key="offer.offer_id || offer.id" :class="{ 'deleted-offer': offer.deleted }">
          <td>{{ offers.find((item) => String(item.id) === String(offer.offer_id ?? offer.id))?.name || offer.name || offer.offer_id || offer.id }}</td>
          <td>
            <v-text-field
              v-model.number="offer.share" type="number" min="0" max="100" step="1"
              :disabled="loading || offer.deleted || !offer.fixed" density="compact" hide-details
              @update:model-value="distribute(stream)" />
          </td>
          <td><v-checkbox-btn :model-value="!!offer.fixed" :disabled="loading || offer.deleted" @update:model-value="updateFixed(stream, offer)" /></td>
          <td>
            <v-btn v-if="offer.deleted" color="primary" variant="text" :disabled="loading" @click="offer.deleted = false; distribute(stream)">{{ t('restore') }}</v-btn>
            <v-btn v-else color="error" variant="text" :disabled="loading" @click="offer.deleted = true; distribute(stream)">{{ t('remove') }}</v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
    <div v-if="showOffers(stream)" class="d-flex ga-2 mt-3">
      <v-autocomplete
        v-model="selectedOffer[index]" :items="offers" item-title="name" item-value="id"
        :label="t('offer')" :disabled="loading" hide-details density="compact" />
      <v-btn color="primary" variant="tonal" :disabled="loading" @click="addOffer(stream, index)">{{ t('addOffer') }}</v-btn>
    </div>
  </v-card>
  <div class="d-flex align-center ga-3">
    <v-btn variant="outlined" prepend-icon="mdi-plus" :disabled="loading" @click="addStream">{{ t('addStream') }}</v-btn>
    <span class="text-medium-emphasis">{{ activeOfferCount }} {{ t('offers').toLowerCase() }}</span>
    <v-spacer />
    <v-btn variant="text" :disabled="loading" @click="router.push('/')">{{ t('cancel') }}</v-btn>
  </div>
  <v-dialog :model-value="leaveDialog" max-width="500" persistent>
    <v-card :title="t('unsavedChanges')">
      <v-card-text>
        {{ t('leaveWithChanges') }}
        <v-alert v-if="error" type="error" class="mt-4">{{ t('error') }}: {{ error }}</v-alert>
      </v-card-text>
      <v-card-actions class="flex-wrap justify-end">
        <v-btn variant="text" :disabled="loading" @click="finishNavigation(false)">{{ t('keepEditing') }}</v-btn>
        <v-btn variant="text" color="error" :disabled="loading" @click="finishNavigation(true)">{{ t('discardChanges') }}</v-btn>
        <v-btn color="primary" variant="flat" :loading="loading" :disabled="loading" @click="saveAndLeave">{{ t('saveAndLeave') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.changed-stream {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -2px;
}

.deleted-offer > td {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.deleted-offer > td:first-child {
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
}
</style>
