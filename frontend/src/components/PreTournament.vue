<template>
  <div class="pre-tournament">
    <div class="hero-section">
       <h1 class="main-title">{{ t('live.pre_title') }}</h1>
       <p class="subtitle">{{ t('live.pre_subtitle') }}</p>

       <div class="countdown-card">
          <div class="label">{{ t('live.countdown_label') }}</div>
          <div class="timer">
             00 : 00 : 00
          </div>
       </div>

       <div class="checkin-action">
          <n-button 
            type="primary" 
            size="large" 
            class="checkin-btn" 
            @click="handleCheckIn"
            :disabled="isCheckedIn"
            :type="isCheckedIn ? 'success' : 'primary'"
          >
            <template #icon>
              <span v-if="isCheckedIn">✅</span>
              <span v-else>📍</span>
            </template>
            {{ isCheckedIn ? t('live.checked_in_label') : t('live.checkin_btn') }}
          </n-button>
       </div>
    </div>

    <n-divider />

    <div class="wall-section">
       <h3>{{ t('live.trainer_wall') }} ({{ players.length }})</h3>
       <div class="trainer-wall">
          <div v-for="player in players" :key="player.id" class="trainer-avatar" :title="player.in_game_name">
             <div class="avatar-circle" :style="{ backgroundColor: getAvatarColor(player.in_game_name) }">
                {{ player.in_game_name.substring(0, 1).toUpperCase() }}
             </div>
             <div class="trainer-name">{{ player.in_game_name }}</div>
          </div>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NDivider, useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()

const players = ref<any[]>([])
const loading = ref(false)

const isCheckedIn = computed(() => {
   if (!auth.user || !players.value) return false
   return players.value.some(p => p.user_id === auth.user?.id)
})

onMounted(async () => {
   await fetchPlayers()
})

const fetchPlayers = async () => {
   try {
      const res = await fetch('/api/v1/players/?claimed=true')
      if (res.ok) {
         players.value = await res.json()
      }
   } catch (e) {
      console.error(e)
   }
}

const handleCheckIn = () => {
   // Check if user has bound player
   // We can check if the user's ID matches any user_id in the players list
   // OR check auth store if we updated it
   
   if (!auth.user) {
       message.error(t('login.required'))
       return
   }

   // Check if user is already in the list
   const found = players.value.find(p => p.user_id === auth.user?.id)
   
   if (found) {
       message.success(t('live.checkin_success'))
   } else {
       // If not found, it means they haven't bound their QQ yet (since the list is claimed players)
       message.error(t('live.checkin_need_bind'))
   }
}

// Visuals
const getAvatarColor = (name: string) => {
   let hash = 0
   for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash)
   }
   const c = (hash & 0x00FFFFFF).toString(16).toUpperCase()
   return '#' + '00000'.substring(0, 6 - c.length) + c
}

</script>

<style scoped>
.pre-tournament {
   text-align: center;
   padding: 40px 20px;
}
.main-title {
   font-size: 2.5rem;
   color: #333;
   margin-bottom: 8px;
}
.subtitle {
   color: #666;
   font-size: 1.2rem;
   margin-bottom: 32px;
}
.countdown-card {
   background: linear-gradient(135deg, #212121, #424242);
   color: white;
   padding: 24px;
   border-radius: 16px;
   display: inline-block;
   margin-bottom: 32px;
   box-shadow: 0 10px 20px rgba(0,0,0,0.2);
   min-width: 300px;
}
.timer {
   font-size: 3rem;
   font-family: monospace;
   font-weight: bold;
   color: #FFD700;
}
.label {
   font-size: 0.9rem;
   text-transform: uppercase;
   letter-spacing: 2px;
   opacity: 0.8;
   margin-bottom: 8px;
}
.checkin-btn {
   padding: 0 40px;
   font-weight: bold;
   font-size: 1.1rem;
   height: 50px;
}
.wall-section {
   margin-top: 40px;
}
.trainer-wall {
   display: flex;
   flex-wrap: wrap;
   justify-content: center;
   gap: 16px;
   margin-top: 24px;
}
.trainer-avatar {
   display: flex;
   flex-direction: column;
   align-items: center;
   width: 80px;
}
.avatar-circle {
   width: 48px;
   height: 48px;
   border-radius: 50%;
   display: flex;
   align-items: center;
   justify-content: center;
   color: white;
   font-weight: bold;
   font-size: 1.2rem;
   margin-bottom: 8px;
   box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.trainer-name {
   font-size: 0.8rem;
   color: #555;
   overflow: hidden;
   text-overflow: ellipsis;
   white-space: nowrap;
   width: 100%;
}
</style>
