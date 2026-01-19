<template>
  <div class="tradeoff-network-viewer">
    <!-- Toolbar -->
    <div class="viewer-toolbar">
      <div class="tool-group">
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
        <button class="tool-btn" @click="resetView" title="Fit">
          <FontAwesomeIcon :icon="['fas', 'expand']" />
        </button>
        <button class="tool-btn" @click="downloadAsImage" title="Download">
          <FontAwesomeIcon :icon="['fas', 'camera']" />
        </button>
      </div>
    </div>

    <div class="network-viewer" ref="viewerContainer">
      <div class="canvas-container">
        <svg
          ref="svgCanvas"
          class="network-canvas"
          :width="canvasWidth * zoom"
          :height="canvasHeight * zoom"
          @contextmenu.prevent
        >
          <!-- Grid pattern -->
          <defs>
            <pattern
              id="grid-tradeoff"
              width="20"
              height="20"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 20 0 L 0 0 0 20"
                fill="none"
                stroke="#f0f0f0"
                stroke-width="0.5"
              />
            </pattern>

            <!-- Arrow markers for negative φ (tradeoff) - red -->
            <marker id="arrow-neg-strong" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#c62828" />
            </marker>
            <marker id="arrow-neg-medium" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#e57373" />
            </marker>
            <marker id="arrow-neg-weak" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#ffcdd2" />
            </marker>

            <!-- Arrow markers for positive φ (synergy) - green -->
            <marker id="arrow-pos-strong" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#2e7d32" />
            </marker>
            <marker id="arrow-pos-medium" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#81c784" />
            </marker>
            <marker id="arrow-pos-weak" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#c8e6c9" />
            </marker>

            <!-- Arrow markers for fallback (orange) -->
            <marker id="arrow-fallback-strong" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#ff9800" />
            </marker>
            <marker id="arrow-fallback-medium" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M 0 0 L 0 6 L 9 3 z" fill="#ffb74d" />
            </marker>

            <!-- Arrow markers for weighted edges (dynamic based on actual colors) -->
            <marker
              v-for="color in uniqueEdgeColors"
              :key="`arrow-${color}`"
              :id="`arrow-tradeoff-${encodeColor(color)}`"
              markerWidth="10"
              markerHeight="10"
              refX="8"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M 0 0 L 0 6 L 9 3 z" :fill="color" />
            </marker>
          </defs>

          <!-- Main content group -->
          <g :transform="`scale(${zoom})`">
            <!-- Grid background -->
            <rect
              :x="0"
              :y="0"
              :width="canvasWidth"
              :height="canvasHeight"
              fill="url(#grid-tradeoff)"
            />

            <!-- PAVE Layer backgrounds -->
            <g class="layer-backgrounds">
              <rect
                v-for="(layer, idx) in layers"
                :key="layer.id"
                :x="0"
                :y="idx * 200"
                :width="canvasWidth"
                :height="200"
                :fill="layer.color"
                opacity="0.1"
              />
            </g>

            <!-- Edges layer -->
            <g class="edges-layer">
              <line
                v-for="edge in network.edges"
                :key="edge.id"
                :x1="getNodeById(edge.source_id)?.x"
                :y1="getNodeById(edge.source_id)?.y"
                :x2="getAdjustedLineEnd(edge).x"
                :y2="getAdjustedLineEnd(edge).y"
                :stroke="getEdgeColor(edge)"
                :stroke-width="getEdgeStrokeWidth(edge)"
                :opacity="getEdgeOpacity(edge)"
                stroke-linecap="round"
                :marker-end="getEdgeMarker(edge)"
              />
            </g>

            <!-- Nodes layer -->
            <g class="nodes-layer">
              <g
                v-for="node in network.nodes"
                :key="node.id"
                class="node"
              >
                <!-- Layer 1: Performance (circle) -->
                <circle
                  v-if="node.layer === 1"
                  :cx="node.x"
                  :cy="node.y"
                  :r="isSelectedPerformance(node) ? 22 : 18"
                  :fill="getNodeFill(node)"
                  :stroke="getNodeStroke(node)"
                  :stroke-width="isSelectedPerformance(node) ? 4 : 1.5"
                  :opacity="getNodeOpacity(node)"
                />

                <!-- Layer 2: Attribute (triangle) -->
                <polygon
                  v-else-if="node.layer === 2"
                  :points="getTrianglePoints(node.x, node.y, isHighContributionNode(node))"
                  :fill="getNodeFill(node)"
                  :stroke="getNodeStroke(node)"
                  :stroke-width="isHighContributionNode(node) ? 3 : 1.5"
                  :opacity="getNodeOpacity(node)"
                />

                <!-- Layer 3: Variable (diamond) -->
                <polygon
                  v-else-if="node.layer === 3"
                  :points="getDiamondPoints(node.x, node.y)"
                  :fill="getNodeFill(node)"
                  stroke="#333"
                  stroke-width="1.5"
                  :opacity="getNodeOpacity(node)"
                />

                <!-- Layer 4: Object (rectangle) -->
                <rect
                  v-else-if="node.layer === 4 && node.type === 'object'"
                  :x="node.x - 36"
                  :y="node.y - 18"
                  :width="72"
                  :height="36"
                  :fill="getNodeFill(node)"
                  stroke="#333"
                  stroke-width="1.5"
                  rx="4"
                  :opacity="getNodeOpacity(node)"
                />

                <!-- Layer 4: Environment (square) -->
                <rect
                  v-else-if="node.layer === 4 && node.type === 'environment'"
                  :x="node.x - 18"
                  :y="node.y - 18"
                  :width="36"
                  :height="36"
                  :fill="getNodeFill(node)"
                  stroke="#333"
                  stroke-width="1.5"
                  rx="4"
                  :opacity="getNodeOpacity(node)"
                />

                <!-- Fallback -->
                <circle
                  v-else-if="node.layer === 4"
                  :cx="node.x"
                  :cy="node.y"
                  :r="18"
                  :fill="getNodeFill(node)"
                  stroke="#333"
                  stroke-width="1.5"
                  :opacity="getNodeOpacity(node)"
                />

                <!-- Node label -->
                <text
                  :x="node.x"
                  :y="node.y + 18 + 15"
                  text-anchor="middle"
                  class="node-label"
                  :fill="getNodeLabelColor(node)"
                  :opacity="getNodeOpacity(node)"
                  :font-weight="isSelectedPerformance(node) || isHighContributionNode(node) ? 'bold' : 'normal'"
                >
                  {{ node.label }}
                </text>
              </g>
            </g>
          </g>
        </svg>
      </div>
    </div>

    <!-- Layer legend -->
    <div class="layer-legend">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import type { NetworkStructure, NetworkNode, Performance } from '../../types/project';
