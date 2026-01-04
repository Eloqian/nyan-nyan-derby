<template>
  <div class="pre-tournament">
    <div class="hero-section">
       <h1 class="main-title">{{ tournament?.name || t('live.pre_title') }}</h1>
       <p class="subtitle">{{ t('live.pre_subtitle') }}</p>

       <!-- Status / Countdown Card -->
       <div class="status-container">
          <!-- Case 1: Not Started (Countdown + Checkin) -->
          <div v-if="!isStarted" class="countdown-modern">
              <div class="timer-label">{{ t('live.countdown_label') }}</div>
              <div class="timer-digits">{{ countdownText }}</div>
              
              <div class="checkin-action" v-if="tournament?.status === 'setup'">
                <n-button 
                  round
                  size="large" 
                  class="checkin-btn-modern" 
                  @click="handleCheckIn"
                  :disabled="isCheckedIn || checkingIn"
                  :type="isCheckedIn ? 'primary' : 'primary'"
                  :class="{ 'is-checked': isCheckedIn }"
                  :loading="checkingIn"
                >
                  <template #icon>
                    <span v-if="isCheckedIn">✅</span>
                    <span v-else>📍</span>
                  </template>
                  {{ isCheckedIn ? t('live.checked_in_label') : t('live.checkin_btn') }}
                </n-button>
                <div v-if="isCheckedIn" class="checkin-tip">
                   {{ t('live.checkin_success') }}
                </div>
             </div>
          </div>

          <!-- Case 2: Started (Live Status) -->
          <div v-else class="live-status-modern">
             <div class="live-icon-box">
                <span class="pulse-ring"></span>
                🔥
             </div>
             <div class="live-text">
                <h2>{{ t('home.live_now') }}</h2>
                <p>{{ t('live.subtitle') }}</p>
             </div>
          </div>
       </div>
    </div>

    <n-divider />

    <!-- Trainer Wall (Moved Up) -->
    <div class="wall-section">
       <div class="section-header">
          <h3>{{ t('live.trainer_wall') }}</h3>
          <span class="count-badge">{{ participants.length }}</span>
       </div>
       <div class="trainer-wall">
          <div v-for="p in participants" :key="p.player_id" class="trainer-avatar" :title="p.player.in_game_name">
             <div class="avatar-circle" :style="{ backgroundColor: getAvatarColor(p.player.in_game_name) }">
                {{ p.player.in_game_name.substring(0, 1).toUpperCase() }}
             </div>
             <div class="trainer-name">{{ p.player.in_game_name }}</div>
          </div>
          <div v-if="participants.length === 0" class="empty-wall">
             Waiting for trainers...
          </div>
       </div>
    </div>

    <n-divider />

    <!-- Rules Section (Moved Down) -->
    <div class="rules-section" v-if="tournament?.rules_content">
       <h3>{{ t('live.rules_title', 'Tournament Rules') }}</h3>
       <div class="rules-card">
          <div class="markdown-body" v-html="renderedRules"></div>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NDivider, useMessage } from 'naive-ui'
import MarkdownIt from 'markdown-it'
import { useAuthStore } from '../stores/auth'
import { 
  checkInTournament, 
  getTournamentParticipants, 
  type Tournament, 
  type TournamentParticipant 
} from '../api/tournaments'

const props = defineProps<{
  tournament: Tournament | null
}>()

const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()
const md = new MarkdownIt()

const participants = ref<TournamentParticipant[]>([])
const checkingIn = ref(false)
const now = ref(Date.now())
let timerInterval: any = null

// Simple check logic (In real app, backend tells us if we checked in)
const isCheckedIn = computed(() => {
   if (!auth.user || !participants.value) return false
   return participants.value.some(p => p.player.qq_id === auth.user?.username && p.checked_in)
})

const renderedRules = computed(() => {
   if (!props.tournament?.rules_content) return ''
   return md.render(props.tournament.rules_content)
})

const isStarted = computed(() => {
   if (!props.tournament?.start_time) return false
   return new Date(props.tournament.start_time).getTime() <= now.value
})

const countdownText = computed(() => {
   if (!props.tournament?.start_time) return "00 : 00 : 00"
   const start = new Date(props.tournament.start_time).getTime()
   const diff = start - now.value
   
   if (diff <= 0) return "00 : 00 : 00"
   
   const days = Math.floor(diff / (1000 * 60 * 60 * 24))
   const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
   const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
   const seconds = Math.floor((diff % (1000 * 60)) / 1000)
   
   if (days > 0) return `${days}d ${hours}h ${minutes}m`
   return `${hours.toString().padStart(2, '0')} : ${minutes.toString().padStart(2, '0')} : ${seconds.toString().padStart(2, '0')}`
})

onMounted(async () => {
   timerInterval = setInterval(() => {
      now.value = Date.now()
   }, 1000)
   if (props.tournament) {
      await loadParticipants()
   }
})

watch(() => props.tournament, async (newVal) => {
   if (newVal) {
      await loadParticipants()
   }
})

onUnmounted(() => {
   if (timerInterval) clearInterval(timerInterval)
})

const loadParticipants = async () => {
   if (props.tournament) {
      participants.value = await getTournamentParticipants(props.tournament.id)
   }
}

