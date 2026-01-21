<template>
  <div class="design-case-detail">
    <div class="detail-header">
      <h2>{{ designCase.name }} Details</h2>
      <button class="close-btn" @click="$emit('close')">✕</button>
    </div>

    <div class="detail-content">
      <!-- Basic Information (always displayed) -->
      <section class="detail-section basic-info-section">
        <h3>Basic Information</h3>
        
        <div class="section-content">
          <!-- Structure mismatch warning -->
          <div v-if="isStructureMismatch" class="structure-warning">
            <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
            <span>This design case's performance tree structure differs from the latest one</span>
          </div>
          
          <div class="info-row">
            <span class="info-label">Elevation</span>
            <span class="info-value">{{ designCase.mountain_position ? designCase.mountain_position.H.toFixed(3) : '-' }}</span>
          </div>
          
          <div class="info-row">
            <span class="info-label">Energy</span>
            <span class="info-value">{{ energyData ? formatEnergy(energyData.total_energy, 2) : '-' }}</span>
          </div> 

          <div class="info-row">
            <span class="info-label">Color</span>
            <div class="color-display">
              <div 
                class="color-box" 
                :style="{ background: designCase.color }"
              ></div>
              <span class="color-text">{{ designCase.color }}</span>
            </div>
          </div>

          <div class="info-row">
            <span class="info-label">Created</span>
            <span class="info-value">{{ formatDateTime(designCase.created_at) }}</span>
          </div>

          <div class="info-row">
            <span class="info-label">Updated</span>
            <span class="info-value">{{ formatDateTime(designCase.updated_at) }}</span>
          </div>

          <div v-if="designCase.description" class="info-row vertical">
            <span class="info-label">Description</span>
            <p class="description-text">{{ designCase.description }}</p>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- Performance Values -->
      <section class="detail-section">
        <h3 @click="toggleSection('performance')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.performance ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          Performance Values
        </h3>
        
        <div v-show="sectionStates.performance" class="section-content">
          <div class="performance-list">
          <div
            v-for="perf in performancesWithValues"
            :key="perf.id"
            class="performance-item"
          >
            <div class="perf-info">
              <span class="perf-name">{{ perf.name }}</span>
              <span class="perf-unit">{{ perf.unit || '' }}</span>
            </div>
            <div class="perf-value">{{ formatValue(designCase.performance_values[perf.id]) }}</div>
          </div>

            <div v-if="performancesWithValues.length === 0" class="empty-state">
              No performance values
            </div>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- Average Utility -->
      <section class="detail-section">
        <h3 @click="toggleSection('utility')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.utility ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          Utility Radar Chart
        </h3>
        
        <div v-show="sectionStates.utility" class="section-content">
          <div v-if="!designCase.partial_heights || !designCase.performance_weights" class="empty-state">
          To calculate average utility, click the recalculate button (<FontAwesomeIcon :icon="['fas', 'rotate-right']" />)
          </div>
          <div v-else class="radar-chart-container">
            <button class="radar-download-btn" @click="downloadRadarChart" title="Download Radar Chart">
              <FontAwesomeIcon :icon="['fas', 'camera']" />
            </button>
            <Radar ref="radarChartRef" :data="radarChartData" :options="radarChartOptions" />
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- Performance Analysis (remaining height + energy) -->
      <section v-if="remainingHeights.length > 0" class="detail-section">
        <h3 @click="toggleSection('remaining')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.remaining ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          Performance Analysis
        </h3>

        <div v-show="sectionStates.remaining" class="section-content">
          <!-- Sort buttons -->
          <div class="sort-buttons">
            <button
              class="sort-btn achievement"
              :class="{ active: perfSortKey === 'achievement' }"
              @click="perfSortKey = 'achievement'"
            >
              Achievement
            </button>
            <button
              class="sort-btn weight"
              :class="{ active: perfSortKey === 'importance' }"
              @click="perfSortKey = 'importance'"
            >
              Weight
            </button>
            <button
              class="sort-btn energy"
              :class="{ active: perfSortKey === 'energy' }"
              @click="perfSortKey = 'energy'"
            >
              Energy
            </button>
          </div>

          <!-- Performance list (table-style) -->
          <div class="perf-analysis-table">
            <!-- Header -->
            <div class="perf-analysis-header">
              <span class="col-name">Performance</span>
              <span class="col-bar">Achievement</span>
              <span class="col-importance">Weight</span>
              <span class="col-energy">Energy</span>
            </div>
            <!-- Rows -->
            <div
              v-for="item in sortedRemainingHeights"
              :key="item.perfId"
              class="perf-analysis-row"
            >
              <span class="col-name">{{ item.perfName }}</span>
              <span class="col-bar">
                <div class="bar-wrapper">
                  <div class="bar-bg">
                    <div
                      class="bar-fill"
                      :style="{ width: `${item.hMax > 0 ? Math.min(item.actual / item.hMax * 100, 100) : 0}%` }"
                    ></div>
                  </div>
                  <span class="bar-value">{{ item.achievementRate.toFixed(0) }}%</span>
                </div>
              </span>
              <span class="col-importance">{{ item.importance.toFixed(1) }}</span>
              <span class="col-energy">{{ formatEnergy(item.partialEnergy, 3) }}</span>
            </div>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- Tradeoff Analysis -->
      <section class="detail-section">
        <h3 @click="toggleSection('tradeoff')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.tradeoff ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          Tradeoff Analysis
        </h3>

        <div v-show="sectionStates.tradeoff" class="section-content">
          <div v-if="!designCase.network || designCase.network.nodes.length === 0" class="empty-state">
            Configure network structure to analyze tradeoffs
          </div>
          <div v-else-if="tradeoffLoading" class="loading-state">
            <div class="spinner"></div>
            <span>Loading analysis...</span>
          </div>
          <div v-else-if="tradeoffError" class="error-state">
            {{ tradeoffError }}
            <button @click="loadTradeoffData">Retry</button>
          </div>
          <div v-else>
            <!-- Mini Matrix Preview -->
            <TradeoffMatrixMini
              v-if="tradeoffData"
              :cos-theta-matrix="tradeoffData.cos_theta_matrix"
              :inner-product-matrix="tradeoffData.inner_product_matrix"
              :energy-matrix="tradeoffData.energy_matrix"
              :performance-names="tradeoffData.performance_names"
              :performance-ids="tradeoffData.performance_ids"
              :total-energy="tradeoffData.total_energy"
              @expand="openTradeoffModal"
              @cell-click="handleTradeoffCellClick"
            />
            <div v-else class="empty-state">
              Click recalculate button to generate tradeoff analysis
            </div>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- Network Structure -->
      <section class="detail-section">
        <h3 @click="toggleSection('network')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.network ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          Network Structure
        </h3>

        <div v-show="sectionStates.network" class="section-content">
          <div class="network-viewer-wrapper">

          <NetworkViewer
            v-if="designCase.network.nodes.length > 0"
            :network="designCase.network"
            :performances="performances"
          />
            <div v-else class="empty-state">
              Network is undefined
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Tradeoff Analysis Modal -->
    <TradeoffAnalysisModal
      v-if="tradeoffData"
      :show="showTradeoffModal"
      :project-id="projectStore.currentProject?.id || ''"
      :case-id="designCase.id"
      :case-name="designCase.name"
      :cos-theta-matrix="tradeoffData.cos_theta_matrix"
      :inner-product-matrix="tradeoffData.inner_product_matrix"
      :energy-matrix="tradeoffData.energy_matrix"
      :performance-names="tradeoffData.performance_names"
      :performance-ids="tradeoffData.performance_ids"
      :performance-id-map="tradeoffData.performance_id_map"
      :performance-weights="designCase.performance_weights"
      :total-energy="tradeoffData.total_energy"
      :spectral-radius="tradeoffData.spectral_radius"
      :network="designCase.network"
      :performances="performances"
      @close="closeTradeoffModal"
      @update:show="showTradeoffModal = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import type { DesignCase, Performance } from '../../types/project';