import type { NodeShapleyValue, EdgeShapleyValue } from '@/utils/api';

interface Props {
  network: NetworkStructure;
  performances: Performance[];
  perfIId?: string;  // First selected performance
  perfJId?: string;  // Second selected performance
  nodeShapleyValues?: NodeShapleyValue[];  // Shapley contribution values for V ∪ A nodes
  edgeShapleyValues?: EdgeShapleyValue[];  // Shapley contribution values for edges
  topN?: number;  // Number of top contributors to highlight
}

const props = withDefaults(defineProps<Props>(), {
  topN: 5,
});

const canvasWidth = ref(1200);
const canvasHeight = ref(800);
const zoom = ref(1);
const minZoom = ref(0.3);
const svgCanvas = ref<SVGSVGElement>();
const viewerContainer = ref<HTMLDivElement>();

// Layer definitions
const layers = [
  { id: 1, label: 'Performance', color: '#4CAF50' },
  { id: 2, label: 'Attribute', color: '#2196F3' },
  { id: 3, label: 'Variable', color: '#FFC107' },
  { id: 4, label: 'Entity', color: '#9C27B0' }
];

// Edge weight colors (supports both new ±5 and legacy ±0.33 formats)
const edgeWeightColors: Record<number, string> = {
  5: '#002040',      // Strong positive (7-level)
  3: '#004563',      // Strong positive (5-level) / Medium-strong (7-level)
  1: '#588da2',      // Moderate positive
  0.33: '#c3dde2',   // Weak positive (legacy)
  0: '#c0c0c0',      // No correlation (neutral gray)
  [-0.33]: '#e9c1c9', // Weak negative (legacy)
  [-1]: '#c94c62',   // Moderate negative
  [-3]: '#9f1e35',   // Strong negative (5-level) / Medium-strong (7-level)
  [-5]: '#6f0020'    // Strong negative (7-level)
};

