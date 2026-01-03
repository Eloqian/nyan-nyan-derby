<template>
  <div class="admin-container">
    <div class="sidebar uma-card" style="border-radius: 8px;">
       <div class="sidebar-header">
          <h3>{{ t('admin.dashboard_title') }}</h3>
          <n-button type="primary" size="small" @click="openCreateModal" block color="#67C05D">
             <template #icon><n-icon><Add /></n-icon></template>
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
       
       <!-- Main Panel -->
       <div v-else class="uma-card" style="min-height: 600px;">
         <div class="card-upper active-bg" style="height: 60px; padding: 0 20px; display: flex; align-items: center; justify-content: flex-start;">
             <h2 style="margin: 0; color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.2);">{{ selectedTournament?.name || 'Tournament' }}</h2>
         </div>
         
         <div class="card-content">
            <n-tabs type="line" animated>
            
            <n-tab-pane name="control" :tab="t('admin.tournament_control')">
               <div class="control-panel">
                  <div class="status-card" :class="selectedTournament?.status">
                     <div class="info">
                        <n-tag :type="getStatusType(selectedTournament?.status || 'setup')">
                           {{ (selectedTournament?.status || '').toUpperCase() }}
                        </n-tag>
                        <span style="margin-left: 12px; font-size: 0.9em; font-weight: bold; opacity: 0.7;">
                           ID: {{ selectedTournament?.id }}
                        </span>
                     </div>
                     
                     <div class="actions">
                        <n-button 
                           size="small"
                           secondary
                           @click="openEditModal"
                           style="margin-bottom: 8px"
                        >
                           {{ t('admin.edit_settings') }}
                        </n-button>

                        <n-text depth="3" style="font-size: 0.8rem; text-transform: uppercase; font-weight: bold;">{{ t('admin.flow_control') }}</n-text>
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
                     <div v-for="stage in stages" :key="stage.id" class="stage-row-item">
                        <div class="stage-info">
                              <div class="s-ord">{{ stage.sequence_order }}</div>
                              <div>
                                 <div class="s-name">{{ stage.name }}</div>
                                 <div class="s-type">{{ stage.stage_type }}</div>
                              </div>
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
         </div>
       </div>
    </div>

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" :title="isEditing ? t('admin.edit_settings') : t('admin.create_modal_title')" style="width: 800px">
       <n-form label-placement="left" label-width="120">
          <n-form-item :label="t('admin.tournament_name')">
             <n-input v-model:value="formModel.name" placeholder="e.g. 第14届喵喵杯" />
          </n-form-item>

          <n-form-item :label="t('admin.start_time')">
             <n-date-picker v-model:value="formModel.startTime" type="datetime" clearable />
          </n-form-item>
          
          <n-divider>{{ t('admin.rules_config') }}</n-divider>
          
          <n-form-item :label="t('admin.points_map')">
             <n-space vertical>
                <n-input-group v-for="i in 5" :key="i">
                   <n-button disabled style="width: 100px">{{ t('admin.rank_label', {rank: i}) }}</n-button>
                   <n-input-number v-model:value="formModel.pointsMap[i]" :min="0" />
                </n-input-group>
             </n-space>
          </n-form-item>

          <n-form-item :label="t('admin.prizes')">
             <div style="width: 100%">
               <n-grid :cols="24" :x-gap="12">
                   <n-grid-item :span="24" style="margin-bottom: 8px">
                       <n-input-group>
                           <n-button disabled>Base Pool</n-button>
                           <n-input v-model:value="formModel.prizePoolTotal" placeholder="e.g. 1100 RMB" />
                       </n-input-group>
                   </n-grid-item>
               </n-grid>
               <div v-for="(item, index) in formModel.prizes" :key="index" style="display: flex; gap: 8px; margin-bottom: 8px;">
                  <n-input v-model:value="item.range" :placeholder="t('admin.prize_rank_placeholder')" style="width: 150px" />
                  <n-input v-model:value="item.amount" :placeholder="t('admin.prize_amount_placeholder')" />
                  <n-button circle type="error" ghost @click="removePrizeItem(index)">
                     <template #icon><n-icon><Trash /></n-icon></template>
                  </n-button>
               </div>
               <n-button dashed block @click="addPrizeItem">
                  <template #icon><n-icon><Add /></n-icon></template>
                  {{ t('admin.add_prize') }}
               </n-button>
             </div>
          </n-form-item>

          <n-divider />

          <n-form-item :label="t('admin.rules_text')" label-placement="top">
             <div style="width: 100%">
                <div style="margin-bottom: 8px; display: flex; justify-content: flex-end;">
                   <n-button size="small" secondary @click="generateRulesTemplate">
                      {{ t('admin.generate_template') }}
                   </n-button>
                </div>
                <n-input 
                   v-model:value="formModel.rulesText" 
                   type="textarea" 
                   :rows="15" 
                   placeholder="Detailed rules..." 
                   style="font-family: monospace;"
                />
             </div>
          </n-form-item>
       </n-form>
       <template #footer>
          <div style="display: flex; justify-content: flex-end; gap: 12px;">
             <n-button @click="showCreateModal = false">{{ t('admin.cancel') }}</n-button>
             <n-button type="primary" @click="handleSave" :disabled="!formModel.name" :loading="saving">
                {{ isEditing ? t('admin.save_changes') : t('admin.create') }}
             </n-button>
          </div>
       </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { 
  useMessage, NTabs, NTabPane, NUpload, NUploadDragger, NIcon, NText, NP, NEmpty, NButton, NTag, NButtonGroup, NDivider, NAlert, NSpace, NModal, NForm, NFormItem, NInput, NSpin, NInputNumber, NInputGroup, NMenu, NDatePicker, NGrid, NGridItem
} from 'naive-ui'
import { ArchiveOutline, Add, Trash } from '@vicons/ionicons5'
import type { UploadCustomRequestOptions } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { listTournaments, createTournament, updateTournament, type Tournament } from '../api/tournaments'
import { getStages } from '../api/stages'

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
const isEditing = ref(false)
const saving = ref(false)

