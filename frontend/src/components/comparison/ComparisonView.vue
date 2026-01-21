<template>
  <div class="comparison-view">
    <!-- Mode Selector -->
    <div class="mode-selector">
      <button
        :class="['mode-btn', { active: mode === 'matrix' }]"
        @click="mode = 'matrix'"
      >
        マトリクス比較
      </button>
      <button
        :class="['mode-btn', { active: mode === 'network' }]"
        @click="mode = 'network'"
      >
        ネットワーク比較
      </button>
    </div>

    <!-- Matrix Comparison Mode -->
    <div v-if="mode === 'matrix'" class="matrix-comparison">
      <!-- Selection Panel -->
      <div class="selection-panel">
        <div class="selection-row">
          <label>比較対象:</label>
          <select v-model="matrixType" class="select-input">
            <option value="cosTheta">cos θ マトリクス</option>
            <option value="energy">エネルギーマトリクス</option>
          </select>
        </div>
        <div class="selection-row">
          <label>設計案 1:</label>
          <select v-model="selectedCase1" class="select-input">
            <option value="">選択してください</option>
            <option v-for="dc in designCases" :key="dc.id" :value="dc.id">
              {{ dc.name }}
            </option>
          </select>
        </div>
        <div class="selection-row">
          <label>設計案 2:</label>
          <select v-model="selectedCase2" class="select-input">
            <option value="">選択してください</option>
            <option v-for="dc in designCases" :key="dc.id" :value="dc.id">
              {{ dc.name }}
            </option>
          </select>
        </div>
        <button
          class="compare-btn"
          :disabled="!selectedCase1 || !selectedCase2 || isLoading"
          @click="loadMatrixData"
        >
          {{ isLoading ? '読み込み中...' : '比較実行' }}
        </button>
      </div>

      <!-- Matrix Display -->
      <div v-if="matrixData1 || matrixData2" class="matrix-display-container">
        <div class="display-header">
          <h3>{{ currentDisplayLabel }}</h3>
          <button class="rotate-btn" @click="rotateDisplay">
            <font-awesome-icon :icon="['fas', 'sync-alt']" />
            次へ ({{ displayModeIndex + 1 }}/3)
          </button>
        </div>
        <div class="matrix-display">
          <table class="matrix-table">
            <thead>
              <tr>
                <th></th>
                <th v-for="label in performanceLabels" :key="label" class="header-cell">
                  {{ label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in currentMatrix" :key="i">
                <th class="row-header">{{ performanceLabels[i] }}</th>
                <td
                  v-for="(value, j) in row"
                  :key="j"
                  :class="getCellClass(value, i, j)"
                  :style="getCellStyle(value, i, j)"
                >
                  {{ formatValue(value) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="legend">
          <div v-if="displayModeIndex === 2" class="diff-legend">
            <span class="legend-item negative">← 負の差分</span>
            <span class="legend-item zero">0</span>
            <span class="legend-item positive">正の差分 →</span>
          </div>
          <div v-else class="value-legend">
            <span v-if="matrixType === 'cosTheta'" class="legend-item tradeoff">トレードオフ (< 0)</span>
            <span v-if="matrixType === 'cosTheta'" class="legend-item synergy">シナジー (> 0)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Network Comparison Mode -->
    <div v-if="mode === 'network'" class="network-comparison">
      <div class="network-layout">
        <div class="network-left">
          <h3>WL カーネル / 距離行列</h3>
          <div class="kernel-matrix-placeholder">
            <p>WLカーネル行列または距離行列をここに表示</p>
            <!-- TODO: Implement kernel matrix display -->
          </div>
        </div>
        <div class="network-right">
          <h3>ネットワーク構造比較</h3>
          <div class="network-diff-placeholder">
            <p>ネットワーク構造の差分表示（実装検討中）</p>
            <!-- TODO: Implement network diff visualization -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useProjectStore } from '../../stores/projectStore'
import { storeToRefs } from 'pinia'
import { structuralTradeoffApi } from '../../utils/api'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const projectStore = useProjectStore()
const { currentProject } = storeToRefs(projectStore)

// Mode selection
const mode = ref<'matrix' | 'network'>('matrix')

// Matrix comparison state
const matrixType = ref<'cosTheta' | 'energy'>('cosTheta')
const selectedCase1 = ref('')
const selectedCase2 = ref('')
const isLoading = ref(false)

// Matrix data
const matrixData1 = ref<number[][] | null>(null)
const matrixData2 = ref<number[][] | null>(null)
const performanceLabels = ref<string[]>([])

// Display mode: 0 = Case1, 1 = Case2, 2 = Diff
const displayModeIndex = ref(0)

const designCases = computed(() => {
  return currentProject.value?.design_cases || []
})

const currentDisplayLabel = computed(() => {
  const case1 = designCases.value.find(dc => dc.id === selectedCase1.value)
  const case2 = designCases.value.find(dc => dc.id === selectedCase2.value)
  const labels = [
    `設計案 1: ${case1?.name || ''}`,
    `設計案 2: ${case2?.name || ''}`,
    '差分 (設計案1 - 設計案2)'
  ]
  return labels[displayModeIndex.value]
})

const currentMatrix = computed(() => {
  if (displayModeIndex.value === 0) return matrixData1.value
  if (displayModeIndex.value === 1) return matrixData2.value
  if (displayModeIndex.value === 2 && matrixData1.value && matrixData2.value) {
    // Calculate difference matrix
    return matrixData1.value.map((row, i) =>
      row.map((val, j) => val - (matrixData2.value?.[i]?.[j] || 0))
    )
  }
  return null
})

function rotateDisplay() {
  displayModeIndex.value = (displayModeIndex.value + 1) % 3
}

async function loadMatrixData() {
  if (!currentProject.value || !selectedCase1.value || !selectedCase2.value) return

  isLoading.value = true
  displayModeIndex.value = 0

  try {
    // Load structural tradeoff data for both cases
    const [result1, result2] = await Promise.all([
      structuralTradeoffApi.getForCase(currentProject.value.id, selectedCase1.value),
      structuralTradeoffApi.getForCase(currentProject.value.id, selectedCase2.value)
    ])

    if (matrixType.value === 'cosTheta') {
      matrixData1.value = result1.data.cos_theta_matrix ?? null
      matrixData2.value = result2.data.cos_theta_matrix ?? null
    } else {
      // Energy matrix - use inner product matrix as proxy
      matrixData1.value = result1.data.inner_product_matrix ?? null
      matrixData2.value = result2.data.inner_product_matrix ?? null
    }

    performanceLabels.value = result1.data.performance_labels || []
  } catch (error) {
    console.error('Failed to load matrix data:', error)
    alert('マトリクスデータの読み込みに失敗しました')
  } finally {
    isLoading.value = false
  }
}

function formatValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return value.toFixed(3)
}

function getCellClass(value: number, i: number, j: number): string {
  if (i === j) return 'diagonal'
  if (displayModeIndex.value === 2) {
    // Diff mode
    if (value > 0.01) return 'positive-diff'
    if (value < -0.01) return 'negative-diff'
    return 'zero-diff'
  }
  if (matrixType.value === 'cosTheta') {
    if (value < 0) return 'tradeoff'
    if (value > 0) return 'synergy'
  }
  return ''
}

function getCellStyle(value: number, i: number, j: number): Record<string, string> {
  if (i === j) return {}

  if (displayModeIndex.value === 2) {
    // Diff mode coloring - using project colors
    const intensity = Math.min(Math.abs(value) * 2, 1)
    if (value > 0.01) {
      // Positive diff - green ($sub_4: #2d9058)
      return { backgroundColor: `rgba(45, 144, 88, ${intensity})` }
    }
    if (value < -0.01) {
      // Negative diff - red ($sub_1: #c36670)
      return { backgroundColor: `rgba(195, 102, 112, ${intensity})` }
    }
    return { backgroundColor: 'rgba(100, 100, 100, 0.3)' }
  }

  if (matrixType.value === 'cosTheta') {
    const intensity = Math.min(Math.abs(value), 1)
    if (value < 0) {
      // Tradeoff - red ($sub_1: #c36670)
      return { backgroundColor: `rgba(195, 102, 112, ${intensity * 0.8})` }
    }
    if (value > 0) {
      // Synergy - green ($sub_4: #2d9058)
      return { backgroundColor: `rgba(45, 144, 88, ${intensity * 0.8})` }
    }
  }

  return {}
}
</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

.comparison-view {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mode-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.mode-btn {
  padding: 10px 24px;
  border: 2px solid color.adjust($white, $alpha: -0.8);
  border-radius: 8px;
  background: transparent;
  color: $white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.mode-btn:hover {
  border-color: $main_2;
  background: color.adjust($main_2, $alpha: -0.9);
}

.mode-btn.active {
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border-color: transparent;
}

/* Matrix Comparison */
.matrix-comparison {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selection-panel {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px;
  background: color.adjust($black, $lightness: -5%);
  border-radius: 8px;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  flex-wrap: wrap;
}

.selection-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-row label {
  font-weight: 500;
  white-space: nowrap;
  color: $white;
}

.select-input {
  padding: 8px 12px;
  border: 1px solid color.adjust($white, $alpha: -0.8);
  border-radius: 4px;
  min-width: 200px;
  font-size: 14px;
  background: color.adjust($black, $lightness: -3%);
  color: $white;
}

.select-input:focus {
  outline: none;
  border-color: $main_2;
}

.compare-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.compare-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px color.adjust($main_2, $alpha: -0.6);
}

.compare-btn:disabled {
  background: color.adjust($white, $alpha: -0.8);
  color: color.adjust($white, $alpha: -0.5);
  cursor: not-allowed;
}

/* Matrix Display */
.matrix-display-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: color.adjust($black, $lightness: -3%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 8px;
  overflow: hidden;
}

.display-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: color.adjust($black, $lightness: -5%);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
}

.display-header h3 {
  margin: 0;
  font-size: 16px;
  color: $white;
}

.rotate-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: $main_1;
  color: $white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.rotate-btn:hover {
  background: color.adjust($main_1, $lightness: 10%);
}

.matrix-display {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.matrix-table {
  border-collapse: collapse;
  font-size: 12px;
  width: 100%;
}

.matrix-table th,
.matrix-table td {
  padding: 8px 12px;
  border: 1px solid color.adjust($white, $alpha: -0.85);
  text-align: center;
  min-width: 70px;
  color: $white;
}

.matrix-table th {
  background: color.adjust($black, $lightness: -5%);
  font-weight: 600;
}

.header-cell {
  font-size: 11px;
  max-width: 80px;
  word-wrap: break-word;
}

.row-header {
  text-align: left !important;
  font-size: 11px;
  max-width: 100px;
}

.diagonal {
  background: color.adjust($black, $lightness: 5%) !important;
  color: color.adjust($white, $alpha: -0.5);
}

.tradeoff {
  color: $white;
  font-weight: 500;
}

.synergy {
  color: $white;
  font-weight: 500;
}

.positive-diff {
  color: $white;
}

.negative-diff {
  color: $white;
}

.zero-diff {
  color: color.adjust($white, $alpha: -0.4);
}

/* Legend */
.legend {
  padding: 12px 16px;
  border-top: 1px solid color.adjust($white, $alpha: -0.9);
  background: color.adjust($black, $lightness: -5%);
}

.diff-legend,
.value-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.legend-item {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.legend-item.negative {
  background: $sub_1;
  color: $white;
}

.legend-item.positive {
  background: $sub_4;
  color: $white;
}

.legend-item.zero {
  background: color.adjust($white, $alpha: -0.7);
  color: $white;
}

.legend-item.tradeoff {
  background: $sub_1;
  color: $white;
}

.legend-item.synergy {
  background: $sub_4;
  color: $white;
}

/* Network Comparison */
.network-comparison {
  flex: 1;
}

.network-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  height: 100%;
}

.network-left,
.network-right {
  background: color.adjust($black, $lightness: -3%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.network-left h3,
.network-right h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: $white;
  padding-bottom: 8px;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
}

.kernel-matrix-placeholder,
.network-diff-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color.adjust($black, $lightness: -5%);
  border-radius: 4px;
  color: color.adjust($white, $alpha: -0.5);
}
</style>
