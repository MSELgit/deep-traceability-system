<template>
  <div class="shapley-breakdown">
    <!-- Header -->
    <div v-if="!hideHeader" class="breakdown-header">
      <div class="pair-info">
        <div class="perf-with-importance">
          <span class="perf-name">{{ perfIName }}</span>
          <span v-if="perfIImportance !== undefined" class="importance">(w={{ perfIImportance.toFixed(1) }})</span>
        </div>
        <span class="vs">vs</span>
        <div class="perf-with-importance">
          <span class="perf-name">{{ perfJName }}</span>
          <span v-if="perfJImportance !== undefined" class="importance">(w={{ perfJImportance.toFixed(1) }})</span>
        </div>
      </div>
      <div class="metrics">
        <span :class="['metric', relationshipClass]">
          cos θ = {{ formatNumber(cosTheta, 3) }}
        </span>
        <span class="metric energy">
          E_ij = {{ formatEnergy(eij, 4) }}
        </span>
      </div>
      <!-- Direction mixing warning -->
      <div v-if="hasMixedConsensus" class="direction-warning">
        <span class="warning-icon">⚠</span>
        <span v-for="(info, idx) in mixedConsensusInfos" :key="idx">
          {{ info.name }} の望ましさ方向が混在（δ/W = {{ info.value >= 0 ? '+' : '' }}{{ info.value.toFixed(2) }}）
          <span v-if="idx < mixedConsensusInfos.length - 1">、</span>
        </span>
        <span v-if="offsetRate !== undefined && offsetRate > 0.01">
          ：構造的対立の約{{ Math.round(offsetRate * 100) }}%がシナジーとして相殺
        </span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>Computing Shapley values...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error">
      <span>{{ error }}</span>
    </div>

    <!-- Contribution Sections -->
    <div v-else-if="nodeShapleyValues.length > 0" class="contributions">
      <!-- Shapley Mode Toggle -->
      <div v-if="lambdaIJ !== undefined" class="shapley-mode-toggle">
        <button
          :class="['toggle-btn', { active: shapleyMode === 'structure' }]"
          @click="shapleyMode = 'structure'"
        >
          構造寄与 (φ)
        </button>
        <button
          :class="['toggle-btn', { active: shapleyMode === 'energy' }]"
          @click="shapleyMode = 'energy'"
        >
          エネルギー寄与 (λφ)
        </button>
      </div>

      <!-- Node Contributions (V ∪ A) -->
      <div class="section">
        <div class="section-title">
          <span class="section-icon">◉</span>
          Top Node Contributions
          <span class="node-counts" v-if="nVariables > 0 || nAttributes > 0">
            (◆{{ nVariables }} ▲{{ nAttributes }})
          </span>
          <span class="computation-info" v-if="computationMethod">
            {{ computationMethod }}, {{ computationTime.toFixed(0) }}ms
          </span>
        </div>

        <div class="bar-container">
          <div
            v-for="item in topNodeValues"
            :key="item.node_id"
            class="bar-row"
          >
            <div class="bar-label node-label" :title="`${item.node_label} (${getNodeTypeLabel(item.node_type)})`">
              <span :class="['node-type-icon', item.node_type.toLowerCase()]">{{ getNodeTypeIcon(item.node_type) }}</span>
              <span class="node-name">{{ truncateName(item.node_label) }}</span>
            </div>
            <div class="bar-track">
              <div
                :class="['bar-fill', shapleyMode === 'energy' ? energySignClass(item.phi) : item.sign]"
                :style="shapleyMode === 'energy' ? energyBarStyle(item.phi, 'node') : { width: Math.abs(item.percentage) + '%' }"
              ></div>
            </div>
            <div :class="['bar-value', shapleyMode === 'energy' ? energySignClass(item.phi) : item.sign]">
              {{ shapleyMode === 'energy' ? formatLambdaPhi(item.phi) : formatPhi(item.phi) }}
              ({{ shapleyMode === 'energy' ? energyPercentage(item.phi, 'node') : item.percentage.toFixed(0) }}%)
            </div>
          </div>
        </div>
        <div v-if="hasMoreNodes" class="more-indicator">
          +{{ nodeShapleyValues.length - topN }} more nodes...
        </div>
      </div>

      <!-- Edge Contributions -->
      <div v-if="edgeShapleyValues && edgeShapleyValues.length > 0" class="section">
        <div class="section-title">
          <span class="section-icon">→</span>
          Top Edge Contributions
          <span class="computation-info" v-if="edgeComputationMethod">
            ({{ edgeComputationMethod }}, {{ edgeComputationTime?.toFixed(0) }}ms)
          </span>
        </div>

        <div class="bar-container">
          <div
            v-for="item in topEdgeValues"
            :key="item.edge_id"
            class="bar-row edge-row"
          >
            <div class="bar-label edge-label" :title="`${item.source_label} → ${item.target_label}`">
              <span class="edge-name">{{ formatEdgeName(item) }}</span>
              <span class="edge-type">{{ getEdgeTypeLabel(item.edge_type) }}</span>
            </div>
            <div class="bar-track">
              <div
                :class="['bar-fill', shapleyMode === 'energy' ? energySignClass(item.phi) : item.sign]"
                :style="shapleyMode === 'energy' ? energyBarStyle(item.phi, 'edge') : { width: Math.abs(item.percentage) + '%' }"
              ></div>
            </div>
            <div :class="['bar-value', shapleyMode === 'energy' ? energySignClass(item.phi) : item.sign]">
              {{ shapleyMode === 'energy' ? formatLambdaPhi(item.phi) : formatPhi(item.phi) }}
              ({{ shapleyMode === 'energy' ? energyPercentage(item.phi, 'edge') : item.percentage.toFixed(0) }}%)
            </div>
          </div>
        </div>
        <div v-if="hasMoreEdges" class="more-indicator">
          +{{ (edgeShapleyValues?.length || 0) - topN }} more edges...
        </div>
      </div>

      <!-- Summary -->
      <div class="summary">
        <!-- Node Shapley Summary -->
        <div class="summary-row">
          <span>Σφ_node:</span>
          <span>{{ sumCheck.toFixed(4) }}</span>
        </div>
        <div class="summary-row">
          <span>C_ij (node):</span>
          <span>{{ nodeExpectedSum.toFixed(4) }}</span>
        </div>
        <div :class="['summary-row', 'additivity-check', additivityOk ? 'ok' : 'warn']">
          <span>Node Error:</span>
          <span>{{ additivityError.toFixed(6) }}</span>
        </div>

        <!-- Edge Shapley Summary -->
        <div v-if="edgeShapleyValues && edgeShapleyValues.length > 0" class="summary-divider"></div>
        <div v-if="edgeShapleyValues && edgeShapleyValues.length > 0" class="summary-row">
          <span>Σφ_edge:</span>
          <span>{{ edgeSumCheck.toFixed(4) }}</span>
        </div>
        <div v-if="edgeShapleyValues && edgeShapleyValues.length > 0" class="summary-row">
          <span>C_ij (edge):</span>
          <span>{{ cij.toFixed(4) }}</span>
        </div>
        <div v-if="edgeShapleyValues && edgeShapleyValues.length > 0" :class="['summary-row', 'additivity-check', edgeAdditivityOk ? 'ok' : 'warn']">
          <span>Edge Error:</span>
          <span>{{ edgeAdditivityError.toFixed(6) }}</span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty">
      <span>Select a cell in the matrix to see contribution breakdown</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { NodeShapleyValue, EdgeShapleyValue } from '@/utils/api';
