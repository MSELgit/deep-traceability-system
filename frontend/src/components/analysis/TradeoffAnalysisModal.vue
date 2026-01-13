<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="tradeoff-modal-overlay"
    >
      <div class="tradeoff-modal-content">
        <!-- Modal Header -->
        <div class="modal-header">
          <h2>Tradeoff Analysis - {{ caseName }}</h2>
          <button class="close-btn" @click="closeModal" title="Close (ESC)">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Modal Body - Two Column Layout -->
        <div class="modal-body">
          <!-- Left Column: Matrix (60%) -->
          <div class="left-column">
            <div class="column-header">
              <h3>Tradeoff Matrix</h3>
              <div class="mode-toggle">
                <button
                  :class="['toggle-btn', { active: currentMode === 'cosTheta' }]"
                  @click="currentMode = 'cosTheta'"
                >
                  cos θ
                </button>
                <button
                  :class="['toggle-btn', { active: currentMode === 'energy' }]"
                  @click="currentMode = 'energy'"
                >
                  Energy
                </button>
              </div>
            </div>
            <div class="matrix-container">
              <MatrixHeatmap
                v-if="cosThetaMatrix && cosThetaMatrix.length > 0"
                :cos-theta-matrix="cosThetaMatrix"
                :inner-product-matrix="innerProductMatrix"
                :energy-matrix="energyMatrix"
                :performance-names="performanceNames"
                :performance-ids="performanceIds"
                :cell-size="cellSize"
                :hide-toggle="true"
                :external-mode="currentMode"
                @cell-click="onCellClick"
              />
              <div v-else class="matrix-placeholder">
                <span>No data available</span>
              </div>
            </div>
          </div>

          <!-- Right Column: Details (40%) -->
          <div class="right-column">
            <!-- Tab Navigation -->
            <div class="right-tabs">
              <button
                :class="['tab-btn', { active: rightTab === 'breakdown' }]"
                @click="rightTab = 'breakdown'"
              >
                Contribution
              </button>
              <button
                :class="['tab-btn', { active: rightTab === 'network' }]"
                @click="rightTab = 'network'"
              >
                Network
              </button>
              <button
                :class="['tab-btn', { active: rightTab === 'confidence' }]"
                @click="rightTab = 'confidence'"
              >
                Confidence
              </button>
            </div>

            <!-- Tab Content -->
            <div class="tab-content">
              <!-- Shapley Breakdown -->
              <div v-if="rightTab === 'breakdown'" class="tab-panel">
                <ShapleyBreakdown
                  v-if="selectedPair"
                  :perf-i-name="selectedPair.perfIName"
                  :perf-j-name="selectedPair.perfJName"
                  :perf-i-importance="selectedPair.perfIImportance"
                  :perf-j-importance="selectedPair.perfJImportance"
                  :cos-theta="selectedPair.cosTheta"
                  :cij="selectedPair.cij"
                  :node-cij="nodeShapleyResult?.C_ij"
                  :eij="selectedPair.eij"
                  :node-shapley-values="nodeShapleyValues"
                  :sum-check="nodeShapleyResult?.sum_check || 0"
                  :computation-method="nodeShapleyResult?.computation.method"
                  :computation-time="nodeShapleyResult?.computation.time_ms || 0"
                  :n-variables="nodeShapleyResult?.computation.n_variables || 0"
                  :n-attributes="nodeShapleyResult?.computation.n_attributes || 0"
                  :edge-shapley-values="edgeShapleyValues"
                  :edge-sum-check="edgeShapleyResult?.sum_check || 0"
                  :edge-computation-method="edgeShapleyResult?.computation.method"
                  :edge-computation-time="edgeShapleyResult?.computation.time_ms || 0"
                  :loading="nodeShapleyLoading || edgeShapleyLoading"
                  :error="nodeShapleyError"
                  :hide-header="false"
                  :top-n="5"
                />
                <div v-else class="select-prompt">
                  Click a cell in the matrix to see contribution breakdown
                </div>
              </div>

              <!-- Network Highlight -->
              <div v-else-if="rightTab === 'network'" class="tab-panel network-panel">
                <!--
                  Tradeoff Network Viewer

                  Node Highlighting (Shapley-based):
                  - P1/P2 nodes: Strongly highlighted (selected performance pair)
                  - Top contributing nodes: Orange/red intensity based on Shapley φ values

                  Edge Highlighting (Shapley-based):
                  - Level 1 (Strong): Top-N edges by edge Shapley |φ_e| values
                  - Level 2 (Medium): Edges with >50% of max |φ_e|
                  - Level 3 (Weak): Edges with >20% of max |φ_e|
                  - Fallback: Hybrid approach when edge Shapley not available

                  Color indicates contribution sign:
                  - Negative φ (tradeoff contributor): Red tones
                  - Positive φ (synergy contributor): Orange tones

                  When no cell is selected:
                  - Shows full network at reduced opacity (0.5)
                -->
                <TradeoffNetworkViewer
                  v-if="network"
                  :network="network"
                  :performances="performances"
                  :perf-i-id="selectedPair?.perfIId"
                  :perf-j-id="selectedPair?.perfJId"
                  :node-shapley-values="nodeShapleyValues"
                  :edge-shapley-values="edgeShapleyValues"
                  :top-n="5"
                />
                <div v-else class="network-placeholder">
                  No network data available
                </div>

                <!-- Network Highlight Legend -->
                <div class="network-legend">
                  <!-- Node Contribution -->
                  <div class="legend-group">
                    <span class="legend-group-title">Node φ</span>
                    <div class="legend-items">
                      <div class="legend-item">
                        <svg width="14" height="14" viewBox="0 0 14 14">
                          <circle cx="7" cy="7" r="5" fill="#ffe3e3" stroke="#d32f2f" stroke-width="2"/>
                        </svg>
                        <span>Selected P</span>
                      </div>
                      <div class="legend-item">
                        <svg width="14" height="14" viewBox="0 0 14 14">
                          <polygon points="7,2 12,7 7,12 2,7" fill="#c62828" stroke="#b71c1c" stroke-width="1.5"/>
                        </svg>
                        <span>−φ (tradeoff)</span>
                      </div>
                      <div class="legend-item">
                        <svg width="14" height="14" viewBox="0 0 14 14">
                          <polygon points="7,2 12,7 7,12 2,7" fill="#2e7d32" stroke="#1b5e20" stroke-width="1.5"/>
                        </svg>
                        <span>+φ (synergy)</span>
                      </div>
                    </div>
                  </div>

                  <!-- Edge Contribution -->
                  <div class="legend-group">
                    <span class="legend-group-title">Edge φ</span>
                    <div class="legend-items">
                      <div class="legend-item">
                        <svg width="20" height="14" viewBox="0 0 20 14">
                          <line x1="2" y1="7" x2="18" y2="7" stroke="#c62828" stroke-width="3"/>
                        </svg>
                        <span>−φ (tradeoff)</span>
                      </div>
                      <div class="legend-item">
                        <svg width="20" height="14" viewBox="0 0 20 14">
                          <line x1="2" y1="7" x2="18" y2="7" stroke="#2e7d32" stroke-width="3"/>
                        </svg>
                        <span>+φ (synergy)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Discretization Confidence -->
              <div v-else-if="rightTab === 'confidence'" class="tab-panel">
                <DiscretizationConfidence
                  :project-id="projectId"
                  :case-id="caseId"
                  :auto-load="true"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="modal-footer">
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
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue';
import MatrixHeatmap from './MatrixHeatmap.vue';
import ShapleyBreakdown from './ShapleyBreakdown.vue';
import DiscretizationConfidence from './DiscretizationConfidence.vue';
import TradeoffNetworkViewer from './TradeoffNetworkViewer.vue';
import { nodeShapleyApi, edgeShapleyApi } from '@/utils/api';
import type { NodeShapleyResult, NodeShapleyValue, EdgeShapleyResult, EdgeShapleyValue } from '@/utils/api';
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
  eij: number;
}

