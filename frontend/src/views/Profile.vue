<template>
  <div class="profile-container">
    <n-card :title="`${t('profile.title')}: ${auth.user?.username}`" style="margin-bottom: 24px;">
      <div class="stats-row">
        <n-statistic :label="t('profile.role')" :value="auth.user?.is_admin ? t('profile.role_admin') : t('profile.role_trainer')" />
        <n-statistic :label="t('profile.bound_player')" :value="boundPlayerName || t('profile.none')" />
      </div>
    </n-card>

    <!-- Claim Section -->
    <n-card :title="`${t('profile.checkin_status')}`" v-if="!boundPlayerName && !loadingPlayer">
      <p>{{ t('profile.qq_verify_prompt') }}</p>
      <n-input-group>
        <n-input v-model:value="qqId" :placeholder="t('profile.enter_qq_id')" />
        <n-button type="primary" @click="handleClaim" :loading="claiming">
          {{ t('profile.checkin') }}
        </n-button>
      </n-input-group>
    </n-card>
    
    <!-- Matches Section -->
    <div v-if="boundPlayerName">
      <div class="section-header">
        <h2>{{ t('profile.my_matches') }}</h2>
        <n-button size="small" secondary circle @click="fetchMatches">
          <template #icon><n-icon><Refresh /></n-icon></template>
        </n-button>
      </div>
      
      <div v-if="matchesLoading && matches.length === 0" class="loading-state">
         <n-spin size="large" />
      </div>
      
      <div v-else-if="matches.length === 0" class="empty-state">
         <n-empty :description="t('profile.no_matches')" />
      </div>

      <div v-else class="matches-grid">
         <PlayerMatchCard 
           v-for="match in matches" 
           :key="match.id" 
           :match="match" 
           @room-updated="fetchMatches"
         />
      </div>
    </div>
    
    <n-divider />
    
    <n-button type="error" ghost @click="logout">{{ t('nav.logout') }}</n-button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { useMessage, NCard, NStatistic, NInput, NInputGroup, NButton, NDivider, NSpin, NEmpty, NIcon } from 'naive-ui'
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
const loadingPlayer = ref(true) // Start assuming we are loading

// Matches Data
const matches = ref<MatchResponse[]>([])
const matchesLoading = ref(false)

onMounted(async () => {
  if (!auth.isAuthenticated) {
     router.push('/login')
     return
  }
  
  // 1. Check User/Player Status (Mocked or Real)
  // Since /me doesn't return player info yet, we rely on trying to fetch matches or claim status.
  // Ideally backend /me should return player info.
  // For now, let's try to fetch matches. If it works, we have a player.
  // Or we can add a simple check endpoint.
  
  // Workaround: We try to fetch matches. If it returns 200, we assume bound.
  // If fetch matches returns [], we still don't know if bound or just no matches.
  
  // Let's rely on local storage or optimistically fetch matches.
  await fetchMatches()
  
  // If we have matches, we definitely have a player.
  // If not, we might check claim status (skipping for this iteration, user sees claim box if logic falls through)
  // For UI stability, let's assume if matches fetch didn't throw 403/404, we are good?
  // Actually, let's just show claim box if we can't confirm player name.
  
  loadingPlayer.value = false
})

const fetchMatches = async () => {
  if (!auth.token) return
  matchesLoading.value = true
  try {
    const data = await getMyMatches(auth.token)
    matches.value = data
    // Side effect: if we got data, we are bound. 
    // We can't easily get the name from matches list if empty.
    // Let's assume user is bound if they logged in successfully for now in this prototype.
    if (data.length > 0) {
       boundPlayerName.value = "Trainer" // Placeholder until we update /me
    }
  } catch (e) {
    console.error(e)
  } finally {
    matchesLoading.value = false
  }
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
      message.success(t('profile.checkin_success'))
      boundPlayerName.value = data.in_game_name
      await fetchMatches()
    } else {
      const err = await res.json()
      message.error(err.detail || t('profile.checkin_fail'))
    }
  } catch (e) {
    message.error(t('profile.checkin_fail'))
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
.profile-container {
  max-width: 800px;
  margin: 0 auto;
}
.stats-row {
  display: flex;
  gap: 32px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 24px 0 16px;
}
.matches-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.loading-state, .empty-state {
  padding: 40px;
  text-align: center;
}
</style>
