<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { 
  useMessage, NSpin, NModal, NCheckbox, NInputGroup, NInput, NButton
} from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { getStageMatchesView, submitMatchResult } from '../api/stages'
import { updateRoomNumber } from '../api/matches'
import { getCurrentTournament, listTournaments, type Tournament } from '../api/tournaments'
import PreTournament from '../components/PreTournament.vue'

const auth = useAuthStore()
const message = useMessage()
const route = useRoute()
const { t } = useI18n()

// Data State
const tournament = ref<Tournament | null>(null)
const stages = ref<any[]>([])
const activeStageId = ref<string>('')
const activeGroupData = ref<any[]>([])
const activeGroupId = ref<string>('')
const loading = ref(false)
const stageLoading = ref(false)

// Init
onMounted(async () => {
   try {
     loading.value = true
     const tournamentId = route.params.tournamentId as string | undefined
     
     if (tournamentId) {
        const all = await listTournaments()
        tournament.value = all.find(t => t.id === tournamentId) || null
     } else {
        tournament.value = await getCurrentTournament()
     }

     if (!tournament.value) {
        loading.value = false
        return
     }

     // Fetch Stages
     let url = `/api/v1/stages/`
     if (tournament.value.id) {
       url += `?tournament_id=${tournament.value.id}`
     }
     
     const res = await fetch(url)
     if (res.ok) {
        const fetchedStages = await res.json()
        // Inject "INFO" tab
        stages.value = [{ id: 'info', name: 'INFO', status: 'always' }, ...fetchedStages]
        
        if (fetchedStages.length > 0) {
           // If we have stages, try to find active one, otherwise stay on info or first stage?
           // Actually, if a stage is active, better to show it. If not, show Info.
           const activeOrFirst = fetchedStages.find((s: any) => s.status === 'active')
           if (activeOrFirst) {
              activeStageId.value = activeOrFirst.id
           } else {
              activeStageId.value = 'info'
           }
        } else {
           activeStageId.value = 'info'
        }
     }
   } catch (e) {
      console.error(e)
   } finally {
      loading.value = false
   }
})

// Watch stage change to load data
watch(activeStageId, (newId) => {
  if (newId && newId !== 'info') loadStageData(newId)
})

const loadStageData = async (stageId: string) => {
   stageLoading.value = true
   try {
      activeGroupData.value = await getStageMatchesView(stageId)
      // Default select first group if not set or invalid
      if (activeGroupData.value.length > 0) {
         // Try to keep current group selection if valid, else first
         if (!activeGroupId.value || !activeGroupData.value.find(g => g.id === activeGroupId.value)) {
            activeGroupId.value = activeGroupData.value[0].id
         }
      } else {
         activeGroupId.value = ''
      }
   } catch (e) {
      message.error("Failed to load stage data")
   } finally {
      stageLoading.value = false
   }
}

const currentGroup = computed(() => {
   return activeGroupData.value.find(g => g.id === activeGroupId.value) || activeGroupData.value[0]
})

const currentStage = computed<any>(() => stages.value.find(s => s.id === activeStageId.value))

const isElimination = computed(() => {
  // @ts-ignore
  return (currentStage.value as any)?.stage_type?.includes('elimination') ?? false
})

// --- Helpers ---
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

const getStageName = (name: string) => {
  if (!name) return ''
  const lower = name.toLowerCase().trim()
  if (lower === 'info') return t('stages.info', 'INFO')
  if (lower.includes('audition')) return t('stages.audition', name)
  if (lower === 'group stage 1' || lower === 'group stage round 1') return t('stages.group_stage_1', name)
  if (lower === 'group stage 2' || lower === 'group stage round 2') return t('stages.group_stage_2', name)
  if (lower.includes('bracket') || lower.includes('elimination')) return t('stages.bracket_stage', name)
  return name
}

// --- Matrix Editing Logic ---
const showModal = ref(false)
const editingMatch = ref<any>(null)
const selectionState = ref<Record<string, number[]>>({})
const submitting = ref(false)