import NetworkViewer from '../network/NetworkViewer.vue';
import TradeoffMatrixMini from '../analysis/TradeoffMatrixMini.vue';
import TradeoffAnalysisModal from '../analysis/TradeoffAnalysisModal.vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { calculationApi, structuralTradeoffApi } from '../../utils/api';
import { useProjectStore } from '../../stores/projectStore';
import { Radar } from 'vue-chartjs';
import { isDesignCaseEditable } from '../../utils/performanceComparison';
import { formatEnergy } from '../../utils/energyFormat';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

// Custom plugin to draw background and reference lines (n-sided polygon)
const referenceLinePlugin = {
  id: 'customLines',
  beforeDraw(chart: any, _args: any, _options: any) {
    const { ctx, width, height } = chart;
    
    // Draw white background for entire canvas
    ctx.save();
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, width, height);
    ctx.restore();
  },
  afterDatasetsDraw(chart: any, _args: any, options: any) {
    const { ctx, scales } = chart;
    const { r } = scales;
    
    if (!options.lines) return;
    
    const pointLabels = r._pointLabels || [];
    const numPoints = pointLabels.length;
    
    if (numPoints === 0) return;
    
    options.lines.forEach((line: any) => {
      const radius = r.getDistanceFromCenterForValue(line.value);
      const centerX = r.xCenter;
      const centerY = r.yCenter;
      
      ctx.save();
      ctx.strokeStyle = line.color;
      ctx.lineWidth = line.width;
      ctx.setLineDash([5, 5]); // Dashed line
      ctx.beginPath();
      
      // Draw n-sided polygon
      for (let i = 0; i < numPoints; i++) {
        const angle = r.getIndexAngle(i) - Math.PI / 2; // -90 degree rotation (start from top)
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.closePath();
      ctx.stroke();
      ctx.restore();
    });
  }
};