interface Props {
  show: boolean;
  projectId: string;
  caseId: string;
  caseName: string;
  cosThetaMatrix?: number[][];
  innerProductMatrix?: number[][];
  energyMatrix?: number[][];
  performanceNames: string[];
  performanceIds?: string[];
  performanceIdMap?: { [networkNodeId: string]: string };
  performanceWeights?: { [dbPerfId: string]: number };
  totalEnergy?: number;
  spectralRadius?: number;
  network?: any;
  performances?: any[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'update:show', value: boolean): void;
}>();

// State
const currentMode = ref<'cosTheta' | 'energy'>('cosTheta');
const rightTab = ref<'breakdown' | 'network' | 'confidence'>('breakdown');
const selectedPair = ref<SelectedPair | null>(null);
const nodeShapleyResult = ref<NodeShapleyResult | null>(null);
const nodeShapleyLoading = ref(false);
const nodeShapleyError = ref<string | null>(null);
const edgeShapleyResult = ref<EdgeShapleyResult | null>(null);
const edgeShapleyLoading = ref(false);

// Computed
const nodeShapleyValues = computed<NodeShapleyValue[]>(() => {
  return nodeShapleyResult.value?.node_shapley_values || [];
});

const edgeShapleyValues = computed<EdgeShapleyValue[]>(() => {
  return edgeShapleyResult.value?.edge_shapley_values || [];
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

// Dynamic cell size based on performance count
const cellSize = computed(() => {
  const n = props.performanceNames.length;
  if (n <= 4) return 64;
  if (n <= 6) return 56;
  if (n <= 8) return 48;
  if (n <= 10) return 40;
  return 36;
});

// Methods
function closeModal() {
  emit('close');
  emit('update:show', false);
}

function resetState() {
  selectedPair.value = null;
  nodeShapleyResult.value = null;
  nodeShapleyError.value = null;
  edgeShapleyResult.value = null;
  edgeShapleyLoading.value = false;
  currentMode.value = 'cosTheta';
  rightTab.value = 'breakdown';
}

async function onCellClick(payload: { i: number; j: number; perfIId?: string; perfJId?: string }) {
  const { i, j, perfIId, perfJId } = payload;

  let perfIImportance: number | undefined;
  let perfJImportance: number | undefined;

  if (props.performanceWeights && perfIId && perfJId) {
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

  if (perfIId && perfJId) {
    await fetchShapleyValues(perfIId, perfJId);
  }
}

async function fetchShapleyValues(perfIId: string, perfJId: string) {
  nodeShapleyLoading.value = true;
  nodeShapleyError.value = null;
  edgeShapleyLoading.value = true;

  // Fetch node Shapley (V ∪ A) and edge Shapley in parallel
  const [nodePromise, edgePromise] = [
    nodeShapleyApi.computeForPair(props.projectId, props.caseId, perfIId, perfJId, 'auto'),
    edgeShapleyApi.computeForPair(props.projectId, props.caseId, perfIId, perfJId, 'auto')
  ];

  // Handle node Shapley
  try {
    const response = await nodePromise;
    nodeShapleyResult.value = response.data;
  } catch (err: any) {
    console.error('Failed to fetch Node Shapley values:', err);
    nodeShapleyError.value = err.response?.data?.detail || 'Failed to compute Shapley values';
    nodeShapleyResult.value = null;
  } finally {
    nodeShapleyLoading.value = false;
  }

  // Handle edge Shapley (don't block on errors)
  try {
    const response = await edgePromise;
    edgeShapleyResult.value = response.data;
    console.log('Edge Shapley loaded:', edgeShapleyResult.value?.edge_shapley_values?.length, 'edges');
  } catch (err: any) {
    console.warn('Failed to fetch Edge Shapley values:', err);
    edgeShapleyResult.value = null;
  } finally {
    edgeShapleyLoading.value = false;
  }
}

// ESC key handler
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.show) {
    closeModal();
  }
}

// Reset state when modal opens
watch(() => props.show, (newVal) => {
  if (newVal) {
    resetState();
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});

// Setup ESC key listener
onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
  document.body.style.overflow = '';
});
</script>