// Encode color string for use in SVG ID
function encodeColor(color: string): string {
  return color.replace(/[^a-zA-Z0-9]/g, '_');
}

// Infer maxWeight from actual edge data
// - If any |weight| > 3: 7-level mode (maxWeight = 5)
// - If any |weight| > 1: 5-level mode (maxWeight = 3)
// - Otherwise: 3-level or continuous mode (maxWeight = 1)
const inferredMaxWeight = computed(() => {
  if (!props.network?.edges) return 1;
  let maxAbsWeight = 0;
  for (const edge of props.network.edges) {
    const absWeight = Math.abs(edge.weight ?? 0);
    if (absWeight > maxAbsWeight) maxAbsWeight = absWeight;
  }
  if (maxAbsWeight > 3) return 5;  // 7-level
  if (maxAbsWeight > 1) return 3;  // 5-level
  return 1;  // 3-level or continuous
});

// Get default edge color based on weight (for non-highlighted edges)
function getDefaultEdgeColor(edge: any): string {
  const weight = edge.weight ?? 0;

  // Check for exact match in color map
  if (weight in edgeWeightColors) {
    return edgeWeightColors[weight as keyof typeof edgeWeightColors];
  }

  // For continuous values, interpolate
  // maxWeight is inferred from actual edge data
  const maxWeight = inferredMaxWeight.value;
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

  return '#c0c0c0';
}

// Compute unique edge colors for marker definitions
const uniqueEdgeColors = computed(() => {
  const colors = new Set<string>();
  for (const edge of props.network.edges) {
    colors.add(getDefaultEdgeColor(edge));
  }
  colors.add('#333'); // Default for undirected edges
  colors.add('#c0c0c0'); // Fallback
  return Array.from(colors);
});

// Get max contribution for normalization (using abs_phi from NodeShapleyValue)
const maxContribution = computed(() => {
  if (!props.nodeShapleyValues || props.nodeShapleyValues.length === 0) return 1;
  return Math.max(...props.nodeShapleyValues.map(nv => nv.abs_phi));
});

// Map of node_id to contribution (normalized 0-1)
const contributionMap = computed<Map<string, number>>(() => {
  const map = new Map<string, number>();
  if (!props.nodeShapleyValues) return map;

  for (const nv of props.nodeShapleyValues) {
    const normalized = nv.abs_phi / maxContribution.value;
    map.set(nv.node_id, normalized);
  }
  return map;
});

// Map of node_id to NodeShapleyValue for detailed access
const nodeShapleyMap = computed<Map<string, NodeShapleyValue>>(() => {
  const map = new Map<string, NodeShapleyValue>();
  if (!props.nodeShapleyValues) return map;

  for (const nv of props.nodeShapleyValues) {
    map.set(nv.node_id, nv);
  }
  return map;
});

// Top N contributing node IDs (V ∪ A, only non-zero contribution)
const topContributorNodeIds = computed<Set<string>>(() => {
  if (!props.nodeShapleyValues) return new Set();
  return new Set(
    props.nodeShapleyValues
      .filter(nv => nv.abs_phi > 0.0001)  // Exclude near-zero contributions
      .slice(0, props.topN)
      .map(nv => nv.node_id)
  );
});