ChartJS.register(referenceLinePlugin);

const props = defineProps<{
  designCase: DesignCase;
  performances: Performance[];
  performanceHMax: { [key: string]: number };
}>();

const emit = defineEmits<{
  close: [];
  edit: [designCase: DesignCase];
  copy: [designCase: DesignCase];
  delete: [designCase: DesignCase];
  tradeoffCellClick: [payload: { i: number; j: number; perfIId?: string; perfJId?: string }];
}>();

const projectStore = useProjectStore();

// Radar chart ref
const radarChartRef = ref();

// Structure mismatch check - use the same logic as DesignCaseForm
const isStructureMismatch = computed(() => {
  if (!props.designCase.performance_snapshot) return false;
  
  const currentPerformances = projectStore.currentProject?.performances || [];
  
  // Use the same structural comparison as the form
  return !isDesignCaseEditable(currentPerformances, props.designCase.performance_snapshot);
});

// Energy data (論文準拠式: E = Σ W_i × W_j × L(C_ij) / (Σ W_k)²)
const energyData = ref<{
  total_energy: number;
  partial_energies: { [key: string]: number };
  inner_product_matrix: number[][];  // C_ij 行列
  cos_theta_matrix: number[][];  // cos θ 行列
  energy_contributions: Array<{
    perf_i_id: string;
    perf_j_id: string;
    perf_i_label: string;
    perf_j_label: string;
    W_i: number;
    W_j: number;
    C_ij: number;
    cos_theta: number;
    L_ij: number;
    contribution: number;
  }>;
  performance_ids: string[];
  performance_labels: string[];
} | null>(null);

// Performance analysis sort key
const perfSortKey = ref<'achievement' | 'importance' | 'energy'>('achievement');

// Section open/close states (basic info is always open so excluded)
const sectionStates = ref({
  performance: true,
  utility: true,
  remaining: true,
  network: true,
  tradeoff: true
});

// Tradeoff modal state
const showTradeoffModal = ref(false);

function openTradeoffModal() {
  showTradeoffModal.value = true;
}

function closeTradeoffModal() {
  showTradeoffModal.value = false;
}

// Tradeoff analysis state
interface TradeoffData {
  cos_theta_matrix: number[][];
  inner_product_matrix: number[][];
  energy_matrix: number[][];
  performance_names: string[];
  performance_ids: string[];
  performance_id_map?: { [networkNodeId: string]: string };  // network_node_id -> db_performance_id
  total_energy?: number;
  spectral_radius?: number;
}
const tradeoffData = ref<TradeoffData | null>(null);
const tradeoffLoading = ref(false);
const tradeoffError = ref<string | null>(null);

// Toggle section open/close
function toggleSection(section: keyof typeof sectionStates.value) {
  sectionStates.value[section] = !sectionStates.value[section];
}

// Load tradeoff analysis data
async function loadTradeoffData() {
  if (!props.designCase.network || props.designCase.network.nodes.length === 0) {
    return;
  }

  tradeoffLoading.value = true;
  tradeoffError.value = null;

  try {
    const response = await structuralTradeoffApi.getForCase(
      projectStore.currentProject!.id,
      props.designCase.id
    );

    tradeoffData.value = {
      cos_theta_matrix: response.data.cos_theta_matrix,
      inner_product_matrix: response.data.inner_product_matrix || [],
      energy_matrix: response.data.energy_matrix || [],
      performance_names: response.data.performance_labels,  // API returns performance_labels
      performance_ids: response.data.performance_ids,
      performance_id_map: response.data.performance_id_map,
    };
  } catch (error: any) {
    console.error('Failed to load tradeoff data:', error);
    tradeoffError.value = error.response?.data?.detail || 'Failed to load tradeoff analysis';
  } finally {
    tradeoffLoading.value = false;
  }
}

