<template>
  <div class="uma-card" :class="{ 'active': match.is_host }">
    <!-- Header -->
    <div class="card-upper" :class="match.is_host ? 'active-bg' : 'setup-bg'" style="height: auto; min-height: 50px; padding: 12px;">
      <div class="card-header">
        <span class="role-badge">{{ match.is_host ? 'HOST' : 'GUEST' }}</span>
        <span class="match-title-text">{{ match.stage_name }} - {{ match.name }}</span>
      </div>
    </div>

    <div class="card-content">
        <!-- Opponents -->
        <div class="opponents-section">
            <n-text depth="3" size="small" style="font-weight: bold;">VS Opponents:</n-text>
            <div class="opponents-list">
                <div v-for="opp in match.opponent_names" :key="opp" class="opp-tag">
                {{ opp }}
                </div>
            </div>
        </div>

        <div class="divider-line"></div>

        <div class="room-section">
        <!-- Host View: Input -->
        <div v-if="match.is_host">
            <n-text strong>🏠 Room Number</n-text>
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
            <span style="font-size: 0.8rem; color: #666;">ROOM:</span>
            <div class="room-code">{{ match.room_number }}</div>
            <button class="copy-btn" @click="copyRoom">Copy</button>
            </div>
            <div v-else class="waiting-room">
            <n-text depth="3" italic>Waiting for host...</n-text>
            </div>
        </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NText, NInput, NInputGroup, NButton, useMessage } from 'naive-ui'
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
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.role-badge {
  background: rgba(0,0,0,0.2);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 900;
  font-size: 0.7rem;
}
.match-title-text {
  font-weight: 800;
  color: white;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
  font-size: 0.95rem;
}

.opponents-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}
.opp-tag {
  background: #f0f0f0;
  color: #555;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 700;
}

.divider-line {
  height: 1px;
  background: #eee;
  margin: 12px 0;
}

.room-display {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #E3F2FD;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #BBDEFB;
}
.room-code {
  font-family: monospace;
  font-size: 1.2rem;
  font-weight: 900;
  color: #1976D2;
  letter-spacing: 1px;
}
.copy-btn {
  margin-left: auto;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.7rem;
  padding: 2px 6px;
}

.waiting-room {
  background: #FFFDE7;
  padding: 8px;
  border-radius: 8px;
  text-align: center;
  border: 1px dashed #FFD600;
}
</style>