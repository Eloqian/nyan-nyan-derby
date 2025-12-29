import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'
import ja from './locales/ja.json'

const savedLocale = localStorage.getItem('locale')
const defaultLocale = savedLocale || 'zh'

const i18n = createI18n({
  legacy: false, // You must set `legacy: false` for Vue 3 Composition API
  locale: defaultLocale, // set locale
  fallbackLocale: 'en', // set fallback locale
  messages: {
    en,
    zh,
    ja
  }
})

export default i18n
