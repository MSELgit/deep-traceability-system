<template>
  <div class="matrix-heatmap">
    <!-- Mode Toggle (hidden when controlled externally) -->
    <div v-if="!hideToggle" class="mode-toggle">
      <button
        :class="['toggle-btn', { active: mode === 'cosTheta' }]"
        @click="internalMode = 'cosTheta'"
      >
        cos θ Matrix
      </button>
      <button
        :class="['toggle-btn', { active: mode === 'energy' }]"
        @click="internalMode = 'energy'"
      >
        Energy Matrix
      </button>
    </div>

    <!-- Matrix Display -->
    <div class="matrix-container" :style="{ '--cell-size': cellSize + 'px' }">
      <!-- Header Row (Performance Names) -->
      <div class="matrix-header">
        <div class="corner-cell"></div>
        <div
          v-for="(name, idx) in performanceNames"
          :key="'h-' + idx"
          class="header-cell"
          :title="name"
        >
          {{ truncateName(name) }}
        </div>
      </div>

      <!-- Direction Indicator Row (Energy mode only) -->
      <div v-if="mode === 'energy' && hasAnyConsensus" class="matrix-header direction-row">
        <div class="corner-cell direction-corner">δ/W</div>
        <div
          v-for="(name, idx) in performanceNames"
          :key="'d-' + idx"
          class="direction-cell"
          :title="getDirectionTooltip(idx)"
        >
          <span :class="['direction-icon', getDirectionClass(idx)]">{{ getDirectionSymbol(idx) }}</span>
        </div>
      </div>

      <!-- Matrix Rows -->
      <div
        v-for="(row, i) in displayMatrix"
        :key="'r-' + i"
        class="matrix-row"
      >
        <div class="row-label" :title="performanceNames[i]">
          <span class="row-name">{{ truncateName(performanceNames[i]) }}</span>
          <span
            v-if="mode === 'energy' && hasAnyConsensus"
            :class="['row-direction', getDirectionClass(i)]"
            :title="getDirectionTooltip(i)"
          >{{ getDirectionSymbol(i) }}</span>
        </div>
        <div
          v-for="(value, j) in row"
          :key="'c-' + j"
          :class="['matrix-cell', getCellClass(i, j, value)]"
          :style="{ backgroundColor: getCellColor(i, j, value) }"
          @click="onCellClick(i, j)"
          :title="getCellTooltip(i, j, value)"
        >
          <span :class="i === j ? 'diagonal' : 'cell-value'">
            {{ formatValue(value) }}
          </span>
          <span
            v-if="mode === 'energy' && i !== j && getOffsetRate(i, j) > 0.01"
            class="offset-badge"
            :title="`相殺率: 約${Math.round(getOffsetRate(i, j) * 100)}%`"
          >~{{ Math.round(getOffsetRate(i, j) * 100) }}%</span>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="legend">
      <div class="legend-title">{{ mode === 'cosTheta' ? 'cos θ' : `Energy (E_ij) [${energyUnit}]` }}</div>
      <div class="legend-bar">
        <div class="legend-gradient" :style="legendGradientStyle"></div>
        <div class="legend-labels">
          <span>{{ mode === 'cosTheta' ? '-1 (Opposition)' : '0' }}</span>
          <span v-if="mode === 'cosTheta'">0</span>
          <span>{{ mode === 'cosTheta' ? '+1 (Cooperation)' : displayMaxEnergy.toFixed(props.compact ? 1 : 2) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

interface Props {
  cosThetaMatrix: number[][];
  innerProductMatrix?: number[][];
  energyMatrix?: number[][];
  performanceNames: string[];
  performanceIds?: string[];
  performanceConsensus?: { [perfId: string]: number };
  performanceIdMap?: { [networkNodeId: string]: string };
  hideToggle?: boolean;
  externalMode?: 'cosTheta' | 'energy';
  cellSize?: number;
  compact?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  cellSize: 48,
  compact: false,
});

const emit = defineEmits<{
  (e: 'cellClick', payload: { i: number; j: number; perfIId?: string; perfJId?: string }): void;
  (e: 'modeChange', mode: 'cosTheta' | 'energy'): void;
}>();

const internalMode = ref<'cosTheta' | 'energy'>('cosTheta');
const selectedCell = ref<{ i: number; j: number } | null>(null);

// Use external mode if provided, otherwise use internal mode
const mode = computed(() => props.externalMode ?? internalMode.value);

watch(internalMode, (newMode) => {
  emit('modeChange', newMode);
});

// Sync external mode changes
watch(() => props.externalMode, (newMode) => {
  if (newMode) {
    emit('modeChange', newMode);
  }
});

const displayMatrix = computed(() => {
  if (mode.value === 'cosTheta') {
    return props.cosThetaMatrix;
  } else {
    return props.energyMatrix || props.cosThetaMatrix.map(row =>
      row.map(v => v < 0 ? Math.abs(v) : 0)
    );
  }
});

const maxEnergy = computed(() => {
  if (!props.energyMatrix) return 1;
  let max = 0;
  for (const row of props.energyMatrix) {
    for (const val of row) {
      if (val > max) max = val;
    }
  }
  return max || 1;
});

// E/mE unit system for energy display
// mE = milli-E = 0.001 E
// Switch threshold: compact (1 decimal) → 0.1, detailed (2 decimals) → 0.01
const useMilliE = computed(() => {
  if (mode.value !== 'energy') return false;
  const threshold = props.compact ? 0.1 : 0.01;
  return maxEnergy.value < threshold && maxEnergy.value > 0;
});

const energyUnit = computed(() => useMilliE.value ? 'mE' : 'E');

const displayMaxEnergy = computed(() => {
  if (useMilliE.value) {
    return maxEnergy.value * 1000;
  }
  return maxEnergy.value;
});

const legendGradientStyle = computed(() => {
  if (mode.value === 'cosTheta') {
    return {
      background: 'linear-gradient(to right, #1565C0, #FFFFFF, #EF6C00)',
    };
  } else {
    return {
      background: 'linear-gradient(to right, #e8f5e9, #ffeb3b, #d32f2f)',
    };
  }
});

function truncateName(name: string): string {
  if (props.compact && name.length > 4) {
    return name.substring(0, 3) + '..';
  }
  if (name.length > 8) {
    return name.substring(0, 7) + '..';
  }
  return name;
}

function getCellClass(i: number, j: number, value: number): string {
  if (i === j) return 'diagonal-cell';
  if (selectedCell.value?.i === i && selectedCell.value?.j === j) {
    return 'selected';
  }
  if (mode.value === 'cosTheta') {
    if (value < -0.1) return 'tradeoff';
    if (value > 0.1) return 'synergy';
    return 'neutral';
  }
  return '';
}

function getCellColor(_i: number, _j: number, value: number): string {
  if (mode.value === 'cosTheta') {
    // -1 (blue) to 0 (white) to +1 (orange) — neutral color scheme for structural quantity
    if (value < 0) {
      const intensity = Math.min(1, Math.abs(value));
      const r = Math.round(255 - (255 - 21) * intensity);   // 255→21
      const g = Math.round(255 - (255 - 101) * intensity);  // 255→101
      const b = Math.round(255 - (255 - 192) * intensity);  // 255→192
      return `rgb(${r}, ${g}, ${b})`;
    } else {
      const intensity = Math.min(1, value);
      const r = Math.round(255 - (255 - 239) * intensity);  // 255→239
      const g = Math.round(255 - (255 - 108) * intensity);  // 255→108
      const b = Math.round(255 - (255 - 0) * intensity);    // 255→0
      return `rgb(${r}, ${g}, ${b})`;
    }
  } else {
    // Energy: 0 (green/white) to max (red)
    const normalized = maxEnergy.value > 0 ? value / maxEnergy.value : 0;
    if (normalized < 0.01) return '#e8f5e9';
    const intensity = Math.min(1, normalized);
    const r = Math.round(232 + (211 - 232) * intensity);
    const g = Math.round(245 - (245 - 47) * intensity);
    const b = Math.round(233 - (233 - 47) * intensity);
    return `rgb(${r}, ${g}, ${b})`;
  }
}

function formatValue(value: number): string {
  // For energy mode, apply mE scaling if needed
  if (mode.value === 'energy' && useMilliE.value) {
    value = value * 1000;
  }

  if (props.compact) {
    return value.toFixed(1);
  }
  return value.toFixed(2);
}

function getConsensusForIndex(idx: number): number | undefined {
  if (!props.performanceConsensus || !props.performanceIds) return undefined;
  const networkId = props.performanceIds[idx];
  if (!networkId) return undefined;
  // Map network node ID to DB performance ID
  const dbId = props.performanceIdMap?.[networkId] || networkId;
  return props.performanceConsensus[dbId];
}

function formatConsensusLabel(consensus: number): string {
  if (Math.abs(consensus - 1.0) < 1e-6) return '全票望大 ↑';
  if (Math.abs(consensus + 1.0) < 1e-6) return '全票望小 ↓';
  const sign = consensus >= 0 ? '+' : '';
  return `混在 (${sign}${consensus.toFixed(2)})`;
}

function getCellTooltip(i: number, j: number, _value: number): string {
  if (i === j) return props.performanceNames[i];
  const cosTheta = props.cosThetaMatrix[i]?.[j] || 0;
  const cij = props.innerProductMatrix?.[i]?.[j];
  const eij = props.energyMatrix?.[i]?.[j];

  const relation = cosTheta < -0.1 ? '構造的対立' : cosTheta > 0.1 ? '構造的協調' : '中立';

  let tooltip = `${props.performanceNames[i]} vs ${props.performanceNames[j]}\n`;
  tooltip += `cos θ = ${cosTheta.toFixed(4)}（${relation}）\n`;
  if (cij !== undefined) tooltip += `C_ij = ${cij.toFixed(4)}\n`;
  if (eij !== undefined) tooltip += `E_ij = ${eij.toFixed(4)}`;

  // 方向合意度情報
  const ci = getConsensusForIndex(i);
  const cj = getConsensusForIndex(j);
  if (ci !== undefined && cj !== undefined) {
    tooltip += `\n\n方向合意度:`;
    tooltip += `\n  ${props.performanceNames[i]}: δ/W = ${ci >= 0 ? '+' : ''}${ci.toFixed(2)}（${formatConsensusLabel(ci)}）`;
    tooltip += `\n  ${props.performanceNames[j]}: δ/W = ${cj >= 0 ? '+' : ''}${cj.toFixed(2)}（${formatConsensusLabel(cj)}）`;

    // 相殺率を表示（混在票がある場合）
    if (Math.abs(ci) < 1 - 1e-6 || Math.abs(cj) < 1 - 1e-6) {
      if (Math.abs(cij ?? 0) > 1e-12) {
        const signC = (cij ?? 0) > 0 ? 1 : -1;
        const offsetRate = (1 + ci * cj * signC) / 2;
        if (offsetRate > 0.01) {
          tooltip += `\n\n${relation}のうち約${Math.round(offsetRate * 100)}%がシナジーとして相殺`;
        }
      }
    }
  }

  return tooltip;
}

// Direction indicator helpers
const hasAnyConsensus = computed(() => {
  if (!props.performanceConsensus || !props.performanceIds) return false;
  return props.performanceIds.some((_, idx) => getConsensusForIndex(idx) !== undefined);
});

function getDirectionSymbol(idx: number): string {
  const c = getConsensusForIndex(idx);
  if (c === undefined) return '';
  if (Math.abs(c - 1.0) < 1e-6) return '↑';
  if (Math.abs(c + 1.0) < 1e-6) return '↓';
  return c > 0 ? '↗' : '↙';  // 混在: 望大寄り↗ / 望小寄り↙
}

function getDirectionClass(idx: number): string {
  const c = getConsensusForIndex(idx);
  if (c === undefined) return '';
  if (Math.abs(c) > 1 - 1e-6) return 'unanimous';
  return 'mixed';
}

function getDirectionTooltip(idx: number): string {
  const c = getConsensusForIndex(idx);
  if (c === undefined) return '';
  const name = props.performanceNames[idx];
  return `${name}: δ/W = ${c >= 0 ? '+' : ''}${c.toFixed(2)}（${formatConsensusLabel(c)}）`;
}

function getOffsetRate(i: number, j: number): number {
  const ci = getConsensusForIndex(i);
  const cj = getConsensusForIndex(j);
  if (ci === undefined || cj === undefined) return 0;
  // 両方全票一致なら相殺なし
  if (Math.abs(ci) > 1 - 1e-6 && Math.abs(cj) > 1 - 1e-6) return 0;
  const cij = props.innerProductMatrix?.[i]?.[j];
  if (cij === undefined || Math.abs(cij) < 1e-12) return 0;
  const signC = cij > 0 ? 1 : -1;
  return (1 + ci * cj * signC) / 2;
}

function onCellClick(i: number, j: number): void {
  if (i === j) return;

  // Keep clicked cell as-is (don't force upper triangle)
  selectedCell.value = { i, j };

  emit('cellClick', {
    i,
    j,
    perfIId: props.performanceIds?.[i],
    perfJId: props.performanceIds?.[j],
  });
}
</script>

<style scoped lang="scss">
@use '../../style/color' as *;
@use 'sass:color';

.matrix-heatmap {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
}

.mode-toggle {
  display: flex;
  gap: 0.4vw;
  margin-bottom: clamp(0.8rem, 1.5vh, 1rem);
}

.toggle-btn {
  flex: 1;
  padding: clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.8rem, 1.2vw, 1rem);
  border: 1px solid color.adjust($white, $alpha: -0.8);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.4vw;
  cursor: pointer;
  font-size: clamp(0.65rem, 0.85vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.4);
  transition: all 0.2s;

  &.active {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    color: $white;
    border-color: $main_1;
  }

  &:hover:not(.active) {
    background: color.adjust($gray, $lightness: 20%);
    color: $white;
  }
}

