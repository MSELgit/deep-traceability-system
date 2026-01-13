<template>
  <div class="tradeoff-matrix-mini">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading analysis...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <span>{{ error }}</span>
      <button @click="$emit('retry')">Retry</button>
    </div>

    <!-- Content -->
    <template v-else-if="cosThetaMatrix && cosThetaMatrix.length > 0">
      <MatrixHeatmap
        :cos-theta-matrix="cosThetaMatrix"
        :inner-product-matrix="innerProductMatrix"
        :energy-matrix="energyMatrix"
        :performance-names="performanceNames"
        :performance-ids="performanceIds"
        :cell-size="cellSize"
        :compact="true"
        @cell-click="onCellClick"
        @mode-change="currentMode = $event"
      />

      <!-- Quick Stats -->
      <div class="quick-stats">
        <div class="stat-item">
          <span class="stat-label">Tradeoffs:</span>
          <span class="stat-value tradeoff">{{ tradeoffCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Synergies:</span>
          <span class="stat-value synergy">{{ synergyCount }}</span>
        </div>
        <div v-if="totalEnergy !== undefined" class="stat-item">
          <span class="stat-label">Total Energy:</span>
          <span class="stat-value">{{ formatEnergy(totalEnergy, 3) }}</span>
        </div>
      </div>

      <!-- Expand Button -->
      <button class="expand-btn" @click="$emit('expand')">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
          <path d="M11 8v6M8 11h6"/>
        </svg>
        Open Detailed Analysis
      </button>
    </template>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <span>No network data available</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import MatrixHeatmap from './MatrixHeatmap.vue';
import { formatEnergy } from '@/utils/energyFormat';

interface Props {
  cosThetaMatrix?: number[][];
  innerProductMatrix?: number[][];
  energyMatrix?: number[][];
  performanceNames: string[];
  performanceIds?: string[];
  totalEnergy?: number;
  loading?: boolean;
  error?: string | null;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: null,
});

const emit = defineEmits<{
  (e: 'expand'): void;
  (e: 'retry'): void;
  (e: 'cellClick', payload: { i: number; j: number; perfIId?: string; perfJId?: string }): void;
}>();

const currentMode = ref<'cosTheta' | 'energy'>('cosTheta');

// Dynamically calculate cell size based on number of performances
const cellSize = computed(() => {
  const n = props.performanceNames.length;
  if (n <= 4) return 48;
  if (n <= 6) return 40;
  if (n <= 8) return 32;
  return 28;
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

function onCellClick(payload: { i: number; j: number; perfIId?: string; perfJId?: string }) {
  emit('cellClick', payload);
}
</script>

<style scoped lang="scss">
@use '../../style/color' as *;
@use 'sass:color';

.tradeoff-matrix-mini {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: clamp(1.5rem, 3vh, 2rem);
  color: color.adjust($white, $alpha: -0.5);
  gap: 0.8vh;
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

.error-state {
  color: $sub_1;
}

.error-state button {
  margin-top: 0.8vh;
  padding: clamp(0.3rem, 0.6vh, 0.4rem) clamp(0.8rem, 1.2vw, 1rem);
  background: color.adjust($sub_1, $alpha: -0.8);
  border: 1px solid $sub_1;
  color: $white;
  border-radius: 0.4vw;
  cursor: pointer;
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  transition: all 0.2s;

  &:hover {
    background: color.adjust($sub_1, $alpha: -0.6);
  }
}

.quick-stats {
  display: flex;
  flex-wrap: wrap;
  gap: clamp(0.8rem, 1.5vw, 1.2rem);
  margin-top: clamp(0.8rem, 1.5vh, 1rem);
  padding: clamp(0.6rem, 1vh, 0.75rem) clamp(0.8rem, 1.2vw, 1rem);
  background: color.adjust($gray, $lightness: 5%);
  border-radius: 0.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5vw;
}

.stat-label {
  font-size: clamp(0.65rem, 0.85vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.5);
}

.stat-value {
  font-weight: 600;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: $white;
}

.stat-value.tradeoff {
  color: $sub_1;
}

.stat-value.synergy {
  color: #4CAF50;
}

.expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6vw;
  width: 100%;
  margin-top: clamp(0.8rem, 1.5vh, 1rem);
  padding: clamp(0.6rem, 1vh, 0.75rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 500;
  transition: all 0.2s;
  box-shadow: 0 0.2vh 0.6vh color.adjust($main_1, $alpha: -0.6);

  &:hover {
    transform: translateY(-0.1vh);
    box-shadow: 0 0.4vh 1vh color.adjust($main_1, $alpha: -0.4);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.6);
  }

  svg {
    stroke: $white;
  }
}

.empty-state {
  font-style: italic;
  color: color.adjust($white, $alpha: -0.6);
}
</style>
