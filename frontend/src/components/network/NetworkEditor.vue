<template>
  <div class="network-editor">
    <!-- Toolbar -->
    <div class="toolbar">
      <div class="tool-group">
        <!-- Layer 2, 3 buttons -->
        <button 
          v-for="layer in layers.filter(l => l.id === 2 || l.id === 3)"
          :key="layer.id"
          class="tool-btn"
          :class="{ active: selectedTool === `add-layer${layer.id}` }"
          @click="selectAddNodeTool(layer.id, layer.type)"
          :style="{ borderColor: layer.color }"
        >
          <span class="tool-icon" :style="{ color: layer.color }">●</span>
          {{ layer.label }}
        </button>
        <!-- Layer 4: Object -->
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'add-layer4-object' }"
          @click="selectAddNodeTool(4, 'object')"
          :style="{ borderColor: layers[3].color }"
        >
          <span class="tool-icon" :style="{ color: layers[3].color }">■</span>
          Object
        </button>
        <!-- Layer 4: Environment -->
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'add-layer4-environment' }"
          @click="selectAddNodeTool(4, 'environment')"
          :style="{ borderColor: layers[3].color }"
        >
          <span class="tool-icon" :style="{ color: layers[3].color }">□</span>
          Environment
        </button>
      </div>

      <div class="tool-divider"></div>

      <div class="tool-group">
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'select' }"
          @click="selectedTool = 'select'"
          title="Select Mode"
        >
          <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'arrow-pointer']" /></span>
          Select
        </button>
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'edge' }"
          @click="selectedTool = 'edge'"
          title="Create Edge"
        >
          <span class="tool-icon">—</span>
          Connect
        </button>
        <button
          class="tool-btn danger"
          @click="deleteSelected"
          :disabled="!selectedNode && !selectedEdge"
          title="Delete"
        >
          <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'trash']" /></span>
          Delete
        </button>
      </div>

      <div class="tool-divider"></div>

      <div class="tool-group weight-mode-group">
        <label class="weight-mode-label">Weight Mode:</label>
        <select
          ref="weightModeSelectRef"
          :value="currentWeightMode"
          @change="handleWeightModeChange(($event.target as HTMLSelectElement).value as WeightMode)"
          class="weight-mode-select"
        >
          <option value="discrete_3">3-level (±1, 0)</option>
          <option value="discrete_5">5-level (±3, ±1, 0)</option>
          <option value="discrete_7">7-level (±5, ±3, ±1, 0)</option>
          <option value="continuous">Continuous (-1 ~ +1)</option>
        </select>
      </div>

      <!-- Excel Import/Export for continuous mode -->
      <template v-if="currentWeightMode === 'continuous'">
        <div class="tool-divider"></div>
        <div class="tool-group">
          <button
            class="tool-btn"
            @click="downloadWeightMatrix"
            title="Download weight matrix as Excel"
          >
            <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'file-export']" /></span>
            Export Excel
          </button>
          <button
            class="tool-btn"
            @click="triggerImportExcel"
            title="Import weight matrix from Excel"
          >
            <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'file-import']" /></span>
            Import Excel
          </button>
          <input
            ref="excelFileInput"
            type="file"
            accept=".xlsx,.xls"
            style="display: none"
            @change="importWeightMatrix"
          />
        </div>
      </template>

    </div>
    
    <div class="network-editor-wrapper">
      <!-- Properties Panel (Always on the left) -->
    <div class="properties-panel">
      <h3 v-if="selectedNode">Node Properties</h3>
      <h3 v-else-if="selectedEdge">Edge Properties</h3>
      <h3 v-else>Properties</h3>
      
      <!-- Node Properties -->
      <template v-if="selectedNode">
        <div class="property-group">
          <label>Label</label>
          <input
            v-model="tempNodeData.label"
            type="text"
            class="property-input"
            :disabled="isPerformanceNode(selectedNode)"
          />
        </div>

        <div class="property-group">
          <label>Layer</label>
          <select
            v-model.number="tempNodeData.layer"
            class="property-select"
            :disabled="isPerformanceNode(selectedNode)"
          >
            <option :value="1">Layer 1 - Performance (P)</option>
            <option :value="2">Layer 2 - Attribute (A)</option>
            <option :value="3">Layer 3 - Variable (V)</option>
            <option :value="4">Layer 4 - Entity (E)</option>
          </select>
        </div>

        <div class="property-group">
          <label>Type</label>
          <select
            v-model="tempNodeData.type"
            class="property-select"
            :disabled="isPerformanceNode(selectedNode)"
          >
            <option value="performance">Performance</option>
            <option value="attribute">Attribute</option>
            <option value="variable">Variable</option>
            <option value="object">Entity (Object)</option>
            <option value="environment">Entity (Environment)</option>
          </select>
        </div>

        <div class="property-group" v-if="tempNodeData.type === 'performance'">
          <label>Performance ID</label>
          <select 
            v-model="tempNodeData.performance_id" 
            class="property-select"
            :disabled="isPerformanceNode(selectedNode)"
          >
            <option v-for="perf in performances.filter(p => p.is_leaf)" :key="perf.id" :value="perf.id">
              {{ perf.name }}
            </option>
          </select>
        </div>

        <div class="property-group">
          <label>Coordinates</label>
          <div class="coords">
            <span>X: {{ Math.round(selectedNode.x) }}</span>
            <span>Y: {{ Math.round(selectedNode.y) }}</span>
          </div>
        </div>
        
        <div class="property-actions">
          <button class="save-btn" @click="saveNodeChanges">Save</button>
          <button class="cancel-btn" @click="cancelNodeChanges">Cancel</button>
        </div>
      </template>

      <!-- Edge Properties -->
      <template v-else-if="selectedEdge">
        <!-- Weight setting: only for directed edges (not V↔E, E↔E) -->
        <div class="property-group" v-if="!isUndirectedEdge(selectedEdge)">
          <label>Weight (Causal Strength)</label>
          <!-- Discrete mode: dropdown -->
          <select
            v-if="currentWeightMode !== 'continuous'"
            v-model.number="tempEdgeWeight"
            class="property-select"
          >
            <option
              v-for="opt in currentWeightOptions"
              :key="opt.value"
              :value="opt.value"
            >{{ opt.label }}</option>
          </select>
          <!-- Continuous mode: number input -->
          <div v-else class="continuous-weight-input">
            <input
              type="number"
              v-model.number="tempEdgeWeight"
              class="property-input"
              step="0.01"
              min="-1"
              max="1"
              placeholder="-1 ~ +1"
            />
            <input
              type="range"
              v-model.number="tempEdgeWeight"
              class="weight-slider"
              step="0.01"
              min="-1"
              max="1"
            />
            <div class="weight-value-display">{{ tempEdgeWeight.toFixed(2) }}</div>
          </div>
        </div>
        <!-- Undirected edge notice -->
        <div class="property-group" v-else>
          <label>Edge Type</label>
          <p class="undirected-notice">Undirected (no weight)</p>
        </div>
        
        <div class="property-group">
          <label>Connection Info</label>
          <div class="connection-info">
            <p>From: {{ getNodeById(selectedEdge.source_id)?.label }}</p>
            <p>To: {{ getNodeById(selectedEdge.target_id)?.label }}</p>
          </div>
        </div>
        
        <div class="property-actions">
          <button class="save-btn" @click="saveEdgeChanges">Save</button>
          <button class="cancel-btn" @click="cancelEdgeChanges">Cancel</button>
        </div>
      </template>

      <!-- When nothing is selected -->
      <div v-else class="property-empty">
        <p>Select a node or edge</p>
      </div>
    </div>

    <!-- Canvas Area -->
    <div class="canvas-container" ref="canvasContainer">
        <!-- SVG Canvas -->
        <svg
          ref="svgCanvas"
          class="network-canvas"
          :class="{ panning: isPanning, dragging: isDragging }"
          :style="canvasStyle"
          :width="canvasWidth * zoom"
          :height="canvasHeight * zoom"
          @click="handleCanvasClick"
          @mousemove="handleCanvasMouseMove"
          @mousedown="handlePanStart"
          @contextmenu.prevent
        >
          <!-- Grid Background Pattern Definition -->
          <defs>
            <pattern
              id="grid"
              width="20"
              height="20"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 20 0 L 0 0 0 20"
                fill="none"
                stroke="#e0e0e0"
                stroke-width="0.5"
              />
            </pattern>
            
            <!-- Arrow Marker Definition (for each unique edge color) -->
            <marker
              v-for="color in uniqueEdgeColors"
              :key="`arrow-${color}`"
              :id="`arrow-editor-${encodeColor(color)}`"
              markerWidth="10"
              markerHeight="10"
              refX="8"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path
                d="M 0 0 L 0 6 L 9 3 z"
                :fill="color"
              />
            </marker>

            <!-- Red arrow when selected -->
            <marker
              id="arrow-selected"
              markerWidth="10"
              markerHeight="10"
              refX="8"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path
                d="M 0 0 L 0 6 L 9 3 z"
                fill="#FF5722"
              />
            </marker>
          </defs>

          <!-- Main Content Group (Zoom/Pan applied) - contains all elements -->
          <g :transform="`scale(${zoom})`">
            <!-- Grid Background -->
            <rect 
              :x="0" 
              :y="0" 
              :width="canvasWidth" 
              :height="canvasHeight" 
              fill="url(#grid)" 
            />

            <!-- PAVE Layer Backgrounds (4 layers) -->
            <g class="layer-backgrounds">
              <!-- Performance Layer (P: Y=0-200) -->
              <rect
                :x="0"
                :y="0"
                :width="canvasWidth"
                :height="200"
                :fill="layers[0].color"
                opacity="0.1"
              />
              <!-- Attribute Layer (A: Y=200-400) -->
              <rect
                :x="0"
                :y="200"
                :width="canvasWidth"
                :height="200"
                :fill="layers[1].color"
                opacity="0.1"
              />
              <!-- Variable Layer (V: Y=400-600) -->
              <rect
                :x="0"
                :y="400"
                :width="canvasWidth"
                :height="200"
                :fill="layers[2].color"
                opacity="0.1"
              />
              <!-- Entity Layer (E: Y=600-800) -->
              <rect
                :x="0"
                :y="600"
                :width="canvasWidth"
                :height="200"
                :fill="layers[3].color"
                opacity="0.1"
              />
            </g>

          <!-- Edges (lines) -->
          <g class="edges-layer">
            <g
              v-for="edge in network.edges"
              :key="edge.id"
              class="edge"
              :class="{ selected: selectedEdge?.id === edge.id }"
              @click.stop="selectEdge(edge)"
            >
              <!-- Transparent thick line for click detection -->
              <line
                :x1="getNodeById(edge.source_id)?.x"
                :y1="getNodeById(edge.source_id)?.y"
                :x2="getNodeById(edge.target_id)?.x"
                :y2="getNodeById(edge.target_id)?.y"
                stroke="transparent"
                stroke-width="10"
                style="cursor: pointer"
              />
              <!-- Display line (no arrow marker for undirected V↔E edges) -->
              <line
                :x1="getNodeById(edge.source_id)?.x"
                :y1="getNodeById(edge.source_id)?.y"
                :x2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!, isUndirectedEdge(edge)).x : getNodeById(edge.target_id)?.x"
                :y2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!, isUndirectedEdge(edge)).y : getNodeById(edge.target_id)?.y"
                :stroke="selectedEdge?.id === edge.id ? '#FF5722' : getEdgeColor(edge)"
                :stroke-width="selectedEdge?.id === edge.id ? '3' : '2'"
                stroke-linecap="round"
                :marker-end="isUndirectedEdge(edge) ? undefined : (selectedEdge?.id === edge.id ? 'url(#arrow-selected)' : `url(#arrow-editor-${encodeColor(getEdgeColor(edge))})`)"
                style="pointer-events: none"
              />
              <!-- Delete button at edge midpoint -->
              <circle
                v-if="selectedEdge?.id === edge.id"
                :cx="(getNodeById(edge.source_id)?.x! + getNodeById(edge.target_id)?.x!) / 2"
                :cy="(getNodeById(edge.source_id)?.y! + getNodeById(edge.target_id)?.y!) / 2"
                r="6"
                fill="white"
                stroke="#FF5722"
                stroke-width="1.5"
                @click.stop="deleteEdge(edge)"
                style="cursor: pointer"
              />
            </g>

            <!-- Edge creation preview -->
            <line
              v-if="edgeStart && tempEdgeEnd"
              :x1="edgeStart.x"
              :y1="edgeStart.y"
              :x2="tempEdgeEnd.x"
              :y2="tempEdgeEnd.y"
              stroke="#2196F3"
              stroke-width="1.5"
              stroke-dasharray="5,5"
              stroke-linecap="round"
              marker-end="url(#arrow-0)"
            />
          </g>

          <!-- Nodes -->
          <g class="nodes-layer">
            <g
              v-for="node in network.nodes"
              :key="node.id"
              class="node"
              :class="{ selected: selectedNode?.id === node.id }"
              @mousedown="startDrag($event, node)"
              @click.stop="handleNodeClick(node)"
            >
              <!-- Layer 1: Performance (circle) -->
              <circle
                v-if="node.layer === 1"
                :cx="node.x"
                :cy="node.y"
                :r="nodeRadius"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- Layer 2: Attribute (equilateral triangle, height 36px) -->
              <polygon
                v-else-if="node.layer === 2"
                :points="getTrianglePoints(node.x, node.y)"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- Layer 3: Variable (horizontal diamond, height 36px, width 54px) -->
              <polygon
                v-else-if="node.layer === 3"
                :points="getDiamondPoints(node.x, node.y)"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- Layer 4: Object (1:2 rectangle) -->
              <rect
                v-else-if="node.layer === 4 && node.type === 'object'"
                :x="node.x - baseSize"
                :y="node.y - nodeRadius"
                :width="baseSize * 2"
                :height="baseSize"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                rx="4"
                class="node-shape"
              />
              
              <!-- Layer 4: Environment (square) -->
              <rect
                v-else-if="node.layer === 4 && node.type === 'environment'"
                :x="node.x - nodeRadius"
                :y="node.y - nodeRadius"
                :width="baseSize"
                :height="baseSize"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                rx="4"
                class="node-shape"
              />
              
              <!-- Fallback: Layer 4 with unknown type (circle) -->
              <circle
                v-else-if="node.layer === 4"
                :cx="node.x"
                :cy="node.y"
                :r="nodeRadius"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- Node label -->
              <text
                :x="node.x"
                :y="node.y + nodeRadius + 15"
                text-anchor="middle"
                class="node-label"
                :fill="selectedNode?.id === node.id ? '#FF5722' : '#333'"
              >
                {{ node.label }}
              </text>
            </g>
          </g>
          </g> <!-- End main content group -->
        </svg>

        <!-- Help text -->
        <div class="canvas-help" v-if="network.nodes.length === 0">
          <p><FontAwesomeIcon :icon="['fas', 'expand']" /> Select "Attribute", "Variable", or "Entity (Object/Environment)" from the toolbar above</p>
          <p>Click on the canvas to place nodes</p>
        </div>
      </div>

      <!-- Layer Guide (Right Side) -->
      <div class="layer-legend">
        <h3>Legend</h3>
        <div
          v-for="layer in layers"
          :key="layer.id"
          class="legend-item"
        >
          <svg class="legend-icon" width="14" height="14" viewBox="0 0 14 14">
            <!-- Performance: circle -->
            <circle v-if="layer.id === 1" cx="7" cy="7" r="5" :fill="layer.color" stroke="#333" stroke-width="1"/>
            <!-- Attribute: triangle -->
            <polygon v-else-if="layer.id === 2" points="7,2 12,12 2,12" :fill="layer.color" stroke="#333" stroke-width="1"/>
            <!-- Variable: diamond -->
            <polygon v-else-if="layer.id === 3" points="7,2 12,7 7,12 2,7" :fill="layer.color" stroke="#333" stroke-width="1"/>
            <!-- Entity: square -->
            <rect v-else x="2" y="2" width="10" height="10" :fill="layer.color" stroke="#333" stroke-width="1"/>
          </svg>
          <span class="legend-label">{{ layer.label }}</span>
        </div>

        <!-- Zoom Controls -->
        <div class="legend-section">
          <h4>View Controls</h4>
          <div class="zoom-controls">
            <label class="zoom-label">Zoom</label>
            <input 
              type="range" 
              v-model.number="zoom" 
              :min="minZoom" 
              max="3" 
              step="0.1"
              class="zoom-slider"
            />
            <span class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
            <button class="control-btn" @click="resetViewWithDebug" title="Fit">
              <FontAwesomeIcon :icon="['fas', 'expand']" />
              <span>Fit</span>
            </button>
          </div>
        </div>

        <!-- Action Controls -->
        <div class="legend-section">
          <h4>Actions</h4>
          <div class="action-controls">
            <button class="control-btn" @click="downloadAsImage" title="Download">
              <FontAwesomeIcon :icon="['fas', 'camera']" />
              <span>Download</span>
            </button>
            <button class="control-btn" @click="autoLayout" title="Auto Layout">
              <FontAwesomeIcon :icon="['fas', 'align-justify']" />
              <span>Auto Layout</span>
            </button>
            <button class="control-btn danger" @click="clearAll" title="Clear All">
              <FontAwesomeIcon :icon="['fas', 'rotate-right']" />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </div>
    </div> <!-- End network-editor-wrapper -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import type { NetworkStructure, NetworkNode, NetworkEdge, Performance, WeightMode } from '../../types/project';
