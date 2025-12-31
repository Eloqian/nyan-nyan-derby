<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  NTabs, NTabPane, NMenu, NDataTable, NCard, NTag, NButton, NModal, NCheckbox, NAlert, NDivider, NSpin, NEmpty, NSpace, NText, useMessage, NInputGroup, NInput
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { getStageMatchesView, submitMatchResult } from '../api/stages'
import { updateRoomNumber } from '../api/matches'

const API_BASE_URL = '/api/v1'
const auth = useAuthStore()
const message = useMessage()

// Data State
const stages = ref<any[]>([])
const activeStageId = ref<string>('')
const activeGroupData = ref<any[]>([])
const activeGroupId = ref<string>('')
const loading = ref(false)

// Init
onMounted(async () => {
   try {
     const res = await fetch(`${API_BASE_URL}/stages/`)
     if (res.ok) {
        stages.value = await res.json()
        if (stages.value.length > 0) {
           activeStageId.value = stages.value[0].id // Default to first
           await loadStageData(activeStageId.value)
        }
     }
   } catch (e) {
      console.error(e)
   }
})

// Stage Logic
const loadStageData = async (stageId: string) => {
   loading.value = true
   try {
      activeGroupData.value = await getStageMatchesView(stageId)
      if (activeGroupData.value.length > 0) {
         activeGroupId.value = activeGroupData.value[0].id
      }
   } catch (e) {
      message.error("Failed to load stage data")
   } finally {
      loading.value = false
   }
}

// Navigation Logic
const groupMenuOptions = computed(() => {
   return activeGroupData.value.map(g => ({
      label: g.name,
      key: g.id
   }))
})

const handleGroupChange = (key: string) => {
   activeGroupId.value = key
}

const currentGroup = computed(() => {
   return activeGroupData.value.find(g => g.id === activeGroupId.value)
})

// Table Config
const standingsColumns: DataTableColumns = [
   { title: 'Rank', key: 'rank', width: 60 },
   { title: 'Player', key: 'player_name' },
   { title: 'Pts', key: 'total_points', sorter: 'default' },
   { title: 'Wins', key: 'wins' }
]

// Match Helpers
const getStatusType = (status: string) => {
   if (status === 'finished') return 'success'
   if (status === 'active') return 'warning'
   return 'default'
}

const getSortedResults = (results: any[]) => {
   return [...results].sort((a,b) => a.rank - b.rank)
}

const getPlayerName = (match: any, playerId: string) => {
   const p = match.participants.find((mp: any) => mp.player.id === playerId)
   return p ? p.player.name : 'Unknown'
}

const canEdit = () => {
   return auth.isAuthenticated
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
   })
   selectionState.value = state
   showModal.value = true
}

const isRankSelected = (pid: string, rank: number) => {
   return selectionState.value[pid]?.includes(rank)
}

const isRankDisabled = (pid: string, rank: number) => {
   const state = selectionState.value
   const currentList = state[pid] || []
   
   for (const otherPid in state) {
      if (otherPid !== pid && state[otherPid]?.includes(rank)) return true
   }
   
   if (!currentList.includes(rank) && currentList.length >= 3) return true
   return false
}

const toggleRank = (pid: string, rank: number, checked: boolean) => {
   if (!selectionState.value[pid]) selectionState.value[pid] = []
   if (checked) {
      selectionState.value[pid].push(rank)
   } else {
      selectionState.value[pid] = selectionState.value[pid].filter(r => r !== rank)
   }
}

const getProjectedScore = (pid: string) => {
   const ranks = selectionState.value[pid] || []
   const pointsMap: Record<number, number> = { 1:9, 2:5, 3:3, 4:2, 5:1 }
   let total = 0
   ranks.forEach(r => total += (pointsMap[r] || 0))
   return total
}

const getOrdinal = (n: number) => {
   const s = ["th", "st", "nd", "rd"]
   const v = n % 100
   return s[(v - 20) % 10] || s[v] || s[0]
}

