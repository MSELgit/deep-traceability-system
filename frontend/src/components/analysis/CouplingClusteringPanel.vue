<template>
  <div class="coupling-clustering-panel">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Computing coupling & clustering...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <span class="error-icon">⚠️</span>
      <span>{{ error }}</span>
      <button class="retry-btn" @click="fetchData">Retry</button>
    </div>

    <!-- No Tradeoffs -->
    <div v-else-if="!data || data.n_tradeoffs === 0" class="empty-state">
      <span>No tradeoffs found (cos θ &lt; 0)</span>
    </div>

    <!-- Content -->
    <div v-else class="content">
      <!-- Tab Navigation -->
      <div class="inner-tabs">
        <button
          :class="['inner-tab', { active: activeTab === 'dendrogram' }]"
          @click="activeTab = 'dendrogram'"
        >
          Dendrogram
        </button>
        <button
          :class="['inner-tab', { active: activeTab === 'clusters' }]"
          @click="activeTab = 'clusters'"
        >
          Clusters
        </button>
        <button
          :class="['inner-tab', { active: activeTab === 'coupling' }]"
          @click="activeTab = 'coupling'"
        >
          Coupling Matrix
        </button>
        <button
          :class="['inner-tab', { active: activeTab === 'connection' }]"
          @click="activeTab = 'connection'"
        >
          Connection Matrix
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Dendrogram View -->
        <div v-if="activeTab === 'dendrogram'" class="dendrogram-view">
          <InteractiveDendrogram
            v-if="data.dendrogram"
            :data="data.dendrogram"
            @threshold-change="onThresholdChange"
          />
          <div v-else class="empty-state">
            <span>Dendrogram data not available</span>
          </div>
        </div>

        <!-- Clusters View -->
        <div v-if="activeTab === 'clusters'" class="clusters-view">
          <div
            v-for="(members, clusterId) in data.clustering.cluster_groups"
            :key="clusterId"
            class="cluster-card"
            :style="{ borderLeftColor: getClusterColor(Number(clusterId)) }"
          >
            <div class="cluster-header">
              <span class="cluster-id" :style="{ backgroundColor: getClusterColor(Number(clusterId)) }">
                Cluster {{ clusterId }}
              </span>
              <span class="member-count">{{ members.length }} performances</span>
            </div>
            <div class="cluster-members">
              <span
                v-for="member in members"
                :key="member.perf_idx"
                class="member-chip"
              >
                {{ member.perf_label }}
              </span>
            </div>
          </div>
        </div>

        <!-- Coupling Matrix View -->
        <div v-if="activeTab === 'coupling'" class="matrix-view">
          <div class="matrix-scroll">
            <table class="heatmap-table">
              <thead>
                <tr>
                  <th></th>
                  <th v-for="(label, idx) in data.tradeoff_labels" :key="idx" class="rotated-header">
                    <span>{{ label }}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in data.coupling_matrix" :key="i">
                  <td class="row-label">{{ data.tradeoff_labels[i] }}</td>
                  <td
                    v-for="(value, j) in row"
                    :key="j"
                    :style="{ backgroundColor: getCouplingColor(value) }"
                    class="matrix-cell"
                    :title="`${data.tradeoff_labels[i]} ↔ ${data.tradeoff_labels[j]}: ${value.toFixed(3)}`"
                  >
                    {{ value.toFixed(2) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="matrix-legend">
            <span>Low coupling</span>
            <div class="gradient-bar"></div>
            <span>High coupling</span>
          </div>
        </div>

        <!-- Connection Matrix View -->
        <div v-if="activeTab === 'connection'" class="matrix-view">
          <div class="matrix-scroll">
            <table class="heatmap-table">
              <thead>
                <tr>
                  <th></th>
                  <th v-for="(label, idx) in data.performance_labels" :key="idx" class="rotated-header">
                    <span>{{ label }}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in data.performance_connection_matrix" :key="i">
                  <td class="row-label">{{ data.performance_labels[i] }}</td>
                  <td
                    v-for="(value, j) in row"
                    :key="j"
                    :style="{ backgroundColor: getConnectionColor(value, i, j) }"
                    class="matrix-cell"
                    :title="`${data.performance_labels[i]} ↔ ${data.performance_labels[j]}: ${value.toFixed(3)}`"
                  >
                    {{ i === j ? '-' : value.toFixed(2) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="matrix-legend">
            <span>Low connection</span>
            <div class="gradient-bar connection"></div>
            <span>High connection</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { couplingApi, type CouplingResult } from '@/utils/api';
import InteractiveDendrogram from './InteractiveDendrogram.vue';

const props = defineProps<{
  projectId: string;
  caseId: string;
  autoLoad?: boolean;
}>();

const loading = ref(false);
const error = ref<string | null>(null);
const data = ref<CouplingResult | null>(null);
const activeTab = ref<'dendrogram' | 'clusters' | 'coupling' | 'connection'>('dendrogram');
const dynamicClusters = ref<number[] | null>(null);

function onThresholdChange(_height: number, clusters: number[]) {
  dynamicClusters.value = clusters;
  // Could update cluster display in real-time if desired
}

const CLUSTER_COLORS = [
  '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336',
  '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#E91E63'
];

function getClusterColor(clusterId: number): string {
  return CLUSTER_COLORS[(clusterId - 1) % CLUSTER_COLORS.length];
}

function getCouplingColor(value: number): string {
  // 0 = dark gray, 1 = orange
  const intensity = Math.min(1, Math.max(0, value));
  const r = Math.round(45 + intensity * (255 - 45));
  const g = Math.round(45 + intensity * (152 - 45));
  const b = Math.round(45 + intensity * (0 - 45));
  return `rgb(${r}, ${g}, ${b})`;
}

function getConnectionColor(value: number, i: number, j: number): string {
  if (i === j) return '#333';
  // 0 = dark gray, 1 = blue
  const intensity = Math.min(1, Math.max(0, value));
  const r = Math.round(45 + intensity * (33 - 45));
  const g = Math.round(45 + intensity * (150 - 45));
  const b = Math.round(45 + intensity * (243 - 45));
  return `rgb(${r}, ${g}, ${b})`;
}

async function fetchData() {
  loading.value = true;
  error.value = null;

  try {
    const response = await couplingApi.getForCase(props.projectId, props.caseId);
    data.value = response.data;
  } catch (err: any) {
    console.error('Failed to fetch coupling data:', err);
    error.value = err.response?.data?.detail || 'Failed to compute coupling';
  } finally {
    loading.value = false;
  }
}

watch(() => [props.projectId, props.caseId], () => {
  if (props.autoLoad !== false) {
    fetchData();
  }
}, { immediate: false });

onMounted(() => {
  if (props.autoLoad !== false) {
    fetchData();
  }
});
</script>

<style scoped lang="scss">
@use '../../style/color' as *;
@use 'sass:color';

.coupling-clustering-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: color.adjust($white, $alpha: -0.4);
  font-size: 0.85rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid color.adjust($white, $alpha: -0.8);
  border-top-color: $main_1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  color: $sub_1;

  .retry-btn {
    padding: 0.4rem 0.8rem;
    background: $sub_1;
    border: none;
    border-radius: 4px;
    color: $white;
    cursor: pointer;
    font-size: 0.75rem;

    &:hover {
      background: color.adjust($sub_1, $lightness: -10%);
    }
  }
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.summary-row {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
}

.stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 6px;
  border: 1px solid color.adjust($white, $alpha: -0.9);

  .stat-value {
    font-size: 1.2rem;
    font-weight: 700;
    color: $white;
  }

  .stat-label {
    font-size: 0.7rem;
    color: color.adjust($white, $alpha: -0.4);
    text-transform: uppercase;
  }
}

.inner-tabs {
  display: flex;
  gap: 2px;
  padding: 0.25rem 0.5rem;
  background: color.adjust($gray, $lightness: 5%);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
}

.inner-tab {
  flex: 1;
  padding: 0.25rem 0.4rem;
  background: transparent;
  border: 1px solid color.adjust($white, $alpha: -0.85);
  border-radius: 3px;
  color: color.adjust($white, $alpha: -0.4);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(.active) {
    background: color.adjust($gray, $lightness: 10%);
    color: $white;
  }

  &.active {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: $main_1;
    color: $white;
    font-weight: 600;
  }
}

.tab-content {
  flex: 1;
  overflow: hidden;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
}

.dendrogram-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.clusters-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: auto;
  min-height: 0;
}

.cluster-card {
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 6px;
  border: 1px solid color.adjust($white, $alpha: -0.85);
  border-left-width: 4px;
  overflow: hidden;
}

.cluster-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: color.adjust($gray, $lightness: 10%);
}

.cluster-id {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: $white;
}

.member-count {
  font-size: 0.7rem;
  color: color.adjust($white, $alpha: -0.4);
}

.cluster-members {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0.5rem 0.75rem;
}

.member-chip {
  padding: 0.25rem 0.5rem;
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 4px;
  font-size: 0.7rem;
  color: $white;
}

.implications-section {
  margin-top: 1rem;
  padding: 0.75rem;
  background: color.adjust($gray, $lightness: 5%);
  border-radius: 6px;
  border: 1px solid color.adjust($white, $alpha: -0.9);

  h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.8rem;
    color: $white;
  }

  ul {
    margin: 0;
    padding-left: 1.25rem;
    font-size: 0.75rem;
    color: color.adjust($white, $alpha: -0.3);
    line-height: 1.5;

    li {
      margin-bottom: 0.4rem;
    }

    strong {
      color: $white;
    }
  }
}