import { WEIGHT_MODE_OPTIONS, migrateNodeType } from '../../types/project';
import * as XLSX from 'xlsx';

/**
 * Migrate network data: 'property' → 'attribute' for PAVE compliance
 */
function migrateNetworkData(network: NetworkStructure): void {
  network.nodes.forEach(node => {
    if (node.type === 'property') {
      node.type = 'attribute';
    }
  });
}

/**
 * PAVE Edge Direction Validation
 *
 * Valid connections (source → target):
 * - A → P: Attribute → Performance (layer 2 → 1)
 * - V → A: Variable → Attribute (layer 3 → 2)
 * - A → A: Attribute ↔ Attribute (layer 2 → 2, for loops)
 * - V ↔ E: Variable ↔ Entity (layer 3 ↔ 4, bidirectional/undirected)
 * - E ↔ E: Entity ↔ Entity (layer 4 ↔ 4, for object-environment links)
 *
 * Invalid connections:
 * - P → X: Performance → anything (layer 1 → X) - FORBIDDEN
 * - V → P: Variable → Performance (layer 3 → 1) - FORBIDDEN
 * - E → P: Entity → Performance (layer 4 → 1) - FORBIDDEN
 * - E → A: Entity → Attribute (layer 4 → 2) - FORBIDDEN
 * - V → V: Variable → Variable (layer 3 → 3) - FORBIDDEN
 * - A → V: Attribute → Variable (layer 2 → 3) - FORBIDDEN
 */
interface EdgeValidationResult {
  valid: boolean;
  reason?: string;
}

