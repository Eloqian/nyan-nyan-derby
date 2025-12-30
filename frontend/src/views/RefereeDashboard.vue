<template>
  <div class="referee-dashboard">
    <n-space vertical size="large">
      <n-card title="Referee Dashboard" :bordered="false">
        <n-space align="center">
            <n-text>Stage ID:</n-text>
            <n-input v-model:value="stageIdInput" placeholder="Enter Stage UUID" style="width: 300px" />
            <n-button type="primary" @click="loadData">Load Matches</n-button>
        </n-space>
      </n-card>

      <div v-if="loading" class="loading-state">
        <n-spin size="large" description="Loading matches..." />
      </div>

      <div v-else-if="error" class="error-state">
        <n-alert title="Error" type="error">
          {{ error }}
        </n-alert>
      </div>

      <div v-else>
        <n-list v-for="group in groups" :key="group.id" bordered class="group-list">
            <template #header>
                <n-text strong class="group-title">{{ group.name }}</n-text>
            </template>
            <n-list-item v-for="match in group.matches" :key="match.id">
                <MatchCard :match="match" @save="handleSave" />
            </n-list-item>
        </n-list>
        <n-empty v-if="groups.length === 0" description="No matches found." />
      </div>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { NSpace, NCard, NText, NInput, NButton, NSpin, NAlert, NList, NListItem, NEmpty, useMessage } from 'naive-ui';
import MatchCard from '../components/MatchCard.vue';
import axios from 'axios';

interface PlayerView {
    id: string;
    name: string;
    is_npc: boolean;
}

interface ParticipantView {
    player: PlayerView;
}

interface MatchResult {
    player_id: string;
    rank: number;
    points: number;
}

interface MatchView {
    id: string;
    name: string | null;
    status: string;
    host_player_id: string | null;
    participants: ParticipantView[];
    results: MatchResult[];
}

interface GroupView {
    id: string;
    name: string;
    matches: MatchView[];
}

const route = useRoute();
const message = useMessage();
const stageIdInput = ref('');
const loading = ref(false);
const error = ref<string | null>(null);
const groups = ref<GroupView[]>([]);

const API_BASE = '/api'; // Adjust based on Vite proxy setup

onMounted(() => {
    if (route.params.stageId) {
        stageIdInput.value = route.params.stageId as string;
        loadData();
    } else {
        // Just for dev/demo purposes, maybe load a default or wait for input
    }
});

const loadData = async () => {
    if (!stageIdInput.value) {
        message.warning('Please enter a Stage ID');
        return;
    }

    loading.value = true;
    error.value = null;
    groups.value = [];

    try {
        const response = await axios.get(`${API_BASE}/stages/${stageIdInput.value}/matches_view`);
        groups.value = response.data;
    } catch (err: any) {
        console.error(err);
        error.value = err.response?.data?.detail || err.message || 'Failed to load matches';
    } finally {
        loading.value = false;
    }
};

const handleSave = async (payload: { matchId: string, results: { player_id: string, rank: number }[] }) => {
    try {
        // Assuming single race (race_number = 1) for now as per dashboard simplicity
        const race_number = 1;

        await axios.post(`${API_BASE}/matches/${payload.matchId}/result`, {
            race_number: race_number,
            rankings: payload.results
        });

        message.success('Match result saved successfully');
        // Refresh data to show updated status/background
        // Or just update local state if we want to avoid reload
        // For simplicity, let's reload to ensure sync
        await loadData();

    } catch (err: any) {
        console.error(err);
        message.error('Failed to save result: ' + (err.response?.data?.detail || err.message));
    }
};
</script>

<style scoped>
.referee-dashboard {
    padding: 20px;
    max-width: 800px; /* Or 100% for mobile */
    margin: 0 auto;
}
.group-list {
    margin-bottom: 20px;
}
.group-title {
    font-size: 1.1em;
}
.loading-state, .error-state {
    padding: 40px;
    text-align: center;
}
</style>
