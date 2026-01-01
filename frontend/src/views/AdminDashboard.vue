<template>
  <div class="admin-container">
    <div class="sidebar">
       <div class="sidebar-header">
          <h3>{{ t('admin.dashboard_title') }}</h3>
          <n-button type="primary" size="small" @click="showCreateModal = true" block>
             {{ t('admin.create_new') }}
          </n-button>
       </div>
       <div v-if="loadingTournaments" class="loading-state-mini">
          <n-spin size="small" />
       </div>
       <n-menu
          v-else
          :options="tournamentOptions"
          :value="selectedTournamentId"
          @update:value="handleTournamentSelect"
       />
    </div>

    <div class="main-content">
       <div v-if="!selectedTournamentId" class="empty-selection">
          <n-empty :description="t('admin.select_tournament_hint')">
          </n-empty>
       </div>
       
       <n-card v-else :title="selectedTournament?.name || 'Tournament'">
         <n-tabs type="line">
           
           <n-tab-pane name="control" :tab="t('admin.tournament_control')">
              <div class="control-panel">
                 <div class="status-card">
                    <div class="info">
                       <n-tag :type="getStatusType(selectedTournament?.status || 'setup')">
                          {{ (selectedTournament?.status || '').toUpperCase() }}
                       </n-tag>
                       <span style="margin-left: 12px; font-size: 0.9em; color: #999;">
                          ID: {{ selectedTournament?.id }}
                       </span>
                    </div>
                    
                    <div class="actions">
                       <n-text depth="3">{{ t('admin.flow_control') }}</n-text>
                       <n-button-group>
                          <n-button 
                             @click="updateStatus('setup')" 
                             :type="selectedTournament?.status === 'setup' ? 'primary' : 'default'"
                             :disabled="selectedTournament?.status === 'setup'"
                          >
                             {{ t('admin.setup') }}
                          </n-button>
                          <n-button 
                             @click="updateStatus('active')" 
                             :type="selectedTournament?.status === 'active' ? 'primary' : 'default'"
                             :disabled="selectedTournament?.status === 'active'"
                          >
                             {{ t('admin.start_active') }}
                          </n-button>
                          <n-button 
                             @click="updateStatus('completed')" 
                             :type="selectedTournament?.status === 'completed' ? 'primary' : 'default'"
                             :disabled="selectedTournament?.status === 'completed'"
                          >
                             {{ t('admin.end') }}
                          </n-button>
                       </n-button-group>
                    </div>
                 </div>
                 
                 <n-divider />
                 
                 <h3>{{ t('admin.stage_flow') }}</h3>
                 <div class="stages-list">
                    <n-card v-for="stage in stages" :key="stage.id" size="small" style="margin-bottom: 12px">
                       <div style="display: flex; justify-content: space-between; align-items: center;">
                          <div>
                             <strong>{{ stage.sequence_order }}. {{ stage.name }}</strong>
                             <div style="font-size: 0.8em; opacity: 0.7">{{ stage.stage_type }}</div>
                          </div>
                          
                          <n-space>
                             <n-button 
                                size="small" 
                                secondary 
                                type="info"
                                @click="handleSettle(stage.id)"
                             >
                                {{ t('admin.settle_next') }}
                             </n-button>
                          </n-space>
                       </div>
                    </n-card>
                 </div>

                 <n-divider />
                 
                 <n-alert :title="t('admin.quick_actions')" type="info">
                    <n-space>
                       <n-button secondary @click="$router.push('/ceremony?stageId=' + (stages[0]?.id || ''))">
                          {{ t('admin.go_draw') }}
                       </n-button>
                       <n-button secondary @click="$router.push('/tournament/' + selectedTournamentId)">
                          {{ t('admin.go_live') }}
                       </n-button>
                    </n-space>
                 </n-alert>
              </div>
           </n-tab-pane>

           <n-tab-pane name="roster" :tab="t('admin.roster_management')">
             <n-upload
               directory-dnd
               :custom-request="customRequest"
               accept=".csv"
             >
               <n-upload-dragger>
                 <div style="margin-bottom: 12px">
                   <n-icon size="48" :depth="3">
                     <archive-outline />
                   </n-icon>
                 </div>
                 <n-text style="font-size: 16px">
                   {{ t('admin.upload_instruction') }}
                 </n-text>
                 <n-p depth="3" style="margin: 8px 0 0 0">
                   {{ t('admin.upload_format') }}
                 </n-p>
               </n-upload-dragger>
             </n-upload>
           </n-tab-pane>
         </n-tabs>
       </n-card>
    </div>

    <!-- Create Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" :title="t('admin.create_modal_title')" style="width: 600px">
       <n-form label-placement="left" label-width="120">
          <n-form-item :label="t('admin.tournament_name')">
             <n-input v-model:value="newTourneyName" placeholder="e.g. Meow Cup 2025" />
          </n-form-item>
          
          <n-divider>{{ t('admin.rules_config') }}</n-divider>
          
          <n-form-item :label="t('admin.points_map')">
             <n-space vertical>
                <n-input-group v-for="i in 5" :key="i">
                   <n-button disabled style="width: 100px">{{ t('admin.rank_label', {rank: i}) }}</n-button>
                   <n-input-number v-model:value="pointsMap[i]" :min="0" />
                </n-input-group>
             </n-space>
          </n-form-item>

          <n-form-item :label="t('admin.prizes')">
             <n-dynamic-input v-model:value="prizes" placeholder="e.g. 200" />
          </n-form-item>
       </n-form>
       <template #footer>
          <div style="display: flex; justify-content: flex-end; gap: 12px;">
             <n-button @click="showCreateModal = false">{{ t('admin.cancel') }}</n-button>
             <n-button type="primary" @click="handleCreate" :disabled="!newTourneyName" :loading="creating">{{ t('admin.create') }}</n-button>
          </div>
       </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { 
  useMessage, NCard, NTabs, NTabPane, NUpload, NUploadDragger, NIcon, NText, NP, NEmpty, NButton, NTag, NButtonGroup, NDivider, NAlert, NSpace, NModal, NForm, NFormItem, NInput, NSpin, NInputNumber, NInputGroup, NDynamicInput, NMenu
} from 'naive-ui'
import { ArchiveOutline } from '@vicons/ionicons5'
import type { UploadCustomRequestOptions } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { listTournaments, createTournament, updateTournament, type Tournament } from '../api/tournaments'