function validateEdgeDirection(from: NetworkNode, to: NetworkNode): EdgeValidationResult {
  const fromLayer = from.layer;
  const toLayer = to.layer;

  // Performance (layer 1) cannot be a source
  if (fromLayer === 1) {
    return {
      valid: false,
      reason: 'Performance nodes cannot be the source of edges. They can only receive effects.'
    };
  }

  // Variable → Performance (layer 3 → 1) is FORBIDDEN
  if (fromLayer === 3 && toLayer === 1) {
    return {
      valid: false,
      reason: 'Variable cannot connect directly to Performance. Use Attribute as an intermediate layer (V → A → P).'
    };
  }

  // Entity → Performance (layer 4 → 1) is FORBIDDEN
  if (fromLayer === 4 && toLayer === 1) {
    return {
      valid: false,
      reason: 'Entity cannot connect directly to Performance. The path must go through Variable and Attribute (E → V → A → P).'
    };
  }

  // Entity → Attribute (layer 4 → 2) is FORBIDDEN
  if (fromLayer === 4 && toLayer === 2) {
    return {
      valid: false,
      reason: 'Entity cannot connect directly to Attribute. Use Variable as an intermediate (E → V → A).'
    };
  }

  // Variable → Variable (layer 3 → 3) is FORBIDDEN
  if (fromLayer === 3 && toLayer === 3) {
    return {
      valid: false,
      reason: 'Variable cannot connect to another Variable. Variables are independent design parameters.'
    };
  }

  // Attribute → Variable (layer 2 → 3) is FORBIDDEN
  if (fromLayer === 2 && toLayer === 3) {
    return {
      valid: false,
      reason: 'Attribute cannot connect to Variable. The causal flow is V → A → P (Variable affects Attribute, not the reverse).'
    };
  }

  // Valid connections:
  // A → P (2 → 1): OK
  // V → A (3 → 2): OK
  // A → A (2 → 2): OK (loops)
  // V ↔ E (3 ↔ 4): OK (bidirectional)
  // E ↔ E (4 ↔ 4): OK

  return { valid: true };
}

/**
 * Check if an edge should be rendered as undirected (no arrow marker)
 * According to PAVE model:
 * - V ↔ E (layer 3 ↔ layer 4): undirected
 * - E ↔ E (layer 4 ↔ layer 4): undirected
 */
function isUndirectedEdge(edge: NetworkEdge): boolean {
  const source = network.value.nodes.find(n => n.id === edge.source_id);
  const target = network.value.nodes.find(n => n.id === edge.target_id);
  if (!source || !target) return false;

  // V ↔ E (layer 3 ↔ layer 4) is undirected
  if ((source.layer === 3 && target.layer === 4) || (source.layer === 4 && target.layer === 3)) {
    return true;
  }

  // E ↔ E (layer 4 ↔ layer 4) is undirected
  if (source.layer === 4 && target.layer === 4) {
    return true;
  }

  return false;
}

const props = defineProps<{
  modelValue: NetworkStructure;
  performances: Performance[];
  weightMode?: WeightMode;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: NetworkStructure];
  'update:weightMode': [value: WeightMode];
}>();

// 現在の重みモード
const currentWeightMode = ref<WeightMode>(props.weightMode || 'discrete_7');

// props.weightModeの変更を監視
watch(() => props.weightMode, (newMode) => {
  if (newMode && newMode !== currentWeightMode.value) {
    currentWeightMode.value = newMode;
  }
}, { immediate: true });

// Canvas size
const canvasWidth = ref(1200);
const canvasHeight = ref(800);

// ノードサイズを性能数に応じて動的に計算
const performanceCount = computed(() => {
  return network.value.nodes.filter(node => node.layer === 1).length;
});

// 基準サイズ（性能数が13以上の場合は18px、それ以外は36px）
const baseSize = computed(() => {
  return performanceCount.value >= 13 ? 18 : 36;
});

// ノードの半径（円形用）
const nodeRadius = computed(() => {
  return baseSize.value / 2;
});

// Zoom/pan state
const zoom = ref(1);
const minZoom = ref(0.3);
const panX = ref(0);
const panY = ref(0);
const isPanning = ref(false);
const panStart = ref({ x: 0, y: 0 });

// Internal state
const network = ref<NetworkStructure>({
  nodes: [],
  edges: []
});

// Update flag (prevent circular references)
const isUpdating = ref(false);

// Tool selection
const selectedTool = ref<string>('select');
const selectedNode = ref<NetworkNode | null>(null);
const selectedEdge = ref<NetworkEdge | null>(null);

// Drag state
const isDragging = ref(false);
const dragNode = ref<NetworkNode | null>(null);
const dragOffset = ref({ x: 0, y: 0 });

// Edge creation state
const edgeStart = ref<NetworkNode | null>(null);
const tempEdgeEnd = ref<{ x: number; y: number } | null>(null);

// Temporary data for property editing
const tempNodeData = ref({
  label: '',
  layer: 1 as 1 | 2 | 3 | 4,
  type: 'attribute' as NetworkNode['type'],
  performance_id: undefined as string | undefined
});
const tempEdgeWeight = ref<number>(0);  // Now supports continuous values

// 重みモード変更時のハンドラ（確認ダイアログ付き）
function handleWeightModeChange(newMode: WeightMode) {
  const edgeCount = network.value.edges.length;
  const oldMode = currentWeightMode.value;

  // エッジがない場合は確認なしで変更
  if (edgeCount === 0) {
    currentWeightMode.value = newMode;
    emit('update:weightMode', newMode);
    return;
  }

  // 同じモードへの変更は無視
  if (newMode === oldMode) {
    return;
  }

  // 確認メッセージを作成
  let message = `Change weight mode from "${getWeightModeLabel(oldMode)}" to "${getWeightModeLabel(newMode)}"?\n\n`;
  message += `${edgeCount} edge(s) will be affected.\n\n`;
  message += `Click OK to proceed, then choose how to handle existing weights.`;

  // 確認ダイアログを表示
  if (!confirm(message)) {
    // キャンセルされた場合、セレクターを元の値に戻す
    if (weightModeSelectRef.value) {
      weightModeSelectRef.value.value = oldMode;
    }
    return;
  }

  // 重み処理オプションを選択
  const resetToZero = confirm(
    `How should existing weights be handled?\n\n` +
    `[OK] = Reset all weights to 0 (recommended for fresh start)\n` +
    `[Cancel] = Adjust to nearest valid values (preserve approximate relationships)`
  );

  // モードを変更
  currentWeightMode.value = newMode;
  emit('update:weightMode', newMode);

  if (resetToZero) {
    // 全エッジの重みを0にリセット
    network.value.edges.forEach(edge => {
      edge.weight = 0;
    });
    emitUpdate();
  } else if (newMode !== 'continuous') {
    // 重みモード変更時、既存エッジの重みを最も近い有効値に丸める
    const validValues = WEIGHT_MODE_OPTIONS[newMode].values;
    network.value.edges.forEach(edge => {
      const weight = edge.weight ?? 0;
      // 最も近い有効値を見つける
      const closest = validValues.reduce((prev, curr) =>
        Math.abs(curr - weight) < Math.abs(prev - weight) ? curr : prev
      );
      edge.weight = closest;
    });
    emitUpdate();
  }
}

// 重みモードのラベルを取得
function getWeightModeLabel(mode: WeightMode): string {
  const labels: Record<WeightMode, string> = {
    discrete_3: '3-level (±1, 0)',
    discrete_5: '5-level (±3, ±1, 0)',
    discrete_7: '7-level (±5, ±3, ±1, 0)',
    continuous: 'Continuous (-1 ~ +1)'
  };
  return labels[mode] || mode;
}

// 現在の重みモードで有効な選択肢を取得
const currentWeightOptions = computed(() => {
  if (currentWeightMode.value === 'continuous') {
    return [];
  }
  const options = WEIGHT_MODE_OPTIONS[currentWeightMode.value];
  return options.values.map((val, idx) => ({
    value: val,
    label: options.labels[idx]
  }));
});

const svgCanvas = ref<SVGSVGElement>();
const canvasContainer = ref<HTMLDivElement>();
const weightModeSelectRef = ref<HTMLSelectElement>();
const excelFileInput = ref<HTMLInputElement>();

// Layer definition (PAVE model)
const layers = [
  { id: 1, label: 'Performance', color: '#4CAF50', type: 'performance' },
  { id: 2, label: 'Attribute', color: '#2196F3', type: 'attribute' },
  { id: 3, label: 'Variable', color: '#FFC107', type: 'variable' },
  { id: 4, label: 'Entity', color: '#9C27B0', type: 'object' }  // Entity has subtypes: object, environment
];

// Edge weight and color mapping (supports both new ±5 and legacy ±0.33 formats)
const edgeWeightColors: Record<number, string> = {
  5: '#002040',      // Strong positive (7-level)
  3: '#004563',      // Strong positive (5-level) / Medium-strong (7-level)
  1: '#588da2',      // Moderate positive
  0.33: '#c3dde2',   // Weak positive (legacy)
  0: 'silver',       // No correlation
  [-0.33]: '#e9c1c9', // Weak negative (legacy)
  [-1]: '#c94c62',   // Moderate negative
  [-3]: '#9f1e35',   // Strong negative (5-level) / Medium-strong (7-level)
  [-5]: '#6f0020'    // Strong negative (7-level)
};

const edgeWeightLabels: Record<number, string> = {
  5: '+5 (Strong positive causality)',
  3: '+3 (Medium-strong positive causality)',
  1: '+1 (Moderate positive causality)',
  0.33: '+1/3 (Weak positive causality - legacy)',
  0: '0 (No correlation)',
  [-0.33]: '-1/3 (Weak negative causality - legacy)',
  [-1]: '-1 (Moderate negative causality)',
  [-3]: '-3 (Medium-strong negative causality)',
  [-5]: '-5 (Strong negative causality)'
};

// Compute unique edge colors for marker definitions
const uniqueEdgeColors = computed(() => {
  const colors = new Set<string>();
  for (const edge of network.value.edges) {
    colors.add(getEdgeColor(edge));
  }
  colors.add('#333'); // Default for undirected edges
  colors.add('silver'); // Fallback
  return Array.from(colors);
});

// Encode color string for use in SVG ID
function encodeColor(color: string): string {
  return color.replace(/[^a-zA-Z0-9]/g, '_');
}

