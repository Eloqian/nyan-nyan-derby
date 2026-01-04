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
import { Language } from '@vicons/ionicons5'
import { useAuthStore } from './stores/auth'
import homeBg from './assets/images/backgrounds/home_bg.jpg'

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
    primaryColor: '#67C05D', // Uma Green
    primaryColorHover: '#8BC34A',
    primaryColorPressed: '#558B2F',
    primaryColorSuppl: '#AED581',
    infoColor: '#4FB3FF', // Uma Blue
    successColor: '#67C05D',
    warningColor: '#FFC800', // Uma Gold
    errorColor: '#FF5252',
    bodyColor: 'transparent', // Let custom background show through
    cardColor: 'rgba(255, 255, 255, 0.95)',
    fontFamily: '"Noto Sans SC", "Microsoft YaHei", "Hiragino Sans GB", "PingFang SC", sans-serif'
  },
  Button: {
    borderRadiusMedium: '20px',
    fontWeight: '800',
    textTransform: 'uppercase'
  },
  Card: {
    borderRadius: '12px'
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
        <div class="app-background">
          <!-- Global Background Image -->
          <div class="global-bg" :style="{ backgroundImage: `url(${homeBg})` }"></div>
          
          <!-- Main Layout -->
          <n-layout style="min-height: 100vh; background: transparent;">
            
            <!-- Game Header -->
            <n-layout-header class="app-header">
              
              <!-- Logo Area -->
              <div class="logo" @click="router.push('/')">
                <div class="logo-icon">
                  🐎
                </div>
                <span class="logo-text">{{ t('nav.title') }}</span>
              </div>
              
              <!-- Navigation -->
              <div class="nav-actions">
                 <n-button quaternary @click="router.push('/')" class="nav-btn">
                   {{ t('nav.home') }}
                 </n-button>
                 <n-button quaternary @click="router.push('/live')" class="nav-btn">
                   {{ t('nav.live') }}
                 </n-button>
                 
                 <template v-if="auth.user?.is_admin">
                   <n-button quaternary @click="router.push('/admin')" class="nav-btn">
                     {{ t('nav.admin') }}
                   </n-button>
                 </template>
  
                 <div class="nav-separator"></div>
  
                 <!-- Auth -->
                 <template v-if="auth.isAuthenticated">
                    <n-dropdown trigger="hover" :options="profileOptions" @select="handleProfileSelect">
                      <n-button text class="user-btn">
                        <n-avatar round size="small" :style="{backgroundColor: '#67C05D', color: 'white'}">
                          {{ auth.user?.username.charAt(0).toUpperCase() }}
                        </n-avatar>
                        <span class="username">{{ auth.user?.username }}</span>
                      </n-button>
                    </n-dropdown>
                 </template>
                 <template v-else>
                    <n-button type="primary" size="small" round @click="router.push('/login')" class="login-btn">
                      {{ t('nav.login') }}
                    </n-button>
                 </template>
                 
                 <n-dropdown trigger="hover" :options="languageOptions" @select="handleLanguageSelect">
                  <n-button circle size="small" quaternary class="lang-btn">
                    <template #icon>
                      <n-icon><Language /></n-icon>
                    </template>
                  </n-button>
                </n-dropdown>
              </div>
            </n-layout-header>
            
            <n-layout-content style="background-color: transparent; min-height: calc(100vh - 64px);">
              <router-view v-slot="{ Component }">
                <transition name="fade" mode="out-in">
                  <component :is="Component" />
                </transition>
              </router-view>
            </n-layout-content>
          </n-layout>
        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style scoped>
.global-bg {
  position: fixed;
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%;
  background-size: cover;
  background-position: center;
  z-index: -1;
}

.global-bg::after {
  content: '';
  position: absolute;
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%;
  /* Light overlay to ensure text readability */
  background: rgba(242, 245, 249, 0.4); 
  backdrop-filter: blur(2px);
}

.app-header {
  height: 64px; 
  padding: 0 24px; 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  background: rgba(255,255,255,0.9); 
  backdrop-filter: blur(10px); 
  box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
  z-index: 100;
}

.logo {
  cursor: pointer; 
  display: flex; 
  align-items: center; 
  gap: 12px;
}
.logo-icon {
  background: var(--uma-green, #67C05D); 
  color: white; 
  width: 36px; 
  height: 36px; 
  border-radius: 8px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-size: 20px;
}
.logo-text {
  font-weight: 800; 
  font-size: 18px; 
  color: #3E3838; 
  letter-spacing: 0.5px;
}

.nav-actions {
  display: flex; 
  gap: 12px; 
  align-items: center;
}
.nav-btn {
  font-weight: bold !important;
  color: #555;
}
.nav-separator {
  width: 1px; 
  height: 20px; 
  background: #e0e0e0; 
  margin: 0 4px;
}
.user-btn {
  display: flex; 
  align-items: center; 
  gap: 8px; 
  font-weight: bold;
}
.username {
  color: #333;
}
.login-btn {
  font-weight: bold;
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