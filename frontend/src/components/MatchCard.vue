<template>
  <div class="match-card" :class="{ 'has-result': hasResult }">
    <div class="match-header">
       <n-text strong>{{ match.name || 'Match' }}</n-text>
       <n-tag v-if="hasResult" type="success" size="small" style="margin-left: 8px">Done</n-tag>
    </div>

    <div class="players-container">
        <div v-for="p in match.participants" :key="p.player.id" class="player-row">
            <div class="player-info">
                <span v-if="match.host_player_id === p.player.id" class="host-icon" title="Host">🏠</span>
                <span class="player-name">{{ p.player.name }}</span>
            </div>

            <div class="rank-selector">
                <div
                    v-for="r in 5"
                    :key="r"
                    class="rank-checkbox"
                    :class="{ 'checked': isRankChecked(p.player.id, r) }"
                    @click="toggleRank(p.player.id, r)"
                >
                    {{ r }}
                </div>
            </div>
        </div>
    </div>

    <div class="actions">
        <n-button type="primary" size="small" @click="save" :disabled="!isDirty && !hasResult">
            Save
        </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { NText, NTag, NButton } from 'naive-ui';

// Props
const props = defineProps<{
    match: any; // Using any for simplicity with complex nested types, or import shared interface
}>();

const emit = defineEmits(['save']);

// State: Map of player_id -> selected rank (number | null)
// But requirement says "Top 5 checkboxes".
// Can a player have multiple ranks? (3 horses).
// "Checking the Nth place means this player took the Nth place."
// If a player has multiple horses, they could take 1st and 3rd.
// So we need a set of (player, rank) tuples.
const selectedRanks = ref<Set<string>>(new Set()); // Format: "playerId_rank"

const hasResult = computed(() => props.match.results && props.match.results.length > 0);
const isDirty = ref(false);

// Initialize from props
const init = () => {
    selectedRanks.value.clear();
    if (props.match.results) {
        for (const res of props.match.results) {
            // Check box if rank is 1-5
            if (res.rank >= 1 && res.rank <= 5) {
                selectedRanks.value.add(`${res.player_id}_${res.rank}`);
            }
        }
    }
};

watch(() => props.match, init, { deep: true, immediate: true });

const isRankChecked = (playerId: string, rank: number) => {
    return selectedRanks.value.has(`${playerId}_${rank}`);
};

const toggleRank = (playerId: string, rank: number) => {
    if (!playerId) return;
    const key = `${playerId}_${rank}`;
    if (selectedRanks.value.has(key)) {
        selectedRanks.value.delete(key);
    } else {
        // Validation: Can another player have this rank?
        // Usually NO. Only one horse wins 1st place.
        // So we should uncheck this rank for OTHER players.
        // Iterate all selectedRanks, remove any that end with `_${rank}`
        // Unless it's the same player? No, distinct players.
        // Wait, what if the SAME player has multiple horses?
        // Can Player A take 1st and 1st? No.
        // Can Player A take 1st and Player B take 1st? No.
        // So uniqueness on Rank is strict.

        // Remove existing owner of this rank
        const toRemove = [];
        for (const k of selectedRanks.value) {
            if (k.endsWith(`_${rank}`)) {
                toRemove.push(k);
            }
        }
        toRemove.forEach(k => selectedRanks.value.delete(k));

        selectedRanks.value.add(key);
    }
    isDirty.value = true;
};

const save = () => {
    // Convert Set to API payload
    const results = [];
    for (const key of selectedRanks.value) {
        const [pid, rStr] = key.split('_');
        if (rStr) { // Check if rStr is defined
            results.push({
                player_id: pid,
                rank: parseInt(rStr)
            });
        }
    }
    emit('save', {
        matchId: props.match.id,
        results: results
    });
    isDirty.value = false;
};

</script>

<style scoped>
.match-card {
    display: flex;
    flex-direction: row; /* Default row */
    align-items: flex-start;
    padding: 10px;
    gap: 10px;
    background-color: #fff; /* Naive UI card usually has bg, but n-list-item might not */
    border-radius: 4px;
}

.match-card.has-result {
    background-color: #f0f9eb; /* Light green */
}

/* Mobile responsive */
@media (max-width: 600px) {
    .match-card {
        flex-direction: column;
    }
}

.match-header {
    width: 100px;
    flex-shrink: 0;
    font-size: 0.9em;
}

.players-container {
    flex: 1;
    display: flex;
    flex-direction: column; /* 3 players vertically stacked */
    gap: 8px;
}

.player-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #eee;
    padding-bottom: 4px;
}
.player-row:last-child {
    border-bottom: none;
}

.player-info {
    display: flex;
    align-items: center;
    min-width: 100px;
    font-weight: 500;
}

.host-icon {
    margin-right: 4px;
}

.rank-selector {
    display: flex;
    gap: 4px;
}

.rank-checkbox {
    width: 24px;
    height: 24px;
    border: 1px solid #ddd;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 0.8em;
    user-select: none;
    background: #fff;
    color: #666;
}

.rank-checkbox:hover {
    border-color: #36ad6a; /* Naive primary */
}

.rank-checkbox.checked {
    background-color: #36ad6a;
    color: white;
    border-color: #36ad6a;
}

.actions {
    display: flex;
    align-items: center;
    justify-content: center;
    padding-left: 10px;
}
</style>
