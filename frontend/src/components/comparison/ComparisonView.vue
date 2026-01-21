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
      <!-- Controls -->
      <div class="network-controls">
        <div class="control-group">
          <label>WL反復回数:</label>
          <select v-model="wlIterations" class="select-input small">
            <option v-for="i in 4" :key="i" :value="i">{{ i }}</option>
          </select>
        </div>
        <button
          class="compute-btn"
          :disabled="designCases.length < 2 || isComputingKernel"
          @click="computeWLKernel"
        >
          {{ isComputingKernel ? '計算中...' : 'WLカーネル計算' }}
        </button>
      </div>

      <div class="network-layout">
        <!-- Left: Distance Matrix -->
        <div class="network-left">
          <h3>距離行列（クリックで比較ペアを選択）</h3>
          <div v-if="distanceMatrix" class="distance-matrix-container">
            <table class="distance-table">
              <thead>
                <tr>
                  <th></th>
                  <th v-for="(dc, i) in designCases" :key="dc.id" class="case-header">
                    {{ i + 1 }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in distanceMatrix" :key="i">
                  <th class="case-row-header" :title="designCases[i]?.name">
                    {{ i + 1 }}. {{ truncateName(designCases[i]?.name) }}
                  </th>
                  <td
                    v-for="(dist, j) in row"
                    :key="j"
                    :class="getDistanceCellClass(i, j)"
                    :style="getDistanceCellStyle(dist, i, j)"
                    @click="selectNetworkPair(i, j)"
                  >
                    {{ i === j ? '-' : dist.toFixed(3) }}
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="distance-legend">
              <span class="legend-text">距離: </span>
              <span class="legend-near">近い (類似)</span>
              <span class="legend-arrow">→</span>
              <span class="legend-far">遠い (相違)</span>
            </div>
          </div>
          <div v-else class="kernel-matrix-placeholder">
            <p>WLカーネルを計算してください</p>
          </div>
        </div>

        <!-- Right: Network Diff Visualization -->
        <div class="network-right">
          <h3>
            ネットワーク構造比較
            <span v-if="selectedPairI !== null && selectedPairJ !== null" class="pair-info">
              （{{ designCases[selectedPairI]?.name }} vs {{ designCases[selectedPairJ]?.name }}）
            </span>
          </h3>
          <div v-if="selectedPairI !== null && selectedPairJ !== null" class="network-diff-view">
            <svg class="diff-svg" :viewBox="svgViewBox">
              <!-- Edges -->
              <g class="edges">
                <line
                  v-for="edge in diffEdges"
                  :key="edge.id"
                  :x1="getNodeX(edge.source)"
                  :y1="getNodeY(edge.source)"
                  :x2="getNodeX(edge.target)"
                  :y2="getNodeY(edge.target)"
                  :stroke="edge.color"
                  :stroke-width="edge.strokeWidth"
                  :stroke-dasharray="edge.dashArray"
                  :opacity="edge.opacity"
                />
              </g>
              <!-- Nodes -->
              <g class="nodes">
                <g v-for="node in diffNodes" :key="node.id" class="node-group">
                  <circle
                    :cx="node.x"
                    :cy="node.y"
                    :r="node.radius"
                    :fill="node.fill"
                    :stroke="node.stroke"
                    :stroke-width="2"
                  />
                  <text
                    :x="node.x"
                    :y="node.y + 4"
                    text-anchor="middle"
                    :fill="node.textColor"
                    font-size="10"
                    font-weight="500"
                  >
                    {{ node.label }}
                  </text>
                </g>
              </g>
            </svg>
            <div class="diff-legend-container">
              <div class="diff-legend-item">
                <span class="legend-dot common"></span>
                <span>共通</span>
              </div>
              <div class="diff-legend-item">
                <span class="legend-dot case1-only"></span>
                <span>{{ designCases[selectedPairI]?.name }}のみ</span>
              </div>
              <div class="diff-legend-item">
                <span class="legend-dot case2-only"></span>
                <span>{{ designCases[selectedPairJ]?.name }}のみ</span>
              </div>
            </div>
            <div class="diff-stats">
              <div class="stat-item">
                <span class="stat-label">共通ノード:</span>
                <span class="stat-value">{{ diffStats.commonNodes }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">{{ designCases[selectedPairI]?.name }}のみ:</span>
                <span class="stat-value case1">{{ diffStats.case1OnlyNodes }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">{{ designCases[selectedPairJ]?.name }}のみ:</span>
                <span class="stat-value case2">{{ diffStats.case2OnlyNodes }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">共通エッジ:</span>
                <span class="stat-value">{{ diffStats.commonEdges }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">異なるエッジ:</span>
                <span class="stat-value diff">{{ diffStats.differentEdges }}</span>
              </div>
            </div>
          </div>
          <div v-else class="network-diff-placeholder">
            <p>左の距離行列から比較するペアをクリックしてください</p>
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
import { CONFIG } from '../../config/environment'
import type { NetworkNode, NetworkEdge } from '../../types/project'

// FontAwesomeIcon is used in template
void FontAwesomeIcon

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

// Network comparison state
const wlIterations = ref(2)
const isComputingKernel = ref(false)
const distanceMatrix = ref<number[][] | null>(null)
const selectedPairI = ref<number | null>(null)
const selectedPairJ = ref<number | null>(null)

// Diff visualization data
interface DiffNode {
  id: string
  x: number
  y: number
  radius: number
  fill: string
  stroke: string
  textColor: string
  label: string
  status: 'common' | 'case1' | 'case2'
}

interface DiffEdge {
  id: string
  source: string
  target: string
  color: string
  strokeWidth: number
  dashArray: string
  opacity: number
  status: 'common' | 'case1' | 'case2' | 'weight-diff'
}

const diffNodes = ref<DiffNode[]>([])
const diffEdges = ref<DiffEdge[]>([])
const nodePositions = ref<Map<string, { x: number, y: number }>>(new Map())

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

// ===== Network Comparison Functions =====

// SVG viewBox
const svgViewBox = computed(() => {
  return '0 0 800 600'
})

// Diff statistics
const diffStats = computed(() => {
  let commonNodes = 0
  let case1OnlyNodes = 0
  let case2OnlyNodes = 0
  let commonEdges = 0
  let differentEdges = 0

  for (const node of diffNodes.value) {
    if (node.status === 'common') commonNodes++
    else if (node.status === 'case1') case1OnlyNodes++
    else if (node.status === 'case2') case2OnlyNodes++
  }

  for (const edge of diffEdges.value) {
    if (edge.status === 'common') commonEdges++
    else differentEdges++
  }

  return { commonNodes, case1OnlyNodes, case2OnlyNodes, commonEdges, differentEdges }
})

function truncateName(name: string | undefined): string {
  if (!name) return ''
  return name.length > 12 ? name.substring(0, 12) + '...' : name
}

function getDistanceCellClass(i: number, j: number): string {
  const classes = ['distance-cell']
  if (i === j) {
    classes.push('diagonal')
  } else {
    classes.push('clickable')
    if (selectedPairI.value === i && selectedPairJ.value === j) {
      classes.push('selected')
    }
  }
  return classes.join(' ')
}

function getDistanceCellStyle(dist: number, i: number, j: number): Record<string, string> {
  if (i === j) return {}

  // Color based on distance (lower = more similar = greener)
  const maxDist = getMaxDistance()
  if (maxDist === 0) return {}

  const normalized = dist / maxDist
  // From green (similar) to red (different)
  const r = Math.round(195 * normalized + 45 * (1 - normalized))
  const g = Math.round(102 * normalized + 144 * (1 - normalized))
  const b = Math.round(112 * normalized + 88 * (1 - normalized))

  return { backgroundColor: `rgba(${r}, ${g}, ${b}, 0.6)` }
}

function getMaxDistance(): number {
  if (!distanceMatrix.value) return 1
  let max = 0
  for (const row of distanceMatrix.value) {
    for (const dist of row) {
      if (dist > max) max = dist
    }
  }
  return max || 1
}

async function computeWLKernel() {
  if (designCases.value.length < 2) return

  isComputingKernel.value = true
  selectedPairI.value = null
  selectedPairJ.value = null
  diffNodes.value = []
  diffEdges.value = []

  try {
    // Prepare network structures for API
    const networkStructures = designCases.value.map(dc => ({
      nodes: dc.network.nodes,
      edges: dc.network.edges
    }))

    const response = await fetch(`${CONFIG.apiBaseUrl}/mds/compute_network_comparison`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        networks: networkStructures,
        iterations: wlIterations.value,
        method: 'circular_mds',
        n_init: 50,
        compare_methods: false
      })
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    const data = await response.json()
    distanceMatrix.value = data.distance_matrix

  } catch (error) {
    console.error('Failed to compute WL kernel:', error)
    alert('WLカーネルの計算に失敗しました')
  } finally {
    isComputingKernel.value = false
  }
}

function selectNetworkPair(i: number, j: number) {
  if (i === j) return

  // Ensure i < j for consistency
  if (i > j) {
    [i, j] = [j, i]
  }

  selectedPairI.value = i
  selectedPairJ.value = j

  // Compute network diff
  computeNetworkDiff(i, j)
}

function computeNetworkDiff(i: number, j: number) {
  const case1 = designCases.value[i]
  const case2 = designCases.value[j]

  if (!case1 || !case2) return

  const nodes1 = case1.network.nodes
  const nodes2 = case2.network.nodes
  const edges1 = case1.network.edges
  const edges2 = case2.network.edges

  // Create node signature for comparison (layer + type + label)
  const getNodeSignature = (node: NetworkNode) => `${node.layer}-${node.type}-${node.label}`

  // Build node maps
  const nodeMap1 = new Map(nodes1.map(n => [getNodeSignature(n), n]))
  const nodeMap2 = new Map(nodes2.map(n => [getNodeSignature(n), n]))

  // Collect all unique signatures
  const allSignatures = new Set([...nodeMap1.keys(), ...nodeMap2.keys()])

  // Build diff nodes
  const newDiffNodes: DiffNode[] = []
  const signatureToId = new Map<string, string>()

  // Layout: group by layer
  const layerCounts: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0 }
  const layerOffsets: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0 }

  // Count nodes per layer
  for (const sig of allSignatures) {
    const layer = parseInt(sig.split('-')[0])
    layerCounts[layer] = (layerCounts[layer] || 0) + 1
  }

  // Calculate positions
  const layerY: Record<number, number> = { 1: 80, 2: 200, 3: 350, 4: 500 }

  for (const sig of allSignatures) {
    const inCase1 = nodeMap1.has(sig)
    const inCase2 = nodeMap2.has(sig)
    const node = nodeMap1.get(sig) || nodeMap2.get(sig)!

    const layer = node.layer
    const count = layerCounts[layer]
    const offset = layerOffsets[layer]
    const x = 100 + (offset + 0.5) * (600 / count)
    const y = layerY[layer]
    layerOffsets[layer]++

    let status: 'common' | 'case1' | 'case2'
    let fill: string
    let stroke: string

    if (inCase1 && inCase2) {
      status = 'common'
      fill = '#888888'  // Gray
      stroke = '#666666'
    } else if (inCase1) {
      status = 'case1'
      fill = '#c36670'  // Red ($sub_1)
      stroke = '#a34550'
    } else {
      status = 'case2'
      fill = '#2d9058'  // Green ($sub_4)
      stroke = '#1d7048'
    }

    const nodeId = `diff-${sig}`
    signatureToId.set(sig, nodeId)

    newDiffNodes.push({
      id: nodeId,
      x,
      y,
      radius: 18,
      fill,
      stroke,
      textColor: '#ffffff',
      label: node.label.substring(0, 6),
      status
    })
  }

  // Build edge signature
  const getEdgeSignature = (edge: NetworkEdge, nodes: NetworkNode[]) => {
    const sourceNode = nodes.find(n => n.id === edge.source_id)
    const targetNode = nodes.find(n => n.id === edge.target_id)
    if (!sourceNode || !targetNode) return null
    return `${getNodeSignature(sourceNode)}=>${getNodeSignature(targetNode)}`
  }

  // Build edge maps
  const edgeMap1 = new Map<string, NetworkEdge>()
  const edgeMap2 = new Map<string, NetworkEdge>()

  for (const edge of edges1) {
    const sig = getEdgeSignature(edge, nodes1)
    if (sig) edgeMap1.set(sig, edge)
  }

  for (const edge of edges2) {
    const sig = getEdgeSignature(edge, nodes2)
    if (sig) edgeMap2.set(sig, edge)
  }

  // Build diff edges
  const newDiffEdges: DiffEdge[] = []
  const allEdgeSignatures = new Set([...edgeMap1.keys(), ...edgeMap2.keys()])

  for (const sig of allEdgeSignatures) {
    const [sourceSig, targetSig] = sig.split('=>')
    const sourceId = signatureToId.get(sourceSig)
    const targetId = signatureToId.get(targetSig)

    if (!sourceId || !targetId) continue

    const inCase1 = edgeMap1.has(sig)
    const inCase2 = edgeMap2.has(sig)

    let status: 'common' | 'case1' | 'case2' | 'weight-diff'
    let color: string
    let strokeWidth: number
    let dashArray: string
    let opacity: number

    if (inCase1 && inCase2) {
      const edge1 = edgeMap1.get(sig)!
      const edge2 = edgeMap2.get(sig)!

      if (edge1.weight === edge2.weight) {
        status = 'common'
        color = '#888888'
        strokeWidth = 2
        dashArray = ''
        opacity = 0.8
      } else {
        status = 'weight-diff'
        color = '#f0a030'  // Orange for weight difference
        strokeWidth = 3
        dashArray = '5,3'
        opacity = 0.9
      }
    } else if (inCase1) {
      status = 'case1'
      color = '#c36670'
      strokeWidth = 2
      dashArray = ''
      opacity = 0.7
    } else {
      status = 'case2'
      color = '#2d9058'
      strokeWidth = 2
      dashArray = ''
      opacity = 0.7
    }

    newDiffEdges.push({
      id: `edge-${sig}`,
      source: sourceId,
      target: targetId,
      color,
      strokeWidth,
      dashArray,
      opacity,
      status
    })
  }

  diffNodes.value = newDiffNodes
  diffEdges.value = newDiffEdges

  // Store positions
  nodePositions.value.clear()
  for (const node of newDiffNodes) {
    nodePositions.value.set(node.id, { x: node.x, y: node.y })
  }
}

function getNodeX(nodeId: string): number {
  const node = diffNodes.value.find(n => n.id === nodeId)
  return node?.x || 0
}

function getNodeY(nodeId: string): number {
  const node = diffNodes.value.find(n => n.id === nodeId)
  return node?.y || 0
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
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.network-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: color.adjust($black, $lightness: -5%);
  border-radius: 8px;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;

  label {
    font-weight: 500;
    color: $white;
  }
}

.select-input.small {
  min-width: 80px;
  padding: 6px 10px;
}

.compute-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px color.adjust($main_2, $alpha: -0.6);
  }

  &:disabled {
    background: color.adjust($white, $alpha: -0.8);
    color: color.adjust($white, $alpha: -0.5);
    cursor: not-allowed;
  }
}