// Handle cell click in tradeoff matrix
function handleTradeoffCellClick(payload: { i: number; j: number; perfIId?: string; perfJId?: string }) {
  // Emit to parent for expanded analysis view
  emit('tradeoffCellClick', payload);
}

// Only performances with values (from snapshot)
const performancesWithValues = computed(() => {
  // Use snapshot if available, otherwise use current performance tree (backward compatibility)
  const performances = props.designCase.performance_snapshot || props.performances;
  
  // Extract only leaf performances and filter those with values
  return performances
    .filter(perf => perf.is_leaf)
    .filter(perf => props.designCase.performance_values[perf.id] !== undefined);
});

// Radar chart data
const radarChartData = computed(() => {
  if (!props.designCase.partial_heights || !props.designCase.performance_weights) {
    return { labels: [], datasets: [] };
  }

  const labels = performancesWithValues.value.map(perf => perf.name);
  const data = performancesWithValues.value.map(perf => getAverageUtilityForPerf(perf.id));

  return {
    labels,
    datasets: [
      {
        label: 'Average Utility',
        data,
        backgroundColor: 'rgba(51, 87, 255, 0.2)',
        borderColor: 'rgba(51, 87, 255, 1)',
        borderWidth: 2,
        pointBackgroundColor: data.map((value) => 
          value < 0.5 ? 'rgba(255, 68, 68, 1)' : 'rgba(51, 87, 255, 1)'
        ),
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: data.map((value) => 
          value < 0.5 ? 'rgba(255, 68, 68, 1)' : 'rgba(51, 87, 255, 1)'
        ),
        pointRadius: 5
      }
    ]
  };
});

// Radar chart options
const radarChartOptions = computed(() => {
  const data = performancesWithValues.value.map(perf => getAverageUtilityForPerf(perf.id));
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 1,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        angleLines: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          stepSize: 0.2,
          font: {
            size: 12
          },
          color: 'rgba(102, 102, 102, 1)',
          backdropColor: 'rgba(255, 255, 255, 0.8)'
        },
        pointLabels: {
          font: {
            size: 14,
            weight: 'bold' as const
          },
          color: (context: any) => {
            // Display performance names below 0.5 in red
            const index = context.index;
            return data[index] < 0.5 ? 'rgba(255, 68, 68, 1)' : '#666';
          }
        }
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `${context.label}: ${context.parsed.r.toFixed(3)}`;
          }
        }
      },
      // Custom plugin to draw reference lines
      customLines: {
        lines: [
          { value: 0.5, color: 'rgba(255, 68, 68, 0.5)', width: 2 },  // Red line (0.5)
          { value: 0.8, color: 'rgba(255, 193, 7, 0.5)', width: 2 }   // Yellow line (0.8)
        ]
      }
    },
    layout: {
      padding: 20
    },
    elements: {
      arc: {
        backgroundColor: 'white'
      }
    }
  };
});

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

function formatValue(value: number | string): string {
  if (value === undefined || value === null) return '-';
  if (typeof value === 'string') return value;
  return Number(value).toFixed(2);
}

// Calculate average utility (partial height / total votes)
function getAverageUtilityForPerf(perfId: string): number {
  if (!props.designCase.partial_heights || !props.designCase.performance_weights) return 0;
  
  const partialHeight = props.designCase.partial_heights[perfId] || 0;
  const totalWeight = props.designCase.performance_weights[perfId] || 0;
  
  if (totalWeight === 0) return 0;
  return partialHeight / totalWeight;
}

