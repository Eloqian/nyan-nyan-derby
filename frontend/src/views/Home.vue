<template>
  <div class="home-container">
    
    <!-- Loading State -->
    <div v-if="loading" class="loading-screen">
       <n-spin size="large" />
    </div>

    <!-- No Tournament Setup -->
    <div v-else-if="!tournament" class="setup-placeholder">
       <n-empty description="No Tournament Active" size="large">
          <template #extra>
             <div class="admin-hint">
                Admin: Go to Dashboard to create one.
             </div>
          </template>
       </n-empty>
    </div>

    <div v-else class="landing-content">
       <!-- Hero Section -->
       <div class="hero-section" :class="tournament.status">
          <div class="hero-overlay">
             <h1 class="title">{{ tournament.name }}</h1>
             <div class="subtitle">
                <span v-if="tournament.status === 'setup'">🚀 COMING SOON</span>
                <span v-else-if="tournament.status === 'active'">🔥 LIVE NOW</span>
                <span v-else>🏁 COMPLETED</span>
             </div>
             
             <!-- Countdown (Mocked for demo) -->
             <div v-if="tournament.status === 'setup'" class="countdown">
                <div class="time-box">
                   <span class="num">02</span>
                   <span class="label">Days</span>
                </div>
                <div class="time-box">
                   <span class="num">14</span>
                   <span class="label">Hours</span>
                </div>
             </div>

             <!-- Action Buttons -->
             <div class="hero-actions">
                <n-button v-if="tournament.status === 'active'" type="warning" size="large" round @click="$router.push('/live')">
                   📺 Watch Live
                </n-button>
                
                <n-button v-if="!isLoggedIn" type="primary" size="large" round @click="$router.push('/login')">
                   👉 Login / Register
                </n-button>
                <n-button v-else type="primary" size="large" round @click="$router.push('/profile')">
                   ✅ Check-in / My Profile
                </n-button>
             </div>
          </div>
       </div>

       <!-- Info Grid -->
       <n-grid x-gap="24" y-gap="24" cols="1 s:3" responsive="screen" class="info-grid">
          
          <!-- Rules Card -->
          <n-grid-item>
             <n-card title="📜 Rules" class="info-card">
                <ul class="rule-list">
                   <li><strong>Audition:</strong> Top 4 advance per group.</li>
                   <li><strong>Group Stage:</strong> Strategic points battle.</li>
                   <li><strong>Elimination:</strong> Double elimination bracket.</li>
                   <li><strong>Scoring:</strong> 1st(9), 2nd(5), 3rd(3)...</li>
                </ul>
             </n-card>
          </n-grid-item>

          <!-- Prizes Card -->
          <n-grid-item>
             <n-card title="🏆 Prizes" class="info-card">
                <div class="prize-list">
                   <div class="prize-item gold">
                      <span class="icon">🥇</span>
                      <span class="amount">¥200</span>
                   </div>
                   <div class="prize-item silver">
                      <span class="icon">🥈</span>
                      <span class="amount">¥160</span>
                   </div>
                   <div class="prize-item bronze">
                      <span class="icon">🥉</span>
                      <span class="amount">¥120</span>
                   </div>
                </div>
             </n-card>
          </n-grid-item>

          <!-- Stats Card -->
          <n-grid-item>
             <n-card title="📊 Stats" class="info-card">
                <n-statistic label="Registered Trainers" :value="players.length" />
                <n-statistic label="Checked-in" :value="checkedInCount" style="margin-top: 12px">
                   <template #suffix>/ 96</template>
                </n-statistic>
             </n-card>
          </n-grid-item>
       </n-grid>
       
       <!-- Player Wall (Check-in Status) -->
       <div class="player-wall-section">
          <h2>Trainer Wall (Checked-in)</h2>
          <div class="wall-grid">
             <div v-for="p in checkedInPlayers" :key="p.id" class="player-badge">
                <n-avatar round size="medium" :style="{ backgroundColor: stringToColor(p.in_game_name) }">
                   {{ p.in_game_name[0] }}
                </n-avatar>
                <span class="name">{{ p.in_game_name }}</span>
             </div>
             <!-- Placeholders -->
             <div v-for="i in Math.max(0, 10 - checkedInPlayers.length)" :key="i" class="player-badge empty">
                <n-avatar round size="medium" color="#eee">?</n-avatar>
                <span class="name">...</span>
             </div>
          </div>
       </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getCurrentTournament, type Tournament } from '../api/tournaments'
