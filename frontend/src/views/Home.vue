<template>
  <div class="home-container">
    
    <!-- Loading State -->
    <div v-if="loading" class="loading-screen">
       <n-spin size="large" />
    </div>

    <!-- Tournament List -->
    <div v-else class="tournament-list">
      <h1 class="page-title">{{ t('home.all_tournaments') }}</h1>
      
      <div v-if="tournaments.length === 0" class="empty-state">
        <n-empty :description="t('home.no_tournaments')">
          <template #extra>
            <div class="admin-hint" v-if="auth.user?.is_admin">
              {{ t('home.admin_create_hint') }}
              <n-button type="primary" @click="$router.push('/admin')">
                {{ t('home.go_to_admin') }}
              </n-button>
            </div>
          </template>
        </n-empty>
      </div>

      <!-- Group tournaments by status -->
      <div v-else>
        <!-- Active Tournaments -->
        <section v-if="activeTournaments.length > 0" class="tournament-section">
          <h2 class="section-title">🔥 {{ t('home.active_tournaments') }}</h2>
          <div class="tournament-grid">
            <div v-for="tournament in activeTournaments" :key="tournament.id" 
                 class="tournament-card active" 
                 @click="goToTournament(tournament.id)">
              <div class="card-header">
                <h3 class="tournament-name">{{ tournament.name }}</h3>
                <n-tag type="success" size="small">{{ t('home.live_now') }}</n-tag>
              </div>
              <div class="card-body">
                <div class="info-row">
                  <span class="label">{{ t('home.created') }}:</span>
                  <span class="value">{{ formatDate(tournament.created_at) }}</span>
                </div>
                <div class="info-row">
                  <span class="label">{{ t('home.status') }}:</span>
                  <span class="value status-active">{{ t('home.status_active') }}</span>
                </div>
              </div>
              <div class="card-footer">
                <n-button type="primary" secondary>
                  {{ t('home.view_details') }} →
                </n-button>
              </div>
            </div>
          </div>
        </section>

        <!-- Setup Tournaments -->
        <section v-if="setupTournaments.length > 0" class="tournament-section">
          <h2 class="section-title">🚀 {{ t('home.upcoming_tournaments') }}</h2>
          <div class="tournament-grid">
            <div v-for="tournament in setupTournaments" :key="tournament.id" 
                 class="tournament-card setup" 
                 @click="goToTournament(tournament.id)">
              <div class="card-header">
                <h3 class="tournament-name">{{ tournament.name }}</h3>
                <n-tag type="warning" size="small">{{ t('home.coming_soon') }}</n-tag>
              </div>
              <div class="card-body">
                <div class="info-row">
                  <span class="label">{{ t('home.created') }}:</span>
                  <span class="value">{{ formatDate(tournament.created_at) }}</span>
                </div>
                <div class="info-row">
                  <span class="label">{{ t('home.status') }}:</span>
                  <span class="value status-setup">{{ t('home.status_setup') }}</span>
                </div>
              </div>
              <div class="card-footer">
                <n-button type="warning" secondary>
                  {{ t('home.view_details') }} →
                </n-button>
              </div>
            </div>
          </div>
        </section>

        <!-- Completed Tournaments -->
        <section v-if="completedTournaments.length > 0" class="tournament-section">
         <h2 class="section-title">🏁 {{ t('home.past_tournaments') }}</h2>
          <div class="tournament-grid">
            <div v-for="tournament in completedTournaments" :key="tournament.id" 
                 class="tournament-card completed" 
                 @click="goToTournament(tournament.id)">
              <div class="card-header">
                <h3 class="tournament-name">{{ tournament.name }}</h3>
                <n-tag type="default" size="small">{{ t('home.completed') }}</n-tag>
              </div>
              <div class="card-body">
                <div class="info-row">
                  <span class="label">{{ t('home.created') }}:</span>
                  <span class="value">{{ formatDate(tournament.created_at) }}</span>
                </div>
                <div class="info-row">
                  <span class="label">{{ t('home.status') }}:</span>
                  <span class="value status-completed">{{ t('home.status_completed') }}</span>
                </div>
              </div>
              <div class="card-footer">
                <n-button type="default" secondary>
                  {{ t('home.view_details') }} →
                </n-button>
              </div>
            </div>
          </div>
        </section>
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
import { NSpin, NEmpty, NButton, NTag } from 'naive-ui'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(true)
const tournaments = ref<Tournament[]>([])

const activeTournaments = computed(() => {
  return tournaments.value.filter(t => t.status === 'active')
})

const setupTournaments = computed(() => {
  return tournaments.value.filter(t => t.status === 'setup')
})

const completedTournaments = computed(() => {
  return tournaments.value.filter(t => t.status === 'completed')
})

onMounted(async () => {
  try {
    tournaments.value = await listTournaments()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const goToTournament = (tournamentId: string) => {
  // Navigate to tournament detail page (LiveTournament with tournament ID)
  router.push(`/tournament/${tournamentId}`)
}

</script>

<style scoped>
.home-container {
  min-height: 80vh;
  padding: 24px;
}

.loading-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60vh;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 900;
  text-align: center;
  margin-bottom: 40px;
  background: linear-gradient(135deg, #7CB342 0%, #558B2F 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
}

.admin-hint {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  color: #666;
}

.tournament-list {
  max-width: 1200px;
  margin: 0 auto;
}

.tournament-section {
  margin-bottom: 48px;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 20px;
  color: #333;
}

.tournament-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.tournament-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 2px solid transparent;
}

.tournament-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.tournament-card.active {
  border-color: #7CB342;
}

.tournament-card.active:hover {
  box-shadow: 0 8px 24px rgba(124, 179, 66, 0.3);
}

.tournament-card.setup {
  border-color: #FFCA28;
}

.tournament-card.setup:hover {
  box-shadow: 0 8px 24px rgba(255, 202, 40, 0.3);
}

.tournament-card.completed {
  border-color: #E0E0E0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.tournament-name {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  flex: 1;
  color: #333;
}

.card-body {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #F5F5F5;
}

.info-row .label {
  color: #999;
  font-size: 0.9rem;
}

.info-row .value {
  font-weight: 500;
  color: #333;
}

.status-active {
  color: #7CB342;
  font-weight: 700;
}

.status-setup {
  color: #FFCA28;
  font-weight: 700;
}

.status-completed {
  color: #9E9E9E;
  font-weight: 700;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