// Calculate achievement rate for each performance
const remainingHeights = computed(() => {
  if (!props.designCase.partial_heights || !props.performanceHMax) return [];

  // Total weight for normalization
  const totalWeight = Object.values(props.designCase.performance_weights || {}).reduce((a, b) => a + b, 0);

  const results: Array<{
    perfId: string;
    perfName: string;
    hMax: number;
    actual: number;
    achievementRate: number;
    importance: number;
    partialEnergy: number;
  }> = [];

  performancesWithValues.value.forEach(perf => {
    const hMax = props.performanceHMax[perf.id] || 0;  // Normalized: W_i / Σ W_k
    const rawActual = props.designCase.partial_heights![perf.id] || 0;  // Unnormalized: Σ (w × u)
    // Normalize actual to match hMax scale
    const actual = totalWeight > 0 ? rawActual / totalWeight : 0;
    const achievementRate = hMax > 0 ? (actual / hMax) * 100 : 0;
    const importance = getPerformanceImportance(perf.id);
    const partialEnergy = energyData.value?.partial_energies[perf.id] || 0;

    results.push({
      perfId: perf.id,
      perfName: perf.name,
      hMax,
      actual,
      achievementRate,
      importance,
      partialEnergy
    });
  });

  return results;
});

// Sorted performance analysis based on selected sort key
const sortedRemainingHeights = computed(() => {
  const items = [...remainingHeights.value];

  switch (perfSortKey.value) {
    case 'achievement':
      return items.sort((a, b) => a.achievementRate - b.achievementRate);  // Low achievement first
    case 'importance':
      return items.sort((a, b) => b.importance - a.importance);
    case 'energy':
      return items.sort((a, b) => b.partialEnergy - a.partialEnergy);
    default:
      return items;
  }
});

// Fetch energy data (論文準拠式)
async function fetchEnergyData() {
  if (!projectStore.currentProject || !props.designCase) return;

  try {
    const response = await calculationApi.calculateCaseEnergy(
      projectStore.currentProject.id,
      props.designCase.id
    );
    energyData.value = {
      total_energy: response.data.total_energy,
      partial_energies: response.data.partial_energies,
      inner_product_matrix: response.data.inner_product_matrix || [],
      cos_theta_matrix: response.data.cos_theta_matrix || [],
      energy_contributions: response.data.energy_contributions || [],
      performance_ids: response.data.performance_ids || [],
      performance_labels: response.data.performance_labels || [],
    };
  } catch (error) {
    console.error('Energy calculation error:', error);
  }
}

// Get performance importance
function getPerformanceImportance(perfId: string | number): number {
  const perfIdStr = String(perfId);
  // performance_weights is total votes per performance
  if (props.designCase.performance_weights && props.designCase.performance_weights[perfIdStr] !== undefined) {
    return props.designCase.performance_weights[perfIdStr];
  }
  return 0.0; // Default value
}