// Get edge color - supports both discrete and continuous values
function getEdgeColor(edge: NetworkEdge): string {
  // Undirected edges (V↔E, E↔E) are always black - no weight concept
  if (isUndirectedEdge(edge)) {
    return '#333';
  }

  const weight = edge.weight ?? 0;

  // maxWeight depends on current weight mode:
  // - discrete_7: ±5, discrete_5: ±3, discrete_3: ±1, continuous: ±1
  const maxWeightMap: Record<string, number> = {
    discrete_7: 5,
    discrete_5: 3,
    discrete_3: 1,
    continuous: 1
  };
  const maxWeight = maxWeightMap[currentWeightMode.value] || 5;

  // For discrete modes, use the predefined colors if weight matches exactly
  if (currentWeightMode.value !== 'continuous' && weight in edgeWeightColors) {
    return edgeWeightColors[weight as keyof typeof edgeWeightColors];
  }

  // For continuous mode (or non-matching discrete values), interpolate
  const clampedWeight = Math.max(-maxWeight, Math.min(maxWeight, weight));

  if (clampedWeight > 0) {
    // Positive: interpolate from light blue (#c3dde2) to dark blue (#002040)
    const t = clampedWeight / maxWeight;
    const r = Math.round(195 * (1 - t) + 0 * t);
    const g = Math.round(221 * (1 - t) + 32 * t);
    const b = Math.round(226 * (1 - t) + 64 * t);
    return `rgb(${r}, ${g}, ${b})`;
  } else if (clampedWeight < 0) {
    // Negative: interpolate from light red (#e9c1c9) to dark red (#6f0020)
    const t = Math.abs(clampedWeight) / maxWeight;
    const r = Math.round(233 * (1 - t) + 111 * t);
    const g = Math.round(193 * (1 - t) + 0 * t);
    const b = Math.round(201 * (1 - t) + 32 * t);
    return `rgb(${r}, ${g}, ${b})`;
  }

  // weight = 0: neutral gray
  return '#c0c0c0';
}

// Canvas cursor style (computed)
const canvasStyle = computed(() => {
  if (isPanning.value) {
    return { cursor: 'move' };
  }
  if (selectedTool.value === 'select' || selectedTool.value === 'edge') {
    return { cursor: 'default' };
  }
  if (selectedTool.value.startsWith('add-layer')) {
    return { cursor: 'crosshair' };
  }
  return { cursor: 'default' };
});

// Node shape calculation functions
// Equilateral triangle coordinates (height 36px, pointing up)
function getTrianglePoints(cx: number, cy: number): string {
  const height = baseSize.value;
  const halfBase = height / Math.sqrt(3); // Half of base
  return `${cx},${cy - height/2} ${cx - halfBase},${cy + height/2} ${cx + halfBase},${cy + height/2}`;
}

// Horizontal diamond coordinates (height = baseSize, width = baseSize * 1.5)
function getDiamondPoints(cx: number, cy: number): string {
  const halfHeight = baseSize.value / 2;
  const halfWidth = baseSize.value * 0.75; // 1.5 ratio
  return `${cx},${cy - halfHeight} ${cx + halfWidth},${cy} ${cx},${cy + halfHeight} ${cx - halfWidth},${cy}`;
}

// Initialize
onMounted(() => {
  if (props.modelValue) {
    network.value = JSON.parse(JSON.stringify(props.modelValue));

    // Migrate 'property' → 'attribute' for PAVE compliance
    migrateNetworkData(network.value);

    // Set default weight for existing edges without weight
    network.value.edges.forEach(edge => {
      if (edge.weight === undefined) {
        edge.weight = 0; // Default is no correlation
      }
    });
  }
  if (network.value.nodes.length === 0) {
    ensurePerformanceNodes(false); // Don't emit
  } else {
    ensurePerformanceNodes(false); // Don't emit
  }

  // Reset view if there are nodes
  if (network.value.nodes.length > 0) {
    nextTick(() => resetView());
  }
});

// Watch
watch(() => props.modelValue, (newVal, oldVal) => {

  // Ignore changes from our own updates
  if (isUpdating.value) {
    return;
  }

  if (newVal) {
    // Copy new data
    network.value = JSON.parse(JSON.stringify(newVal));

    // Migrate 'property' → 'attribute' for PAVE compliance
    migrateNetworkData(network.value);

    // Set default weight for existing edges without weight
    network.value.edges.forEach(edge => {
      if (edge.weight === undefined) {
        edge.weight = 0; // Default is no correlation
      }
    });
  }
}, { deep: true });

// Watch performance data changes
watch(() => props.performances, (newVal) => {
  
  // 性能ノードがない場合のみ追加
  const hasPerfNodes = network.value.nodes.some(
    n => n.type === 'performance' && n.performance_id
  );
  
  if (!hasPerfNodes) {
    ensurePerformanceNodes();
  } else {
  }
}, { deep: true });

// Ensure performance nodes exist
function ensurePerformanceNodes(shouldEmit: boolean = true) {
  if (props.performances.length === 0) {
    return;
  }
  
  const leafPerfs = props.performances.filter(p => p.is_leaf);
  
  // Get existing performance node IDs
  const existingPerfIds = new Set(
    network.value.nodes
      .filter(n => n.type === 'performance' && n.performance_id)
      .map(n => n.performance_id)
  );
  const startX = 100;
  const startY = 100; // Center of layer 1
  const spacingX = 180;
  const spacingY = 80;
  const itemsPerRow = 6;
  
  let addedCount = 0;
  leafPerfs.forEach((perf) => {
    if (!existingPerfIds.has(perf.id)) {
      const index = network.value.nodes.filter(n => n.layer === 1).length;
      const col = index % itemsPerRow;
      const row = Math.floor(index / itemsPerRow);
      
      const node: NetworkNode = {
        id: `perf-${perf.id}`,
        layer: 1,
        type: 'performance',
        label: perf.name,
        x: startX + col * spacingX,
        y: startY + row * spacingY,
        performance_id: perf.id
      };
      network.value.nodes.push(node);
      addedCount++;
    } else {
    }
  });
  
  if (addedCount > 0 && shouldEmit) {
    emitUpdate();
  } else if (addedCount > 0) {
  }
}

// Helper to output debug information
function logResetViewDebug() {
  network.value.nodes.forEach(node => {
  });
}

// Get node color
function getNodeColor(node: NetworkNode): string {
  const layer = layers.find(l => l.id === node.layer);
  return layer?.color || '#999';
}

// Adjust edge endpoint (prevent arrow overlapping with node)
function getAdjustedLineEnd(source: NetworkNode, target: NetworkNode, isUndirected: boolean = false): { x: number, y: number } {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  // Node radius (adjusted by shape)
  let targetRadius = nodeRadius.value; // Default (circle)

  if (target.layer === 2) { // Triangle
    targetRadius = baseSize.value * 0.56; // Approximate radius for triangle
  } else if (target.layer === 3) { // Diamond
    targetRadius = baseSize.value * 0.67; // Approximate radius for diamond
  } else if (target.layer === 4 && target.type === 'object') { // Rectangle
    targetRadius = baseSize.value; // Half width of rectangle
  } else if (target.layer === 4 && target.type === 'environment') { // Square
    targetRadius = nodeRadius.value;
  }

  // For directed edges, shorten further by arrow size (10px)
  // For undirected edges, no arrow adjustment needed
  const arrowAdjustment = isUndirected ? 0 : 10;
  const adjustment = targetRadius + arrowAdjustment;
  const ratio = (distance - adjustment) / distance;

  return {
    x: source.x + dx * ratio,
    y: source.y + dy * ratio
  };
}

// Get node by ID
function getNodeById(id: string): NetworkNode | undefined {
  return network.value.nodes.find(n => n.id === id);
}

// Convert SVG coordinates to world coordinates (considering zoom)
function screenToWorld(screenX: number, screenY: number): { x: number; y: number } {
  return {
    x: screenX / zoom.value,
    y: screenY / zoom.value
  };
}

// Check if node is performance node
function isPerformanceNode(node: NetworkNode | null): boolean {
  if (!node) return false;
  return node.type === 'performance' && !!node.performance_id;
}

// Handle type change
function handleTypeChange() {
  if (!selectedNode.value) return;

  // Automatically set layer based on type (PAVE model)
  const typeLayerMap: Record<string, 1 | 2 | 3 | 4> = {
    'performance': 1,
    'attribute': 2,
    'property': 2,  // deprecated, for backward compatibility
    'variable': 3,
    'object': 4,
    'environment': 4
  };

  const newLayer = typeLayerMap[selectedNode.value.type];
  if (newLayer) {
    selectedNode.value.layer = newLayer;
  }

  emitUpdate();
}

// Initialize temporary data when node is selected
function updateTempNodeData() {
  if (selectedNode.value) {
    tempNodeData.value = {
      label: selectedNode.value.label,
      layer: selectedNode.value.layer,
      type: selectedNode.value.type,
      performance_id: selectedNode.value.performance_id
    };
  }
}

// Initialize temporary data when edge is selected
function updateTempEdgeData() {
  if (selectedEdge.value) {
    tempEdgeWeight.value = selectedEdge.value.weight ?? 0;
  }
}

// Save node changes
function saveNodeChanges() {
  if (!selectedNode.value) return;
  
  // Apply changes
  selectedNode.value.label = tempNodeData.value.label;
  selectedNode.value.layer = tempNodeData.value.layer;
  selectedNode.value.type = tempNodeData.value.type;
  selectedNode.value.performance_id = tempNodeData.value.performance_id;
  
  // Automatically set layer based on type (PAVE model)
  const typeLayerMap: Record<string, 1 | 2 | 3 | 4> = {
    'performance': 1,
    'attribute': 2,
    'property': 2,  // deprecated, for backward compatibility
    'variable': 3,
    'object': 4,
    'environment': 4
  };

  const newLayer = typeLayerMap[tempNodeData.value.type];
  if (newLayer) {
    selectedNode.value.layer = newLayer;
  }

  emitUpdate();
  selectedNode.value = null; // Clear selection
}

// Cancel node changes
function cancelNodeChanges() {
  selectedNode.value = null;
}

// Save edge changes
function saveEdgeChanges() {
  if (!selectedEdge.value) return;
  
  selectedEdge.value.weight = tempEdgeWeight.value;
  emitUpdate();
  selectedEdge.value = null; // Clear selection
}

// Cancel edge changes
function cancelEdgeChanges() {
  selectedEdge.value = null;
}

