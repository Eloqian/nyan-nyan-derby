<script setup lang="ts">
import { 
  NConfigProvider, NMessageProvider, NDialogProvider, NGlobalStyle,
  zhCN, enUS, jaJP, dateZhCN, dateEnUS, dateJaJP,
  NLayout, NLayoutHeader, NLayoutContent, NButton, NIcon, NDropdown, NAvatar
} from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import type { GlobalThemeOverrides } from 'naive-ui'
import { Language, Person } from '@vicons/ionicons5'
import { useAuthStore } from './stores/auth'

const { locale, t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

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

// Uma Musume Inspired Theme
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#7CB342', // Grass Green
    primaryColorHover: '#8BC34A',
    primaryColorPressed: '#689F38',
    primaryColorSuppl: '#AED581',
    infoColor: '#29B6F6', // Sky Blue
    successColor: '#66BB6A',
    warningColor: '#FFA726',
    errorColor: '#EF5350',
    bodyColor: '#F5F5F5',
    fontFamily: '"M PLUS 1p", "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans SC", sans-serif'
  },
  Button: {
    borderRadiusMedium: '20px', // Rounded buttons
    fontWeight: 'bold'
  },
  Card: {
    borderRadius: '16px'
  }
}

// Language Switcher
const languageOptions = [
  { label: 'English', key: 'en' },
  { label: '中文', key: 'zh' },
  { label: '日本語', key: 'ja' }
]

function handleLanguageSelect(key: string) {
  locale.value = key
  localStorage.setItem('locale', key)
}

// Profile Menu
const profileOptions = [
  { label: () => t('nav.profile'), key: 'profile' },
  { label: () => t('nav.logout'), key: 'logout' }
]

function handleProfileSelect(key: string) {
  if (key === 'profile') router.push('/profile')
  if (key === 'logout') {
    auth.logout()
    router.push('/login')
  }
}

</script>

<template>
  <n-config-provider :locale="naiveLocale" :date-locale="naiveDateLocale" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
        <n-layout style="min-height: 100vh;">
          <n-layout-header bordered style="padding: 0 24px; height: 64px; display: flex; align-items: center; justify-content: space-between; background-color: #ffffff;">
            <div class="logo" @click="router.push('/')" style="cursor: pointer; display: flex; align-items: center; gap: 10px;">
              <span style="font-size: 24px; color: #7CB342;">🐎</span>
              <span style="font-weight: 900; font-size: 18px; color: #333; letter-spacing: 1px;">{{ t('nav.title') }}</span>
            </div>
            
            <div style="display: flex; gap: 12px; align-items: center;">
               <n-button quaternary @click="router.push('/')">
                 {{ t('nav.home') }}
               </n-button>
               <n-button type="error" ghost @click="router.push('/live')">
                 {{ t('nav.live') }}
               </n-button>
               
               <!-- Admin-only buttons -->
               <template v-if="auth.user?.is_admin">

                 <n-button quaternary @click="router.push('/admin')">
                   {{ t('nav.admin') }}
                 </n-button>
               </template>

               <n-divider vertical />

               <!-- Auth Section -->
               <template v-if="auth.isAuthenticated">
                  <n-dropdown trigger="hover" :options="profileOptions" @select="handleProfileSelect">
                    <n-button text style="display: flex; align-items: center; gap: 8px;">
                      <n-avatar round size="small" :style="{ backgroundColor: '#7CB342' }">
                        <n-icon><Person /></n-icon>
                      </n-avatar>
                      {{ auth.user?.username }}
                    </n-button>
                  </n-dropdown>
               </template>
               <template v-else>
                  <n-button type="primary" secondary @click="router.push('/login')">
                    {{ t('nav.login') }}
                  </n-button>
               </template>
               
               <n-dropdown trigger="hover" :options="languageOptions" @select="handleLanguageSelect">
                <n-button circle secondary>
                  <template #icon>
                    <n-icon><Language /></n-icon>
                  </template>
                </n-button>
              </n-dropdown>
            </div>
          </n-layout-header>
          
          <n-layout-content style="background-color: #f0f2f5; min-height: calc(100vh - 64px);">
            <div style="max-width: 1200px; margin: 0 auto; padding: 24px;">
              <router-view v-slot="{ Component }">
                <transition name="fade" mode="out-in">
                  <component :is="Component" />
                </transition>
              </router-view>
            </div>
          </n-layout-content>
        </n-layout>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
/* Global styles */
body {
  margin: 0;
  font-family: v-sans, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