const router = useRouter()
const message = useMessage()
const auth = useAuthStore()
const { t } = useI18n()

// State
const tournaments = ref<Tournament[]>([])
const selectedTournamentId = ref<string | null>(null)
const stages = ref<any[]>([])
const loadingTournaments = ref(true)
const showCreateModal = ref(false)
const newTourneyName = ref('')
const creating = ref(false)

// Config State
const pointsMap = ref<Record<number, number>>({ 1: 9, 2: 5, 3: 3, 4: 2, 5: 1 })
const prizes = ref<string[]>(['200', '160', '120'])

// Computed
const tournamentOptions = computed(() => {
   return tournaments.value.map(t => ({
      label: t.name,
      key: t.id,
      extra: t.status.toUpperCase() // Optional: show status in menu
   }))
})

const selectedTournament = computed(() => {
   return tournaments.value.find(t => t.id === selectedTournamentId.value) || null
})

// Lifecycle
onMounted(() => {
   fetchAllTournaments()
})

const fetchAllTournaments = async () => {
   loadingTournaments.value = true
   try {
      tournaments.value = await listTournaments()
      // Auto-select first if none selected
      if (!selectedTournamentId.value && tournaments.value.length > 0) {
         const first = tournaments.value[0]
         if (first) {
            selectedTournamentId.value = first.id
            await fetchStages(first.id)
         }
      } else if (selectedTournamentId.value) {
         await fetchStages(selectedTournamentId.value)
      }
   } catch (e) {
      console.error(e)
   } finally {
      loadingTournaments.value = false
   }
}

const handleTournamentSelect = async (key: string) => {
   selectedTournamentId.value = key
   await fetchStages(key)
}

const fetchStages = async (tourneyId: string) => {
   try {
      const res = await fetch(`/api/v1/stages/?tournament_id=${tourneyId}`)
      if (res.ok) {
         stages.value = await res.json()
      }
   } catch (e) {
      console.error(e)
   }
}

