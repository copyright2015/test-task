<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from 'vuetify'

const drawer = ref(true)
const { t, locale } = useI18n()
const theme = useTheme()
const currentTheme = computed(() => theme.global.name.value)

watch(locale, (value) => localStorage.setItem('locale', value))

function toggleTheme() {
  const next = currentTheme.value === 'light' ? 'dark' : 'light'
  theme.global.name.value = next
  localStorage.setItem('theme', next)
}
</script>

<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" color="surface">
      <v-list nav>
        <v-list-item prepend-icon="mdi-view-dashboard" :title="t('campaigns')" to="/" />
      </v-list>
    </v-navigation-drawer>
    <v-app-bar color="surface" elevation="1">
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-app-bar-title>{{ t('app') }}</v-app-bar-title>
      <v-btn variant="text" @click="toggleTheme">{{ t('theme') }}: {{ t(currentTheme) }}</v-btn>
      <v-btn variant="text" @click="locale = locale === 'en' ? 'ru' : 'en'">
        {{ t('language') }}: {{ locale.toUpperCase() }}
      </v-btn>
    </v-app-bar>
    <v-main>
      <v-container fluid class="pa-6">
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>