import { formatEnergy } from '@/utils/energyFormat';

interface Props {
  perfIName: string;
  perfJName: string;
  perfIImportance?: number;
  perfJImportance?: number;
  cosTheta: number;
  cij: number;
  nodeCij?: number;  // Node Shapley's C_ij (different from edge's C_ij)
  eij?: number;  // Partial energy E_ij
  nodeShapleyValues: NodeShapleyValue[];  // V ∪ A node Shapley values
  edgeShapleyValues?: EdgeShapleyValue[];  // Edge Shapley values
  edgeSumCheck?: number;
  edgeComputationMethod?: string;
  edgeComputationTime?: number;
  sumCheck?: number;
  computationMethod?: string;
  computationTime?: number;
  nVariables?: number;  // |V|
  nAttributes?: number;  // |A|
  loading?: boolean;
  error?: string | null;
  hideHeader?: boolean;
  maxNameLength?: number;
  topN?: number;  // Show top N items
  consensusI?: number;  // 方向合意度 P_i
  consensusJ?: number;  // 方向合意度 P_j
  offsetRate?: number;  // 相殺率
  lambdaIJ?: number;  // λ_ij = E_ij / C_ij
}

const props = withDefaults(defineProps<Props>(), {
  sumCheck: 0,
  computationTime: 0,
  edgeSumCheck: 0,
  edgeComputationTime: 0,
  nVariables: 0,
  nAttributes: 0,
  loading: false,
  error: null,
  hideHeader: false,
  maxNameLength: 12,
  topN: 5,
});