// Form State
const formModel = ref({
   name: '',
   startTime: null as number | null,
   pointsMap: { 1: 9, 2: 5, 3: 3, 4: 2, 5: 1 } as Record<number, number>,
   prizePoolTotal: '1100 RMB',
   prizes: [] as { range: string, amount: string }[],
   rulesText: ''
})

const defaultPrizes = [
   { range: '1', amount: '200' },
   { range: '2', amount: '160' },
   { range: '3', amount: '120' },
   { range: '4~7', amount: '60' },
   { range: '8~9', amount: '40' },
   { range: '10~21', amount: '20' },
   { range: '22~27', amount: '10' }
]

const selectedTournament = computed(() => 
   tournaments.value.find(t => t.id === selectedTournamentId.value)
)

const tournamentOptions = computed(() => 
   tournaments.value.map(t => ({
      label: t.name,
      key: t.id
   }))
)

onMounted(async () => {
   if (!auth.isAuthenticated) {
      router.push('/login')
      return
   }
   await fetchAllTournaments()
})

watch(selectedTournamentId, async (newVal) => {
   if (newVal) {
      await fetchStages(newVal)
   }
})

const fetchAllTournaments = async () => {
   loadingTournaments.value = true
   try {
      tournaments.value = await listTournaments()
      if (tournaments.value.length > 0 && !selectedTournamentId.value) {
         selectedTournamentId.value = tournaments.value[0]!.id
      }
   } catch (e) {
      console.error(e)
   } finally {
      loadingTournaments.value = false
   }
}

const fetchStages = async (tId: string) => {
   try {
      stages.value = await getStages(tId)
   } catch (e) {
      console.error(e)
   }
}

const handleTournamentSelect = (key: string) => {
   selectedTournamentId.value = key
}

const openCreateModal = () => {
   isEditing.value = false
   formModel.value = {
      name: '',
      startTime: Date.now(),
      pointsMap: { 1: 9, 2: 5, 3: 3, 4: 2, 5: 1 },
      prizePoolTotal: '1100 RMB',
      prizes: JSON.parse(JSON.stringify(defaultPrizes)),
      rulesText: ''
   }
   generateRulesTemplate()
   showCreateModal.value = true
}