import { NSpin, NEmpty, NButton, NGrid, NGridItem, NCard, NStatistic, NAvatar } from 'naive-ui'

const auth = useAuthStore()
const loading = ref(true)
const tournament = ref<Tournament | null>(null)
const players = ref<any[]>([])

const isLoggedIn = computed(() => auth.isAuthenticated)

const checkedInPlayers = computed(() => {
   return players.value.filter(p => p.user_id !== null)
})

const checkedInCount = computed(() => checkedInPlayers.value.length)

onMounted(async () => {
   try {
      const [t, pRes] = await Promise.all([
         getCurrentTournament(),
         fetch('/api/v1/players/').then(r => r.json())
      ])
      tournament.value = t
      players.value = pRes
   } catch (e) {
      console.error(e)
   } finally {
      loading.value = false
   }
})

// Helpers
const stringToColor = (str: string) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
  return '#' + "00000".substring(0, 6 - c.length) + c;
}

</script>

<style scoped>
.home-container {
  min-height: 80vh;
}
.loading-screen, .setup-placeholder {
   display: flex;
   justify-content: center;
   align-items: center;
   height: 60vh;
}

.hero-section {
   position: relative;
   background: linear-gradient(135deg, #7CB342 0%, #558B2F 100%);
   color: white;
   padding: 60px 24px;
   border-radius: 0 0 24px 24px;
   text-align: center;
   box-shadow: 0 4px 20px rgba(0,0,0,0.15);
   overflow: hidden;
}
.hero-section.setup {
   background: linear-gradient(135deg, #42A5F5 0%, #1565C0 100%);
}
.hero-section.completed {
   background: linear-gradient(135deg, #FFB74D 0%, #EF6C00 100%);
}

.title {
   font-size: 3.5rem;
   margin: 0;
   font-weight: 900;
   letter-spacing: -1px;
   text-shadow: 2px 2px 0px rgba(0,0,0,0.1);
}
.subtitle {
   font-size: 1.5rem;
   margin-top: 10px;
   font-weight: bold;
   opacity: 0.9;
   letter-spacing: 2px;
}

.countdown {
   display: flex;
   justify-content: center;
   gap: 20px;
   margin: 30px 0;
}
.time-box {
   background: rgba(255,255,255,0.2);
   padding: 10px 20px;
   border-radius: 12px;
   backdrop-filter: blur(5px);
}
.time-box .num {
   display: block;
   font-size: 2.5rem;
   font-weight: bold;
}
.time-box .label {
   font-size: 0.9rem;
   text-transform: uppercase;
   opacity: 0.8;
}

.hero-actions {
   margin-top: 30px;
   display: flex;
   gap: 16px;
   justify-content: center;
}

.info-grid {
   max-width: 1200px;
   margin: -30px auto 0;
   padding: 0 24px;
   position: relative;
   z-index: 2;
}
.info-card {
   height: 100%;
   box-shadow: 0 4px 12px rgba(0,0,0,0.05);
   border-radius: 16px;
}

.rule-list {
   padding-left: 20px;
   margin: 0;
   line-height: 1.6;
}

.prize-list {
   display: flex;
   flex-direction: column;
   gap: 12px;
}
.prize-item {
   display: flex;
   align-items: center;
   gap: 12px;
   font-size: 1.1rem;
   font-weight: bold;
}
.prize-item.gold { color: #FFD700; }
.prize-item.silver { color: #9E9E9E; }
.prize-item.bronze { color: #A1887F; }

.player-wall-section {
   max-width: 1200px;
   margin: 40px auto;
   padding: 0 24px;
   text-align: center;
}
.wall-grid {
   display: flex;
   flex-wrap: wrap;
   gap: 16px;
   justify-content: center;
   margin-top: 20px;
}
.player-badge {
   display: flex;
   flex-direction: column;
   align-items: center;
   width: 80px;
   gap: 8px;
}
.player-badge.empty {
   opacity: 0.3;
}
.name {
   font-size: 0.85rem;
   white-space: nowrap;
   overflow: hidden;
   text-overflow: ellipsis;
   max-width: 100%;
}
</style>