// Download radar chart as image
function downloadRadarChart() {
  if (!radarChartRef.value?.chart) {
    console.error('Radar chart not available');
    return;
  }

  try {
    const chart = radarChartRef.value.chart;
    const canvas = chart.canvas;
    
    // Create download link
    const link = document.createElement('a');
    link.download = `radar-chart-${props.designCase.name}-${new Date().toISOString().slice(0, 10)}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  } catch (error) {
    console.error('Failed to download radar chart:', error);
    alert('Failed to download radar chart');
  }
}

// Recalculate energy when design case changes
watch(() => props.designCase.id, () => {
  fetchEnergyData();
  // Reset tradeoff data for new case
  tradeoffData.value = null;
  tradeoffError.value = null;
  if (sectionStates.value.tradeoff) {
    loadTradeoffData();
  }
});

// Load tradeoff data when section opens
watch(() => sectionStates.value.tradeoff, (isOpen) => {
  if (isOpen && !tradeoffData.value && !tradeoffLoading.value) {
    loadTradeoffData();
  }
});

// Fetch energy data on initial load
onMounted(() => {
  fetchEnergyData();
  // Load tradeoff data if section is open by default
  if (sectionStates.value.tradeoff) {
    loadTradeoffData();
  }
});

</script>

<style scoped lang="scss">
@use 'sass:color';
@use '../../style/color' as *;

// カスタムスクロールバースタイル
@mixin custom-scrollbar {
  &::-webkit-scrollbar {
    width: 0.8vw;
    height: 0.8vw;
  }
  
  &::-webkit-scrollbar-track {
    background: color.adjust($gray, $lightness: 5%);
    border-radius: 0.4vw;
  }
  
  &::-webkit-scrollbar-thumb {
    background: color.adjust($main_1, $alpha: -0.5);
    border-radius: 0.4vw;
    transition: background 0.3s ease;
    
    &:hover {
      background: color.adjust($main_1, $alpha: -0.3);
    }
    
    &:active {
      background: $main_1;
    }
  }
  
  // Firefox
  scrollbar-width: thin;
  scrollbar-color: color.adjust($main_1, $alpha: -0.5) color.adjust($gray, $lightness: 5%);
}

.design-case-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: color.adjust($gray, $lightness: 8%);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1rem, 2vw, 1.5rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  background: linear-gradient(145deg, color.adjust($gray, $lightness: 10%), color.adjust($gray, $lightness: 6%));
}

.detail-header h2 {
  margin: 0;
  font-size: clamp(1.1rem, 1.8vw, 1.3rem);
  font-weight: 600;
  color: $white;
}

.close-btn {
  width: clamp(1.8rem, 3vw, 2rem);
  height: clamp(1.8rem, 3vw, 2rem);
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: clamp(1.2rem, 2vw, 1.4rem);
  color: color.adjust($white, $alpha: -0.4);
  border-radius: 0.3vw;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: color.adjust($gray, $lightness: 15%);
  color: $white;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1rem, 2vw, 1.5rem);
  background: $gray;
  @include custom-scrollbar;
}

.detail-section {
  margin-bottom: clamp(1.2rem, 2vh, 1.5rem);
  background: color.adjust($gray, $lightness: 8%);
  padding: clamp(1rem, 2vh, 1.5rem);
  border-radius: 0.8vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.detail-section h3 {
  margin: 0 0 clamp(0.8rem, 1.5vh, 1rem) 0;
  font-size: clamp(0.95rem, 1.3vw, 1.1rem);
  font-weight: 600;
  color: $white;
}

/* Section header */
.section-header {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
  margin: 0 0 clamp(0.8rem, 1.5vh, 1rem) 0 !important;
}

.section-header:hover {
  color: $main_1;
}

.toggle-icon {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.5);
  transition: transform 0.2s;
}

.section-content {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-0.4vh);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.divider {
  height: 1px;
  background: color.adjust($white, $alpha: -0.95);
  margin: clamp(1.2rem, 2vh, 1.5rem) 0;
}

/* Mountain coordinate information */
.mountain-info {
  margin-bottom: 0;
}

.mountain-stats {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.2vw;
}

.stat-card {
  padding: clamp(0.8rem, 1.5vh, 1rem);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.8vw;
  text-align: center;
}

.stat-card.primary {
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  grid-column: 1 / -1;
}

.stat-label {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  color: inherit;
  opacity: 0.8;
  margin-bottom: 0.8vh;
}

.stat-card.primary .stat-label {
  color: $white;
}

.stat-value {
  font-size: clamp(1.6rem, 2.5vw, 2rem);
  font-weight: 700;
}

/* Basic information */
.basic-info-section h3 {
  margin-bottom: clamp(0.8rem, 1.5vh, 1rem) !important;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(0.6rem, 1.2vh, 0.8rem) 0;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.97);
}

.info-row.highlight {
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  padding: clamp(0.8rem, 1.5vh, 1rem);
  margin: calc(-1 * clamp(0.8rem, 1.5vh, 1rem)) calc(-1 * clamp(0.8rem, 1.5vh, 1rem)) clamp(0.8rem, 1.5vh, 1rem) calc(-1 * clamp(0.8rem, 1.5vh, 1rem));
  border-radius: 0.8vw;
  border-bottom: none;
}

.info-row.highlight .info-label {
  color: $white;
  opacity: 0.9;
}

.info-value-large {
  font-size: clamp(1.4rem, 2.2vw, 1.75rem);
  font-weight: 700;
  color: $white;
}

.info-row.vertical {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.8vh;
}

.info-label {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.5);
  font-weight: 500;
}

.info-value {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: $white;
}

.description-text {
  margin: 0;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: color.adjust($white, $alpha: -0.3);
  line-height: 1.6;
}

/* Color display */
.color-display {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  position: relative;
}

.color-box {
  width: clamp(1.8rem, 3vw, 2rem);
  height: clamp(1.8rem, 3vw, 2rem);
  border-radius: 0.5vw;
  border: 2px solid color.adjust($white, $alpha: -0.9);
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.5);
}

.color-text {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-family: monospace;
  color: color.adjust($white, $alpha: -0.4);
}


/* Performance values */
.performance-list {
  display: flex;
  flex-direction: column;
  gap: 0.8vh;
}

.performance-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(0.6rem, 1.2vh, 0.8rem);
  background: $gray;
  border-radius: 0.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.97);
  transition: all 0.2s;
}

.performance-item:hover {
  background: color.adjust($gray, $lightness: 5%);
  border-color: color.adjust($white, $alpha: -0.9);
}

.perf-info {
  display: flex;
  flex-direction: column;
  gap: 0.4vh;
}

.perf-name {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  color: $white;
}

.perf-unit {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.5);
}

.perf-value {
  font-size: clamp(0.9rem, 1.2vw, 1rem);
  font-weight: 600;
  color: $sub_4;
}

/* Utility vector */
.utility-list {
  display: flex;
  flex-direction: column;
  gap: 1.2vh;
}

/* Radar chart */
.radar-chart-container {
  width: 100%;
  height: clamp(20rem, 40vh, 25rem);
  margin: clamp(1rem, 2vh, 1.25rem) auto;
  padding: clamp(1rem, 2vh, 1.25rem);
  display: flex;
  justify-content: center;
  align-items: center;
  background: white;
  border-radius: 0.8vw;
  position: relative;
}

.radar-download-btn {
  position: absolute;
  top: clamp(0.8rem, 1.5vh, 1rem);
  right: clamp(0.8rem, 1.5vw, 1rem);
  background: color.adjust($gray, $lightness: 20%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1vw, 0.8rem);
  cursor: pointer;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  color: $white;
  transition: all 0.3s ease;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.8);
  z-index: 10;

  &:hover {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: color.adjust($main_1, $alpha: -0.3);
    transform: translateY(-0.1vh);
    box-shadow: 0 0.4vh 1vh color.adjust($main_1, $alpha: -0.5);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.6);
  }
}

/* Performance Analysis - Sort buttons */
.sort-buttons {
  display: flex;
  gap: 0.5vw;
  margin-bottom: 1vh;
}

.sort-btn {
  padding: clamp(0.3rem, 0.6vh, 0.4rem) clamp(0.6rem, 1vw, 0.8rem);
  background: $gray;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  color: color.adjust($white, $alpha: -0.4);
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;

  &:hover {
    background: color.adjust($gray, $lightness: 5%);
    color: $white;
  }

  &.achievement.active {
    background: rgba($sub_4, 0.2);
    border-color: $sub_4;
    color: $sub_4;
  }

  &.weight.active {
    background: rgba($sub_6, 0.2);
    border-color: $sub_6;
    color: $sub_6;
  }

  &.energy.active {
    background: rgba($sub_1, 0.2);
    border-color: $sub_1;
    color: $sub_1;
  }
}

/* Performance Analysis - Table */
.perf-analysis-table {
  display: flex;
  flex-direction: column;
  gap: 0.3vh;
}

.perf-analysis-header {
  display: grid;
  grid-template-columns: 2fr 1fr 3.5vw 4.5vw;
  gap: 0.8vw;
  padding: clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.6rem, 1.2vw, 0.8rem);
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);

  .col-name {
    color: color.adjust($white, $alpha: -0.5) !important;
  }
  .col-bar {
    color: $sub_4 !important;
  }
  .col-importance {
    color: $sub_6 !important;
  }
  .col-energy {
    color: $sub_1 !important;
  }
}

.perf-analysis-row {
  display: grid;
  grid-template-columns: 2fr 1fr 3.5vw 4.5vw;
  gap: 0.8vw;
  padding: clamp(0.5rem, 1vh, 0.7rem) clamp(0.6rem, 1.2vw, 0.8rem);
  background: $gray;
  border-radius: 0.4vw;
  align-items: center;
  transition: background 0.2s ease;

  &:hover {
    background: color.adjust($gray, $lightness: 3%);
  }
}

.col-name {
  font-weight: 600;
  color: $white !important;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-bar {
  display: flex;
  align-items: center;
}

.bar-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  width: 100%;
}

.bar-bg {
  flex: 1;
  height: 0.5vh;
  background: color.adjust($white, $alpha: -0.9);
  border-radius: 0.3vw;
  overflow: hidden;
  max-width: 5vw;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, $sub_4, color.adjust($sub_4, $lightness: 10%));
  border-radius: 0.3vw;
  transition: width 0.3s ease;
}

.bar-value {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  font-weight: 500;
  color: $sub_4 !important;
  min-width: 2.5vw;
  text-align: right;
}

.col-importance {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 600;
  color: $sub_6 !important;
  text-align: right;
}

.col-energy {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 600;
  color: $sub_1 !important;
  text-align: right;
}

.utility-item {
  display: flex;
  flex-direction: column;
  gap: 0.6vh;
}

.utility-label {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 500;
  color: color.adjust($white, $alpha: -0.3);
}

.utility-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 0.8vw;
}

.utility-bar {
  flex: 1;
  height: 0.8vh;
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.4vw;
  overflow: hidden;
}

.utility-fill {
  height: 100%;
  background: linear-gradient(90deg, $sub_4 0%, color.adjust($sub_4, $lightness: 15%) 100%);
  transition: width 0.3s ease;
}

.utility-value {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 600;
  color: $sub_4;
  min-width: clamp(2.5rem, 4vw, 3rem);
  text-align: right;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.8vw;
}

.stat-label {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
}

.stat-value {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  color: $white;
}

/* Empty state */
.empty-state {
  padding: clamp(4rem, 8vh, 5rem) clamp(1.2rem, 2vw, 1.5rem);
  text-align: center;
  color: color.adjust($white, $alpha: -0.5);
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
}

/* Loading state */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.8vw;
  padding: clamp(2rem, 4vh, 2.5rem);
  color: color.adjust($white, $alpha: -0.5);
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
}

.spinner {
  width: clamp(1rem, 1.5vw, 1.2rem);
  height: clamp(1rem, 1.5vw, 1.2rem);
  border: 2px solid color.adjust($white, $alpha: -0.8);
  border-top-color: $main_1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error state */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.8vh;
  padding: clamp(1.5rem, 3vh, 2rem);
  text-align: center;
  color: $sub_1;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
}

.error-state button {
  margin-top: 0.8vh;
  padding: clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.8rem, 1.5vw, 1rem);
  background: color.adjust($sub_1, $alpha: -0.8);
  border: 1px solid $sub_1;
  border-radius: 0.4vw;
  color: $white;
  cursor: pointer;
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  transition: all 0.2s;
}

.error-state button:hover {
  background: color.adjust($sub_1, $alpha: -0.6);
}

/* Footer */
.detail-footer {
  display: flex;
  gap: 0.8vw;
  padding: clamp(0.8rem, 1.5vh, 1rem) clamp(1rem, 2vw, 1.25rem);
  border-top: 1px solid color.adjust($white, $alpha: -0.95);
  background: linear-gradient(145deg, color.adjust($gray, $lightness: 10%), color.adjust($gray, $lightness: 6%));
}

.action-btn {
  flex: 1;
  padding: clamp(0.5rem, 1vh, 0.625rem);
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  transition: all 0.2s;
}

.action-btn.edit {
  background: $sub_6;
  color: $white;
}

.action-btn.edit:hover {
  background: color.adjust($sub_6, $lightness: -10%);
  transform: translateY(-0.1vh);
  box-shadow: 0 0.3vh 1vh color.adjust($sub_6, $alpha: -0.5);
}

.action-btn.copy {
  background: $sub_3;
  color: $black;
}

.action-btn.copy:hover {
  background: color.adjust($sub_3, $lightness: -10%);
  transform: translateY(-0.1vh);
  box-shadow: 0 0.3vh 1vh color.adjust($sub_3, $alpha: -0.5);
}

.action-btn.delete {
  background: $sub_1;
  color: $white;
}

.action-btn.delete:hover {
  background: color.adjust($sub_1, $lightness: -10%);
  transform: translateY(-0.1vh);
  box-shadow: 0 0.3vh 1vh color.adjust($sub_1, $alpha: -0.5);
}

.network-viewer-wrapper {
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.8vw;
  overflow: hidden;
  background: $gray;
}

.partial-energies-list h4 {
  margin: 0 0 clamp(0.6rem, 1.2vh, 0.75rem) 0;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.4);
}

.partial-energy-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(0.6rem, 1.2vh, 0.75rem);
  margin-bottom: 0.8vh;
  background: $gray;
  border-radius: 0.5vw;
  border-left: 0.3vw solid $main_1;
}

/* Structure mismatch warning */
.structure-warning {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  padding: clamp(0.6rem, 1.2vh, 0.75rem);
  margin: calc(-0.4vh) calc(-0.4vw) clamp(0.8rem, 1.5vh, 1rem) calc(-0.4vw);
  background: color.adjust($sub_2, $alpha: -0.9);
  color: $sub_2;
  border: 1px solid $sub_2;
  border-radius: 0.8vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
}

.structure-warning svg {
  flex-shrink: 0;
  color: $sub_2;
}

</style>