<template>
  <div class="ceremony-container">
    <n-card title="Group Draw Ceremony">
      <div class="controls">
        <n-input v-model:value="stageId" placeholder="Enter Stage ID" style="width: 300px; margin-right: 1rem;" />
        <n-button type="primary" @click="startShuffle" :disabled="isShuffling || isRevealing || !stageId">
          Start Shuffle
        </n-button>
        <n-button type="warning" @click="stopShuffle" :disabled="!isShuffling" style="margin-left: 1rem;">
          Stop & Reveal
        </n-button>
        <n-button type="success" @click="confirmGroups" :disabled="!finalData || isRevealing || isShuffling" style="margin-left: 1rem;">
          Confirm & Save
        </n-button>
      </div>

      <div class="groups-grid">
        <n-card v-for="(groupName) in groupNames" :key="groupName" :title="groupName" class="group-card">
          <n-list>
            <n-list-item v-for="(player, idx) in getDisplayPlayers(groupName)" :key="idx">
              <div class="player-slot" :class="{ 'highlight': player.seed_level === 1 }">
                {{ player.in_game_name || '???' }}
              </div>
            </n-list-item>
          </n-list>
        </n-card>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useMessage, NCard, NButton, NInput, NList, NListItem } from 'naive-ui'
import { getDrawPreview, saveGroups } from '../api/stages'

const message = useMessage()
const stageId = ref('')
const isShuffling = ref(false)
const isRevealing = ref(false)
const finalData = ref<Record<string, any[]> | null>(null)

// For visualization, we need a set of group names.
// Initially we might not know them, but once we start shuffle, we can assume 14 groups or just show "Group A"..."Group N" based on some default.
// For the shuffling effect, we can just show random names?
// To make it look "real", maybe we should fetch the eligible players first?
// For MVP, we will just cycle through "???" or random strings,
// AND rely on the assumption that we will have roughly 14 groups (A-N).

const groupNames = ref<string[]>([])
// Initialize with A-N (14 groups) as default placeholders
for (let i = 0; i < 14; i++) {
  groupNames.value.push(`Group ${String.fromCharCode(65 + i)}`)
}

// Temporary "Shuffling" state
const shuffleState = ref<Record<string, any[]>>({})
let shuffleInterval: number | null = null

// Dummy names for visual effect
const dummyNames = ["Player A", "Player B", "Player C", "Player D", "Wait...", "Loading...", "???"]

const startShuffle = () => {
  if (!stageId.value) {
    message.error("Please enter a Stage ID")
    return
  }
  isShuffling.value = true
  finalData.value = null

  // Start animation loop
  shuffleInterval = setInterval(() => {
    // For each group, generate random list of players
    // We assume 7-8 slots per group?
    const temp: Record<string, any[]> = {}
    groupNames.value.forEach(g => {
      temp[g] = Array(8).fill(null).map(() => ({
        in_game_name: dummyNames[Math.floor(Math.random() * dummyNames.length)],
        seed_level: 0
      }))
    })
    shuffleState.value = temp
  }, 100) // update every 100ms
}

const stopShuffle = async () => {
  // 1. Call API
  try {
    const data = await getDrawPreview(stageId.value)
    // data is { "Group A": [...], ... }

    // Update group names if they differ
    groupNames.value = Object.keys(data).sort()

    finalData.value = data

    // Stop shuffling loop
    if (shuffleInterval) clearInterval(shuffleInterval)
    isShuffling.value = false
    isRevealing.value = true

    // 2. Reveal Logic (Slow down / Lock in)
    // We can do this gradually or instant for MVP.
    // Let's do a simple "instant" reveal for now, or a short delay.

    // Set shuffleState to finalData immediately?
    // Let's mimic "locking" by setting it directly.
    shuffleState.value = data

    isRevealing.value = false
    message.success("Draw Complete! Review and Confirm.")

  } catch (e) {
    console.error(e)
    message.error("Failed to fetch draw preview. Check Stage ID and backend.")
    if (shuffleInterval) clearInterval(shuffleInterval)
    isShuffling.value = false
  }
}

const getDisplayPlayers = (groupName: string) => {
  if (finalData.value && !isShuffling.value) {
    return finalData.value[groupName] || []
  }
  return shuffleState.value[groupName] || []
}

const confirmGroups = async () => {
  if (!finalData.value || !stageId.value) return

  try {
    await saveGroups(stageId.value, finalData.value)
    message.success("Groups saved successfully!")
    // Redirect or Reset?
  } catch (e) {
    message.error("Failed to save groups.")
  }
}

onUnmounted(() => {
  if (shuffleInterval) clearInterval(shuffleInterval)
})
</script>

<style scoped>
.ceremony-container {
  padding: 2rem;
}
.controls {
  display: flex;
  margin-bottom: 2rem;
  align-items: center;
}
.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}
.player-slot {
  padding: 0.5rem;
  background: #f5f5f5;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
}
.player-slot.highlight {
  background: #ffe082; /* Gold for seeds */
  border: 2px solid #ffb300;
}
</style>