// Select add node tool
function selectAddNodeTool(layerId: number, nodeType?: string) {
  if (layerId === 4 && nodeType) {
    selectedTool.value = `add-layer4-${nodeType}`;
  } else {
    selectedTool.value = `add-layer${layerId}`;
  }
  selectedNode.value = null;
  selectedEdge.value = null;
}

// Canvas click
function handleCanvasClick(event: MouseEvent) {
  // Ignore during panning
  if (isPanning.value) return;
  
  const rect = svgCanvas.value!.getBoundingClientRect();
  const screenX = event.clientX - rect.left;
  const screenY = event.clientY - rect.top;
  
  // Convert to world coordinates
  const { x, y } = screenToWorld(screenX, screenY);

  // Node addition mode
  if (selectedTool.value.startsWith('add-layer')) {
    // For layer 4, determine object/environment
    if (selectedTool.value === 'add-layer4-object') {
      addNode(x, y, 4, 'object');
    } else if (selectedTool.value === 'add-layer4-environment') {
      addNode(x, y, 4, 'environment');
    } else {
      const layerId = parseInt(selectedTool.value.replace('add-layer', ''));
      addNode(x, y, layerId);
    }
  }
  // Deselect
  else if (selectedTool.value === 'select') {
    selectedNode.value = null;
    selectedEdge.value = null;
  }
}

// Add node
function addNode(x: number, y: number, layer: number, nodeType?: string) {
  const layerInfo = layers.find(l => l.id === layer);
  
  // Y coordinate range based on layer (canvas 800 divided by 4)
  const layerYStart = (layer - 1) * 200;
  const layerYEnd = layer * 200;
  
  // Restrict Y coordinate within layer range
  let adjustedY = y;
  if (y < layerYStart) {
    adjustedY = layerYStart + 50;
  } else if (y > layerYEnd) {
    adjustedY = layerYEnd - 50;
  }
  
  // Determine type
  let type: NetworkNode['type'];
  if (nodeType) {
    type = nodeType as NetworkNode['type'];
  } else {
    type = layerInfo?.type as NetworkNode['type'] || 'attribute';
  }
  
  // Determine label
  let label: string;
  if (layer === 4) {
    if (type === 'object') {
      label = `Object ${network.value.nodes.filter(n => n.layer === 4 && n.type === 'object').length + 1}`;
    } else if (type === 'environment') {
      label = `Environment ${network.value.nodes.filter(n => n.layer === 4 && n.type === 'environment').length + 1}`;
    } else {
      label = `${layerInfo?.label || 'Node'} ${network.value.nodes.filter(n => n.layer === layer).length + 1}`;
    }
  } else {
    label = `${layerInfo?.label || 'ノード'} ${network.value.nodes.filter(n => n.layer === layer).length + 1}`;
  }
  
  const newNode: NetworkNode = {
    id: `node-${Date.now()}-${Math.random()}`,
    layer: layer as 1 | 2 | 3 | 4,
    type,
    label,
    x,
    y: adjustedY
  };

  network.value.nodes.push(newNode);
  emitUpdate();
  
  // Return to selection mode after adding
  selectedTool.value = 'select';
  selectedNode.value = newNode;
  updateTempNodeData(); // Update temporary data
}

// Node click
function handleNodeClick(node: NetworkNode) {
  if (selectedTool.value === 'select') {
    selectedNode.value = node;
    selectedEdge.value = null;
    updateTempNodeData(); // Update temporary data
  } else if (selectedTool.value === 'edge') {
    // Start edge creation
    if (!edgeStart.value) {
      edgeStart.value = node;
    } else {
      // Complete edge creation
      createEdge(edgeStart.value, node);
      edgeStart.value = null;
      tempEdgeEnd.value = null;
    }
  }
}

// Create edge with PAVE validation
function createEdge(from: NetworkNode, to: NetworkNode) {
  if (from.id === to.id) return;

  // Check if exists
  const exists = network.value.edges.some(
    e => (e.source_id === from.id && e.target_id === to.id) ||
         (e.source_id === to.id && e.target_id === from.id)
  );

  if (exists) {
    alert('This edge already exists');
    return;
  }

  // PAVE edge direction validation
  const validation = validateEdgeDirection(from, to);
  if (!validation.valid) {
    alert(`Invalid edge direction:\n\n${validation.reason}`);
    return;
  }

  const newEdge: NetworkEdge = {
    id: `edge-${Date.now()}`,
    source_id: from.id,
    target_id: to.id,
    type: 'type1',
    weight: 0 // Default is no correlation
  };

  network.value.edges.push(newEdge);
  emitUpdate();

  // Automatically select edge and show properties
  selectedTool.value = 'select';
  selectedEdge.value = newEdge;
  selectedNode.value = null;
  updateTempEdgeData(); // Update temporary data
}

// Select edge
function selectEdge(edge: NetworkEdge) {
  if (selectedTool.value === 'select') {
    selectedEdge.value = edge;
    selectedNode.value = null;
    updateTempEdgeData(); // Update temporary data
  }
}

// Delete edge
function deleteEdge(edge: NetworkEdge) {
  network.value.edges = network.value.edges.filter(e => e.id !== edge.id);
  selectedEdge.value = null;
  emitUpdate();
}

// Mouse move (edge preview)
function handleCanvasMouseMove(event: MouseEvent) {
  if (selectedTool.value === 'edge' && edgeStart.value) {
    const rect = svgCanvas.value!.getBoundingClientRect();
    const screenX = event.clientX - rect.left;
    const screenY = event.clientY - rect.top;
    const world = screenToWorld(screenX, screenY);
    tempEdgeEnd.value = { x: world.x, y: world.y };
  }
}

// Start drag
function startDrag(event: MouseEvent, node: NetworkNode) {
  if (selectedTool.value !== 'select') return;
  
  event.preventDefault();
  event.stopPropagation();
  isDragging.value = true;
  dragNode.value = node;
  
  const rect = svgCanvas.value!.getBoundingClientRect();
  const screenX = event.clientX - rect.left;
  const screenY = event.clientY - rect.top;
  const world = screenToWorld(screenX, screenY);
  
  dragOffset.value = {
    x: world.x - node.x,
    y: world.y - node.y
  };
  
  document.addEventListener('mousemove', handleDragMove);
  document.addEventListener('mouseup', handleDragEnd);
}

// During drag
function handleDragMove(event: MouseEvent) {
  if (!isDragging.value || !dragNode.value) return;
  
  const rect = svgCanvas.value!.getBoundingClientRect();
  const screenX = event.clientX - rect.left;
  const screenY = event.clientY - rect.top;
  const world = screenToWorld(screenX, screenY);
  
  dragNode.value.x = world.x - dragOffset.value.x;
  dragNode.value.y = world.y - dragOffset.value.y;
  
  // 境界内に制限（ワールド座標で）
  const maxX = canvasWidth.value / zoom.value;
  const maxY = canvasHeight.value / zoom.value;
  dragNode.value.x = Math.max(nodeRadius.value, Math.min(maxX - nodeRadius.value, dragNode.value.x));
  dragNode.value.y = Math.max(nodeRadius.value, Math.min(maxY - nodeRadius.value, dragNode.value.y));
}

// ドラッグ終了
function handleDragEnd() {
  if (isDragging.value) {
    isDragging.value = false;
    dragNode.value = null;
    emitUpdate();
  }
  document.removeEventListener('mousemove', handleDragMove);
  document.removeEventListener('mouseup', handleDragEnd);
}

// 選択削除
function deleteSelected() {
  if (selectedNode.value) {
    // 性能ノードは削除不可
    if (isPerformanceNode(selectedNode.value)) {
      alert('性能ノードは削除できません');
      return;
    }
    
    // ノード削除（関連エッジも削除）
    const nodeId = selectedNode.value.id;
    network.value.nodes = network.value.nodes.filter(n => n.id !== nodeId);
    network.value.edges = network.value.edges.filter(
      e => e.source_id !== nodeId && e.target_id !== nodeId
    );
    selectedNode.value = null;
    emitUpdate();
  } else if (selectedEdge.value) {
    deleteEdge(selectedEdge.value);
  }
}

// 自動レイアウト
function autoLayout() {
  
  // レイヤーごとの中央Y座標（キャンバス800を4分割）
  const layerCenterY = [100, 300, 500, 700]; // レイヤー1-4の中央
  
  // ノード数が多い場合の2段組用のしきい値
  const twoRowThreshold = 12; // 12個以上で2段組
  const layerHeight = 120; // 2段の場合の行間隔
  
  for (let layer = 1; layer <= 4; layer++) {
    if (layer === 4) {
      // レイヤー4は特別な処理：モノを左半分、環境を右半分に配置
      const objectNodes = network.value.nodes.filter(n => n.layer === 4 && n.type === 'object');
      const envNodes = network.value.nodes.filter(n => n.layer === 4 && n.type === 'environment');
      
      const yCenter = layerCenterY[layer - 1];
      const halfWidth = canvasWidth.value / 2;
      
      // モノを左半分に配置（多い場合は2段）
      if (objectNodes.length > 0) {
        if (objectNodes.length >= twoRowThreshold) {
          const nodesPerRow = Math.ceil(objectNodes.length / 2);
          const objectSpacing = halfWidth / (nodesPerRow + 1);
          objectNodes.forEach((node, index) => {
            const row = Math.floor(index / nodesPerRow);
            const col = index % nodesPerRow;
            node.x = objectSpacing * (col + 1);
            node.y = yCenter + (row === 0 ? -layerHeight/4 : layerHeight/4);
          });
        } else {
          const objectSpacing = halfWidth / (objectNodes.length + 1);
          objectNodes.forEach((node, index) => {
            node.x = objectSpacing * (index + 1);
            node.y = yCenter;
          });
        }
      }
      
      // 環境を右半分に配置（多い場合は2段）
      if (envNodes.length > 0) {
        if (envNodes.length >= twoRowThreshold) {
          const nodesPerRow = Math.ceil(envNodes.length / 2);
          const envSpacing = halfWidth / (nodesPerRow + 1);
          envNodes.forEach((node, index) => {
            const row = Math.floor(index / nodesPerRow);
            const col = index % nodesPerRow;
            node.x = halfWidth + envSpacing * (col + 1);
            node.y = yCenter + (row === 0 ? -layerHeight/4 : layerHeight/4);
          });
        } else {
          const envSpacing = halfWidth / (envNodes.length + 1);
          envNodes.forEach((node, index) => {
            node.x = halfWidth + envSpacing * (index + 1);
            node.y = yCenter;
          });
        }
      }
    } else {
      // レイヤー1-3の処理
      const layerNodes = network.value.nodes.filter(n => n.layer === layer);
      
      if (layerNodes.length === 0) continue;
      
      // このレイヤーの中央Y座標
      const yCenter = layerCenterY[layer - 1];
      
      // ノード数に応じて1段か2段かを決定
      if (layerNodes.length >= twoRowThreshold) {
        // 2段組
        const nodesPerRow = Math.ceil(layerNodes.length / 2);
        const spacing = canvasWidth.value / (nodesPerRow + 1);
        
        layerNodes.forEach((node, index) => {
          const row = Math.floor(index / nodesPerRow);
          const col = index % nodesPerRow;
          node.x = spacing * (col + 1);
          node.y = yCenter + (row === 0 ? -layerHeight/4 : layerHeight/4);
        });
      } else {
        // 1段組（従来通り）
        const spacing = canvasWidth.value / (layerNodes.length + 1);
        
        layerNodes.forEach((node, index) => {
          node.x = spacing * (index + 1);
          node.y = yCenter;
        });
      }
    }
  }
  
  emitUpdate();
}