.matrix-container {
  overflow-x: auto;
  margin-bottom: clamp(0.8rem, 1.5vh, 1rem);
  padding: clamp(0.5rem, 1vh, 0.75rem);
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 0.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.matrix-header {
  display: flex;
}

.corner-cell {
  width: calc(var(--cell-size) + 12px);
  height: clamp(1.2rem, 2vh, 1.5rem);
  flex-shrink: 0;
}

.header-cell {
  width: var(--cell-size);
  height: clamp(1.2rem, 2vh, 1.5rem);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  font-size: clamp(0.55rem, 0.75vw, 0.65rem);
  color: color.adjust($white, $alpha: -0.4);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.matrix-row {
  display: flex;
}

.row-label {
  width: calc(var(--cell-size) + 12px);
  height: var(--cell-size);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  padding-right: 0.5vw;
  font-weight: 500;
  font-size: clamp(0.55rem, 0.75vw, 0.65rem);
  color: color.adjust($white, $alpha: -0.4);
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}

.matrix-cell {
  width: var(--cell-size);
  height: var(--cell-size);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid color.adjust($white, $alpha: -0.85);
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
  position: relative;
}

.offset-badge {
  position: absolute;
  bottom: 1px;
  right: 1px;
  font-size: clamp(6px, 0.6vw, 7px);
  color: #CE93D8;
  line-height: 1;
  pointer-events: none;
  font-weight: 600;
}

.direction-row {
  height: clamp(1rem, 1.5vh, 1.2rem);
}

.direction-corner {
  width: calc(var(--cell-size) + 12px);
  font-size: clamp(0.5rem, 0.65vw, 0.55rem);
  color: color.adjust($white, $alpha: -0.6);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 0.5vw;
  font-style: italic;
  flex-shrink: 0;
}

.direction-cell {
  width: var(--cell-size);
  height: clamp(1rem, 1.5vh, 1.2rem);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.direction-icon {
  font-size: clamp(0.6rem, 0.8vw, 0.7rem);
  font-weight: 600;
}

.direction-icon.unanimous {
  color: color.adjust($white, $alpha: -0.5);
}

.direction-icon.mixed {
  color: #AB47BC;
}

.row-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-direction {
  font-size: clamp(0.55rem, 0.7vw, 0.6rem);
  font-weight: 600;
  flex-shrink: 0;
}

.row-direction.unanimous {
  color: color.adjust($white, $alpha: -0.5);
}

.row-direction.mixed {
  color: #AB47BC;
}

.matrix-cell:hover:not(.diagonal-cell) {
  transform: scale(1.1);
  z-index: 1;
  box-shadow: 0 0.2vh 0.8vh color.adjust($black, $alpha: -0.5);
}

.matrix-cell.selected {
  outline: 3px solid $main_1;
  outline-offset: -1px;
  z-index: 2;
}

.diagonal-cell {
  cursor: default;
}

.cell-value,
.diagonal {
  font-size: clamp(0.55rem, 0.75vw, 0.65rem);
  font-weight: 500;
  color: #333;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
}

.legend {
  margin-top: clamp(0.8rem, 1.5vh, 1rem);
  padding: clamp(0.5rem, 1vh, 0.75rem);
  background: color.adjust($gray, $lightness: 5%);
  border-radius: 0.4vw;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.legend-title {
  font-weight: 500;
  font-size: clamp(0.65rem, 0.85vw, 0.75rem);
  margin-bottom: 0.6vh;
  color: color.adjust($white, $alpha: -0.4);
}

.legend-bar {
  position: relative;
}

.legend-gradient {
  height: clamp(0.6rem, 1vh, 0.75rem);
  border-radius: 0.2vw;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: clamp(0.55rem, 0.75vw, 0.65rem);
  color: color.adjust($white, $alpha: -0.5);
  margin-top: 0.4vh;
}

.selected-info {
  margin-top: clamp(0.8rem, 1.5vh, 1rem);
  padding: clamp(0.6rem, 1vh, 0.75rem);
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 0.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.selected-header {
  font-weight: 600;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  margin-bottom: 0.8vh;
  color: $white;
}

.selected-values {
  display: flex;
  flex-wrap: wrap;
  gap: clamp(0.8rem, 1.2vw, 1rem);
}

.value-item {
  display: flex;
  align-items: center;
  gap: 0.4vw;
}

.value-label {
  font-size: clamp(0.65rem, 0.85vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.5);
}

.value-num {
  font-weight: 600;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: $white;

  &.tradeoff {
    color: $sub_1;
  }

  &.synergy {
    color: #4CAF50;
  }

  &.neutral {
    color: color.adjust($white, $alpha: -0.4);
  }
}

.selected-relationship {
  margin-top: 0.6vh;
  font-size: clamp(0.65rem, 0.85vw, 0.75rem);
  font-weight: 500;
  color: $main_1;
}
</style>
