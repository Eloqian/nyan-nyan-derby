<template>
  <div style="padding: 24px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h1>{{ t('general.welcome') }}</h1>
      <n-select v-model:value="locale" :options="localeOptions" style="width: 120px;" />
    </div>
    <p>{{ t('general.subtitle') }}</p>
    <div style="margin-top: 20px;">
       <GroupDrawCeremony />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { NSelect } from 'naive-ui'
import { watch } from 'vue'
import GroupDrawCeremony from '../components/GroupDrawCeremony.vue'

const { t, locale } = useI18n()

const localeOptions = [
  { label: 'English', value: 'en' },
  { label: '中文', value: 'zh' },
  { label: '日本語', value: 'ja' }
]

watch(locale, (newLocale) => {
  localStorage.setItem('locale', newLocale as string)
})
</script>
