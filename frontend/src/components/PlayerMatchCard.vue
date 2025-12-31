<template>
  <n-card class="match-card" :class="{ 'host-card': match.is_host }">
    <template #header>
      <div class="card-header">
        <n-tag :type="match.is_host ? 'success' : 'default'" size="small" round>
          {{ match.is_host ? 'YOU ARE HOST' : 'GUEST' }}
        </n-tag>
        <span class="match-title">{{ match.stage_name }} - {{ match.name }}</span>
      </div>
    </template>

    <div class="opponents-section">
      <n-text depth="3" size="small">VS Opponents:</n-text>
      <div class="opponents-list">
        <n-tag v-for="opp in match.opponent_names" :key="opp" size="small" :bordered="false" type="info">
          {{ opp }}
        </n-tag>
      </div>
    </div>

    <n-divider style="margin: 12px 0" />

    <div class="room-section">
      <!-- Host View: Input -->
      <div v-if="match.is_host">
        <n-text strong>🏠 Room Number (Required)</n-text>
        <n-input-group style="margin-top: 8px;">
          <n-input 
            v-model:value="localRoomNumber" 
            placeholder="Ex: 123456" 
            :status="!localRoomNumber ? 'warning' : undefined"
          />
          <n-button type="primary" @click="saveRoom" :loading="saving" :disabled="!localRoomNumber || localRoomNumber === match.room_number">
            Update
          </n-button>
        </n-input-group>
      </div>

      <!-- Guest View: Display -->
      <div v-else>
        <div v-if="match.room_number" class="room-display">
          <n-text depth="3">Room Number:</n-text>
          <div class="room-code">{{ match.room_number }}</div>
          <n-button size="tiny" secondary type="info" @click="copyRoom">Copy</n-button>
        </div>
        <div v-else class="waiting-room">
          <n-spin size="small" v-if="false" /> 
          <n-text depth="3" italic>Waiting for host to create room...</n-text>
        </div>
      </div>
    </div>
    
    <template #action>
       <!-- Future: Add 'Submit Result' button here -->
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NCard, NTag, NText, NInput, NInputGroup, NButton, NDivider, NSpin, useMessage } from 'naive-ui'
import type { MatchResponse } from '../api/matches'
import { updateRoomNumber } from '../api/matches'
import { useAuthStore } from '../stores/auth'

const props = defineProps<{
  match: MatchResponse
}>()

const emit = defineEmits(['room-updated'])

const auth = useAuthStore()
const message = useMessage()
const saving = ref(false)
const localRoomNumber = ref(props.match.room_number || '')

// Keep local state in sync if parent updates (e.g. polling)
watch(() => props.match.room_number, (newVal) => {
  if (newVal) localRoomNumber.value = newVal
})

const saveRoom = async () => {
  if (!auth.token) return
  saving.value = true
  try {
    await updateRoomNumber(auth.token, props.match.id, localRoomNumber.value)
    message.success('Room number updated!')
    emit('room-updated') // Tell parent to refresh
  } catch (e) {
    message.error('Failed to update room')
  } finally {
    saving.value = false
  }
}

const copyRoom = () => {
  if (props.match.room_number) {
    navigator.clipboard.writeText(props.match.room_number)
    message.success('Copied!')
  }
}
</script>

<style scoped>
.match-card {
  transition: all 0.2s;
}
.host-card {
  border-color: #7CB342;
  border-width: 2px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.match-title {
  font-weight: bold;
  font-size: 0.95rem;
}
.opponents-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}
.room-display {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f5f5f5;
  padding: 8px 12px;
  border-radius: 8px;
}
.room-code {
  font-family: monospace;
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
  letter-spacing: 2px;
}
.waiting-room {
  background: #fff8e1;
  padding: 8px;
  border-radius: 8px;
  text-align: center;
  border: 1px dashed #ffb300;
}
</style>