const openEditModal = () => {
   if (!selectedTournament.value) return
   const t = selectedTournament.value
   const rules = t.rules_config || {}
   const prizeConfig = t.prize_pool_config || {}
   
   isEditing.value = true
   formModel.value = {
      name: t.name,
      startTime: t.start_time ? new Date(t.start_time).getTime() : null,
      pointsMap: rules.points_map || { 1: 9, 2: 5, 3: 3, 4: 2, 5: 1 },
      prizePoolTotal: prizeConfig.total || '1100 RMB',
      prizes: parsePrizes(prizeConfig.allocation || defaultPrizes),
      rulesText: t.rules_content || ''
   }
   showCreateModal.value = true
}

const parsePrizes = (prizesData: any): { range: string, amount: string }[] => {
   // If it's the new Dict format { "1": "200" }, convert to array
   if (prizesData && !Array.isArray(prizesData)) {
       return Object.entries(prizesData).map(([k, v]) => ({
           range: k,
           amount: String(v)
       }))
   }
   // Legacy array
   if (Array.isArray(prizesData)) {
       if (prizesData.length > 0 && typeof prizesData[0] === 'string') {
          return prizesData.map((amt, idx) => ({ range: String(idx + 1), amount: amt }))
       }
       return prizesData
   }
   return JSON.parse(JSON.stringify(defaultPrizes))
}

const addPrizeItem = () => {
   formModel.value.prizes.push({ range: '', amount: '' })
}

const removePrizeItem = (index: number) => {
   formModel.value.prizes.splice(index, 1)
}

const generateRulesTemplate = () => {
   const { name, startTime, pointsMap, prizes, prizePoolTotal } = formModel.value
   const startDate = startTime ? new Date(startTime) : new Date()
   
   // Helper to get week day
   const weekDays = ['日', '一', '二', '三', '四', '五', '六']
   const getWd = (d: Date) => weekDays[d.getDay()]
   
   const d1 = startDate
   const d2 = new Date(d1.getTime() + 86400000)
   const d3 = new Date(d1.getTime() + 86400000 * 2)
   const d4 = new Date(d1.getTime() + 86400000 * 3)
   const d5 = new Date(d1.getTime() + 86400000 * 4)

   let prizeText = ''
   prizes.forEach(p => {
      prizeText += `- 第${p.range}名：**${p.amount}**\n`
   })

   const tpl = `# ${name}赛事赛程赛制

一只小水晶 ${new Date().getFullYear()}.${new Date().getMonth()+1}.${new Date().getDate()}

## 1. 比赛时间安排

这次是${name}啦，本次比赛将分为三个阶段：**海选赛**、**小组赛**、**淘汰赛**。

- **海选赛**：${d1.getMonth()+1}月${d1.getDate()}日（星期${getWd(d1)}）
- **小组赛第一轮**：${d2.getMonth()+1}月${d2.getDate()}日（星期${getWd(d2)}）
- **小组赛第二轮**：${d3.getMonth()+1}月${d3.getDate()}日（星期${getWd(d3)}）
- **淘汰赛前两轮**：${d4.getMonth()+1}月${d4.getDate()}日（星期${getWd(d4)}）
- **淘汰赛最终轮与决赛**：${d5.getMonth()+1}月${d5.getDate()}日（星期${getWd(d5)}）

> [!NOTE]
> 本文档赛程赛制以报名人数为准制定，开赛时若人数与预期差距较大，可能有小幅度流程变动请谅解。

## 2. 报名与Check-in流程

本届设种子选手制度...（请根据实际情况填写）...

## 3. 赛事阶段与晋级规则

### I. 海选赛（${d1.getMonth()+1}月${d1.getDate()}日）

...

## 4. 比赛形式与积分规则

- 每日比赛第一轮均截至北京时间**19:30**建房，**20:00**进房。
- 每人出三匹马，3人一组，进行9匹马的混战。
- 每场比赛，第一名得 **${pointsMap[1]}** 分，第二名 **${pointsMap[2]}** 分，第三名 **${pointsMap[3]}** 分，第四名 **${pointsMap[4]}** 分，第五名 **${pointsMap[5]}** 分。
- 各阶段多场房间中“一位”数超过总房间数一半（向下取整）的，每多一场额外 **+2** 分。

## 5. 奖金池

本届基础奖金池为：**${prizePoolTotal}**

奖励分配如下：
${prizeText}

## 6. 注意事项

- 喵喵杯不设置强制开始的最早时间，同房间选手均到场，且所有人同意的情况下，可以直接开始比赛并记录结果
- 房主不允许在房间人满前随意开始；选手仍需在最晚时间前入场，否则由NPC代打
- 比赛结果需自行记录表格，分数由表格自动计算；建议保存自己参加的所有对局截图
- 海选及小组赛阶段，加赛按胜负关系、一位数、积分排序为准，避免频繁加赛
- 关于本届如何建房，填表，请参照群内另一图文文件

## 7. 主办方声明

> 喵喵杯由猫猫头的炼金工坊主办，是非盈利娱乐赛事，欢迎各位放松心情享受比赛。我们会尽量维持比赛公平，也希望大家多多包容、配合。群内有任何疑问或意见欢迎随时联系主办方。期待与你再续前缘喵！`

   formModel.value.rulesText = tpl
}