const openResultModal = (match: any) => {
   editingMatch.value = match
   const state: Record<string, number[]> = {}
   match.participants.forEach((p: any) => {
      state[p.player.id] = []
      // Pre-fill existing results
      match.results?.forEach((r: any) => {
        if (r.player_id === p.player.id) {
             state[p.player.id]!.push(r.rank)
        }
      })
   })
   selectionState.value = state
   showModal.value = true
}

// @ts-ignore
const isRankSelected = (pid: string, rank: number) => {
  const list = selectionState.value[pid]
  return list ? list.includes(rank) : false
}

const toggleRank = (pid: string, rank: number, checked: boolean) => {
   if (!selectionState.value[pid]) selectionState.value[pid] = []
   if (checked) {
      // Ensure single selection for rank if needed, but logic allows multiple for now
      // Let's enforce unique rank per match? No, let admin decide.
      selectionState.value[pid]!.push(rank)
   } else {
      selectionState.value[pid] = selectionState.value[pid]!.filter(r => r !== rank)
   }
}

const submitResult = async () => {
   if (!editingMatch.value) return
   submitting.value = true
   const rankings: any[] = []
   for (const [pid, ranks] of Object.entries(selectionState.value)) {
      ranks.forEach(r => rankings.push({ player_id: pid, rank: r }))
   }
   try {
      await submitMatchResult(auth.token!, editingMatch.value.id, rankings)
      message.success("Result Saved")
      showModal.value = false
      await loadStageData(activeStageId.value)
   } catch (e) {
      message.error("Failed to save")
   } finally {
      submitting.value = false
   }
}

// --- Room Logic ---
const showRoomModal = ref(false)
const editingRoomMatch = ref<any>(null)
const roomInput = ref('')
const updatingRoom = ref(false)

const openRoomModal = (match: any) => {
   editingRoomMatch.value = match
   roomInput.value = match.room_number || ''
   showRoomModal.value = true
}

const saveRoomNumber = async () => {
   if (!editingRoomMatch.value || !auth.token) return
   updatingRoom.value = true
   try {
      await updateRoomNumber(auth.token, editingRoomMatch.value.id, roomInput.value)
      message.success("Room Updated")
      showRoomModal.value = false
      await loadStageData(activeStageId.value)
   } catch (e) {
      message.error("Failed")
   } finally {
      updatingRoom.value = false
   }
}
</script>