const shapleyMode = ref<'structure' | 'energy'>('structure');

const relationshipClass = computed(() => {
  if (props.cosTheta < -0.1) return 'tradeoff';
  if (props.cosTheta > 0.1) return 'synergy';
  return 'neutral';
});

// Direction mixing detection
const hasMixedConsensus = computed(() => {
  if (props.consensusI === undefined || props.consensusJ === undefined) return false;
  return Math.abs(props.consensusI) < 1 - 1e-6 || Math.abs(props.consensusJ) < 1 - 1e-6;
});

const mixedConsensusInfos = computed(() => {
  const infos: Array<{ name: string; value: number }> = [];
  if (props.consensusI !== undefined && Math.abs(props.consensusI) < 1 - 1e-6) {
    infos.push({ name: props.perfIName, value: props.consensusI });
  }
  if (props.consensusJ !== undefined && Math.abs(props.consensusJ) < 1 - 1e-6) {
    infos.push({ name: props.perfJName, value: props.consensusJ });
  }
  return infos;
});

// Node Shapley values (V ∪ A) - sorted and limited to top N
const sortedNodeValues = computed(() => {
  return [...props.nodeShapleyValues].sort((a, b) => b.abs_phi - a.abs_phi);
});

const topNodeValues = computed(() => {
  return sortedNodeValues.value.slice(0, props.topN);
});

const hasMoreNodes = computed(() => {
  return props.nodeShapleyValues.length > props.topN;
});

// Get icon for node type
function getNodeTypeIcon(type: string): string {
  return type === 'V' ? '◆' : '▲';  // Diamond for Variable, Triangle for Attribute
}

function getNodeTypeLabel(type: string): string {
  return type === 'V' ? 'Variable' : 'Attribute';
}

// Edge Shapley values - sorted and limited to top N
const sortedEdgeValues = computed(() => {
  if (!props.edgeShapleyValues) return [];
  return [...props.edgeShapleyValues].sort((a, b) => b.abs_phi - a.abs_phi);
});

const topEdgeValues = computed(() => {
  return sortedEdgeValues.value.slice(0, props.topN);
});

const hasMoreEdges = computed(() => {
  return (props.edgeShapleyValues?.length || 0) > props.topN;
});

// Node error: use nodeCij if provided (node Shapley has different C_ij than edge Shapley)
const nodeExpectedSum = computed(() => {
  return props.nodeCij !== undefined ? props.nodeCij : props.cij;
});

