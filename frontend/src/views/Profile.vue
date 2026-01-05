<template>
  <div class="profile-screen">
    
    <!-- Header / Banner -->
    <div class="profile-header">
       <div class="header-bg"></div>
       <div class="header-content">
          <div class="user-identity">
             <n-avatar
                round
                :size="100"
                :src="auth.user?.avatar_url"
                fallback-src="https://07akioni.oss-cn-beijing.aliyuncs.com/07akioni.jpeg"
                class="user-avatar"
             />
             <div class="user-text">
                <h1 class="username">{{ auth.user?.username }}</h1>
                <div class="user-role-badge">
                   {{ auth.user?.is_admin ? t('profile.role_admin') : t('profile.role_trainer') }}
                </div>
             </div>
          </div>
       </div>
    </div>

    <div class="profile-layout">
       
       <!-- Left Sidebar: Stats & Actions -->
       <div class="profile-sidebar">
          
          <!-- Stats Card -->
          <div class="sidebar-card">
             <h3 class="sidebar-title">TRAINER INFO</h3>
             <div class="info-list">
                <div class="info-item">
                   <span class="label">{{ t('profile.bound_player') }}</span>
                   <span class="value highlight">{{ boundPlayerName || t('profile.none') }}</span>
                </div>
                <!-- Future stats could go here -->
             </div>
          </div>

          <!-- Bind Account (If needed) -->
          <div class="sidebar-card highlight-border" v-if="!boundPlayerName && !loadingPlayer">
             <h3 class="sidebar-title">{{ t('profile.bind_account') }}</h3>
             <p class="helper-text">{{ t('profile.qq_verify_prompt') }}</p>
             <n-input-group>
                <n-input v-model:value="qqId" :placeholder="t('profile.enter_qq_id')" />
                <n-button type="primary" color="#FFC800" text-color="#333" @click="handleClaim" :loading="claiming" style="font-weight: bold;">
                  {{ t('profile.bind_btn') }}
                </n-button>
             </n-input-group>
          </div>

          <!-- Security -->
          <div class="sidebar-card">
             <h3 class="sidebar-title">{{ t('profile.security') || 'SECURITY' }}</h3>
             <n-button block secondary @click="showPasswordModal = true">
                {{ t('profile.change_password') || 'Change Password' }}
             </n-button>
          </div>

          <!-- Actions -->
          <div class="sidebar-actions">
             <n-button type="error" secondary block strong @click="logout" size="large">
                {{ t('nav.logout') }}
             </n-button>
          </div>
       </div>

       <!-- Right Content: Matches -->
       <div class="profile-main">
          <div class="section-header-modern">
             <div class="title-group">
                <span class="section-icon">⚔️</span>
                <h2 class="section-title">{{ t('profile.my_matches') }}</h2>
             </div>
             <n-button size="medium" secondary circle @click="fetchMatches">
                <template #icon><n-icon><Refresh /></n-icon></template>
             </n-button>
          </div>

          <div v-if="matchesLoading && matches.length === 0" class="loading-state">
             <n-spin size="large" stroke="#67C05D" />
          </div>
          
          <div v-else-if="matches.length === 0" class="empty-state-modern">
             <div class="empty-content">
                <n-empty :description="t('profile.no_matches')" size="large" />
                <p class="empty-hint">Join a tournament to see your upcoming races here!</p>
             </div>
          </div>

          <div v-else class="matches-grid-modern">
             <PlayerMatchCard 
               v-for="match in matches" 
               :key="match.id" 
               :match="match" 
               @room-updated="fetchMatches"
               class="match-item"
             />
          </div>
       </div>

    </div>

    <!-- Password Change Modal -->
    <n-modal v-model:show="showPasswordModal" preset="card" :title="t('profile.change_password') || 'Change Password'" style="width: 400px">
      <n-form>
        <n-form-item :label="t('profile.old_password') || 'Old Password'">
          <n-input v-model:value="passwordForm.old_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item :label="t('profile.new_password') || 'New Password'">
          <n-input v-model:value="passwordForm.new_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item :label="t('profile.confirm_password') || 'Confirm New Password'">
          <n-input v-model:value="passwordForm.confirm_password" type="password" show-password-on="click" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 12px;">
           <n-button @click="showPasswordModal = false">{{ t('profile.cancel') || 'Cancel' }}</n-button>
           <n-button type="primary" @click="handleChangePassword" :loading="changingPassword" :disabled="!passwordForm.old_password || !passwordForm.new_password">
              {{ t('profile.confirm_change') || 'Update' }}
           </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { useMessage, NInput, NInputGroup, NButton, NSpin, NEmpty, NIcon, NAvatar, NModal, NForm, NFormItem } from 'naive-ui'
import { Refresh } from '@vicons/ionicons5'
import { getMyMatches, type MatchResponse } from '../api/matches'
import PlayerMatchCard from '../components/PlayerMatchCard.vue'


const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const message = useMessage()

const qqId = ref('')
const claiming = ref(false)
const boundPlayerName = ref('')
const loadingPlayer = ref(true)