<template>
  <div class="live-screen-container">
    
    <!-- Hero Header (Compact & Flat) -->
    <div class="tournament-hero-compact">
       <div class="hero-overlay"></div>
       <div class="hero-content-compact">
          <div class="hero-left">
             <div class="status-row">
                <span class="live-badge" v-if="tournament?.status === 'active'">
                   <span class="pulse-dot"></span> LIVE NOW
                </span>
                <span class="date-badge">{{ formatDate(tournament?.created_at || '') }}</span>
             </div>
             <h1 class="hero-title-compact">{{ tournament?.name || 'Tournament' }}</h1>
          </div>
          <div class="hero-right">
             <div class="hero-subtitle-compact">{{ t('nav.live_subtitle', 'Official Match Center') }}</div>
          </div>
       </div>
    </div>

    <!-- Stage Navigation (Sticky Tabs) -->
    <div class="stage-nav-bar">
       <div class="nav-scroll-container">
          <div 
             v-for="(stage, index) in stages" 
             :key="stage.id" 
             class="nav-tab"
             :class="{ active: activeStageId === stage.id }"
             @click="activeStageId = stage.id"
          >
             <span class="tab-idx">{{ index + 1 }}</span>
             <span class="tab-name">{{ getStageName(stage.name) }}</span>
          </div>
       </div>
    </div>

    <!-- Main Content (Full Width) -->
    <div class="content-wrapper" v-if="!loading && activeStageId !== 'info'">
       
       <!-- Group Tabs (If multiple) -->
       <div v-if="activeGroupData.length > 1" class="group-filter-bar">
          <button 
             v-for="g in activeGroupData" 
             :key="g.id"
             class="group-filter-btn"
             :class="{ active: activeGroupId === g.id }"
             @click="activeGroupId = g.id"
          >
             {{ g.name }}
          </button>
       </div>

       <!-- Active View -->
       <div v-if="currentGroup" class="stage-view-layout">
          
          <!-- LEFT: Standings (Fixed Width) -->
          <div class="layout-sidebar">
             <div class="standings-panel-modern">
                <div class="panel-header-modern">
                   <span class="icon">🏆</span> RANKING
                </div>
                <div class="standings-list-modern custom-scroll">
                   <div 
                      v-for="p in currentGroup.standings" 
                      :key="p.player_id" 
                      class="standing-item"
                      :class="{'top-rank': p.rank <= 3}"
                   >
                      <div class="rank-num">{{ p.rank }}</div>
                      <div class="p-info">
                         <div class="p-name">{{ p.player_name }}</div>
                         <div class="p-stats">{{ p.wins }} Wins</div>
                      </div>
                      <div class="p-points">{{ p.total_points }} <small>pts</small></div>
                   </div>
                </div>
             </div>
          </div>

          <!-- RIGHT: Matches (Flexible Grid) -->
          <div class="layout-main">
             
             <!-- ELIMINATION / KNOCKOUT STYLE (Special Design) -->
             <div v-if="isElimination" class="knockout-section">
                <div class="section-title">
                   <span class="icon">⚔️</span> ELIMINATION STAGE
                </div>
                <div class="knockout-track">
                   <div v-for="match in currentGroup.matches" :key="match.id" class="knockout-duel-card">
                      <div class="duel-header">
                         <span class="match-name">{{ match.name }}</span>
                         <div class="room-indicator" v-if="match.room_number" @click="openRoomModal(match)">
                            ROOM: <strong>{{ match.room_number }}</strong>
                         </div>
                         <div class="room-indicator empty" v-else-if="auth.isAuthenticated" @click="openRoomModal(match)">
                            + ROOM
                         </div>
                         <div class="status-badge" :class="match.status">{{ match.status }}</div>
                      </div>
                      
                      <div class="duel-arena">
                         <!-- 3-Way Battle Layout -->
                         <div class="duel-competitors">
                            <div 
                               v-for="p in match.participants" 
                               :key="p.player.id"
                               class="competitor-slot"
                               :class="{ 
                                  'winner': match.results.some((r: any) => r.player_id === p.player.id && r.rank === 1),
                                  'is-host': match.host_player_id === p.player.id
                               }"
                            >
                               <div class="slot-rank" v-if="match.status === 'finished'">
                                  {{ match.results.find((r:any) => r.player_id === p.player.id)?.rank || '-' }}
                               </div>
                               <div class="slot-avatar">
                                  {{ p.player.name.charAt(0) }}
                               </div>
                               <div class="slot-info">
                                  <div class="c-name">{{ p.player.name }}</div>
                               </div>
                            </div>
                         </div>
                      </div>

                      <div class="duel-actions" v-if="auth.isAuthenticated">
                         <button class="action-btn" @click="openResultModal(match)">UPDATE RESULT</button>
                      </div>
                   </div>
                </div>
             </div>

             <!-- REGULAR / GROUP STYLE -->
             <div v-else class="regular-section">
                <div class="section-title">
                   <span class="icon">🏁</span> MATCH LIST
                </div>
                <div class="regular-grid">
                   <div v-for="match in currentGroup.matches" :key="match.id" class="match-card-modern" :class="match.status">
                      <div class="card-status-strip" :class="match.status"></div>
                      <div class="m-header">
                         <span class="m-title">{{ match.name }}</span>
                         <span 
                            class="m-room" 
                            :class="{'has-room': match.room_number}" 
                            @click="openRoomModal(match)"
                         >
                            {{ match.room_number ? `🔑 ${match.room_number}` : 'No Room' }}
                         </span>
                      </div>
                      
                      <div class="m-body">
                         <div 
                            v-for="p in match.participants" 
                            :key="p.player.id" 
                            class="m-player"
                            :class="{ 'host': match.host_player_id === p.player.id }"
                         >
                            <div class="mp-avatar">{{ p.player.name.charAt(0) }}</div>
                            <div class="mp-name">{{ p.player.name }}</div>
                            <div class="mp-rank" v-if="match.status === 'finished'">
                               #{{ match.results.find((r:any) => r.player_id === p.player.id)?.rank }}
                            </div>
                         </div>
                      </div>

                      <div class="m-footer" v-if="auth.isAuthenticated">
                         <button class="m-btn" @click="openResultModal(match)">Record</button>
                      </div>
                   </div>
                </div>
             </div>

          </div>

       </div>

    </div>

    <!-- INFO / PRE-TOURNAMENT TAB -->
    <div v-else-if="activeStageId === 'info'" class="pre-tournament-wrapper">
       <PreTournament :tournament="tournament" />
    </div>
    
    <div v-if="stageLoading" class="loading-overlay">
       <n-spin size="large" stroke="#67C05D" />
    </div>

    <!-- Modals -->
    <n-modal v-model:show="showModal" preset="card" title="Update Result" style="width: 500px">
       <div v-if="editingMatch">
          <div class="modal-rows">
             <div v-for="p in editingMatch.participants" :key="p.player.id" class="m-row">
                <span class="name">{{ p.player.name }}</span>
                <div class="checks">
                   <n-checkbox v-for="r in 5" :key="r" :label="String(r)" 
                      :checked="isRankSelected(p.player.id, r)"
                      @update:checked="(v) => toggleRank(p.player.id, r, v)"
                   />
                </div>
             </div>
          </div>
          <div style="text-align: right; margin-top: 20px;">
             <n-button type="primary" @click="submitResult" :loading="submitting">Confirm Result</n-button>
          </div>
       </div>
    </n-modal>

    <n-modal v-model:show="showRoomModal" preset="card" title="Room Number" style="width: 400px">
       <n-input-group>
          <n-input v-model:value="roomInput" placeholder="Enter Room ID" />
          <n-button type="primary" @click="saveRoomNumber" :loading="updatingRoom">Save</n-button>
       </n-input-group>
    </n-modal>

  </div>
