<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { api } from '../api'

const { t } = useI18n()
const router = useRouter()
const campaigns = ref([])
const loading = ref(false)
const error = ref('')

async function load(refresh = false) {
  loading.value = true
  error.value = ''
  try {
    campaigns.value = await api.campaigns(refresh)
  } catch (reason) {
    error.value = reason.message
  } finally {
    loading.value = false
  }
}

async function perform(action, campaign) {
  try {
    if (action === 'delete') await api.deleteCampaign(campaign.id)
    else await api.setCampaignState(campaign.id, action)
    await load()
  } catch (reason) {
    error.value = reason.message
  }
}

onMounted(async () => {
  await load()
  await load(true)
})
</script>

<template>
  <div class="page-heading">
    <h1>{{ t('campaigns') }}</h1>
    <v-btn color="primary" prepend-icon="mdi-plus" @click="router.push('/campaigns/new')">
      {{ t('createCampaign') }}
    </v-btn>
  </div>
  <v-alert v-if="error" type="error" class="mb-4">{{ t('error') }}: {{ error }}</v-alert>
  <v-card>
    <v-progress-linear v-if="loading" indeterminate color="primary" />
    <v-table>
      <thead>
        <tr><th>{{ t('name') }}</th><th>{{ t('status') }}</th><th>{{ t('actions') }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="campaign in campaigns" :key="campaign.id">
          <td>{{ campaign.name }}</td>
          <td>{{ campaign.state || '—' }}</td>
          <td>
            <v-btn icon="mdi-pencil" variant="text" :aria-label="t('edit')" @click="router.push(`/campaigns/${campaign.id}/edit`)" />
            <v-btn
              :icon="campaign.state === 'active' ? 'mdi-pause' : 'mdi-play'"
              variant="text"
              :disabled="loading"
              :aria-label="campaign.state === 'active' ? t('disable') : t('enable')"
              @click="perform(campaign.state === 'active' ? 'disable' : 'enable', campaign)"
            />
            <v-btn icon="mdi-delete" variant="text" color="error" :disabled="loading" :aria-label="t('delete')" @click="perform('delete', campaign)" />
          </td>
        </tr>
        <tr v-if="!campaigns.length && !loading"><td colspan="3" class="text-center py-8">{{ t('noCampaigns') }}</td></tr>
      </tbody>
    </v-table>
  </v-card>
</template>