const additivityError = computed(() => {
  return Math.abs(props.sumCheck - nodeExpectedSum.value);
});

const additivityOk = computed(() => {
  return additivityError.value < 0.001;
});

// Edge error: always use cij (edge Shapley's C_ij)
const edgeAdditivityError = computed(() => {
  return Math.abs(props.edgeSumCheck - props.cij);
});

const edgeAdditivityOk = computed(() => {
  return edgeAdditivityError.value < 0.01;  // エッジは近似計算なので緩めに
});

function truncateName(name: string): string {
  if (name.length > props.maxNameLength) {
    return name.substring(0, props.maxNameLength - 2) + '..';
  }
  return name;
}

function formatEdgeName(edge: EdgeShapleyValue): string {
  const src = truncateName(edge.source_label || 'src');
  const tgt = truncateName(edge.target_label || 'tgt');
  return `${src} → ${tgt}`;
}

function getEdgeTypeLabel(type: string): string {
  switch (type) {
    case 'PA': return 'A→P';
    case 'AA': return 'A→A';
    case 'AV': return 'V→A';
    default: return type;
  }
}

function formatNumber(value: number | undefined | null, decimals: number): string {
  if (value === undefined || value === null || isNaN(value)) {
    return '-';
  }
  return value.toFixed(decimals);
}

function formatPhi(phi: number): string {
  const sign = phi >= 0 ? '+' : '';
  return sign + phi.toFixed(3);
}

// Energy mode (λφ) helpers
// ノード群・エッジ群で別々に分母を計算（構造モードのpercentageと一致させるため）
const nodeTotalAbsLambdaPhi = computed(() => {
  if (props.lambdaIJ === undefined) return 1;
  const lambda = props.lambdaIJ;
  return props.nodeShapleyValues.reduce((sum, item) => sum + Math.abs(item.phi * lambda), 0) || 1;
});

const edgeTotalAbsLambdaPhi = computed(() => {
  if (props.lambdaIJ === undefined || !props.edgeShapleyValues) return 1;
  const lambda = props.lambdaIJ;
  return props.edgeShapleyValues.reduce((sum, item) => sum + Math.abs(item.phi * lambda), 0) || 1;
});

// エネルギー寄与の符号: positive=悪化(赤), negative=緩和(ティール)
function energySignClass(phi: number): string {
  if (props.lambdaIJ === undefined) return 'energy-positive';
  return (phi * props.lambdaIJ) >= 0 ? 'energy-positive' : 'energy-negative';
}

function formatLambdaPhi(phi: number): string {
  if (props.lambdaIJ === undefined) return formatPhi(phi);
  const lambdaPhi = phi * props.lambdaIJ;
  const sign = lambdaPhi >= 0 ? '+' : '';
  return sign + lambdaPhi.toFixed(4);
}

function energyPercentage(phi: number, group: 'node' | 'edge'): string {
  if (props.lambdaIJ === undefined) return '0';
  const lambdaPhi = Math.abs(phi * props.lambdaIJ);
  const total = group === 'node' ? nodeTotalAbsLambdaPhi.value : edgeTotalAbsLambdaPhi.value;
  return ((lambdaPhi / total) * 100).toFixed(0);
}

function energyBarStyle(phi: number, group: 'node' | 'edge'): Record<string, string> {
  if (props.lambdaIJ === undefined) return { width: '0%' };
  const lambdaPhi = phi * props.lambdaIJ;
  const absLambdaPhi = Math.abs(lambdaPhi);
  const total = group === 'node' ? nodeTotalAbsLambdaPhi.value : edgeTotalAbsLambdaPhi.value;
  const pct = (absLambdaPhi / total) * 100;
  const intensity = Math.min(1, pct / 100 * 2);
  if (lambdaPhi >= 0) {
    // 正: エネルギー悪化 → 赤
    return {
      width: pct + '%',
      background: `linear-gradient(90deg, rgba(211,47,47,${0.3 + intensity * 0.3}), rgba(211,47,47,${0.4 + intensity * 0.6}))`,
    };
  } else {
    // 負: エネルギー緩和 → ティール
    return {
      width: pct + '%',
      background: `linear-gradient(90deg, rgba(0,150,136,${0.3 + intensity * 0.3}), rgba(0,150,136,${0.4 + intensity * 0.6}))`,
    };
  }
}
</script>