// 全削除
function clearAll() {
  if (confirm('性能以外のノードとエッジを全て削除しますか？')) {
    // 性能ノード以外を削除
    network.value.nodes = network.value.nodes.filter(n => isPerformanceNode(n));
    network.value.edges = [];
    selectedNode.value = null;
    selectedEdge.value = null;
    emitUpdate();
  }
}

// 更新を通知
function emitUpdate() {
  isUpdating.value = true;
  emit('update:modelValue', JSON.parse(JSON.stringify(network.value)));
  
  // nextTickで更新フラグを下げる（Vueの更新サイクルが完了してから）
  nextTick(() => {
    isUpdating.value = false;
  });
}

// ズーム機能
function resetView() {
  
  // キャンバス全体のサイズ（ワールド座標）
  const worldWidth = canvasWidth.value; // 1200
  const worldHeight = canvasHeight.value; // 800
  
  // 実際の表示領域のサイズを取得（canvas-containerのサイズ）
  const rect = canvasContainer.value!.getBoundingClientRect();
  const viewWidth = rect.width;
  const viewHeight = rect.height;
  
  // キャンバス全体が表示領域に収まるズーム比率を計算（余白として0.95倍）
  const zoomX = (viewWidth * 0.95) / worldWidth;
  const zoomY = (viewHeight * 0.95) / worldHeight;
  zoom.value = Math.min(zoomX, zoomY);
  
  // 計算されたズーム値を最小値として設定
  minZoom.value = Math.max(0.1, Math.floor(zoom.value * 10) / 10);
  
  // スクロールを左上にリセット
  if (canvasContainer.value) {
    canvasContainer.value.scrollTop = 0;
    canvasContainer.value.scrollLeft = 0;
  }
}

function resetViewWithDebug() {
  logResetViewDebug();
  resetView();
}

function handlePanStart(event: MouseEvent) {
  // パン機能は一時的に無効化（スクロールで代替）
  return;
  
  // 右クリックまたはSpaceキー押下中のみパン
  if (event.button === 2 || event.shiftKey) {
    event.preventDefault();
    isPanning.value = true;
    panStart.value = {
      x: event.clientX - panX.value,
      y: event.clientY - panY.value
    };
    document.addEventListener('mousemove', handlePanMove);
    document.addEventListener('mouseup', handlePanEnd);
  }
}

function handlePanMove(event: MouseEvent) {
  if (isPanning.value) {
    panX.value = event.clientX - panStart.value.x;
    panY.value = event.clientY - panStart.value.y;
  }
}

function handlePanEnd() {
  isPanning.value = false;
  document.removeEventListener('mousemove', handlePanMove);
  document.removeEventListener('mouseup', handlePanEnd);
}