</template>

<style scoped>
/* --- Container --- */
.live-screen-container {
  width: 100%;
  min-height: 100vh;
  background-color: transparent;
  padding-bottom: 80px;
}

/* --- Hero Section (Compact) --- */
.tournament-hero-compact {
  height: 160px;
  width: 100%;
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 4rem;
  background: linear-gradient(135deg, #ffffff 0%, #e3f2fd 100%);
  overflow: hidden;
  border-bottom: 1px solid rgba(255,255,255,0.5);
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.hero-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: 
    linear-gradient(45deg, rgba(103, 192, 93, 0.05) 25%, transparent 25%), 
    linear-gradient(-45deg, rgba(103, 192, 93, 0.05) 25%, transparent 25%);
  background-size: 60px 60px;
  z-index: 0;
}
.hero-content-compact {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hero-left { display: flex; flex-direction: column; justify-content: center; gap: 8px; }

.hero-title-compact {
  font-size: 2.5rem;
  font-weight: 900;
  font-style: italic;
  color: var(--uma-blue);
  margin: 0;
  text-shadow: 2px 2px 0px white, 3px 3px 0px rgba(0,0,0,0.05);
  line-height: 1;
  text-transform: uppercase;
}
.hero-subtitle-compact {
  font-size: 1rem;
  font-weight: 700;
  color: #777;
  background: rgba(255,255,255,0.6);
  padding: 4px 16px;
  border-radius: 20px;
}
.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.live-badge {
  background: #FF5252;
  color: white;
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 800;
  font-size: 0.75rem;
  display: flex; align-items: center; gap: 6px;
}
.pulse-dot {
  width: 6px; height: 6px; background: white; border-radius: 50%;
  animation: pulse 1.5s infinite;
}
.date-badge {
  background: #444;
  color: white;
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.75rem;
}
@media (max-width: 768px) {
  .tournament-hero-compact { padding: 1rem 1.5rem; height: auto; }
  .hero-content-compact { flex-direction: column; align-items: flex-start; gap: 1rem; }
}

/* --- Stage Navigation --- */
.stage-nav-bar {
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  position: sticky;
  top: 0; /* Or 64px if header is fixed */
  z-index: 10;
  padding: 0 1rem;
}
.nav-scroll-container {
  display: flex;
  justify-content: center;
  max-width: 1800px;
  margin: 0 auto;
  overflow-x: auto;
  gap: 2rem;
}
.nav-tab {
  padding: 1rem 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #999;
  border-bottom: 4px solid transparent;
  transition: all 0.2s;
}
.nav-tab:hover { color: #555; }
.nav-tab.active {
  color: var(--uma-blue);
  border-bottom-color: var(--uma-blue);
}
.tab-idx {
  background: #eee;
  width: 24px; height: 24px;
  border-radius: 50%;
  display: flex; justify-content: center; align-items: center;
  font-size: 0.75rem; font-weight: bold;
}
.nav-tab.active .tab-idx {
  background: var(--uma-blue);
  color: white;
}
.tab-name { font-weight: 800; font-size: 1rem; text-transform: uppercase; }

/* --- Content Wrapper --- */
.content-wrapper {
  width: 100%;
  max-width: 1800px; /* Match Home Page width */
  margin: 0 auto;
  padding: 2rem;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .content-wrapper { padding: 1rem; }
  .group-filter-bar { gap: 8px; }
  .group-filter-btn { padding: 6px 16px; font-size: 0.9rem; }
}

/* Filter Bar */
.group-filter-bar {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.group-filter-btn {
  background: rgba(255,255,255,0.7);
  border: 2px solid transparent;
  padding: 8px 24px;
  border-radius: 20px;
  font-weight: 700;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(5px);
}
.group-filter-btn:hover { background: white; }
.group-filter-btn.active {
  background: white;
  border-color: var(--uma-blue);
  color: var(--uma-blue);
  box-shadow: 0 4px 10px rgba(79, 179, 255, 0.2);
}

/* Layout Grid */
.stage-view-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 2rem;
  align-items: start;
}
@media (max-width: 1024px) {
  .stage-view-layout { grid-template-columns: 1fr; }
  .layout-sidebar { display: none; /* Hide standings on mobile for now or move to bottom */ }
}

/* Sidebar (Standings) */
.standings-panel-modern {
  background: rgba(255,255,255,0.9);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.6);
}
.panel-header-modern {
  background: linear-gradient(90deg, #3E3838 0%, #555 100%);
  color: white;
  padding: 1rem;
  font-weight: 900;
  font-style: italic;
  display: flex; align-items: center; gap: 8px;
  font-size: 1.1rem;
}
.standings-list-modern {
  max-height: calc(100vh - 300px);
  overflow-y: auto;
  padding: 0.5rem;
}
.standing-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: background 0.2s;
}
.standing-item:hover { background: rgba(0,0,0,0.02); }
.standing-item.top-rank { background: linear-gradient(90deg, rgba(255, 200, 0, 0.1), transparent); }
.rank-num {
  width: 28px; height: 28px;
  background: #eee;
  color: #888;
  border-radius: 6px;
  display: flex; justify-content: center; align-items: center;
  font-weight: 800;
  margin-right: 12px;
}
.top-rank .rank-num { background: var(--uma-gold); color: #3E3838; }
.p-info { flex: 1; }
.p-name { font-weight: bold; font-size: 0.95rem; color: #333; }
.p-stats { font-size: 0.75rem; color: #999; }
.p-points { font-weight: 900; font-size: 1.1rem; color: var(--uma-green); text-align: right; }

/* Main Content Section Styles */
.section-title {
  font-size: 1.5rem;
  font-weight: 900;
  color: #3E3838;
  margin-bottom: 1.5rem;
  display: flex; align-items: center; gap: 8px;
  opacity: 0.8;
}

/* --- Regular Matches Grid --- */
.regular-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}
.match-card-modern {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  border: 1px solid #f0f0f0;
}
.match-card-modern:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.1);
}
.card-status-strip { height: 4px; width: 100%; background: #eee; }
.card-status-strip.active { background: #FF5252; }
.card-status-strip.finished { background: var(--uma-green); }

.m-header {
  padding: 12px 16px;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px dashed #f0f0f0;
}
.m-title { font-weight: 800; font-size: 0.9rem; color: #888; }
.m-room {
  font-size: 0.75rem; padding: 2px 8px; border-radius: 12px;
  background: #f5f5f5; color: #bbb; cursor: pointer; font-weight: bold;
}
.m-room.has-room { background: var(--uma-blue); color: white; }

.m-body { padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.m-player {
  display: flex; align-items: center; gap: 10px;
  padding: 6px; border-radius: 8px;
}
.m-player.host { background: rgba(0,0,0,0.02); border: 1px solid #eee; }
.mp-avatar {
  width: 32px; height: 32px;
  background: #ddd; border-radius: 50%;
  display: flex; justify-content: center; align-items: center;
  font-weight: bold; color: #555;
  font-size: 0.8rem;
}
.mp-name { font-weight: bold; font-size: 0.95rem; color: #444; flex: 1; }
.mp-rank { font-weight: 900; font-size: 1.1rem; color: #333; }

.m-footer { padding: 12px; text-align: center; background: #fcfcfc; border-top: 1px solid #f0f0f0; }
.m-btn {
  background: var(--uma-green); color: white; border: none;
  padding: 6px 20px; border-radius: 20px; font-weight: bold; cursor: pointer;
  font-size: 0.85rem;
}

/* --- Elimination / Knockout (3-Way) --- */
.knockout-track {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 2rem;
}
.knockout-duel-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  overflow: hidden;
  border: 1px solid rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}
.duel-header {
  background: #222;
  color: white;
  padding: 12px 20px;
  display: flex; justify-content: space-between; align-items: center;
}
.match-name { font-weight: 900; font-size: 1rem; color: #ddd; }
.room-indicator {
  background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 4px; font-size: 0.8rem; cursor: pointer;
}
.room-indicator.empty { border: 1px dashed rgba(255,255,255,0.3); background: transparent; }
.status-badge {
  font-size: 0.7rem; font-weight: bold; text-transform: uppercase; padding: 2px 6px; border-radius: 4px; background: #444;
}
.status-badge.active { background: #FF5252; color: white; }
.status-badge.finished { background: var(--uma-green); color: white; }

.duel-arena {
  padding: 20px;
  background: linear-gradient(to bottom, #f9f9f9, white);
  flex: 1;
}
.duel-competitors {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}
/* Connectors could be added here */
.competitor-slot {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: white;
  border: 1px solid #eee;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.03);
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}
.competitor-slot.winner {
  border-color: var(--uma-gold);
  background: #FFFDE7;
  transform: scale(1.02);
  z-index: 2;
  box-shadow: 0 4px 12px rgba(255, 200, 0, 0.2);
}
.competitor-slot.winner::after {
  content: '🏆';
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.5rem;
  opacity: 0.2;
}

.slot-rank {
  font-size: 1.5rem; font-weight: 900; color: #ccc; width: 30px; text-align: center;
}
.competitor-slot.winner .slot-rank { color: var(--uma-gold); }

.slot-avatar {
  width: 40px; height: 40px; background: #eee; border-radius: 50%;
  display: flex; justify-content: center; align-items: center;
  font-weight: bold; color: #666; font-size: 1rem;
}
.slot-info { flex: 1; }
.c-name { font-weight: 800; font-size: 1.1rem; color: #333; }

.duel-actions {
  padding: 12px; text-align: center; border-top: 1px solid #eee;
}
.action-btn {
  background: #333; color: white; border: none; padding: 8px 24px; border-radius: 6px;
  font-weight: bold; cursor: pointer; width: 100%;
  transition: background 0.2s;
}
.action-btn:hover { background: #555; }

/* Empty State */
.empty-state-modern {
  height: 50vh;
  display: flex; justify-content: center; align-items: center;
}
.empty-content {
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(10px);
  padding: 3rem;
  border-radius: 20px;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
}
.empty-content h2 { margin-top: 0; color: var(--uma-blue); }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