<style scoped>
.shapley-breakdown {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.9);
}

.breakdown-header {
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.pair-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.perf-with-importance {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.perf-name {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.importance {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
}

.vs {
  color: rgba(255, 255, 255, 0.4);
  font-size: 11px;
}

.metrics {
  display: flex;
  gap: 16px;
}

.metric {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}

.metric.tradeoff {
  background: rgba(21, 101, 192, 0.3);
  color: #90CAF9;
}

.metric.synergy {
  background: rgba(239, 108, 0, 0.3);
  color: #FFB74D;
}

.metric.neutral {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

.metric.energy {
  background: rgba(230, 81, 0, 0.3);
  color: #ffcc80;
}

.direction-warning {
  margin-top: 8px;
  padding: 6px 8px;
  background: rgba(171, 71, 188, 0.15);
  border: 1px solid rgba(171, 71, 188, 0.3);
  border-radius: 4px;
  font-size: 10px;
  color: #CE93D8;
  line-height: 1.4;
}

.warning-icon {
  margin-right: 4px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: rgba(255, 255, 255, 0.6);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #64b5f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  padding: 12px;
  background: rgba(198, 40, 40, 0.3);
  color: #ef9a9a;
  border-radius: 4px;
  text-align: center;
}

.section {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  &:last-of-type {
    border-bottom: none;
    margin-bottom: 8px;
  }
}

.section-title {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.section-icon {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
}

.node-counts {
  font-weight: 400;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 4px;
}

.computation-info {
  font-weight: 400;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  margin-left: auto;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

.node-type-icon {
  font-size: 8px;
  flex-shrink: 0;

  &.v {
    color: #FFC107;
  }

  &.a {
    color: #64b5f6;
  }
}

.node-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-indicator {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  text-align: right;
  margin-top: 4px;
  font-style: italic;
}

.bar-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: 4px;
}

.bar-label {
  width: 80px;
  flex-shrink: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edge-label {
  width: 110px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.edge-name {
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.edge-type {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.4);
}

.edge-row {
  padding: 5px 6px;
}

.bar-track {
  flex: 1;
  height: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.bar-fill.positive {
  background: linear-gradient(90deg, #FFB74D, #EF6C00);
}

.bar-fill.negative {
  background: linear-gradient(90deg, #64B5F6, #1565C0);
}

.bar-fill.neutral {
  background: rgba(255, 255, 255, 0.3);
}

.bar-fill.energy-positive,
.bar-fill.energy-negative {
  /* Dynamically styled via :style binding */
  border-radius: 3px;
}

.shapley-mode-toggle {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}

.toggle-btn {
  padding: 4px 10px;
  font-size: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}

.toggle-btn.active {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.4);
  color: rgba(255, 255, 255, 0.95);
  font-weight: 600;
}

.bar-value {
  width: 95px;
  flex-shrink: 0;
  text-align: right;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.bar-value.positive {
  color: #FFB74D;
}

.bar-value.negative {
  color: #90CAF9;
}

.bar-value.neutral {
  color: rgba(255, 255, 255, 0.6);
}

.bar-value.energy-positive {
  color: #EF9A9A;
}

.bar-value.energy-negative {
  color: #80CBC4;
}

.summary {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 6px 0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  padding: 2px 0;
}

.additivity-check.ok {
  color: #a5d6a7;
}

.additivity-check.warn {
  color: #ffb74d;
}

.empty {
  padding: 24px;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-style: italic;
}
</style>