// Edge Shapley value computations
const maxEdgeContribution = computed(() => {
  if (!props.edgeShapleyValues || props.edgeShapleyValues.length === 0) return 1;
  return Math.max(...props.edgeShapleyValues.map(ev => ev.abs_phi));
});

// Map of edge_id to normalized contribution (0-1)
const edgeContributionMap = computed<Map<string, number>>(() => {
  const map = new Map<string, number>();
  if (!props.edgeShapleyValues) return map;

  for (const ev of props.edgeShapleyValues) {
    const normalized = ev.abs_phi / maxEdgeContribution.value;
    map.set(ev.edge_id, normalized);
  }
  return map;
});

// Map of edge_id to EdgeShapleyValue for detailed access
const edgeShapleyMap = computed<Map<string, EdgeShapleyValue>>(() => {
  const map = new Map<string, EdgeShapleyValue>();
  if (!props.edgeShapleyValues) return map;

  for (const ev of props.edgeShapleyValues) {
    map.set(ev.edge_id, ev);
  }
  return map;
});

// Top N contributing edge IDs (only edges with non-zero contribution)
const topContributorEdgeIds = computed<Set<string>>(() => {
  if (!props.edgeShapleyValues) return new Set();
  return new Set(
    props.edgeShapleyValues
      .filter(ev => ev.abs_phi > 0.0001)  // Exclude near-zero contributions
      .slice(0, props.topN)
      .map(ev => ev.edge_id)
  );
});

// Find P1 and P2 nodes
// Note: perfIId/perfJId have 'perf-' prefix, node.id has prefix but node.performance_id doesn't
const perfINode = computed(() => {
  if (!props.perfIId) return null;
  // Compare with node.id (has prefix) or check if performance_id matches without prefix
  return props.network.nodes.find(n =>
    n.layer === 1 && (n.id === props.perfIId || `perf-${n.performance_id}` === props.perfIId)
  );
});

const perfJNode = computed(() => {
  if (!props.perfJId) return null;
  return props.network.nodes.find(n =>
    n.layer === 1 && (n.id === props.perfJId || `perf-${n.performance_id}` === props.perfJId)
  );
});

// Nodes connected to P1 or P2 (for edge path calculation)
const nodesConnectedToSelectedPerfs = computed<Set<string>>(() => {
  const set = new Set<string>();
  if (!perfINode.value && !perfJNode.value) return set;

  // BFS to find all connected nodes within 2 hops from P1 and P2
  const queue: string[] = [];
  if (perfINode.value) queue.push(perfINode.value.id);
  if (perfJNode.value) queue.push(perfJNode.value.id);

  const visited = new Set<string>();
  const distances = new Map<string, number>();

  for (const id of queue) {
    visited.add(id);
    distances.set(id, 0);
  }

  while (queue.length > 0) {
    const current = queue.shift()!;
    const currentDist = distances.get(current) || 0;

    // Limit to 2 hops for performance
    if (currentDist >= 2) continue;

    for (const edge of props.network.edges) {
      let neighbor: string | null = null;
      if (edge.source_id === current) neighbor = edge.target_id;
      else if (edge.target_id === current) neighbor = edge.source_id;

      if (neighbor && !visited.has(neighbor)) {
        visited.add(neighbor);
        distances.set(neighbor, currentDist + 1);
        queue.push(neighbor);
        set.add(neighbor);
      }
    }
  }

  return set;
});

// Helper functions
function getNodeById(id: string): NetworkNode | undefined {
  return props.network.nodes.find(n => n.id === id);
}

function isSelectedPerformance(node: NetworkNode): boolean {
  if (node.layer !== 1) return false;
  // Check both node.id and perf-{performance_id} formats
  const nodeIdWithPrefix = `perf-${node.performance_id}`;
  return node.id === props.perfIId || nodeIdWithPrefix === props.perfIId ||
         node.id === props.perfJId || nodeIdWithPrefix === props.perfJId;
}

function isHighContributionNode(node: NetworkNode): boolean {
  // V ∪ A: both Attribute (layer 2) and Variable (layer 3) can be high contributors
  if (node.layer !== 2 && node.layer !== 3) return false;
  return topContributorNodeIds.value.has(node.id);
}

