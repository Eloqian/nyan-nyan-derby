<template>
  <div class="home-screen">
    <div class="main-content-wrapper">
      
      <!-- HERO SECTION: Active Tournament -->
      <section v-if="activeTournaments.length > 0" class="hero-section">
        <div v-for="t in activeTournaments" :key="t.id" class="hero-card" @click="goToTournament(t.id)" :style="{ backgroundImage: `url(${raceCardBg})` }">
          
          <div class="hero-overlay"></div>
          <div class="hero-bg-pattern"></div>
          
          <div class="hero-info">
            <div class="live-badge-wrapper">
              <span class="live-badge">LIVE NOW</span>
              <span class="viewer-count">● {{ $t('home.status_active') }}</span>
            </div>
            
            <h2 class="hero-title">{{ t.name }}</h2>
            
            <div class="hero-meta">
              <div class="meta-item">
                <span class="label">GRADE</span>
                <span class="value g1">G1</span>
              </div>
              <div class="meta-item">
                <span class="label">DATE</span>
                <span class="value">{{ formatDate(t.created_at) }}</span>
              </div>
            </div>

            <button class="enter-btn">
              {{ $t('home.view_details') }} <span class="arrow">ᐳ</span>
            </button>
          </div>

          <div class="hero-character">
            <img :src="charImg" class="hero-tachie" alt="Character" />
          </div>
        </div>
      </section>

      <!-- Placeholder Hero if no active race -->
      <section v-else class="hero-section empty">
        <div class="hero-card empty-state">
           <div class="hero-character-empty">
            <img :src="charImg" class="hero-tachie-empty" alt="Character" />
          </div>
          <div class="hero-info centered">
            <h2 class="hero-title">{{ $t('home.no_active_tournament') || 'NO ACTIVE RACES' }}</h2>
            <p class="hero-subtitle">{{ $t('home.coming_soon') }}</p>
            <div v-if="auth.user?.is_admin" style="margin-top: 20px;">
              <button class="enter-btn" @click="$router.push('/admin')">{{ $t('home.go_to_admin') }}</button>
            </div>
          </div>
        </div>
      </section>

      <!-- History Section (Full Width) -->
      <div class="history-section">
          <div class="section-head">
            <h3>{{ $t('home.past_tournaments') }}</h3>
            <div class="line"></div>
          </div>
          
          <div v-if="completedTournaments.length > 0" class="history-grid">
             <div v-for="t in completedTournaments" :key="t.id" class="history-card" @click="goToTournament(t.id)">
               <div class="card-top">
                 <span class="grade-badge g3">G3</span>
                 <span class="date-badge">{{ formatDate(t.created_at) }}</span>
               </div>
               <h4 class="history-title">{{ t.name }}</h4>
               <div class="card-bottom">
                 <button class="result-btn">RESULT</button>
               </div>
             </div>
          </div>
           <div v-else class="empty-text">{{ $t('home.no_tournaments') }}</div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { listTournaments, type Tournament } from '../api/tournaments'

// Assets
import charImg from '../assets/images/characters/char_01.png'
import raceCardBg from '../assets/images/backgrounds/race_card_bg.jpg'

const { t } = useI18n()
void t // Suppress unused error
const router = useRouter()
const auth = useAuthStore()

const tournaments = ref<Tournament[]>([])

const activeTournaments = computed(() => tournaments.value.filter(t => t.status === 'active'))
// Setup tournaments are hidden as per request
const completedTournaments = computed(() => tournaments.value.filter(t => t.status === 'completed'))