const handleCheckIn = async () => {
   if (!auth.isAuthenticated) {
       message.error(t('login.required'))
       return
   }
   if (!props.tournament) return

   checkingIn.value = true
   try {
      await checkInTournament(auth.token!, props.tournament.id)
      message.success(t('live.checkin_success'))
      await loadParticipants()
   } catch (e: any) {
      message.error(e.message || t('live.checkin_fail'))
   } finally {
      checkingIn.value = false
   }
}

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
   max-width: 1400px;
   margin: 0 auto;
}
.main-title {
   font-size: 3rem;
   color: #3E3838;
   margin-bottom: 8px;
   font-weight: 900;
}
.subtitle {
   color: #888;
   font-size: 1.2rem;
   margin-bottom: 40px;
   font-weight: 500;
}

/* --- Status Container --- */
.status-container {
   display: flex;
   justify-content: center;
   margin-bottom: 20px;
}

/* Countdown Modern */
.countdown-modern {
   background: white;
   padding: 2rem 4rem;
   border-radius: 24px;
   box-shadow: 0 10px 30px rgba(0,0,0,0.08);
   border: 1px solid rgba(0,0,0,0.05);
   display: flex;
   flex-direction: column;
   align-items: center;
   gap: 1rem;
   min-width: 400px;
}
.timer-label {
   font-size: 0.9rem;
   text-transform: uppercase;
   letter-spacing: 3px;
   color: #aaa;
   font-weight: 800;
}
.timer-digits {
   font-family: 'Montserrat', monospace;
   font-size: 4rem;
   font-weight: 700;
   color: var(--uma-blue, #4FB3FF);
   line-height: 1;
   font-variant-numeric: tabular-nums;
}

/* Live Status Modern */
.live-status-modern {
   background: white;
   padding: 2rem 4rem;
   border-radius: 24px;
   box-shadow: 0 10px 30px rgba(255, 82, 82, 0.15);
   border: 2px solid #FF5252;
   display: flex;
   align-items: center;
   gap: 2rem;
}
.live-icon-box {
   width: 80px; height: 80px;
   background: #FF5252;
   border-radius: 50%;
   display: flex; justify-content: center; align-items: center;
   font-size: 2.5rem; color: white;
   position: relative;
}
.pulse-ring {
   position: absolute;
   width: 100%; height: 100%;
   border-radius: 50%;
   border: 4px solid #FF5252;
   animation: pulse-ring 2s infinite;
}
@keyframes pulse-ring {
   0% { transform: scale(1); opacity: 0.8; }
   100% { transform: scale(1.5); opacity: 0; }
}
.live-text h2 { margin: 0; font-size: 2rem; color: #333; }
.live-text p { margin: 0; color: #888; }

/* Checkin Button */
.checkin-action {
   margin-top: 1rem;
   display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.checkin-btn-modern {
   padding: 0 40px;
   font-weight: 800;
   font-size: 1.1rem;
   height: 56px;
   box-shadow: 0 4px 12px rgba(103, 192, 93, 0.3);
   background-color: var(--uma-green, #67C05D);
   border: none;
   transition: all 0.2s;
}
.checkin-btn-modern:hover {
   transform: translateY(-2px);
   box-shadow: 0 8px 16px rgba(103, 192, 93, 0.4);
   background-color: #58a84f;
}
.checkin-btn-modern.is-checked {
   background-color: #eee;
   color: #888;
   box-shadow: none;
   cursor: default;
}
.checkin-tip {
   font-size: 0.8rem; color: var(--uma-green, #67C05D); font-weight: bold;
}

/* Wall Section */
.wall-section { margin: 40px 0; }
.section-header {
   display: flex; justify-content: center; align-items: center; gap: 12px;
   margin-bottom: 24px;
}
.wall-section h3 { margin: 0; font-size: 1.5rem; color: #444; }
.count-badge {
   background: #eee; color: #666;
   padding: 2px 10px; border-radius: 12px; font-weight: 800; font-size: 0.9rem;
}
.trainer-wall {
   display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;
}
.trainer-avatar {
   display: flex; flex-direction: column; align-items: center; width: 90px;
   transition: transform 0.2s;
}
.trainer-avatar:hover { transform: translateY(-4px); }
.avatar-circle {
   width: 56px; height: 56px;
   border-radius: 50%;
   display: flex; align-items: center; justify-content: center;
   color: white; font-weight: 800; font-size: 1.4rem;
   margin-bottom: 8px;
   box-shadow: 0 4px 10px rgba(0,0,0,0.1);
   text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
}
.trainer-name {
   font-size: 0.85rem; color: #555;
   overflow: hidden; text-overflow: ellipsis; white-space: nowrap; width: 100%;
   font-weight: 600;
}
.empty-wall { color: #ccc; font-style: italic; }

/* Rules Section */
.rules-section { text-align: left; max-width: 1200px; margin: 0 auto; }
.rules-section h3 {
   text-align: center; font-size: 1.5rem; color: #444; margin-bottom: 24px;
}
.rules-card {
   background: #fcfcfc;
   border: 1px solid #eee;
   padding: 30px;
   border-radius: 16px;
   box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

/* Markdown Overrides */
.markdown-body { font-family: sans-serif; color: #444; }
.markdown-body :deep(h1), .markdown-body :deep(h2) { border-bottom: none; color: var(--uma-blue, #4FB3FF); }
</style>