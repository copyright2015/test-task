<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { api } from '../api'

const { t } = useI18n()
const router = useRouter()
const form = ref()
const name = ref('')
const geo = ref(null)
const offer = ref(null)
const catalog = ref({ geos: [], offers: [] })
const loading = ref(false)
const error = ref('')
const required = (value) => !!value || t('required')

onMounted(async () => {
  try {
    catalog.value = await api.catalog()
  } catch (reason) {
    error.value = reason.message
  }
})

async function submit() {
  const result = await form.value.validate()
  if (!result.valid) return
  loading.value = true
  error.value = ''
  try {
    await api.createCampaign({ name: name.value, geo_code: geo.value, offer_id: String(offer.value) })
    router.push('/')
  } catch (reason) {
    error.value = reason.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-heading"><h1>{{ t('createCampaign') }}</h1></div>
  <v-alert v-if="error" type="error" class="mb-4">{{ t('error') }}: {{ error }}</v-alert>
  <v-card class="form-card pa-6">
    <v-form ref="form" @submit.prevent="submit">
      <v-text-field v-model="name" :label="t('name')" :rules="[required]" required />
      <v-select v-model="geo" :items="catalog.geos" item-title="name" item-value="code" :label="t('geo')" :rules="[required]" required />
      <v-autocomplete v-model="offer" :items="catalog.offers" item-title="name" item-value="id" :label="t('offer')" :rules="[required]" required />
      <div class="d-flex justify-end ga-2 mt-4">
        <v-btn variant="text" @click="router.push('/')">{{ t('cancel') }}</v-btn>
        <v-btn color="primary" type="submit" :loading="loading">{{ t('create') }}</v-btn>
      </div>
    </v-form>
  </v-card>
</template>