<style scoped lang="scss">
@use '../../style/color' as *;
@use 'sass:color';

.tradeoff-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.tradeoff-modal-content {
  background: $gray;
  width: 90vw;
  height: 85vh;
  max-height: 85vh;
  border-radius: 1.2vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 2vh 6vh rgba(0, 0, 0, 0.5);
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(0.8rem, 1.5vh, 1.2rem) clamp(1rem, 2vw, 1.5rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.85);
  background: linear-gradient(135deg, color.adjust($gray, $lightness: 8%) 0%, color.adjust($gray, $lightness: 5%) 100%);

  h2 {
    margin: 0;
    font-size: clamp(1rem, 1.6vw, 1.2rem);
    font-weight: 600;
    color: $white;
  }

  .close-btn {
    padding: 0.5rem;
    background: color.adjust($gray, $lightness: 18%);
    border: 1px solid color.adjust($white, $alpha: -0.85);
    border-radius: 6px;
    color: $white;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      background: $sub_1;
      border-color: $sub_1;
    }
  }
}

.modal-body {
  flex: 1;
  display: flex;
  gap: 1.5vw;
  padding: 1.5vw;
  overflow: hidden;
  min-height: 0;
}

.left-column {
  flex: 0 0 60%;
  max-width: 60%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: color.adjust($gray, $lightness: 6%);
  border-radius: 10px;
  padding: 1rem;
  border: 1px solid color.adjust($white, $alpha: -0.9);

  .column-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid color.adjust($white, $alpha: -0.9);

    h3 {
      margin: 0;
      font-size: 0.95rem;
      font-weight: 600;
      color: $white;
    }

    .mode-toggle {
      display: flex;
      gap: 2px;
      background: color.adjust($gray, $lightness: 12%);
      border-radius: 6px;
      padding: 3px;
      border: 1px solid color.adjust($white, $alpha: -0.9);
    }

    .toggle-btn {
      padding: 0.4rem 0.85rem;
      background: transparent;
      border: none;
      border-radius: 4px;
      color: color.adjust($white, $alpha: -0.3);
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;

      &:hover:not(.active) {
        color: $white;
        background: color.adjust($gray, $lightness: 18%);
      }

      &.active {
        background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
        color: $white;
        box-shadow: 0 2px 6px color.adjust($main_1, $alpha: -0.5);
      }
    }
  }

  .matrix-container {
    flex: 1;
    overflow: auto;
    background: color.adjust($gray, $lightness: 10%);
    border-radius: 8px;
    padding: 0.75rem;

    // Custom scrollbar
    &::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    &::-webkit-scrollbar-track {
      background: color.adjust($gray, $lightness: 8%);
      border-radius: 4px;
    }
    &::-webkit-scrollbar-thumb {
      background: color.adjust($gray, $lightness: 25%);
      border-radius: 4px;
      &:hover {
        background: color.adjust($gray, $lightness: 30%);
      }
    }
  }
}