const isValidResult = computed(() => {
   const allRanks: number[] = []
   Object.values(selectionState.value).forEach(list => allRanks.push(...list))
   if (allRanks.length !== 5) return false
   const set = new Set(allRanks)
   return set.size === 5 && set.has(1) && set.has(5)
})

const submitResult = async () => {
   if (!editingMatch.value) return
   submitting.value = true
   
   const rankings: any[] = []
   for (const [pid, ranks] of Object.entries(selectionState.value)) {
      ranks.forEach(r => {
         rankings.push({ player_id: pid, rank: r })
      })
   }
   
   try {
      await submitMatchResult(auth.token!, editingMatch.value.id, rankings)
      message.success("Result Saved!")
      showModal.value = false
      await loadStageData(activeStageId.value)
   } catch (e) {
      message.error("Failed to save")
   } finally {
      submitting.value = false
   }
}

// --- Room Number Logic ---
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
      message.success("Room number updated")
      showRoomModal.value = false
      await loadStageData(activeStageId.value)
   } catch (e) {
      message.error("Failed to update room")
   } finally {
      updatingRoom.value = false
   }
}
</script>

<template>
  <div class="live-container">
    <div class="header-section">
      <h2>🔴 Live Tournament Center</h2>
      <n-text depth="3">Real-time updates & results</n-text>
    </div>

    <n-tabs type="card" v-model:value="activeStageId" @update:value="loadStageData">
      <n-tab-pane v-for="stage in stages" :key="stage.id" :name="stage.id" :tab="stage.name" />
    </n-tabs>

    <div v-if="loading" class="loading-area">
      <n-spin size="large" />
    </div>

    <div v-else-if="activeGroupData.length > 0" class="content-split">
      <!-- Left: Group List -->
      <div class="group-sidebar">
        <n-menu 
          :options="groupMenuOptions" 
          v-model:value="activeGroupId"
          @update:value="handleGroupChange"
        />
      </div>

      <!-- Right: Detail View -->
      <div class="group-detail">
        <div v-if="currentGroup" class="detail-wrapper">
          <div class="group-header">
            <h3>{{ currentGroup.name }} Standings</h3>
          </div>
          
          <!-- Standings Table -->
          <n-data-table 
            :columns="standingsColumns" 
            :data="currentGroup.standings" 
            size="small"
            :single-line="false"
          />

          <n-divider />

          <!-- Match List -->
          <h3>Matches</h3>
          <div class="matches-list">
             <div v-for="match in currentGroup.matches" :key="match.id" class="match-item">
               <n-card size="small" :bordered="true">
                 <div class="match-row">
                    <div class="match-info">
                       <strong>{{ match.name }}</strong>
                       <n-tag :type="getStatusType(match.status)" size="tiny" style="margin-left: 8px">
                         {{ match.status }}
                       </n-tag>
                    </div>
                    
                    <div class="action-area" v-if="canEdit()">
                       <n-space>
                          <!-- Room Button -->
                          <n-button 
                             size="small" 
                             :type="match.room_number ? 'default' : 'warning'" 
                             dashed 
                             @click="openRoomModal(match)"
                          >
                             <template v-if="match.room_number">🏠 {{ match.room_number }}</template>
                             <template v-else>🏠 Set Room</template>
                          </n-button>

                          <n-button size="small" type="primary" secondary @click="openResultModal(match)">
                            📝 Result
                          </n-button>
                       </n-space>
                    </div>
                 </div>
                 
                 <!-- Simple Result Preview -->
                 <div v-if="match.results && match.results.length > 0" class="result-preview">
                    <n-space>
                       <n-tag v-for="res in getSortedResults(match.results)" :key="res.player_id" size="small" :color="{ color: '#fafafa', textColor: '#333', borderColor: '#eee' }">
                          <template #icon>
                             <span style="font-weight:bold; color:#fbc02d" v-if="res.rank===1">🥇</span>
                             <span style="font-weight:bold; color:#9e9e9e" v-else-if="res.rank===2">🥈</span>
                             <span style="font-weight:bold; color:#a1887f" v-else-if="res.rank===3">🥉</span>
                             <span v-else>{{ res.rank }}.</span>
                          </template>
                          {{ getPlayerName(match, res.player_id) }} (+{{ res.points }})
                       </n-tag>
                    </n-space>
                 </div>
               </n-card>
             </div>
          </div>
        </div>
      </div>
    </div>
    
    <n-empty v-else description="No groups data available" />

    <!-- Result Input Modal -->
    <n-modal v-model:show="showModal" preset="card" title="Update Match Result" style="width: 600px">
       <div v-if="editingMatch">
          <n-alert type="info" style="margin-bottom: 16px">
             Tick the rank obtained by each player. <br>
             Rule: 1st(9pts), 2nd(5pts), 3rd(3pts), 4th(2pts), 5th(1pts). <br>
             Each player has 3 horses. Total 5 ranks to assign.
          </n-alert>

          <table class="matrix-table">
             <thead>
                <tr>
                   <th>Player</th>
                   <th v-for="r in 5" :key="r">{{ r }}{{ getOrdinal(r) }}</th>
                </tr>
             </thead>
             <tbody>
                <tr v-for="p in editingMatch.participants" :key="p.player.id">
                   <td class="player-cell">
                      <strong>{{ p.player.name }}</strong>
                      <div class="live-score">
                         Current: {{ getProjectedScore(p.player.id) }} pts
                      </div>
                   </td>
                   <td v-for="r in 5" :key="r" class="check-cell">
                      <n-checkbox 
                         :checked="isRankSelected(p.player.id, r)"
                         @update:checked="(v) => toggleRank(p.player.id, r, v)"
                         :disabled="isRankDisabled(p.player.id, r)"
                      />
                   </td>
                </tr>
             </tbody>
          </table>
          
          <div class="modal-footer" style="margin-top: 24px; display: flex; justify-content: flex-end; gap: 12px;">
             <n-button @click="showModal = false">Cancel</n-button>
             <n-button type="primary" @click="submitResult" :loading="submitting" :disabled="!isValidResult">
                Confirm & Save
             </n-button>
          </div>
       </div>
    </n-modal>

    <!-- Room Number Modal -->
    <n-modal v-model:show="showRoomModal" preset="card" title="Update Room Number" style="width: 400px">
       <n-input-group>
          <n-input v-model:value="roomInput" placeholder="Enter Room ID" autofocus />
          <n-button type="primary" @click="saveRoomNumber" :loading="updatingRoom">Save</n-button>
       </n-input-group>
    </n-modal>

  </div>
</template>

<style scoped>
.live-container {
   max-width: 1200px;
   margin: 0 auto;
   padding: 16px;
}
.header-section {
   margin-bottom: 24px;
}
.content-split {
   display: flex;
   gap: 24px;
   min-height: 500px;
}
.group-sidebar {
   width: 200px;
   border-right: 1px solid #eee;
}
.group-detail {
   flex: 1;
}
.matches-list {
   display: flex;
   flex-direction: column;
   gap: 12px;
   margin-top: 12px;
}
.match-row {
   display: flex;
   justify-content: space-between;
   align-items: center;
}
.result-preview {
   margin-top: 12px;
   padding-top: 12px;
   border-top: 1px dashed #eee;
}

/* Matrix Table */
.matrix-table {
   width: 100%;
   border-collapse: collapse;
}
.matrix-table th, .matrix-table td {
   border: 1px solid #eee;
   padding: 12px;
   text-align: center;
}
.matrix-table th {
   background: #f9f9f9;
}
.player-cell {
   text-align: left;
   width: 180px;
}
.live-score {
   font-size: 0.8em;
   color: #7CB342;
   font-weight: bold;
}
.check-cell {
   cursor: pointer;
}
.check-cell:hover {
   background: #f5f5f5;
}
</style>
