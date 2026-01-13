<template>
  <div class="tradeoff-analysis-panel">
    <!-- Header with Back Button -->
    <div class="panel-header">
      <button class="back-btn" @click="$emit('close')">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Back
      </button>
      <h3 class="panel-title">Tradeoff Analysis</h3>
    </div>

    <!-- Main Content - Two Column Layout -->
    <div class="panel-content">
      <!-- Left Column: Matrix -->
      <div class="left-column">
        <MatrixHeatmap
          v-if="cosThetaMatrix && cosThetaMatrix.length > 0"
          :cos-theta-matrix="cosThetaMatrix"
          :inner-product-matrix="innerProductMatrix"
          :energy-matrix="energyMatrix"
          :performance-names="performanceNames"
          :performance-ids="performanceIds"
          :cell-size="56"
          @cell-click="onCellClick"
          @mode-change="currentMode = $event"
        />
        <div v-else class="matrix-placeholder">
          <span>No data available</span>
        </div>
      </div>

      <!-- Right Column: Details -->
      <div class="right-column">
        <!-- Shapley Breakdown -->
        <div class="section shapley-section">
          <h4 class="section-title">Contribution Breakdown</h4>
          <ShapleyBreakdown
            v-if="selectedPair"
            :perf-i-name="selectedPair.perfIName"
            :perf-j-name="selectedPair.perfJName"
            :perf-i-importance="selectedPair.perfIImportance"
            :perf-j-importance="selectedPair.perfJImportance"
            :cos-theta="selectedPair.cosTheta"
            :cij="selectedPair.cij"
            :eij="selectedPair.eij"
            :shapley-values="shapleyValues"
            :sum-check="shapleyResult?.sum_check || 0"
            :computation-method="shapleyResult?.computation.method"
            :computation-time="shapleyResult?.computation.time_ms || 0"
            :highlighted-properties="highlightedProperties"
            :loading="shapleyLoading"
            :error="shapleyError"
            :hide-header="false"
            @property-hover="onPropertyHover"
            @property-click="onPropertyClick"
          />
          <div v-else class="select-prompt">
            Click a cell in the matrix to see contribution breakdown
          </div>
        </div>

        <!-- Network Highlight -->
        <div class="section network-section">
          <h4 class="section-title">Network Highlight</h4>
          <div v-if="selectedPair" class="network-viewer-container">
            <NetworkHighlightViewer
              v-if="network"
              :network="network"
              :performances="performances"
              :highlighted-perf-id="selectedPair.perfIId"
              :highlighted-properties="highlightedPropertyIds"
              :hide-toolbar="true"
              height="280px"
            />
          </div>
          <div v-else class="select-prompt">
            Select a performance pair to highlight relevant paths
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Footer -->
    <div class="panel-footer">
      <div class="summary-stats">
        <div class="stat">
          <span class="stat-label">Total Pairs:</span>
          <span class="stat-value">{{ totalPairs }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Tradeoffs:</span>
          <span class="stat-value tradeoff">{{ tradeoffCount }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Synergies:</span>
          <span class="stat-value synergy">{{ synergyCount }}</span>
        </div>
        <div class="stat" v-if="totalEnergy !== undefined">
          <span class="stat-label">Total Energy:</span>
          <span class="stat-value">{{ formatEnergy(totalEnergy, 4) }}</span>
        </div>
        <div class="stat" v-if="spectralRadius !== undefined">
          <span class="stat-label">Spectral Radius:</span>
          <span :class="['stat-value', spectralRadius >= 1 ? 'warn' : '']">
            {{ spectralRadius.toFixed(4) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import MatrixHeatmap from './MatrixHeatmap.vue';
import ShapleyBreakdown from './ShapleyBreakdown.vue';
import NetworkHighlightViewer from '@/components/network/NetworkHighlightViewer.vue';
import { shapleyApi } from '@/utils/api';
import type { ShapleyResult, ShapleyValue } from '@/utils/api';
import { formatEnergy } from '@/utils/energyFormat';

interface SelectedPair {
  i: number;
  j: number;
  perfIId?: string;
  perfJId?: string;
  perfIName: string;
  perfJName: string;
  perfIImportance?: number;
  perfJImportance?: number;
  cosTheta: number;
  cij: number;
  eij: number;  // Partial energy E_ij
}

interface Props {
  projectId: string;
  caseId: string;
  cosThetaMatrix?: number[][];
  innerProductMatrix?: number[][];
  energyMatrix?: number[][];
  performanceNames: string[];
  performanceIds?: string[];
  performanceIdMap?: { [networkNodeId: string]: string };  // network_node_id -> db_performance_id
  performanceWeights?: { [dbPerfId: string]: number };     // db_performance_id -> weight
  totalEnergy?: number;
  spectralRadius?: number;
  network?: any;
  performances?: any[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const currentMode = ref<'cosTheta' | 'energy'>('cosTheta');
const selectedPair = ref<SelectedPair | null>(null);
const shapleyResult = ref<ShapleyResult | null>(null);
const shapleyLoading = ref(false);
const shapleyError = ref<string | null>(null);
const highlightedProperties = ref<number[]>([]);

const shapleyValues = computed<ShapleyValue[]>(() => {
  return shapleyResult.value?.shapley_values || [];
});

const highlightedPropertyIds = computed<string[]>(() => {
  // Map property indices to IDs based on network
  if (!props.network || !shapleyResult.value) return [];
  const propertyNodes = props.network.nodes?.filter((n: any) => n.layer === 2) || [];
  return highlightedProperties.value
    .map(idx => propertyNodes[idx]?.id)
    .filter(Boolean);
});

const totalPairs = computed(() => {
  const n = props.performanceNames.length;
  return (n * (n - 1)) / 2;
});

const tradeoffCount = computed(() => {
  if (!props.cosThetaMatrix) return 0;
  let count = 0;
  const n = props.cosThetaMatrix.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (props.cosThetaMatrix[i][j] < -0.1) count++;
    }
  }
  return count;
});

const synergyCount = computed(() => {
  if (!props.cosThetaMatrix) return 0;
  let count = 0;
  const n = props.cosThetaMatrix.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (props.cosThetaMatrix[i][j] > 0.1) count++;
    }
  }
  return count;
});

async function onCellClick(payload: { i: number; j: number; perfIId?: string; perfJId?: string }) {
  const { i, j, perfIId, perfJId } = payload;

  // Get importance from performance_weights (keyed by database performance ID)
  // We need to map network node IDs to database IDs using performanceIdMap
  let perfIImportance: number | undefined;
  let perfJImportance: number | undefined;

  if (props.performanceWeights && perfIId && perfJId) {
    // Map network node IDs to database IDs
    const dbPerfIId = props.performanceIdMap?.[perfIId] || perfIId;
    const dbPerfJId = props.performanceIdMap?.[perfJId] || perfJId;

    perfIImportance = props.performanceWeights[dbPerfIId];
    perfJImportance = props.performanceWeights[dbPerfJId];
  }

  const cosTheta = props.cosThetaMatrix?.[i]?.[j] || 0;
  const cij = props.innerProductMatrix?.[i]?.[j] || 0;
  const eij = props.energyMatrix?.[i]?.[j] || 0;

  selectedPair.value = {
    i,
    j,
    perfIId,
    perfJId,
    perfIName: props.performanceNames[i],
    perfJName: props.performanceNames[j],
    perfIImportance,
    perfJImportance,
    cosTheta,
    cij,
    eij,
  };

  // Reset highlights
  highlightedProperties.value = [];

  // Fetch Shapley values
  if (perfIId && perfJId) {
    await fetchShapleyValues(perfIId, perfJId);
  }
}

async function fetchShapleyValues(perfIId: string, perfJId: string) {
  shapleyLoading.value = true;
  shapleyError.value = null;

  try {
    const response = await shapleyApi.computeForPair(
      props.projectId,
      props.caseId,
      perfIId,
      perfJId,
      'auto'
    );
    shapleyResult.value = response.data;

    // Auto-highlight top contributors
    const topContributors = shapleyResult.value.shapley_values
      .slice(0, 3)
      .map((sv: ShapleyValue) => sv.property_idx);
    highlightedProperties.value = topContributors;
  } catch (err: any) {
    console.error('Failed to fetch Shapley values:', err);
    shapleyError.value = err.response?.data?.detail || 'Failed to compute Shapley values';
    shapleyResult.value = null;
  } finally {
    shapleyLoading.value = false;
  }
}

function onPropertyHover(propertyIdx: number | null) {
  if (propertyIdx === null) {
    // Restore auto-highlight
    if (shapleyResult.value) {
      highlightedProperties.value = shapleyResult.value.shapley_values
        .slice(0, 3)
        .map((sv: ShapleyValue) => sv.property_idx);
    }
  } else {
    highlightedProperties.value = [propertyIdx];
  }
}

function onPropertyClick(propertyIdx: number) {
  // Toggle highlight
  const idx = highlightedProperties.value.indexOf(propertyIdx);
  if (idx >= 0) {
    highlightedProperties.value = highlightedProperties.value.filter(p => p !== propertyIdx);
  } else {
    highlightedProperties.value = [...highlightedProperties.value, propertyIdx];
  }
}

// Reset when matrix changes
watch(() => props.cosThetaMatrix, () => {
  selectedPair.value = null;
  shapleyResult.value = null;
  highlightedProperties.value = [];
});
</script>

<style scoped>
.tradeoff-analysis-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f0f0f0;
  border-color: #ccc;
}

.panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.panel-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.left-column {
  flex: 0 0 45%;
  max-width: 45%;
  overflow: auto;
}

.right-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: auto;
}

.section {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 12px;
}

.shapley-section {
  flex: 0 0 auto;
}

.network-section {
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.section-title {
  margin: 0 0 10px 0;
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.select-prompt {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #999;
  font-style: italic;
  font-size: 12px;
}

.network-viewer-container {
  flex: 1;
  min-height: 200px;
  background: white;
  border-radius: 6px;
  overflow: hidden;
}

.matrix-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  background: #f5f5f5;
  border-radius: 8px;
  color: #999;
}

.panel-footer {
  padding: 10px 16px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.summary-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  color: #666;
}

.stat-value {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.stat-value.tradeoff {
  color: #c62828;
}

.stat-value.synergy {
  color: #2e7d32;
}

.stat-value.warn {
  color: #f57c00;
}
</style>
