<template>
  <div class="ceremony-container">
    
    <!-- Title / Header Section -->
    <div class="ceremony-header">
       <div class="header-content">
          <n-icon size="40" color="#67C05D" class="header-icon"><Shuffle /></n-icon>
          <div>
             <h1>{{ t('ceremony.title') || 'Draw Ceremony' }}</h1>
             <p class="subtitle">{{ t('ceremony.subtitle') || 'Official Tournament Stage Draw' }}</p>
          </div>
       </div>
       
       <div class="status-badge" v-if="statusText">
          <n-tag :type="statusType" round size="large" :bordered="false" style="font-weight: bold; padding: 4px 16px;">
             {{ statusText }}
          </n-tag>
       </div>
    </div>

    <!-- Control Station -->
    <div class="control-station uma-card">
      <div class="control-row">
         <div class="input-area">
            <span class="label">{{ t('ceremony.target_stage') }}</span>
            <n-input-group>
               <n-input v-model:value="stageId" :placeholder="t('ceremony.placeholder_stage_id')" />
            </n-input-group>
         </div>

         <div class="actions-area">
            <n-button type="primary" size="medium" round @click="startShuffle" :disabled="isShuffling || isRevealing || !stageId" class="action-btn">
              <template #icon><n-icon><Shuffle /></n-icon></template>
              {{ t('ceremony.start_shuffle') }}
            </n-button>
            
            <n-button type="warning" size="medium" round @click="stopShuffle" :disabled="!isShuffling" dashed class="action-btn">
               🛑 {{ t('ceremony.stop_reveal') }}
            </n-button>

            <div class="divider-vertical"></div>

            <n-button type="success" size="medium" round secondary @click="confirmGroups" :disabled="!finalData || isRevealing || isShuffling" class="action-btn">
               💾 {{ t('ceremony.confirm_save') }}
            </n-button>
         </div>
      </div>
    </div>

    <!-- Groups Display -->
    <transition-group name="staggered-fade" tag="div" class="groups-grid">
      <div v-for="(groupName, gIdx) in groupNames" :key="groupName" class="group-column">
        <div class="group-card">
           <div class="group-card-header" :style="{ borderTopColor: getGroupColor(gIdx) }">
              <div class="group-letter" :style="{ background: getGroupColor(gIdx) }">{{ groupName.split(' ').pop() }}</div>
              <span class="group-full-name">{{ groupName }}</span>
           </div>
           
           <div class="group-list">
             <div v-for="(player, pIdx) in getDisplayPlayers(groupName)" :key="pIdx" class="player-slot">
               <div class="slot-number">{{ pIdx + 1 }}</div>
               <div class="player-content" :class="{ 'is-empty': !player.in_game_name || player.in_game_name === '---' }">
                  <div class="p-name">{{ player.in_game_name || '---' }}</div>
                  <div class="badges">
                     <span v-if="player.seed_level === 1" class="mini-badge seed">SEED</span>
                  </div>
               </div>
             </div>
           </div>
        </div>
      </div>
    </transition-group>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage, NButton, NInput, NInputGroup, NIcon, NTag } from 'naive-ui'
import { Shuffle } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { getDrawPreview, saveGroups } from '../api/stages'

const { t } = useI18n()
const route = useRoute()
const message = useMessage()
const stageId = ref('')
const isShuffling = ref(false)
const isRevealing = ref(false)
const finalData = ref<Record<string, any[]> | null>(null)

onMounted(() => {
   if (route.query.stageId) {
      stageId.value = route.query.stageId as string
   }
})

const statusText = computed(() => {
  if (finalData.value) return t('ceremony.status.finalized')
  if (isRevealing.value) return t('ceremony.status.revealing')
  if (isShuffling.value) return t('ceremony.status.shuffling')
  return ''
})

const statusType = computed(() => {
   if (finalData.value) return 'success'
   if (isShuffling.value) return 'warning'
   return 'default'
})

const groupNames = ref<string[]>([])
// Initialize with A-N (14 groups) as default placeholders
for (let i = 0; i < 14; i++) {
  groupNames.value.push(`${t('ceremony.group_prefix') || 'Group'} ${String.fromCharCode(65 + i)}`)
}

// Temporary "Shuffling" state
const shuffleState = ref<Record<string, any[]>>({})
let shuffleInterval: number | null = null

// Dummy names for visual effect
const dummyNames = ["Special Week", "Silence Suzuka", "Tokai Teio", "Oguri Cap", "Gold Ship", "Vodka", "Daiwa Scarlet", "Mejiro McQueen", "Symboli Rudolf", "Narita Brian"]

const startShuffle = () => {
  if (!stageId.value) {
    message.error(t('ceremony.please_enter_stage_id'))
    return
  }
  isShuffling.value = true
  finalData.value = null

  // Start animation loop
  shuffleInterval = setInterval(() => {
    const temp: Record<string, any[]> = {}
    groupNames.value.forEach(g => {
      temp[g] = Array(6).fill(null).map(() => ({
        in_game_name: dummyNames[Math.floor(Math.random() * dummyNames.length)],
        seed_level: Math.random() > 0.9 ? 1 : 0
      }))
    })
    shuffleState.value = temp
  }, 60) // Faster shuffle
}

const stopShuffle = async () => {
  try {
    const data = await getDrawPreview(stageId.value)
    
    // Sort keys just in case
    const sortedKeys = Object.keys(data).sort()
    groupNames.value = sortedKeys
    finalData.value = data

    if (shuffleInterval) clearInterval(shuffleInterval)
    isShuffling.value = false
    isRevealing.value = true
    
    // Instant reveal for now (could add staged reveal later)
    shuffleState.value = data
    isRevealing.value = false
    message.success(t('ceremony.draw_complete'))

  } catch (e) {
    console.error(e)
    message.error(t('ceremony.fetch_fail'))
    if (shuffleInterval) clearInterval(shuffleInterval)
    isShuffling.value = false
  }
}

