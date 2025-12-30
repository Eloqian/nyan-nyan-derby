<template>
  <div class="stage-standings">
    <n-space vertical size="large">
      <n-card title="Stage Standings" :bordered="false">
        <n-space align="center">
          <n-text>Stage ID:</n-text>
          <n-input v-model:value="stageIdInput" placeholder="Enter Stage UUID" style="width: 300px" />
          <n-button type="primary" @click="loadStandings">Load Standings</n-button>
        </n-space>
      </n-card>

      <div v-if="loading" class="loading-state">
        <n-spin size="large" description="Calculating Standings..." />
      </div>

      <div v-else-if="error" class="error-state">
        <n-alert title="Error" type="error">
          {{ error }}
        </n-alert>
      </div>

      <div v-else-if="standings.length > 0">
        <n-data-table
          :columns="columns"
          :data="standings"
          :bordered="false"
          :single-line="false"
          striped
        />
      </div>
      <n-empty v-else description="No data loaded or stage empty." />
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue';
import { useRoute } from 'vue-router';
import { NSpace, NCard, NText, NInput, NButton, NSpin, NAlert, NDataTable, NEmpty, NTag } from 'naive-ui';
import axios from 'axios';

interface StandingsItem {
  rank: number;
  player_id: string;
  name: string;
  total_points: number;
  matches_played: number;
  first_places: number;
  is_npc: boolean;
}

const route = useRoute();
const stageIdInput = ref('');
const loading = ref(false);
const error = ref<string | null>(null);
const standings = ref<StandingsItem[]>([]);

const API_BASE = '/api';

const columns = [
  {
    title: 'Rank',
    key: 'rank',
    sorter: 'default',
    width: 80,
    render(row: StandingsItem) {
      // Highlight top ranks maybe?
      return h('strong', {}, row.rank);
    }
  },
  {
    title: 'Player',
    key: 'name',
    sorter: (row1: StandingsItem, row2: StandingsItem) => row1.name.localeCompare(row2.name),
    render(row: StandingsItem) {
      if (row.is_npc) {
         return h('span', { style: { color: 'gray' } }, `${row.name} (NPC)`);
      }
      return row.name;
    }
  },
  {
    title: 'Total Points',
    key: 'total_points',
    sorter: (row1: StandingsItem, row2: StandingsItem) => row1.total_points - row2.total_points,
    render(row: StandingsItem) {
        return h(NTag, { type: 'success', bordered: false }, { default: () => row.total_points });
    }
  },
  {
    title: '1st Places',
    key: 'first_places',
    sorter: (row1: StandingsItem, row2: StandingsItem) => row1.first_places - row2.first_places
  },
  {
    title: 'Matches Played',
    key: 'matches_played'
  }
];

onMounted(() => {
  if (route.params.stageId) {
    stageIdInput.value = route.params.stageId as string;
    loadStandings();
  }
});

const loadStandings = async () => {
  if (!stageIdInput.value) {
    return;
  }
  loading.value = true;
  error.value = null;
  standings.value = [];

  try {
    const response = await axios.get(`${API_BASE}/stages/${stageIdInput.value}/standings`);
    standings.value = response.data;
  } catch (err: any) {
    console.error(err);
    error.value = err.response?.data?.detail || err.message || 'Failed to load standings';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.stage-standings {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}
.loading-state, .error-state {
  padding: 40px;
  text-align: center;
}
</style>