function getNodeContribution(node: NetworkNode): number {
  // V ∪ A: both Attribute (layer 2) and Variable (layer 3) have contributions
  if (node.layer !== 2 && node.layer !== 3) return 0;
  return contributionMap.value.get(node.id) || 0;
}

function getNodeFill(node: NetworkNode): string {
  const hasSelection = props.perfIId || props.perfJId;

  // Performance nodes
  if (node.layer === 1) {
    if (isSelectedPerformance(node)) {
      return '#ffe3e3';  // Light red for selected
    }
    return layers[0].color;
  }

  // V ∪ A: Attribute (layer 2) and Variable (layer 3) - color by sign and contribution
  if ((node.layer === 2 || node.layer === 3) && hasSelection) {
    const nodeInfo = nodeShapleyMap.value.get(node.id);
    const contribution = getNodeContribution(node);

    if (nodeInfo && contribution > 0) {
      const intensity = Math.min(1, contribution);
      const isNegative = nodeInfo.sign === 'negative';

      if (isNegative) {
        // Negative φ (tradeoff contributor): red tones
        // Light red (#ffcdd2) to deep red (#c62828)
        const r = Math.round(255 - (255 - 198) * intensity);
        const g = Math.round(205 - (205 - 40) * intensity);
        const b = Math.round(210 - (210 - 40) * intensity);
        return `rgb(${r}, ${g}, ${b})`;
      } else {
        // Positive φ (synergy contributor): green tones
        // Light green (#c8e6c9) to deep green (#2e7d32)
        const r = Math.round(200 - (200 - 46) * intensity);
        const g = Math.round(230 - (230 - 125) * intensity);
        const b = Math.round(201 - (201 - 50) * intensity);
        return `rgb(${r}, ${g}, ${b})`;
      }
    }
    // No contribution data: use layer base color
    return node.layer === 2 ? layers[1].color : layers[2].color;
  }

  // Other nodes (Entity)
  const layer = layers.find(l => l.id === node.layer);
  return layer?.color || '#999';
}

function getNodeStroke(node: NetworkNode): string {
  if (isSelectedPerformance(node)) return '#d32f2f';

  const nodeInfo = nodeShapleyMap.value.get(node.id);
  if (isHighContributionNode(node) && nodeInfo) {
    // Stroke color based on sign
    return nodeInfo.sign === 'negative' ? '#b71c1c' : '#1b5e20';
  }
  return '#333';
}

function getNodeOpacity(node: NetworkNode): number {
  const hasSelection = props.perfIId || props.perfJId;
  if (!hasSelection) return 0.4;  // Dimmed when no selection

  if (isSelectedPerformance(node)) return 1;
  if (isHighContributionNode(node)) return 1;
  // V ∪ A: both Attribute (layer 2) and Variable (layer 3) can have contributions
  if ((node.layer === 2 || node.layer === 3) && getNodeContribution(node) > 0.1) return 0.9;

  return 0.4;
}

function getNodeLabelColor(node: NetworkNode): string {
  if (isSelectedPerformance(node)) return '#d32f2f';
  if (isHighContributionNode(node)) return '#e65100';
  return '#333';
}

// Get edge contribution from Shapley values
function getEdgeContribution(edge: any): number {
  const edgeId = edge.id;
  if (!edgeId) return 0;
  return edgeContributionMap.value.get(edgeId) || 0;
}

// Check if edge is a top contributor
function isHighContributionEdge(edge: any): boolean {
  const edgeId = edge.id;
  if (!edgeId) return false;
  return topContributorEdgeIds.value.has(edgeId);
}