.right-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  background: color.adjust($gray, $lightness: 6%);
  border-radius: 10px;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.right-tabs {
  display: flex;
  gap: 2px;
  padding: 0.75rem 0.75rem 0;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 10px 10px 0 0;

  .tab-btn {
    flex: 1;
    padding: 0.6rem 0.75rem;
    background: transparent;
    border: none;
    border-radius: 6px 6px 0 0;
    color: color.adjust($white, $alpha: -0.35);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;

    &:hover:not(.active) {
      color: $white;
      background: color.adjust($gray, $lightness: 12%);
    }

    &.active {
      background: color.adjust($gray, $lightness: 6%);
      color: $white;
      font-weight: 600;

      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, $main_1, $main_2);
      }
    }
  }
}

.tab-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tab-panel {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;

  // Custom scrollbar
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: color.adjust($gray, $lightness: 8%);
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb {
    background: color.adjust($gray, $lightness: 25%);
    border-radius: 3px;
  }

  &.network-panel {
    padding: 0.75rem;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
}

.network-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.5rem 0.75rem;
  background: color.adjust($gray, $lightness: 5%);
  border-radius: 6px;
  flex-shrink: 0;
}

.legend-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-group-title {
  font-size: 0.65rem;
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-items {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  color: color.adjust($white, $alpha: -0.2);

  svg {
    flex-shrink: 0;
  }
}

.network-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: color.adjust($white, $alpha: -0.3);
  font-style: italic;
  font-size: 0.85rem;
}

.matrix-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 8px;
  color: color.adjust($white, $alpha: -0.3);
  font-style: italic;
}

.select-prompt {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  color: color.adjust($white, $alpha: -0.3);
  font-style: italic;
  font-size: 0.85rem;
  text-align: center;
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 6px;
}

.modal-footer {
  padding: 0.85rem 1.5rem;
  border-top: 1px solid color.adjust($white, $alpha: -0.85);
  background: linear-gradient(135deg, color.adjust($gray, $lightness: 8%) 0%, color.adjust($gray, $lightness: 5%) 100%);
}

.summary-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
  background: color.adjust($gray, $lightness: 12%);
  border-radius: 6px;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.stat-label {
  font-size: 0.75rem;
  color: color.adjust($white, $alpha: -0.25);
  font-weight: 500;
}

.stat-value {
  font-size: 0.9rem;
  font-weight: 700;
  color: $white;

  &.tradeoff {
    color: $sub_1;
  }

  &.synergy {
    color: $sub_4;
  }

  &.warn {
    color: #FFC107;
  }
}
</style>