const handleSettle = async (stageId: string) => {
   // Call settle endpoint
   try {
      const res = await fetch(`/api/v1/stages/${stageId}/settle`, {
         method: 'POST',
         headers: { 'Authorization': `Bearer ${auth.token || ''}` }
      })
      if (!res.ok) throw new Error('Settle failed')
      
      const data = await res.json()
      if (data.next_stage_id) {
         message.success(t('admin.stage_complete', { stage: data.next_stage_name }))
         router.push(`/ceremony?stageId=${data.next_stage_id}`)
      } else {
         message.info(t('admin.tournament_complete'))
      }
   } catch (e) {
      message.error(t('admin.failed_settle'))
   }
}

// Actions
const getStatusType = (status: string) => {
   if (status === 'active') return 'success'
   if (status === 'setup') return 'warning'
   return 'default'
}

const handleCreate = async () => {
   if (!newTourneyName.value) return
   creating.value = true
   try {
      // Create with configured rules
      const payload = {
         name: newTourneyName.value,
         rules_config: { 
            "prizes": prizes.value,
            "points_map": pointsMap.value
         },
         stages_config: [
            { "name": "Audition", "stage_type": "round_robin", "rules_config": {"group_count": 14, "advancement": {"type": "top_n", "value": 4}} },
            { "name": "Group Stage 1", "stage_type": "round_robin", "rules_config": {"group_count": 13, "advancement": {"type": "top_n", "value": 4}} },
            { "name": "Group Stage 2", "stage_type": "round_robin", "rules_config": {"group_count": 9, "advancement": {"type": "position_map", "map": {"1": "winner", "2": "loser", "3": "loser"}}} },
            { "name": "Bracket Stage", "stage_type": "double_elimination", "rules_config": {} }
         ]
      }
      const newT = await createTournament(auth.token!, payload)
      message.success(t('admin.tournament_created'))
      showCreateModal.value = false
      await fetchAllTournaments()
      // Switch to new tournament
      selectedTournamentId.value = newT.id
      await fetchStages(newT.id)
   } catch (e) {
      message.error(t('admin.failed_create'))
   } finally {
      creating.value = false
   }
}

const updateStatus = async (status: string) => {
   if (!selectedTournamentId.value) return
   try {
      await updateTournament(auth.token!, selectedTournamentId.value, { status })
      message.success(t('admin.status_updated', { status }))
      await fetchAllTournaments()
   } catch (e) {
      message.error(t('admin.failed_update'))
   }
}

const customRequest = async ({ file, onFinish, onError }: UploadCustomRequestOptions) => {
  const formData = new FormData()
  formData.append('file', file.file as File)

  try {
    const res = await fetch('/api/v1/players/import', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${auth.token || ''}`
      },
      body: formData
    })

    if (res.ok) {
      const data = await res.json()
      message.success(data.message || t('admin.upload_success'))
      onFinish()
    } else {
      message.error(t('admin.upload_fail'))
      onError()
    }
  } catch (e) {
    message.error(t('admin.upload_fail'))
    onError()
  }
}
</script>

<style scoped>
.admin-container {
  display: flex;
  height: calc(100vh - 80px); /* Adjust based on navbar height */
  max-width: 1400px;
  margin: 0 auto;
  gap: 24px;
}

.sidebar {
   width: 250px;
   background: #fff;
   border-right: 1px solid #eee;
   display: flex;
   flex-direction: column;
   padding: 16px;
   border-radius: 8px;
   box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.sidebar-header {
   margin-bottom: 16px;
}

.sidebar-header h3 {
   margin: 0 0 12px 0;
   font-size: 1.2rem;
}

.main-content {
   flex: 1;
   overflow-y: auto;
}

.loading-state-mini {
   padding: 20px;
   text-align: center;
}

.control-panel {
   padding: 8px;
}

.status-card {
   display: flex;
   justify-content: space-between;
   align-items: center;
   background: #f9f9f9;
   padding: 16px;
   border-radius: 8px;
}
.info h3 {
   margin: 0 0 8px 0;
}
.actions {
   display: flex;
   flex-direction: column;
   align-items: flex-end;
   gap: 4px;
}

.empty-selection {
   display: flex;
   justify-content: center;
   align-items: center;
   height: 100%;
   color: #999;
}
</style>