async function downloadAsImage() {
  if (!svgCanvas.value) return;

  try {
    // SVGを複製
    const svgClone = svgCanvas.value.cloneNode(true) as SVGSVGElement;
    
    // 複製したSVGのtransformをリセットして、全体を表示
    const mainGroup = svgClone.querySelector('g[transform]');
    if (mainGroup) {
      mainGroup.setAttribute('transform', 'translate(0, 0) scale(1)');
    }
    
    // SVGのviewBoxを設定して全体が見えるようにする
    svgClone.setAttribute('viewBox', `0 0 ${canvasWidth.value} ${canvasHeight.value}`);
    svgClone.setAttribute('width', String(canvasWidth.value));
    svgClone.setAttribute('height', String(canvasHeight.value));
    
    // SVGをdata URLに変換
    const svgData = new XMLSerializer().serializeToString(svgClone);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    
    // Imageオブジェクトを作成してSVGを読み込む
    const img = new Image();
    img.onload = () => {
      // Canvasを作成
      const canvas = document.createElement('canvas');
      canvas.width = canvasWidth.value;
      canvas.height = canvasHeight.value;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      // 背景を塗る
      ctx.fillStyle = '#fafafa';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // SVGを描画
      ctx.drawImage(img, 0, 0);
      
      // ダウンロード
      const link = document.createElement('a');
      link.download = `network-diagram-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      
      // クリーンアップ
      URL.revokeObjectURL(svgUrl);
    };
    
    img.onerror = () => {
      console.error('SVGの変換に失敗しました');
      alert('画像のダウンロードに失敗しました');
      URL.revokeObjectURL(svgUrl);
    };
    
    img.src = svgUrl;
  } catch (error) {
    console.error('画像の生成に失敗しました:', error);
    alert('画像のダウンロードに失敗しました');
  }
}

/**
 * Trigger file input for Excel import
 */
function triggerImportExcel() {
  excelFileInput.value?.click();
}

/**
 * Download weight matrix as Excel file
 * - Rows: Source nodes (PAVE order)
 * - Columns: Target nodes (PAVE order)
 * - Editable cells: V→A, A→A, A→P only
 * - Other cells: Grey background (disabled)
 */
function downloadWeightMatrix() {
  // Sort nodes by PAVE order (P=1, A=2, V=3, E=4)
  const sortedNodes = [...network.value.nodes].sort((a, b) => a.layer - b.layer);

  // Get layer boundaries for labeling
  const layerBoundaries: { layer: number; label: string; start: number; end: number }[] = [];
  let currentLayer = 0;
  let startIdx = 0;

  sortedNodes.forEach((node, idx) => {
    if (node.layer !== currentLayer) {
      if (currentLayer !== 0) {
        layerBoundaries.push({
          layer: currentLayer,
          label: ['P', 'A', 'V', 'E'][currentLayer - 1],
          start: startIdx,
          end: idx - 1
        });
      }
      currentLayer = node.layer;
      startIdx = idx;
    }
  });
  // Add last layer
  if (currentLayer !== 0) {
    layerBoundaries.push({
      layer: currentLayer,
      label: ['P', 'A', 'V', 'E'][currentLayer - 1],
      start: startIdx,
      end: sortedNodes.length - 1
    });
  }

  // Create edge lookup map (source_id -> target_id -> weight)
  const edgeMap = new Map<string, Map<string, number>>();
  network.value.edges.forEach(edge => {
    if (!edgeMap.has(edge.source_id)) {
      edgeMap.set(edge.source_id, new Map());
    }
    edgeMap.get(edge.source_id)!.set(edge.target_id, edge.weight ?? 0);
  });

  // Build worksheet data
  // Row 0: "Target →" header with layer labels
  // Row 1: Empty corner + node labels
  // Row 2+: Source nodes (rows) × Target nodes (columns)
  const wsData: (string | number | null)[][] = [];

  // Header row 1: "Target →" + Layer labels for columns
  const targetLabelRow: (string | null)[] = ['Target →'];
  sortedNodes.forEach(node => {
    const layerLabel = ['P', 'A', 'V', 'E'][node.layer - 1];
    targetLabelRow.push(`[${layerLabel}]`);
  });
  wsData.push(targetLabelRow);

  // Header row 2: "↓ Source" + node labels for columns
  const headerRow: (string | null)[] = ['↓ Source'];
  sortedNodes.forEach(node => {
    headerRow.push(node.label);
  });
  wsData.push(headerRow);

  // Data rows: Each source node (rows)
  sortedNodes.forEach((sourceNode, rowIdx) => {
    const row: (string | number | null)[] = [];
    // First column: source node label with layer prefix
    const sourceLayerLabel = ['P', 'A', 'V', 'E'][sourceNode.layer - 1];
    row.push(`[${sourceLayerLabel}] ${sourceNode.label}`);

    // Other columns: weights, empty (editable), or "-" (non-editable)
    sortedNodes.forEach((targetNode, colIdx) => {
      // Check if this cell is editable (V→A, A→A, A→P)
      // Also exclude self-loops (same node)
      const isSelfLoop = sourceNode.id === targetNode.id;
      const isEditable = !isSelfLoop && isEditableCell(sourceNode.layer, targetNode.layer);

      if (isEditable) {
        // Get weight if edge exists
        const weight = edgeMap.get(sourceNode.id)?.get(targetNode.id);
        row.push(weight !== undefined ? weight : null);
      } else {
        // Non-editable cell - mark with "-" to indicate disabled
        row.push('-');
      }
    });
    wsData.push(row);
  });

  // Create worksheet
  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // Set column widths
  const colWidths = [{ wch: 25 }]; // First column wider
  sortedNodes.forEach(() => colWidths.push({ wch: 12 }));
  ws['!cols'] = colWidths;

  // Create workbook and download
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Weight Matrix');

  // Add a legend sheet
  const legendData = [
    ['Weight Matrix Legend'],
    [''],
    ['Matrix Structure:'],
    ['- Rows = Source nodes (↓ Source)'],
    ['- Columns = Target nodes (Target →)'],
    ['- Cell value = Weight of edge from row node to column node'],
    [''],
    ['Layers:'],
    ['[P] = Performance (Layer 1) - Cannot be source'],
    ['[A] = Attribute (Layer 2)'],
    ['[V] = Variable (Layer 3)'],
    ['[E] = Entity (Layer 4)'],
    [''],
    ['Cell Markers:'],
    ['(number) = Edge weight (-1.0 to +1.0)'],
    ['(empty) = No edge (editable area)'],
    ['"-" = Non-editable cell (invalid connection in PAVE model)'],
    [''],
    ['Editable Cells (Valid Connections):'],
    ['V → A: Variable affects Attribute'],
    ['A → A: Attribute affects Attribute (between different nodes)'],
    ['A → P: Attribute affects Performance'],
    ['Note: Self-loops (A → same A) are NOT allowed'],
    [''],
    ['Weight Range: -1.0 to +1.0'],
    ['Positive: Positive causal effect'],
    ['Negative: Negative causal effect'],
    ['Zero: No effect'],
    [''],
    ['Instructions:'],
    ['1. Edit values only in cells without "-"'],
    ['2. Leave cell empty to delete existing edge'],
    ['3. Add value to empty cell to create new edge'],
    ['4. Do NOT modify cells marked with "-"'],
    ['5. Import the modified file back to the system']
  ];
  const legendWs = XLSX.utils.aoa_to_sheet(legendData);
  legendWs['!cols'] = [{ wch: 50 }];
  XLSX.utils.book_append_sheet(wb, legendWs, 'Legend');

  // Download
  const filename = `weight_matrix_${new Date().toISOString().slice(0, 10)}.xlsx`;
  XLSX.writeFile(wb, filename);
}

/**
 * Check if a cell is editable based on source and target layers
 * Valid: V→A (3→2), A→A (2→2), A→P (2→1)
 */
function isEditableCell(sourceLayer: number, targetLayer: number): boolean {
  // V → A (3 → 2)
  if (sourceLayer === 3 && targetLayer === 2) return true;
  // A → A (2 → 2)
  if (sourceLayer === 2 && targetLayer === 2) return true;
  // A → P (2 → 1)
  if (sourceLayer === 2 && targetLayer === 1) return true;
  return false;
}

/**
 * Import weight matrix from Excel file
 */
async function importWeightMatrix(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  try {
    const data = await file.arrayBuffer();
    const workbook = XLSX.read(data);

    // Get the first sheet (Weight Matrix)
    const ws = workbook.Sheets[workbook.SheetNames[0]];
    const jsonData = XLSX.utils.sheet_to_json<(string | number | null)[]>(ws, { header: 1 });

    if (jsonData.length < 3) {
      alert('Invalid Excel format: Not enough rows');
      return;
    }

    // Parse header rows
    // Row 0: Layer labels ("Target →", "[P]", "[A]", "[V]", "[E]", ...)
    // Row 1: Node labels ("↓ Source", "node1", "node2", ...)
    const headerRow = jsonData[1] as string[];

    // Create map from node label to node
    const nodeLabelMap = new Map<string, NetworkNode>();
    network.value.nodes.forEach(node => {
      nodeLabelMap.set(node.label, node);
    });

    // Build column index to target node mapping (using header row labels)
    const colToTargetNode: (NetworkNode | null)[] = [null]; // Column 0 is source label
    for (let colIdx = 1; colIdx < headerRow.length; colIdx++) {
      const targetLabel = headerRow[colIdx];
      const targetNode = nodeLabelMap.get(targetLabel) || null;
      colToTargetNode.push(targetNode);
    }

    // Track changes
    const changes = {
      updated: 0,
      created: 0,
      deleted: 0,
      skipped: 0
    };

    // Process data rows (starting from row 2)
    for (let rowIdx = 2; rowIdx < jsonData.length; rowIdx++) {
      const row = jsonData[rowIdx] as (string | number | null)[];
      if (!row || row.length === 0) continue;

      // Parse source node label from first cell (format: "[P] NodeLabel")
      const sourceCellValue = String(row[0] || '');
      const sourceLabel = sourceCellValue.replace(/^\[[PAVE]\]\s*/, '');
      const sourceNode = nodeLabelMap.get(sourceLabel);

      if (!sourceNode) {
        console.warn(`Source node not found: "${sourceLabel}"`);
        changes.skipped++;
        continue;
      }

      // Process each target column
      for (let colIdx = 1; colIdx < row.length; colIdx++) {
        const targetNode = colToTargetNode[colIdx];
        if (!targetNode) {
          continue;
        }

        // Check if this cell is editable (skip self-loops and invalid connections)
        if (sourceNode.id === targetNode.id) continue; // Self-loop
        if (!isEditableCell(sourceNode.layer, targetNode.layer)) continue;

        const cellValue = row[colIdx];
        const existingEdgeIdx = network.value.edges.findIndex(
          e => e.source_id === sourceNode.id && e.target_id === targetNode.id
        );

        if (cellValue === null || cellValue === undefined || cellValue === '') {
          // Empty cell - delete edge if exists
          if (existingEdgeIdx !== -1) {
            network.value.edges.splice(existingEdgeIdx, 1);
            changes.deleted++;
          }
        } else if (cellValue === '-') {
          // Non-editable cell marker - skip
          continue;
        } else {
          // Has value - update or create edge
          const weight = typeof cellValue === 'number' ? cellValue : parseFloat(String(cellValue));

          if (isNaN(weight)) continue;

          // Clamp to valid range
          const clampedWeight = Math.max(-1, Math.min(1, weight));

          if (existingEdgeIdx !== -1) {
            // Update existing edge
            const existingWeight = network.value.edges[existingEdgeIdx].weight ?? 0;
            if (Math.abs(existingWeight - clampedWeight) > 0.0001) {
              network.value.edges[existingEdgeIdx].weight = clampedWeight;
              changes.updated++;
            }
          } else {
            // Create new edge
            const newEdge: NetworkEdge = {
              id: `edge-${Date.now()}-${Math.random()}`,
              source_id: sourceNode.id,
              target_id: targetNode.id,
              type: 'type1',
              weight: clampedWeight
            };
            network.value.edges.push(newEdge);
            changes.created++;
          }
        }
      }
    }

    // Emit update
    emitUpdate();

    // Show result
    let message = `Import completed!\n\nUpdated: ${changes.updated} edges\nCreated: ${changes.created} edges\nDeleted: ${changes.deleted} edges`;
    if (changes.skipped > 0) {
      message += `\nSkipped: ${changes.skipped} rows (node not found)`;
    }
    alert(message);

  } catch (error) {
    console.error('Excel import error:', error);
    alert('Failed to import Excel file. Please check the file format.');
  } finally {
    // Reset file input
    input.value = '';
  }
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDragMove);
  document.removeEventListener('mouseup', handleDragEnd);
  document.removeEventListener('mousemove', handlePanMove);
  document.removeEventListener('mouseup', handlePanEnd);
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

.network-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: $gray;
  min-height: 0; // flexboxで適切に縮小できるように
}

.network-editor-wrapper {
  display: flex;
  flex-direction: row;
  flex: 1;
  gap: 1.2vw;
  overflow: visible;
  min-height: 0; /* flexboxで縮小可能にする */
  position: relative;
}

.toolbar {
  display: flex;
  align-items: center;
  padding: clamp(0.6rem, 1.2vh, 0.8rem) clamp(0.8rem, 1.5vw, 1rem);
  background: linear-gradient(145deg, color.adjust($gray, $lightness: 10%), color.adjust($gray, $lightness: 6%));
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  gap: 1.2vw;
  overflow-x: auto;
  flex-wrap: nowrap;
  flex-shrink: 0; /* ツールバーは縮まないように */
  @include custom-scrollbar;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.7);
}

.tool-group {
  display: flex;
  gap: 0.6vw;
  align-items: center;
}

.zoom-label {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
  font-weight: 500;
}

.zoom-slider {
  width: clamp(6rem, 10vw, 8rem);
  height: 0.6vh;
  cursor: pointer;
  
  // Webkitブラウザ用のスタイル
  &::-webkit-slider-track {
    background: color.adjust($gray, $lightness: 15%);
    border-radius: 0.3vh;
  }
  
  &::-webkit-slider-thumb {
    background: $main_1;
    border: none;
    width: 1.2vw;
    height: 1.2vw;
    border-radius: 50%;
    cursor: pointer;
  }
  
  // Firefox用のスタイル
  &::-moz-range-track {
    background: color.adjust($gray, $lightness: 15%);
    border-radius: 0.3vh;
  }
  
  &::-moz-range-thumb {
    background: $main_1;
    border: none;
    width: 1.2vw;
    height: 1.2vw;
    border-radius: 50%;
    cursor: pointer;
  }
}

.zoom-value {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.4);
  min-width: clamp(2.5rem, 4vw, 3rem);
  text-align: right;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 0.6vw;
  padding: clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.6rem, 1.2vw, 0.8rem);
  background: color.adjust($gray, $lightness: 20%);
  border: 2px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: $white;
  transition: all 0.2s;
}

.tool-btn:hover:not(:disabled) {
  background: color.adjust($gray, $lightness: 25%);
  border-color: color.adjust($white, $alpha: -0.7);
  transform: translateY(-0.1vh);
}

.tool-btn.active {
  background: color.adjust($main_1, $alpha: -0.85);
  border-color: $main_1;
  color: $main_1;
  box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.7);
}

.tool-btn.danger {
  color: $sub_1;
  
  &:hover:not(:disabled) {
    color: color.adjust($sub_1, $lightness: 10%);
    border-color: $sub_1;
  }
}

.tool-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: color.adjust($gray, $lightness: 10%);
}

// Weight mode selector styles
.weight-mode-group {
  display: flex;
  align-items: center;
  gap: 0.5vw;
}

.weight-mode-label {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.3);
  white-space: nowrap;
}

.weight-mode-select {
  padding: clamp(0.3rem, 0.6vh, 0.4rem) clamp(0.5rem, 1vw, 0.6rem);
  background: color.adjust($gray, $lightness: 20%);
  border: 1px solid color.adjust($white, $alpha: -0.8);
  border-radius: 0.4vw;
  color: $white;
  font-size: clamp(0.7rem, 0.85vw, 0.75rem);
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: color.adjust($white, $alpha: -0.6);
  }

  &:focus {
    outline: none;
    border-color: $main_1;
    box-shadow: 0 0 0 2px color.adjust($main_1, $alpha: -0.7);
  }

  option {
    background: $gray;
    color: $white;
  }
}

// Continuous weight input styles
.continuous-weight-input {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  .property-input {
    text-align: center;
    font-family: monospace;
  }

  .weight-slider {
    width: 100%;
    height: 6px;
    -webkit-appearance: none;
    appearance: none;
    background: linear-gradient(to right, $sub_1 0%, silver 50%, $main_1 100%);
    border-radius: 3px;
    cursor: pointer;

    &::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      background: $white;
      border-radius: 50%;
      border: 2px solid $main_1;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        transform: scale(1.1);
        box-shadow: 0 2px 8px color.adjust($main_1, $alpha: -0.5);
      }
    }

    &::-moz-range-thumb {
      width: 16px;
      height: 16px;
      background: $white;
      border-radius: 50%;
      border: 2px solid $main_1;
      cursor: pointer;
    }
  }

  .weight-value-display {
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    color: $main_1;
    font-family: monospace;
  }
}

.tool-icon {
  font-size: clamp(0.9rem, 1.2vw, 1rem);
}

.tool-divider {
  width: 1px;
  height: 24px;
  background: #e0e0e0;
}

.spacer {
  flex: 1;
}

.info-group {
  display: flex;
  gap: 16px;
}

.info-text {
  font-size: 13px;
  color: #666;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: auto;
  background: color.adjust($gray, $lightness: 5%);
  min-width: 0; /* flexboxで必要 */
  @include custom-scrollbar;
  margin-top: 0; // 上部の余白を削除して見切れを防ぐ
}

.layer-legend {
  display: flex;
  flex-direction: column;
  width: clamp(12rem, 20vw, 16rem);
  padding: clamp(1rem, 2vh, 1.25rem);
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 0 0 0.8vw 0;
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.5);
  overflow-y: auto;
  flex-shrink: 0;
  border: 1px solid color.adjust($white, $alpha: -0.95);
  @include custom-scrollbar;
}

.layer-legend h3 {
  margin: 0 0 clamp(0.8rem, 1.5vh, 1rem) 0;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  font-weight: 600;
  color: $white;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.6vw;
  font-size: clamp(0.7rem, 0.9vw, 0.75rem);
}

.legend-icon {
  width: clamp(0.8rem, 1.4vw, 1rem);
  height: clamp(0.8rem, 1.4vw, 1rem);
  flex-shrink: 0;
}

.legend-label {
  color: color.adjust($white, $alpha: -0.3);
}

.legend-section {
  margin-top: clamp(1.2rem, 2vh, 1.5rem);
  padding-top: clamp(1rem, 1.8vh, 1.25rem);
  border-top: 1px solid color.adjust($white, $alpha: -0.9);
}

.legend-section h4 {
  margin: 0 0 clamp(0.6rem, 1.2vh, 0.8rem) 0;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 600;
  color: $white;
}

.zoom-controls {
  display: flex;
  flex-direction: column;
  gap: clamp(0.4rem, 0.8vh, 0.6rem);
}

.zoom-label {
  font-size: clamp(0.7rem, 0.9vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.3);
  font-weight: 500;
}

.zoom-slider {
  width: 100%;
  height: clamp(0.3rem, 0.5vh, 0.4rem);
  cursor: pointer;
  background: color.adjust($gray, $lightness: -10%);
  border-radius: 0.3vw;
  outline: none;
  
  // Track styling
  &::-webkit-slider-track {
    background: linear-gradient(90deg, 
      color.adjust($gray, $lightness: -15%) 0%, 
      color.adjust($main_1, $alpha: -0.7) 50%, 
      color.adjust($main_2, $alpha: -0.7) 100%);
    border-radius: 0.3vw;
    height: 100%;
  }
  
  &::-moz-range-track {
    background: linear-gradient(90deg, 
      color.adjust($gray, $lightness: -15%) 0%, 
      color.adjust($main_1, $alpha: -0.7) 50%, 
      color.adjust($main_2, $alpha: -0.7) 100%);
    border-radius: 0.3vw;
    height: 100%;
    border: none;
  }
  
  // Thumb styling
  &::-webkit-slider-thumb {
    appearance: none;
    width: clamp(0.8rem, 1.2vw, 1rem);
    height: clamp(0.8rem, 1.2vw, 1rem);
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.5);
    transition: all 0.2s ease;
    
    &:hover {
      transform: scale(1.1);
      background: linear-gradient(135deg, color.adjust($main_1, $lightness: 15%) 0%, color.adjust($main_2, $lightness: 15%) 100%);
    }
  }
  
  &::-moz-range-thumb {
    width: clamp(0.8rem, 1.2vw, 1rem);
    height: clamp(0.8rem, 1.2vw, 1rem);
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.5);
  }
}

.zoom-value {
  font-size: clamp(0.65rem, 0.85vw, 0.7rem);
  color: color.adjust($white, $alpha: -0.4);
  text-align: center;
  font-weight: 500;
  font-family: monospace;
}

.action-controls {
  display: flex;
  flex-direction: column;
  gap: clamp(0.4rem, 0.8vh, 0.6rem);
}

.control-btn {
  display: flex;
  align-items: center;
  gap: clamp(0.3rem, 0.5vw, 0.4rem);
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1vw, 0.8rem);
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  cursor: pointer;
  font-size: clamp(0.7rem, 0.9vw, 0.75rem);
  font-weight: 500;
  color: $white;
  transition: all 0.3s ease;
  text-align: left;
  width: 100%;

  &:hover {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: color.adjust($main_1, $alpha: -0.3);
    transform: translateY(-0.05vh);
    box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.6);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 0.1vh 0.3vh color.adjust($main_1, $alpha: -0.7);
  }

  &.danger {
    &:hover {
      background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
      border-color: #d32f2f;
      box-shadow: 0 0.2vh 0.5vh rgba(211, 47, 47, 0.4);
    }
  }

  svg {
    font-size: clamp(0.75rem, 0.95vw, 0.8rem);
    flex-shrink: 0;
  }

  span {
    flex: 1;
  }
}

.network-canvas {
  display: block;
  background: $white; // SVGキャンバスは白背景を維持
  user-select: none;
}

.network-canvas.panning {
  cursor: move;
}

.network-canvas.dragging {
  cursor: grabbing;
}

.node {
  cursor: grab;
}

.node:active {
  cursor: grabbing;
}

.node-circle {
  transition: stroke 0.2s;
}

.node-circle:hover {
  filter: brightness(1.1);
}

.node.selected .node-circle {
  filter: drop-shadow(0 0 8px rgba(255, 87, 34, 0.6));
}

.node-label {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 500;
  pointer-events: none;
  user-select: none;
}

.node-layer-number {
  pointer-events: none;
  user-select: none;
}

.edge {
  cursor: pointer;
}

.edge:hover line {
  stroke: $sub_1 !important;
  stroke-width: 3 !important;
}

.canvas-help {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: color.adjust($gray, $lightness: 30%);
  pointer-events: none;
}

.canvas-help p {
  margin: 0.8vh 0;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
}

.properties-panel {
  width: clamp(12rem, 20vw, 16rem);
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 0 0 0 0.8vw;
  padding: clamp(1rem, 2vh, 1.25rem);
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.5);
  overflow-y: auto;
  flex-shrink: 0;
  border: 1px solid color.adjust($white, $alpha: -0.95);
  @include custom-scrollbar;
}

.properties-panel h3 {
  margin: 0 0 clamp(0.8rem, 1.5vh, 1rem) 0;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  font-weight: 600;
  color: $white;
}

.property-group {
  margin-bottom: clamp(0.6rem, 1.2vh, 0.75rem);
}

.property-group label {
  display: block;
  margin-bottom: clamp(0.3rem, 0.6vh, 0.4rem);
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 500;
  color: color.adjust($white, $alpha: -0.3);
}

.property-input,
.property-select {
  width: 100%;
  padding: clamp(0.4rem, 0.8vh, 0.5rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  background: $gray;
  color: $white;
  transition: all 0.2s;
  
  &:focus {
    outline: none;
    border-color: $main_1;
  }
}

.coords {
  display: flex;
  gap: 1.2vw;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
}

.connection-info {
  background: $gray;
  padding: clamp(0.4rem, 0.8vh, 0.5rem);
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.undirected-notice {
  color: color.adjust($white, $alpha: -0.3);
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-style: italic;
  margin: 0;
}

.connection-info p {
  margin: 0.4vh 0;
  color: color.adjust($white, $alpha: -0.4);
}

.property-empty {
  color: color.adjust($white, $alpha: -0.5);
  text-align: center;
  padding: clamp(2rem, 4vh, 2.5rem) clamp(1rem, 2vw, 1.25rem);
}

.property-empty p {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
}

.property-actions {
  display: flex;
  gap: 0.8vw;
  margin-top: clamp(1rem, 2vh, 1.25rem);
  padding-top: clamp(0.8rem, 1.5vh, 1rem);
  border-top: 1px solid color.adjust($white, $alpha: -0.95);
}

.save-btn,
.cancel-btn {
  flex: 1;
  padding: 8px 8px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #ddd;
}

.save-btn {
  background: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.save-btn:hover {
  background: #45a049;
  border-color: #45a049;
}

.cancel-btn {
  background: white;
  color: #666;
}

.cancel-btn:hover {
  background: #f5f5f5;
  border-color: #999;
}
</style>