const handleSave = async () => {
   if (!formModel.value.name) return
   saving.value = true
   
   try {
      // Convert prizes array to Map for backend storage if desired, or keep structure
      // We'll store as object for easier querying: { "1": 200, "2": 160 }
      // But user wants "4~7": 60. So keys are strings.
      const prizeAlloc: Record<string, string> = {}
      formModel.value.prizes.forEach(p => {
          if (p.range) prizeAlloc[p.range] = p.amount
      })

      const payload = {
         name: formModel.value.name,
         start_time: formModel.value.startTime ? new Date(formModel.value.startTime).toISOString() : null,
         prize_pool_config: {
             total: formModel.value.prizePoolTotal,
             allocation: prizeAlloc
         },
         rules_content: formModel.value.rulesText,
         rules_config: {
            points_map: formModel.value.pointsMap
         }
      }
      
      // On create, add default stages
      if (!isEditing.value) {
          Object.assign(payload, {
            stages_config: [
               { "name": "Audition", "stage_type": "round_robin", "rules_config": {"group_count": 14, "advancement": {"type": "top_n", "value": 4}} },
               { "name": "Group Stage 1", "stage_type": "round_robin", "rules_config": {"group_count": 13, "advancement": {"type": "top_n", "value": 4}} },
               { "name": "Group Stage 2", "stage_type": "round_robin", "rules_config": {"group_count": 9, "advancement": {"type": "position_map", "map": {"1": "winner", "2": "loser", "3": "loser"}}} },
               { "name": "Bracket Stage", "stage_type": "double_elimination", "rules_config": {} }
            ]
          })
      }

      if (isEditing.value && selectedTournamentId.value) {
         await updateTournament(auth.token!, selectedTournamentId.value, payload)
         message.success(t('admin.status_updated', { status: 'settings' }))
      } else {
         const newT = await createTournament(auth.token!, payload)
         message.success(t('admin.tournament_created'))
         selectedTournamentId.value = newT.id
         // fetchStages triggered by watcher
      }
      
      showCreateModal.value = false
      await fetchAllTournaments()
      
   } catch (e) {
      message.error(isEditing.value ? t('admin.failed_update') : t('admin.failed_create'))
   } finally {
      saving.value = false
   }
}

// ... existing helper functions ...

const handleSettle = async (stageId: string) => {
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

const getStatusType = (status: string) => {
   if (status === 'active') return 'success'
   if (status === 'setup') return 'warning'
   return 'default'
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
  min-height: calc(100vh - 80px); /* Adjust based on navbar height */
  max-width: 1800px;
  margin: 0 auto;
  gap: 24px;
  padding: 20px;
}

@media (max-width: 768px) {
  .admin-container { flex-direction: column; padding: 10px; }
  .sidebar { width: 100%; height: auto; }
  .main-content { padding-bottom: 20px; }
}

.sidebar {
   width: 280px;
   flex-shrink: 0;
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
   padding-bottom: 40px;
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