// Edge highlighting logic (Shapley-based when available, hybrid fallback)
function getEdgeHighlightLevel(edge: any): 'strong' | 'medium' | 'weak' | 'none' {
  const source = getNodeById(edge.source_id);
  const target = getNodeById(edge.target_id);
  if (!source || !target) return 'none';

  const hasSelection = props.perfIId || props.perfJId;
  if (!hasSelection) return 'none';

  // If edge Shapley values are available, use them
  if (props.edgeShapleyValues && props.edgeShapleyValues.length > 0) {
    const contribution = getEdgeContribution(edge);

    // Top N edges get strong highlight
    if (isHighContributionEdge(edge)) {
      return 'strong';
    }

    // High contribution edges (> 50% of max) get medium highlight
    if (contribution > 0.5) {
      return 'medium';
    }

    // Moderate contribution edges (> 20% of max) get weak highlight
    if (contribution > 0.2) {
      return 'weak';
    }

    return 'none';
  }

  // Fallback to hybrid approach when edge Shapley values are not available
  // Level 1: Direct edges to P1 or P2
  const sourceIsSelected = isSelectedPerformance(source);
  const targetIsSelected = isSelectedPerformance(target);
  if (sourceIsSelected || targetIsSelected) {
    return 'strong';
  }

  // Level 2: Edges connected to top contributors on path to P1/P2
  const sourceIsTopContrib = topContributorNodeIds.value.has(source.id);
  const targetIsTopContrib = topContributorNodeIds.value.has(target.id);

  if (sourceIsTopContrib || targetIsTopContrib) {
    // Check if either end is connected to P1/P2 path
    const sourceOnPath = nodesConnectedToSelectedPerfs.value.has(source.id);
    const targetOnPath = nodesConnectedToSelectedPerfs.value.has(target.id);
    if (sourceOnPath || targetOnPath) {
      return 'medium';
    }
  }

  return 'none';
}

function getEdgeColor(edge: any): string {
  const level = getEdgeHighlightLevel(edge);

  // If edge Shapley is available, use contribution-based coloring
  if (props.edgeShapleyValues && props.edgeShapleyValues.length > 0) {
    const edgeInfo = edgeShapleyMap.value.get(edge.id);

    // If this edge has Shapley data, use sign-based coloring
    if (edgeInfo) {
      const isNegative = edgeInfo.sign === 'negative';

      if (level === 'strong') {
        return isNegative ? '#c62828' : '#2e7d32';  // Deep red / Deep green
      }
      if (level === 'medium') {
        return isNegative ? '#e57373' : '#81c784';  // Medium red / Medium green
      }
      if (level === 'weak') {
        return isNegative ? '#ffcdd2' : '#c8e6c9';  // Light red / Light green
      }
      // Has Shapley data but low contribution - use neutral color
      return 'silver';
    }
  }

  // Default highlight colors for fallback (when no Shapley data)
  if (level === 'strong') return '#ff9800';
  if (level === 'medium') return '#ffb74d';
  if (level === 'weak') return '#ffe0b2';

  // Default color based on weight
  if (isUndirectedEdge(edge)) return '#333';
  const weight = edge.weight ?? 0;
  return edgeWeightColors[weight as keyof typeof edgeWeightColors] || 'silver';
}

function getEdgeStrokeWidth(edge: any): number {
  const level = getEdgeHighlightLevel(edge);
  if (level === 'strong') return 3.5;
  if (level === 'medium') return 2.5;
  if (level === 'weak') return 2;
  return 1.5;
}

function getEdgeOpacity(edge: any): number {
  const hasSelection = props.perfIId || props.perfJId;
  if (!hasSelection) return 0.4;

  const level = getEdgeHighlightLevel(edge);
  if (level === 'strong') return 1;
  if (level === 'medium') return 0.9;
  if (level === 'weak') return 0.7;
  return 0.2;
}