// Password Change
const showPasswordModal = ref(false)
const changingPassword = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const handleChangePassword = async () => {
  if (!passwordForm.old_password || !passwordForm.new_password) return
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    message.error(t('profile.passwords_no_match') || 'New passwords do not match')
    return
  }
  
  changingPassword.value = true
  try {
    const res = await fetch('/api/v1/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      })
    })
    
    if (res.ok) {
      message.success(t('profile.password_updated') || 'Password updated successfully')
      showPasswordModal.value = false
      passwordForm.old_password = ''
      passwordForm.new_password = ''
      passwordForm.confirm_password = ''
    } else {
      const err = await res.json()
      message.error(err.detail || 'Failed to update password')
    }
  } catch (e) {
    message.error('An error occurred')
  } finally {
    changingPassword.value = false
  }
}

// Matches Data
const matches = ref<MatchResponse[]>([])
const matchesLoading = ref(false)

const fetchProfileData = async () => {
  if (!auth.token) return
  loadingPlayer.value = true
  matchesLoading.value = true
  
  // 1. Fetch Bound Player Info
  try {
     const res = await fetch('/api/v1/players/me', {
        headers: { 'Authorization': `Bearer ${auth.token}` }
     })
     if (res.ok) {
        const player = await res.json()
        boundPlayerName.value = player.in_game_name
     } else {
        boundPlayerName.value = ''
     }
  } catch (e) {
     console.error(e)
  }

  // 2. Fetch Matches
  try {
    const data = await getMyMatches(auth.token)
    matches.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loadingPlayer.value = false
    matchesLoading.value = false
  }
}

onMounted(async () => {
  if (!auth.isAuthenticated) {
     router.push('/login')
     return
  }
  
  await fetchProfileData()
})

const fetchMatches = async () => {
   // Legacy wrapper if called by events
   await fetchProfileData()
}

const handleClaim = async () => {
  if (!qqId.value) return
  claiming.value = true
  try {
    const res = await fetch('/api/v1/players/claim', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({ qq_id: qqId.value })
    })
    
    if (res.ok) {
      const data = await res.json()
      message.success(t('profile.bind_success'))
      boundPlayerName.value = data.in_game_name
      await fetchMatches()
    } else {
      const err = await res.json()
      message.error(err.detail || t('profile.bind_fail'))
    }
  } catch (e) {
    message.error(t('profile.bind_fail'))
  } finally {
    claiming.value = false
  }
}

const logout = () => {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.profile-screen {
  width: 100%;
  min-height: 100vh;
  padding-bottom: 60px;
}

/* Header */
.profile-header {
  position: relative;
  height: 200px;
  background: white;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  overflow: hidden;
}
.header-bg {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(120deg, #e0f7fa 0%, #ffffff 100%);
  opacity: 0.6;
}
.header-bg::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: radial-gradient(#4FB3FF 1px, transparent 1px);
  background-size: 20px 20px;
  opacity: 0.2;
}

.header-content {
  position: relative;
  max-width: 1800px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 5%;
}

.user-identity {
  display: flex;
  align-items: center;
  gap: 20px; /* Space between avatar and text */
}

.user-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.username {
  font-size: 2.2rem;
  font-weight: 900; /* Make username bolder */
  color: #333;
  margin: 0;
}

.user-role-badge {
  background: var(--uma-green);
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: bold;
  display: inline-block; /* Ensure it takes only necessary width */
  margin-top: 5px; /* Add some space above the badge */
}



/* Layout */
.profile-layout {
  max-width: 1800px;
  margin: 0 auto;
  margin-top: 40px;
  padding: 0 5%;
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 40px;
  position: relative;
  z-index: 2;
}
@media (max-width: 1024px) {
  .profile-layout { grid-template-columns: 1fr; padding: 0 5%; }
  .profile-header { padding: 0; height: auto; padding-bottom: 60px; }
  .header-content { flex-direction: column; align-items: center; text-align: center; padding-top: 40px; }
  .user-identity { flex-direction: column; gap: 16px; }
  .profile-sidebar { margin-top: 0; }
  .username {
    font-size: 1.8rem; /* Adjusted for smaller screens */
  }
}

/* Sidebar */
.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border: 1px solid #f0f0f0;
}
.sidebar-card.highlight-border {
  border: 2px solid var(--uma-gold);
}
.sidebar-title {
  margin: 0 0 16px 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: #888;
  letter-spacing: 1px;
}
.helper-text {
  font-size: 0.9rem; color: #666; margin-bottom: 12px;
}

.info-list {
  display: flex; flex-direction: column; gap: 12px;
}
.info-item {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px dashed #eee;
}
.info-item:last-child { border-bottom: none; padding-bottom: 0; }
.label { font-weight: bold; color: #555; }
.value { font-weight: 900; font-size: 1.1rem; }
.value.highlight { color: var(--uma-green); }

/* Main Content */
.profile-main {
  /* No top margin needed */
}
.section-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.title-group { display: flex; align-items: center; gap: 12px; }
.section-icon { font-size: 2rem; }
.section-title {
  font-size: 2rem;
  font-weight: 900;
  color: #3E3838;
  margin: 0;
  font-style: italic;
  text-shadow: 2px 2px 0 white;
}

.matches-grid-modern {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}
.match-item {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: transform 0.2s;
}
.match-item:hover { transform: translateY(-4px); }

.empty-state-modern {
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(10px);
  padding: 60px;
  border-radius: 20px;
  text-align: center;
  border: 2px dashed #ddd;
}
.empty-hint { color: #888; font-weight: bold; margin-top: 16px; }
</style>
