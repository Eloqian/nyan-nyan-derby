<template>
  <div class="pre-tournament">
    <div class="hero-section">
       <h1 class="main-title">{{ tournament?.name || t('live.pre_title') }}</h1>
       <p class="subtitle">{{ t('live.pre_subtitle') }}</p>

       <div class="countdown-card" v-if="tournament?.start_time">
          <div class="label">{{ t('live.countdown_label') }}</div>
          <div class="timer">
             {{ countdownText }}
          </div>
       </div>

       <div class="checkin-action" v-if="tournament?.status === 'setup'">
          <n-button 
            size="large" 
            class="checkin-btn" 
            @click="handleCheckIn"
            :disabled="isCheckedIn || checkingIn"
            :type="isCheckedIn ? 'success' : 'primary'"
            :loading="checkingIn"
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

    <!-- Rules Section -->
    <div class="rules-section" v-if="tournament?.rules_content">
       <h3>{{ t('live.rules_title', 'Tournament Rules') }}</h3>
       <div class="rules-content custom-scroll">
          <div class="markdown-body" v-html="renderedRules"></div>
       </div>
    </div>

    <n-divider />

    <div class="wall-section">
       <h3>{{ t('live.trainer_wall') }} ({{ participants.length }})</h3>
       <div class="trainer-wall">
          <div v-for="p in participants" :key="p.player_id" class="trainer-avatar" :title="p.player.in_game_name">
             <div class="avatar-circle" :style="{ backgroundColor: getAvatarColor(p.player.in_game_name) }">
                {{ p.player.in_game_name.substring(0, 1).toUpperCase() }}
             </div>
             <div class="trainer-name">{{ p.player.in_game_name }}</div>
          </div>
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

const isCheckedIn = computed(() => {
   // Simplified check
   return false 
})

const renderedRules = computed(() => {
   if (!props.tournament?.rules_content) return ''
   return md.render(props.tournament.rules_content)
})

onMounted(async () => {
   timerInterval = setInterval(() => {
      now.value = Date.now()
   }, 1000)
   if (props.tournament) {
      await loadParticipants()
   }
})
// ... (rest of the script)

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

const countdownText = computed(() => {
   if (!props.tournament?.start_time) return "00 : 00 : 00"
   const start = new Date(props.tournament.start_time).getTime()
   const diff = start - now.value
   
   if (diff <= 0) return "In Progress"
   
   const days = Math.floor(diff / (1000 * 60 * 60 * 24))
   const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
   const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
   const seconds = Math.floor((diff % (1000 * 60)) / 1000)
   
   if (days > 0) return `${days}d ${hours}h ${minutes}m`
   return `${hours.toString().padStart(2, '0')} : ${minutes.toString().padStart(2, '0')} : ${seconds.toString().padStart(2, '0')}`
})

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
   max-width: 100%;
   margin: 0 auto;
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
.rules-content {
   line-height: 1.6; 
   text-align: left;
   background: #f9f9f9;
   padding: 20px;
   border-radius: 8px;
}
.markdown-body :deep(h1), .markdown-body :deep(h2) {
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}
.markdown-body :deep(h3) {
  font-size: 1.25em;
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
}
.markdown-body :deep(p) {
  margin-bottom: 16px;
  line-height: 1.8;
}
.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 2em;
  margin-bottom: 16px;
}
.markdown-body :deep(li) {
  margin-bottom: 4px;
}
.markdown-body :deep(blockquote) {
  margin: 0 0 16px;
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
}
.markdown-body :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
}
.markdown-body :deep(a) {
  color: #0366d6;
  text-decoration: none;
}
.markdown-body :deep(a:hover) {
  text-decoration: underline;
}
</style>