function getEdgeMarker(edge: any): string | undefined {
  if (isUndirectedEdge(edge)) return undefined;

  const level = getEdgeHighlightLevel(edge);

  // Use sign-based markers when Shapley data is available
  if (props.edgeShapleyValues && props.edgeShapleyValues.length > 0) {
    const edgeInfo = edgeShapleyMap.value.get(edge.id);

    if (edgeInfo) {
      const prefix = edgeInfo.sign === 'negative' ? 'neg' : 'pos';
      if (level === 'strong') return `url(#arrow-${prefix}-strong)`;
      if (level === 'medium') return `url(#arrow-${prefix}-medium)`;
      if (level === 'weak') return `url(#arrow-${prefix}-weak)`;
      // Has Shapley data but low contribution - use default weight-based marker
      const weight = edge.weight ?? 0;
      return `url(#arrow-tradeoff-${weight})`;
    }
  }

  // Fallback markers (orange)
  if (level === 'strong') return 'url(#arrow-fallback-strong)';
  if (level === 'medium') return 'url(#arrow-fallback-medium)';
  if (level === 'weak') return 'url(#arrow-fallback-medium)';

  // Use color-based marker for all edges (supports continuous values)
  const color = getDefaultEdgeColor(edge);
  return `url(#arrow-tradeoff-${encodeColor(color)})`;
}

function isUndirectedEdge(edge: any): boolean {
  const source = getNodeById(edge.source_id);
  const target = getNodeById(edge.target_id);
  if (!source || !target) return false;

  // V ↔ E and E ↔ E are undirected
  if ((source.layer === 3 && target.layer === 4) || (source.layer === 4 && target.layer === 3)) {
    return true;
  }
  if (source.layer === 4 && target.layer === 4) {
    return true;
  }
  return false;
}

// Node shape helpers
function getTrianglePoints(cx: number, cy: number, enlarged: boolean = false): string {
  const height = enlarged ? 40 : 36;
  const halfBase = height / Math.sqrt(3);
  return `${cx},${cy - height/2} ${cx - halfBase},${cy + height/2} ${cx + halfBase},${cy + height/2}`;
}

function getDiamondPoints(cx: number, cy: number): string {
  const halfHeight = 18;
  const halfWidth = 27;
  return `${cx},${cy - halfHeight} ${cx + halfWidth},${cy} ${cx},${cy + halfHeight} ${cx - halfWidth},${cy}`;
}

function getAdjustedLineEnd(edge: any): { x: number; y: number } {
  const source = getNodeById(edge.source_id);
  const target = getNodeById(edge.target_id);
  if (!source || !target) {
    return { x: target?.x || 0, y: target?.y || 0 };
  }

  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  let targetRadius = 18;
  if (target.layer === 2) targetRadius = 20;
  else if (target.layer === 3) targetRadius = 24;
  else if (target.layer === 4 && target.type === 'object') targetRadius = 36;
  else if (target.layer === 4 && target.type === 'environment') targetRadius = 18;

  const arrowAdjustment = isUndirectedEdge(edge) ? 0 : 10;
  const adjustment = targetRadius + arrowAdjustment;
  const ratio = (distance - adjustment) / distance;

  return {
    x: source.x + dx * ratio,
    y: source.y + dy * ratio
  };
}

function resetView() {
  if (props.network.nodes.length === 0) {
    zoom.value = 1;
    minZoom.value = 0.3;
    return;
  }

  if (!svgCanvas.value) return;

  const container = viewerContainer.value?.querySelector('.canvas-container') as HTMLElement;
  if (!container) return;

  const rect = container.getBoundingClientRect();
  const viewWidth = rect.width;
  const viewHeight = rect.height;

  if (viewWidth === 0 || viewHeight === 0) return;

  const zoomX = viewWidth / canvasWidth.value;
  const zoomY = viewHeight / canvasHeight.value;
  const calculatedZoom = Math.min(zoomX, zoomY);

  if (calculatedZoom <= 0 || !isFinite(calculatedZoom)) {
    zoom.value = 1;
    minZoom.value = 0.3;
    return;
  }

  zoom.value = calculatedZoom;
  minZoom.value = Math.max(0.1, Math.floor(zoom.value * 10) / 10);

  if (container) {
    container.scrollTop = 0;
    container.scrollLeft = 0;
  }
}

