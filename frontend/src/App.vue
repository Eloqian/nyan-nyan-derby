<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NDialogProvider, zhCN, enUS, jaJP, dateZhCN, dateEnUS, dateJaJP } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const naiveLocale = computed(() => {
  if (locale.value === 'zh') return zhCN
  if (locale.value === 'ja') return jaJP
  return enUS
})

const naiveDateLocale = computed(() => {
  if (locale.value === 'zh') return dateZhCN
  if (locale.value === 'ja') return dateJaJP
  return dateEnUS
})
</script>

<template>
  <n-config-provider :locale="naiveLocale" :date-locale="naiveDateLocale">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
/* Global styles if needed */
body {
  margin: 0;
  font-family: v-sans, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
</style>
