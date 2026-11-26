import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import './style.css'
import App from './App.vue'
import router from './router'
import { messages } from './locales'
import { themes } from './theme'

const locale = localStorage.getItem('locale') || 'en'
const theme = localStorage.getItem('theme') || 'light'
const i18n = createI18n({ legacy: false, locale, fallbackLocale: 'en', messages })
const vuetify = createVuetify({
  theme: { defaultTheme: theme, themes },
  icons: { defaultSet: 'mdi' },
})

createApp(App).use(router).use(i18n).use(vuetify).mount('#app')