// Download network as PNG image
async function downloadAsImage() {
  if (!svgCanvas.value) return;

  try {
    // Clone SVG
    const svgClone = svgCanvas.value.cloneNode(true) as SVGSVGElement;

    // Reset transform to show full view
    const mainGroup = svgClone.querySelector('g[transform]');
    if (mainGroup) {
      mainGroup.setAttribute('transform', 'scale(1)');
    }

    // Set viewBox and dimensions
    svgClone.setAttribute('viewBox', `0 0 ${canvasWidth.value} ${canvasHeight.value}`);
    svgClone.setAttribute('width', String(canvasWidth.value));
    svgClone.setAttribute('height', String(canvasHeight.value));

    // Serialize SVG to string
    const svgData = new XMLSerializer().serializeToString(svgClone);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);

    // Load into image
    const img = new Image();
    img.onload = () => {
      // Create canvas
      const canvas = document.createElement('canvas');
      canvas.width = canvasWidth.value;
      canvas.height = canvasHeight.value;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Fill background
      ctx.fillStyle = '#fafafa';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw SVG
      ctx.drawImage(img, 0, 0);

      // Download
      const link = document.createElement('a');
      const perfIName = props.perfIId ? props.performances.find(p => p.id === props.perfIId || `perf-${p.id}` === props.perfIId)?.name || 'P1' : 'all';
      const perfJName = props.perfJId ? props.performances.find(p => p.id === props.perfJId || `perf-${p.id}` === props.perfJId)?.name || 'P2' : 'all';
      link.download = `tradeoff-network-${perfIName}-${perfJName}-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();

      // Cleanup
      URL.revokeObjectURL(svgUrl);
    };

    img.onerror = () => {
      console.error('Failed to load SVG as image');
      alert('Failed to download network image');
      URL.revokeObjectURL(svgUrl);
    };

    img.src = svgUrl;
  } catch (error) {
    console.error('Failed to download network image:', error);
    alert('Failed to download network image');
  }
}

onMounted(() => {
  nextTick(() => {
    if (props.network.nodes.length > 0) {
      resetView();
    }
  });
});
</script>

<style scoped lang="scss">
@use '../../style/color' as *;
@use 'sass:color';

.tradeoff-network-viewer {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: $gray;
  border-radius: 8px;
  overflow: hidden;
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(145deg, lighten($gray, 10%), lighten($gray, 6%));
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
  gap: 0.75rem;
  flex-shrink: 0;
}

.tool-group {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.zoom-label {
  font-size: 0.75rem;
  color: color.adjust($white, $alpha: -0.3);
  font-weight: 500;
}

.zoom-slider {
  width: 80px;
  height: 4px;
  cursor: pointer;
  background: color.adjust($gray, $lightness: -10%);
  border-radius: 2px;
  outline: none;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 14px;
    height: 14px;
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  &::-moz-range-thumb {
    width: 14px;
    height: 14px;
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border: none;
    border-radius: 50%;
    cursor: pointer;
  }
}

.zoom-value {
  font-size: 0.7rem;
  color: color.adjust($white, $alpha: -0.4);
  min-width: 2.5rem;
  text-align: right;
  font-family: monospace;
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.5rem;
  background: color.adjust($gray, $lightness: 18%);
  border: 1px solid color.adjust($white, $alpha: -0.85);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  color: $white;
  transition: all 0.2s;

  &:hover {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  }
}

.network-viewer {
  position: relative;
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

.canvas-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #fafafa;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;

  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  &::-webkit-scrollbar-track {
    background: #f0f0f0;
  }
  &::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
  }
}

.network-canvas {
  display: block;
  user-select: none;
}

.node-label {
  font-size: 11px;
  pointer-events: none;
  user-select: none;
}

.layer-legend {
  display: flex;
  gap: 1rem;
  padding: 0.4rem 0.75rem;
  background: linear-gradient(145deg, lighten($gray, 10%), lighten($gray, 6%));
  border-top: 1px solid color.adjust($white, $alpha: -0.9);
  justify-content: center;
  flex-shrink: 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.7rem;
}

.legend-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.legend-label {
  color: color.adjust($white, $alpha: -0.3);
}
</style>