const getDisplayPlayers = (groupName: string) => {
  if (finalData.value && !isShuffling.value) {
    return finalData.value[groupName] || []
  }
  return shuffleState.value[groupName] || Array(6).fill({ in_game_name: '---' })
}

const confirmGroups = async () => {
  if (!finalData.value || !stageId.value) return
  try {
    await saveGroups(stageId.value, finalData.value)
    message.success(t('ceremony.save_success'))
  } catch (e) {
    message.error(t('ceremony.save_fail'))
  }
}

// Visual Helpers
const getGroupColor = (idx: number) => {
   const colors = ['#EF5350', '#AB47BC', '#5C6BC0', '#29B6F6', '#26A69A', '#9CCC65', '#FFCA28', '#FF7043', '#8D6E63', '#78909C']
   return colors[idx % colors.length]
}

onUnmounted(() => {
  if (shuffleInterval) clearInterval(shuffleInterval)
})
</script>

<style scoped>
.ceremony-container {
  width: 90%;
  max-width: 1200px;
  margin: 40px auto;
  padding-bottom: 80px;
}

.ceremony-header {
   display: flex;
   justify-content: space-between;
   align-items: flex-end;
   margin-bottom: 24px;
   padding: 0 12px;
}

.header-content {
   display: flex;
   align-items: center;
   gap: 16px;
}
.header-icon {
   background: white;
   padding: 8px;
   border-radius: 12px;
   box-shadow: 0 4px 12px rgba(103, 192, 93, 0.2);
}

.ceremony-header h1 {
   margin: 0;
   font-size: 2rem;
   color: #333;
   line-height: 1.2;
}
.ceremony-header .subtitle {
   margin: 4px 0 0 0;
   color: #666;
   font-size: 1rem;
}

.control-station {
   background: white;
   border-radius: 16px;
   padding: 20px 32px;
   box-shadow: 0 8px 24px rgba(0,0,0,0.06);
   margin-bottom: 40px;
   border: 1px solid rgba(0,0,0,0.03);
}

.control-row {
   display: flex;
   align-items: center;
   justify-content: space-between;
   flex-wrap: wrap;
   gap: 20px;
}

.input-area {
   display: flex;
   align-items: center;
   gap: 12px;
   flex: 1;
   min-width: 250px;
}
.input-area .label {
   font-weight: bold;
   color: #555;
   white-space: nowrap;
}

.actions-area {
   display: flex;
   align-items: center;
   gap: 16px;
}

.divider-vertical {
   width: 1px;
   height: 32px;
   background: #eee;
   margin: 0 8px;
}

.action-btn {
   font-weight: bold;
   min-width: 120px;
}

/* GRID LAYOUT */
.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
}

.group-card {
   background: white;
   border-radius: 12px;
   overflow: hidden;
   box-shadow: 0 2px 8px rgba(0,0,0,0.05);
   transition: transform 0.2s, box-shadow 0.2s;
   border: 1px solid #f0f0f0;
   height: 100%;
}
.group-card:hover {
   transform: translateY(-4px);
   box-shadow: 0 12px 24px rgba(0,0,0,0.1);
}

.group-card-header {
   display: flex;
   align-items: center;
   gap: 12px;
   padding: 12px 16px;
   background: #fafafa;
   border-top: 4px solid transparent; /* Colored by inline style */
   border-bottom: 1px solid #eee;
}

.group-letter {
   width: 32px;
   height: 32px;
   border-radius: 8px;
   color: white;
   display: flex;
   align-items: center;
   justify-content: center;
   font-weight: 800;
   font-size: 1.1rem;
   box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.group-full-name {
   font-weight: bold;
   color: #444;
   font-size: 1.05rem;
}

.group-list {
   padding: 12px;
   display: flex;
   flex-direction: column;
   gap: 8px;
}

.player-slot {
   display: flex;
   align-items: center;
   gap: 10px;
   font-size: 0.95rem;
}

.slot-number {
   width: 20px;
   color: #999;
   font-size: 0.8rem;
   text-align: right;
   font-weight: bold;
}

.player-content {
   flex: 1;
   background: #fdfdfd;
   border: 1px solid #f0f0f0;
   border-radius: 6px;
   padding: 6px 10px;
   display: flex;
   align-items: center;
   justify-content: space-between;
   transition: background 0.2s;
}

.player-content.is-empty {
   background: #fafafa;
   border-style: dashed;
   color: #ccc;
}

.p-name {
   font-weight: 600;
   color: #333;
}

.badges {
   display: flex;
   gap: 4px;
}

.mini-badge {
   font-size: 0.7rem;
   padding: 1px 4px;
   border-radius: 4px;
   font-weight: bold;
   text-transform: uppercase;
}
.mini-badge.seed {
   background: #FFF8E1;
   color: #FBC02D;
   border: 1px solid #FFE082;
}
.mini-badge.npc {
   background: #EEEEEE;
   color: #9E9E9E;
   border: 1px solid #E0E0E0;
}

/* Animations */
.staggered-fade-enter-active,
.staggered-fade-leave-active {
  transition: all 0.4s ease;
}
.staggered-fade-enter-from,
.staggered-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 768px) {
   .ceremony-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
   }
   .control-row {
      flex-direction: column;
      align-items: stretch;
   }
   .actions-area {
      flex-wrap: wrap;
      justify-content: center;
   }
   .divider-vertical { display: none; }
}
</style>