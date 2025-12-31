<template>
  <div class="ceremony-container">
    <div class="controls-card">
      <div class="controls-header">
        <h2>🎲 Stage Draw</h2>
        <p class="subtitle">Setup the next stage groups</p>
      </div>
      <div class="controls-body">
         <n-input-group>
            <n-input v-model:value="stageId" :placeholder="t('ceremony.placeholder_stage_id')" size="large" />
            <n-button type="primary" size="large" @click="startShuffle" :disabled="isShuffling || isRevealing || !stageId">
              <template #icon><n-icon><Shuffle /></n-icon></template>
              {{ t('ceremony.start_shuffle') }}
            </n-button>
         </n-input-group>
         
         <div class="action-buttons">
            <n-button type="warning" size="large" @click="stopShuffle" :disabled="!isShuffling" dashed>
               🛑 {{ t('ceremony.stop_reveal') }}
            </n-button>
            <n-button type="success" size="large" @click="confirmGroups" :disabled="!finalData || isRevealing || isShuffling">
               💾 {{ t('ceremony.confirm_save') }}
            </n-button>
         </div>
      </div>
    </div>

    <n-divider />

    <div v-if="statusText" class="status-indicator">
       <n-tag :type="statusType" size="large" round>
         Status: {{ statusText }}
       </n-tag>
    </div>

    <transition-group name="list" tag="div" class="groups-grid">
      <div v-for="(groupName, gIdx) in groupNames" :key="groupName" class="uma-group-card">
        <div class="group-header" :style="{ backgroundColor: getGroupColor(gIdx) }">
          <span class="group-title">{{ groupName }}</span>
        </div>
        <div class="group-body">
          <div v-for="(player, pIdx) in getDisplayPlayers(groupName)" :key="pIdx" class="uma-gate">
            <div class="gate-number" :style="{ backgroundColor: getGateColor(pIdx + 1) }">{{ pIdx + 1 }}</div>
            <div class="gate-info">
               <div class="player-name">{{ player.in_game_name || '---' }}</div>
               <div v-if="player.seed_level === 1" class="seed-badge">👑 Seed</div>
               <div v-if="player.is_npc" class="npc-badge">🤖 NPC</div>
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
import { useMessage, NButton, NInput, NInputGroup, NIcon, NDivider, NTag } from 'naive-ui'
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
  groupNames.value.push(`Group ${String.fromCharCode(65 + i)}`)
}

// Temporary "Shuffling" state
const shuffleState = ref<Record<string, any[]>>({})
let shuffleInterval: number | null = null

// Dummy names for visual effect
const dummyNames = ["Special Week", "Silence Suzuka", "Tokai Teio", "Oguri Cap", "Gold Ship", "Vodka", "Daiwa Scarlet"]

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
        seed_level: Math.random() > 0.8 ? 1 : 0
      }))
    })
    shuffleState.value = temp
  }, 80)
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
    
    // Instant reveal for now
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
   const colors = ['#EF5350', '#EC407A', '#AB47BC', '#7E57C2', '#5C6BC0', '#42A5F5', '#29B6F6', '#26C6DA', '#26A69A', '#66BB6A', '#9CCC65', '#D4E157', '#FFEE58', '#FFCA28']
   return colors[idx % colors.length]
}

// Gate Colors (Standard Horse Racing: 1=White, 2=Black, 3=Red, 4=Blue, 5=Yellow, 6=Green, 7=Orange, 8=Pink)
const getGateColor = (gate: number) => {
   const map: Record<number, string> = {
      1: '#FFFFFF', // White cap (border usually) - let's use border grey for contrast
      2: '#212121', // Black
      3: '#F44336', // Red
      4: '#2196F3', // Blue
      5: '#FFEB3B', // Yellow
      6: '#4CAF50', // Green
      7: '#FF9800', // Orange
      8: '#F06292'  // Pink
   }
   return map[gate] || '#9E9E9E'
}

onUnmounted(() => {
  if (shuffleInterval) clearInterval(shuffleInterval)
})
</script>

<style scoped>
.ceremony-container {
  padding: 0;
}
.controls-card {
   background: white;
   padding: 24px;
   border-radius: 16px;
   box-shadow: 0 4px 12px rgba(0,0,0,0.05);
   display: flex;
   flex-direction: column;
   align-items: center;
   text-align: center;
}
.controls-body {
   display: flex;
   flex-direction: column;
   gap: 16px;
   width: 100%;
   max-width: 500px;
}
.action-buttons {
   display: flex;
   gap: 16px;
   justify-content: center;
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

/* Uma Style Card */
.uma-group-card {
   background: white;
   border-radius: 12px;
   overflow: hidden;
   box-shadow: 0 2px 8px rgba(0,0,0,0.08);
   transition: transform 0.2s;
   border: 1px solid #eee;
}
.uma-group-card:hover {
   transform: translateY(-4px);
   box-shadow: 0 8px 16px rgba(0,0,0,0.12);
}

.group-header {
   padding: 8px 16px;
   color: white;
   font-weight: bold;
   text-transform: uppercase;
   letter-spacing: 1px;
   text-align: center;
   text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.group-body {
   padding: 12px;
   display: flex;
   flex-direction: column;
   gap: 8px;
}

.uma-gate {
   display: flex;
   align-items: center;
   background: #FAFAFA;
   border-radius: 8px;
   padding: 6px;
   border: 1px solid #f0f0f0;
}

.gate-number {
   width: 24px;
   height: 24px;
   border-radius: 4px;
   display: flex;
   align-items: center;
   justify-content: center;
   font-weight: bold;
   font-size: 12px;
   margin-right: 10px;
   color: #333; /* Default for yellow/white */
   border: 1px solid rgba(0,0,0,0.1);
}
/* Adjust text color for dark gates */
.gate-number[style*="rgb(33, 33, 33)"],
.gate-number[style*="#212121"],
.gate-number[style*="#F44336"],
.gate-number[style*="#2196F3"],
.gate-number[style*="#4CAF50"] {
   color: white;
}

.gate-info {
   flex: 1;
   display: flex;
   align-items: center;
   justify-content: space-between;
}

.player-name {
   font-weight: 500;
   font-size: 14px;
}

.seed-badge {
   background: #FFD700;
   color: #554400;
   font-size: 10px;
   padding: 2px 6px;
   border-radius: 10px;
   font-weight: bold;
}

.npc-badge {
   background: #E0E0E0;
   color: #757575;
   font-size: 10px;
   padding: 2px 6px;
   border-radius: 10px;
}

.status-indicator {
   text-align: center;
   margin-bottom: 16px;
}

/* Animations */
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