onMounted(async () => {
  try {
    tournaments.value = await listTournaments()
  } catch (e) {
    console.error(e)
  }
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const goToTournament = (tournamentId: string) => {
  router.push(`/tournament/${tournamentId}`)
}
</script>

<style scoped>
.home-screen {
  position: relative;
  width: 100%;
  overflow-x: hidden;
  font-family: 'M PLUS Rounded 1c', sans-serif;
  color: #333;
}

.main-content-wrapper {
  max-width: 1800px; /* Wider container */
  margin: 0 auto;
  padding: 40px 5%;
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .main-content-wrapper { padding: 20px 16px; }
  .hero-card { height: auto; min-height: 400px; flex-direction: column; }
  .hero-info { padding: 30px 20px; align-items: center; text-align: center; }
  .hero-character { display: none; /* Hide tachie on mobile to save space */ }
  .hero-title { font-size: 2.5rem; }
  .hero-meta { gap: 16px; margin-bottom: 20px; }
}

/* Hero Section */
.hero-section {
  margin-bottom: 60px;
}

.hero-card {
  position: relative;
  /* Background Image Set Inline */
  background-size: cover;
  background-position: center;
  border-radius: 24px;
  height: 450px; /* Taller hero */
  display: flex;
  overflow: hidden;
  box-shadow: 
    0 10px 30px rgba(0,0,0,0.3),
    0 0 0 4px white, /* Crisp white border */
    0 0 0 8px rgba(255, 255, 255, 0.2); /* Outer glow */
  cursor: pointer;
  transition: transform 0.3s;
  margin-bottom: 40px;
}
.hero-card:hover { transform: scale(1.005); }

/* Dark Gradient Overlay to make text pop */
.hero-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(to right, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 50%, transparent 100%);
  z-index: 0;
}

.hero-bg-pattern {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  /* Polka dots overlay for anime texture */
  background-image: radial-gradient(rgba(255,255,255,0.15) 15%, transparent 16%);
  background-size: 20px 20px;
  z-index: 1;
  mix-blend-mode: overlay;
}

/* Diagonal Decorative Strip */
.hero-bg-pattern::after {
  content: '';
  position: absolute;
  top: 0; right: 20%; width: 100px; height: 100%;
  background: rgba(255,255,255,0.1);
  transform: skewX(-20deg);
}

.hero-info {
  flex: 1;
  padding: 60px;
  color: white;
  z-index: 5;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.hero-info.centered { align-items: center; text-align: center; }

.live-badge-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  background: rgba(0,0,0,0.2);
  padding: 4px 16px 4px 4px;
  border-radius: 20px;
}
.live-badge {
  background: #FF5252;
  color: white;
  font-weight: 900;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 0.9rem;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  animation: pulse 2s infinite;
}
.viewer-count {
  color: white;
  font-size: 0.9rem;
  font-weight: 700;
}

.hero-title {
  font-size: 4rem; /* Larger title */
  margin: 0 0 24px 0;
  line-height: 1.1;
  font-weight: 900;
  font-style: italic;
  /* White outline text */
  -webkit-text-stroke: 4px white;
  paint-order: stroke fill;
  color: var(--uma-blue, #4FB3FF); /* Fill color */
  filter: drop-shadow(4px 4px 0 rgba(0,0,0,0.1));
}

.hero-meta {
  display: flex;
  gap: 40px;
  margin-bottom: 40px;
}
.meta-item {
  display: flex;
  flex-direction: column;
}
.meta-item .label {
  font-size: 0.9rem;
  color: rgba(255,255,255,0.8);
  font-weight: 800;
  letter-spacing: 1px;
}
.meta-item .value {
  font-size: 1.6rem;
  font-weight: 900;
  color: white;
}
.meta-item .value.g1 { 
  color: var(--uma-gold, #FFC800); 
  font-size: 2rem;
  text-shadow: 2px 2px 0 rgba(0,0,0,0.2);
}

.enter-btn {
  background: linear-gradient(to bottom, #FFF 0%, #F0F0F0 100%);
  color: var(--uma-green, #67C05D);
  border: none;
  padding: 16px 48px;
  border-radius: 40px;
  font-size: 1.4rem;
  font-weight: 900;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 6px 0 #DBDBDB, 0 10px 10px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 12px;
}
.enter-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 0 #DBDBDB, 0 12px 15px rgba(0,0,0,0.15); }
.enter-btn:active { transform: translateY(4px); box-shadow: 0 0 0 #DBDBDB; }
.enter-btn .arrow { font-size: 1rem; }

/* Hero Character Integration */
.hero-character {
  position: relative;
  width: 500px;
  height: 100%;
  z-index: 4;
}
.hero-tachie {
  position: absolute;
  bottom: -40px; 
  right: -50px;
  height: 130%; /* Pop out more */
  width: auto;
  object-fit: contain;
  filter: drop-shadow(-4px 4px 10px rgba(0,0,0,0.2));
  mask-image: none;
  -webkit-mask-image: none;
}

/* Empty State Styling - Softer */
.hero-card.empty-state {
  background: rgba(255, 255, 255, 0.9);
  border: 4px dashed var(--uma-green);
  box-shadow: 0 10px 30px rgba(0,0,0,0.05);
  height: 300px;
}
.hero-card.empty-state .hero-title {
  color: #ccc;
  -webkit-text-stroke: 0;
  text-shadow: none;
  font-size: 2.5rem;
  filter: none;
}
.hero-card.empty-state .hero-subtitle {
  color: #999;
  font-size: 1.2rem;
  font-weight: bold;
}
.hero-character-empty {
  width: 300px;
  opacity: 0.8;
  filter: grayscale(0.5);
}
.hero-tachie-empty {
  height: 100%;
  width: auto;
  object-fit: contain;
}

/* History Section Grid */
.history-section {
  margin-top: 40px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.section-head h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 900;
  color: var(--uma-dark, #3E3838);
}
.section-head .line {
  flex: 1;
  height: 2px;
  background: #eee;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.history-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 160px;
}
.history-card:hover { 
  transform: translateY(-5px); 
  box-shadow: 0 12px 24px rgba(0,0,0,0.1);
  border-color: #ddd;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.grade-badge {
  background: #999;
  color: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 900;
  font-size: 0.8rem;
}
.date-badge {
  font-size: 0.85rem;
  color: #999;
  font-weight: bold;
}

.history-title {
  margin: 0 0 16px 0;
  font-size: 1.2rem;
  font-weight: 800;
  color: #333;
  line-height: 1.4;
  flex: 1;
}

.card-bottom {
  text-align: right;
}
.result-btn {
  font-size: 0.75rem;
  font-weight: 800;
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid #eee;
  background: #f9f9f9;
  color: #999;
  cursor: pointer;
}
.history-card:hover .result-btn {
  background: var(--uma-blue);
  color: white;
  border-color: var(--uma-blue);
}

.empty-text {
  color: #999;
  font-style: italic;
  padding: 20px 0;
  font-size: 1.1rem;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}
</style>