.network-layout {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.network-left,
.network-right {
  background: color.adjust($black, $lightness: -3%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.network-left h3,
.network-right h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: $white;
  padding-bottom: 8px;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
}

.pair-info {
  font-weight: 400;
  font-size: 12px;
  color: color.adjust($white, $alpha: -0.3);
}

/* Distance Matrix */
.distance-matrix-container {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.distance-table {
  border-collapse: collapse;
  font-size: 11px;
  width: 100%;
}

.distance-table th,
.distance-table td {
  padding: 6px 8px;
  border: 1px solid color.adjust($white, $alpha: -0.85);
  text-align: center;
  color: $white;
}

.distance-table th {
  background: color.adjust($black, $lightness: -5%);
  font-weight: 600;
}

.case-header {
  min-width: 40px;
}

.case-row-header {
  text-align: left !important;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.distance-cell {
  font-family: monospace;
  transition: all 0.15s;

  &.diagonal {
    background: color.adjust($black, $lightness: 5%);
    color: color.adjust($white, $alpha: -0.5);
  }

  &.clickable {
    cursor: pointer;

    &:hover {
      outline: 2px solid $main_2;
      outline-offset: -2px;
    }
  }

  &.selected {
    outline: 3px solid $main_2;
    outline-offset: -3px;
    font-weight: 600;
  }
}

.distance-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 12px;
  padding: 8px;
  background: color.adjust($black, $lightness: -5%);
  border-radius: 4px;
  font-size: 11px;
}

.legend-text {
  color: color.adjust($white, $alpha: -0.3);
}

.legend-near {
  color: $sub_4;
  font-weight: 500;
}

.legend-arrow {
  color: color.adjust($white, $alpha: -0.5);
}

.legend-far {
  color: $sub_1;
  font-weight: 500;
}

/* Network Diff View */
.network-diff-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.diff-svg {
  flex: 1;
  min-height: 300px;
  background: color.adjust($black, $lightness: -5%);
  border-radius: 4px;
}

.diff-legend-container {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 8px;
  background: color.adjust($black, $lightness: -5%);
  border-radius: 4px;
}

.diff-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: $white;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;

  &.common {
    background: #888888;
  }

  &.case1-only {
    background: $sub_1;
  }

  &.case2-only {
    background: $sub_4;
  }
}

.diff-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 10px 12px;
  background: color.adjust($black, $lightness: -5%);
  border-radius: 4px;
}

.stat-item {
  display: flex;
  gap: 6px;
  font-size: 12px;
}

.stat-label {
  color: color.adjust($white, $alpha: -0.4);
}

.stat-value {
  font-weight: 600;
  color: $white;

  &.case1 {
    color: $sub_1;
  }

  &.case2 {
    color: $sub_4;
  }

  &.diff {
    color: #f0a030;
  }
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
  min-height: 200px;
}
</style>