.matrix-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 0;
}

.matrix-scroll {
  flex: 1;
  overflow: auto;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 6px;
  padding: 0.5rem;
  min-height: 0;
}

.heatmap-table {
  border-collapse: collapse;
  font-size: 0.65rem;

  th, td {
    padding: 0.3rem;
    text-align: center;
    border: 1px solid color.adjust($white, $alpha: -0.9);
  }

  th {
    background: color.adjust($gray, $lightness: 10%);
    color: $white;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .rotated-header {
    height: 80px;
    white-space: nowrap;
    vertical-align: bottom;

    span {
      display: block;
      transform: rotate(-45deg);
      transform-origin: bottom left;
      width: 1.5em;
    }
  }

  .row-label {
    background: color.adjust($gray, $lightness: 10%);
    color: $white;
    font-weight: 500;
    text-align: left;
    position: sticky;
    left: 0;
    z-index: 1;
    white-space: nowrap;
    padding: 0.3rem 0.5rem;
  }

  .matrix-cell {
    color: $white;
    font-weight: 500;
    min-width: 40px;
    cursor: default;
  }
}

.matrix-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  color: color.adjust($white, $alpha: -0.4);
}

.gradient-bar {
  width: 100px;
  height: 12px;
  border-radius: 3px;
  background: linear-gradient(90deg, #2d2d2d, #FF9800);

  &.connection {
    background: linear-gradient(90deg, #2d2d2d, #2196F3);
  }
}
</style>
