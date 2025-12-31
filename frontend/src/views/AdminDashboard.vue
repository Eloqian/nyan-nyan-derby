<template>
  <div class="admin-container">
    <n-card :title="t('admin.dashboard_title')">
      <n-tabs type="line">
        
        <n-tab-pane name="control" :tab="t('admin.tournament_control')">
           <div v-if="loadingTourney" class="loading-state">
              <n-spin size="medium" />
           </div>
           
           <div v-else-if="!tournament">
              <n-empty :description="t('admin.no_active_tournament')">
                 <template #extra>
                    <n-button type="primary" @click="showCreateModal = true">
                       {{ t('admin.create_new') }}
                    </n-button>
                 </template>
              </n-empty>
           </div>
           
           <div v-else class="control-panel">
              <div class="status-card">
                 <div class="info">
                    <h3>{{ tournament.name }}</h3>
                    <n-tag :type="getStatusType(tournament.status)">
                       {{ tournament.status.toUpperCase() }}
                    </n-tag>
                 </div>
                 
                 <div class="actions">
                    <n-text depth="3">{{ t('admin.flow_control') }}</n-text>
                    <n-button-group>
                       <n-button 
                          @click="updateStatus('setup')" 
                          :type="tournament.status === 'setup' ? 'primary' : 'default'"
                          :disabled="tournament.status === 'setup'"
                       >
                          {{ t('admin.setup') }}
                       </n-button>
                       <n-button 
                          @click="updateStatus('active')" 
                          :type="tournament.status === 'active' ? 'primary' : 'default'"
                          :disabled="tournament.status === 'active'"
                       >
                          {{ t('admin.start_active') }}
                       </n-button>
                       <n-button 
                          @click="updateStatus('completed')" 
                          :type="tournament.status === 'completed' ? 'primary' : 'default'"
                          :disabled="tournament.status === 'completed'"
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
                          <!-- Settle Button -->
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
                    <n-button secondary @click="$router.push('/ceremony')">
                       {{ t('admin.go_draw') }}
                    </n-button>
                    <n-button secondary @click="$router.push('/live')">
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

    <!-- Create Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" :title="t('admin.create_modal_title')" style="width: 500px">
       <n-form>
          <n-form-item :label="t('admin.tournament_name')">
             <n-input v-model:value="newTourneyName" placeholder="e.g. Meow Cup 2025" />
          </n-form-item>
          <!-- Additional config could go here -->
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { 
  useMessage, NCard, NTabs, NTabPane, NUpload, NUploadDragger, NIcon, NText, NP, NEmpty, NButton, NTag, NButtonGroup, NDivider, NAlert, NSpace, NModal, NForm, NFormItem, NInput, NSpin
} from 'naive-ui'
import { ArchiveOutline } from '@vicons/ionicons5'
import type { UploadCustomRequestOptions } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { getCurrentTournament, createTournament, updateTournament, type Tournament } from '../api/tournaments'

const router = useRouter()
const message = useMessage()
const auth = useAuthStore()
const { t } = useI18n()

// State
const tournament = ref<Tournament | null>(null)
const stages = ref<any[]>([])
const loadingTourney = ref(true)
const showCreateModal = ref(false)
const newTourneyName = ref('')
const creating = ref(false)

// Lifecycle
onMounted(() => {
   fetchTournament()
   fetchStages()
})

const fetchTournament = async () => {
   loadingTourney.value = true
   try {
      const t = await getCurrentTournament()
      tournament.value = t
   } catch (e) {
      console.error(e)
   } finally {
      loadingTourney.value = false
   }
}

const fetchStages = async () => {
   try {
      const res = await fetch('/api/v1/stages/')
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
         headers: { 'Authorization': `Bearer ${auth.token}` }
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
      // Create with default stages config
      const payload = {
         name: newTourneyName.value,
         rules_config: { "prizes": ["200", "160", "120"] },
         stages_config: [
            { "name": "Audition", "stage_type": "round_robin", "rules_config": {"group_count": 14, "advancement": {"type": "top_n", "value": 4}} },
            { "name": "Group Stage 1", "stage_type": "round_robin", "rules_config": {"group_count": 13, "advancement": {"type": "top_n", "value": 4}} },
            { "name": "Group Stage 2", "stage_type": "round_robin", "rules_config": {"group_count": 9, "advancement": {"type": "position_map", "map": {"1": "winner", "2": "loser", "3": "loser"}}} },
            { "name": "Bracket Stage", "stage_type": "double_elimination", "rules_config": {} }
         ]
      }
      await createTournament(auth.token!, payload)
      message.success(t('admin.tournament_created'))
      showCreateModal.value = false
      await fetchTournament()
   } catch (e) {
      message.error(t('admin.failed_create'))
   } finally {
      creating.value = false
   }
}

const updateStatus = async (status: string) => {
   if (!tournament.value) return
   try {
      await updateTournament(auth.token!, tournament.value.id, { status })
      message.success(t('admin.status_updated', { status }))
      await fetchTournament()
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
        'Authorization': `Bearer ${auth.token}`
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
  max-width: 800px;
  margin: 0 auto;
}
.loading-state {
   padding: 40px;
   text-align: center;
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
</style>
