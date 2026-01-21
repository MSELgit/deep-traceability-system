<template>
  <div class="network-viewer-wrapper">
      <!-- Toolbar -->
      <div class="viewer-toolbar">
        <div class="tool-group">
          <label v-if="!hideToolbar" class="zoom-label">Zoom</label>
          <input  v-if="!hideToolbar"
            type="range" 
            v-model.number="zoom" 
            :min="minZoom" 
            max="3" 
            step="0.1"
            class="zoom-slider"
          />
          <span v-if="!hideToolbar" class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
          <button v-if="!hideToolbar" class="tool-btn" @click="resetView" title="Fit">
            <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'expand']" /></span>
            Fit
          </button>
          <button class="tool-btn" @click="downloadAsImage" title="Download">
            <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'camera']" /></span>
            Download
          </button>
        </div>
      </div>
    <div class="network-viewer" ref="viewerContainer">

      <div class="canvas-container">
        <svg
        ref="svgCanvas"
        class="network-canvas"
        :class="{ panning: isPanning }"
        :width="canvasWidth * zoom"
        :height="canvasHeight * zoom"
        @contextmenu.prevent
      >
      <!-- Grid background pattern definition -->
      <defs>
        <pattern
          id="grid-viewer"
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
        
        <!-- Arrow marker definition (for each unique edge color) -->
        <marker
          v-for="color in uniqueEdgeColors"
          :key="`arrow-${color}`"
          :id="`arrow-viewer-${encodeColor(color)}`"
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
      </defs>

      <!-- Main content group (zoom applied) - contains all elements -->
      <g :transform="`scale(${zoom})`">
        <!-- Grid background -->
        <rect 
          :x="0" 
          :y="0" 
          :width="canvasWidth" 
          :height="canvasHeight" 
          fill="url(#grid-viewer)" 
        />

        <!-- PAVE Layer backgrounds (4 divisions) -->
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

      <!-- Edges (no arrow marker for undirected V↔E edges) -->
      <g class="edges-layer">
        <line
          v-for="edge in network.edges"
          :key="edge.id"
          :x1="getNodeById(edge.source_id)?.x"
          :y1="getNodeById(edge.source_id)?.y"
          :x2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!, isUndirectedEdge(edge)).x : getNodeById(edge.target_id)?.x"
          :y2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!, isUndirectedEdge(edge)).y : getNodeById(edge.target_id)?.y"
          :stroke="getEdgeColor(edge)"
          stroke-width="1.5"
          stroke-linecap="round"
          :marker-end="isUndirectedEdge(edge) ? undefined : `url(#arrow-viewer-${encodeColor(getEdgeColor(edge))})`"
        />
      </g>

      <!-- Nodes -->
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
            :r="18"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
          />
          
          <!-- Layer 2: Attribute (equilateral triangle, height 36px) -->
          <polygon
            v-else-if="node.layer === 2"
            :points="getTrianglePoints(node.x, node.y)"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
          />
          
          <!-- Layer 3: Variable (horizontal diamond, height 36px, width 54px) -->
          <polygon
            v-else-if="node.layer === 3"
            :points="getDiamondPoints(node.x, node.y)"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
          />
          
          <!-- Layer 4: Object (1:2 rectangle, height 36px, width 72px) -->
          <rect
            v-else-if="node.layer === 4 && node.type === 'object'"
            :x="node.x - 36"
            :y="node.y - 18"
            :width="72"
            :height="36"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
            rx="4"
          />
          
          <!-- Layer 4: Environment (square, 36px × 36px) -->
          <rect
            v-else-if="node.layer === 4 && node.type === 'environment'"
            :x="node.x - 18"
            :y="node.y - 18"
            :width="36"
            :height="36"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
            rx="4"
          />
          
          <!-- Fallback: Layer 4 with unknown type (circle) -->
          <circle
            v-else-if="node.layer === 4"
            :cx="node.x"
            :cy="node.y"
            :r="18"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
          />
          
          <text
            :x="node.x"
            :y="node.y + 18 + 15"
            text-anchor="middle"
            class="node-label"
            fill="#333"
          >
            {{ node.label }}
          </text>
        </g>
      </g>
      </g> <!-- End main content group -->
    </svg>
    </div> <!-- End canvas-container -->
    </div> <!-- End network-viewer -->

    <!-- Layer guide (outside network display area) -->
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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import type { NetworkStructure, NetworkNode, Performance } from '../../types/project';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

defineExpose({
  resetView
});

const props = defineProps<{
  network: NetworkStructure;
  performances: Performance[];
  hideToolbar?: boolean;
}>();

const canvasWidth = ref(1200);
const canvasHeight = ref(800);
const nodeRadius = 18;

// Zoom/pan state
const zoom = ref(1);
const minZoom = ref(0.3);
const panX = ref(0);
const panY = ref(0);
const isPanning = ref(false);
const panStart = ref({ x: 0, y: 0 });

const svgCanvas = ref<SVGSVGElement>();
const viewerContainer = ref<HTMLDivElement>();

// Layer definition (PAVE model)
const layers = [
  { id: 1, label: 'Performance', color: '#4CAF50' },
  { id: 2, label: 'Attribute', color: '#2196F3' },
  { id: 3, label: 'Variable', color: '#FFC107' },
  { id: 4, label: 'Entity', color: '#9C27B0' }
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

// Get edge color - supports both discrete and continuous values
function getEdgeColor(edge: any): string {
  // Undirected edges (V↔E, E↔E) are always black - no weight concept
  if (isUndirectedEdge(edge)) {
    return '#333';
  }
  const weight = edge.weight ?? 0;

  // For discrete values, use the predefined colors
  if (weight in edgeWeightColors) {
    return edgeWeightColors[weight as keyof typeof edgeWeightColors];
  }

  // For continuous values, interpolate between colors
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

  // weight = 0: neutral gray
  return '#c0c0c0';
}

// Compute unique edge colors for marker definitions
const uniqueEdgeColors = computed(() => {
  if (!props.network?.edges) return ['#c0c0c0'];
  const colors = new Set<string>();
  for (const edge of props.network.edges) {
    colors.add(getEdgeColor(edge));
  }
  // Always include default colors
  colors.add('#c0c0c0');
  colors.add('#333');
  return Array.from(colors);
});

// Encode color string for use in SVG ID (remove special characters)
function encodeColor(color: string): string {
  return color.replace(/[^a-zA-Z0-9]/g, '_');
}

/**
 * Check if an edge should be rendered as undirected (no arrow marker)
 * According to PAVE model: V ↔ E and E ↔ E are undirected
 */
function isUndirectedEdge(edge: any): boolean {
  const source = getNodeById(edge.source_id);
  const target = getNodeById(edge.target_id);
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

// Node shape calculation functions
// Equilateral triangle coordinates (height 36px, pointing up)
function getTrianglePoints(cx: number, cy: number): string {
  const height = 36;
  const halfBase = height / Math.sqrt(3); // Half of base ≈ 20.8
  return `${cx},${cy - height/2} ${cx - halfBase},${cy + height/2} ${cx + halfBase},${cy + height/2}`;
}

// Horizontal diamond coordinates (height 36px, width 54px)
function getDiamondPoints(cx: number, cy: number): string {
  const halfHeight = 18;
  const halfWidth = 27;
  return `${cx},${cy - halfHeight} ${cx + halfWidth},${cy} ${cx},${cy + halfHeight} ${cx - halfWidth},${cy}`;
}

function getNodeColor(node: NetworkNode): string {
  const layer = layers.find(l => l.id === node.layer);
  return layer?.color || '#999';
}

function getNodeById(id: string): NetworkNode | undefined {
  return props.network.nodes.find(n => n.id === id);
}

// Adjust edge endpoint (prevent arrow overlapping with node)
function getAdjustedLineEnd(source: NetworkNode, target: NetworkNode, isUndirected: boolean = false): { x: number, y: number } {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  // Node radius (adjusted by shape)
  let targetRadius = 18; // Default (circle)

  if (target.layer === 2) { // Triangle
    targetRadius = 20;
  } else if (target.layer === 3) { // Diamond
    targetRadius = 24;
  } else if (target.layer === 4 && target.type === 'object') { // Rectangle
    targetRadius = 36;
  } else if (target.layer === 4 && target.type === 'environment') { // Square
    targetRadius = 18;
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

// Zoom/pan functionality
function resetView() {
  
  if (props.network.nodes.length === 0) {
    zoom.value = 1;
    minZoom.value = 0.3;
    panX.value = 0;
    panY.value = 0;
    return;
  }

  // Check if SVG canvas is ready
  if (!svgCanvas.value) {
    console.warn('  ⚠️ SVG canvas is not ready');
    return;
  }

  // Use entire canvas size (regardless of node placement)
  const contentWidth = canvasWidth.value; // 1200
  const contentHeight = canvasHeight.value; // 800
  
  // Get actual display area size (canvas-container size)
  const container = viewerContainer.value?.querySelector('.canvas-container') as HTMLElement;
  if (!container) {
    console.warn('  ⚠️ canvas-container not found');
    return;
  }
  const rect = container.getBoundingClientRect();
  const viewWidth = rect.width;
  const viewHeight = rect.height;
  
  // Also check parent element size
  const viewerRect = viewerContainer.value?.getBoundingClientRect();
  const wrapperElement = viewerContainer.value?.parentElement;
  const wrapperRect = wrapperElement?.getBoundingClientRect();
  
  // Skip processing if viewSize is 0
  if (viewWidth === 0 || viewHeight === 0) {
    return;
  }
  
  // Calculate considering scrollbar width (about 17px)
  const scrollbarSize = 0;
  const effectiveWidth = viewWidth - scrollbarSize;
  const effectiveHeight = viewHeight - scrollbarSize;
  
  // Calculate zoom ratio for content to fit in display area
  const zoomX = effectiveWidth / contentWidth;
  const zoomY = effectiveHeight / contentHeight;
  const calculatedZoom = Math.min(zoomX, zoomY); // Add some margin
  
  // Check for abnormal values
  if (calculatedZoom <= 0 || !isFinite(calculatedZoom)) {
    console.warn('  ⚠️ Abnormal zoom value:', calculatedZoom);
    zoom.value = 1;
    minZoom.value = 0.3;
    return;
  }
  
  zoom.value = calculatedZoom;
  
  // Set calculated zoom value as minimum
  minZoom.value = Math.max(0.1, Math.floor(zoom.value * 10) / 10);
  
  // Reset scroll
  if (container) {
    container.scrollTop = 0;
    container.scrollLeft = 0;
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
    // Clone SVG
    const svgClone = svgCanvas.value.cloneNode(true) as SVGSVGElement;
    
    // Reset transform of cloned SVG to show entire view
    const mainGroup = svgClone.querySelector('g[transform]');
    if (mainGroup) {
      mainGroup.setAttribute('transform', 'translate(0, 0) scale(1)');
    }
    
    // Set SVG viewBox to make everything visible
    svgClone.setAttribute('viewBox', `0 0 ${canvasWidth.value} ${canvasHeight.value}`);
    svgClone.setAttribute('width', String(canvasWidth.value));
    svgClone.setAttribute('height', String(canvasHeight.value));
    
    // Convert SVG to data URL
    const svgData = new XMLSerializer().serializeToString(svgClone);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    
    // Create Image object and load SVG
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
      link.download = `network-diagram-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      
      // Cleanup
      URL.revokeObjectURL(svgUrl);
    };
    
    img.onerror = () => {
      console.error('Failed to convert SVG');
      alert('Failed to Download');
      URL.revokeObjectURL(svgUrl);
    };
    
    img.src = svgUrl;
  } catch (error) {
    console.error('Failed to generate image:', error);
    alert('画像のダウンロードに失敗しました');
  }
}

// Hold resize handler
let resizeHandler: (() => void) | null = null;

onMounted(() => {
  nextTick(() => {
    //setContainerMaxHeight();
    if (props.network.nodes.length > 0) {
      resetView();
    }
  });
});

onUnmounted(() => {
  document.removeEventListener('mousemove', handlePanMove);
  document.removeEventListener('mouseup', handlePanEnd);
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
  }
});
</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

// Custom scrollbar style
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

.network-viewer-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: $gray;
}

.network-viewer {
  display: flex;
  flex-direction: column;
  flex: 1;
  position: relative;
  background: #fafafa;
  overflow: visible;
  min-height: 0;
  aspect-ratio: 3 / 2;
}

.canvas-container {
  flex: 1;
  overflow: auto;
  background: white;
  min-height: 0;
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(0.75rem, 1.5vw, 1rem);
  background: linear-gradient(145deg, color.adjust($gray, $lightness: 10%), color.adjust($gray, $lightness: 6%));
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  gap: clamp(0.75rem, 1.5vw, 1rem);
  flex-shrink: 0;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.7);
}

.tool-group {
  display: flex;
  gap: clamp(0.4rem, 0.8vw, 0.6rem);
  align-items: center;
}

.zoom-label {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.3);
  font-weight: 500;
}

.zoom-slider {
  width: clamp(6rem, 10vw, 8rem);
  height: clamp(0.4rem, 0.6vh, 0.5rem);
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
    width: clamp(1rem, 1.5vw, 1.2rem);
    height: clamp(1rem, 1.5vw, 1.2rem);
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.5), 
                0 0 0 0.1vw color.adjust($white, $alpha: -0.8);
    transition: all 0.2s ease;
    
    &:hover {
      transform: scale(1.1);
      background: linear-gradient(135deg, color.adjust($main_1, $lightness: 15%) 0%, color.adjust($main_2, $lightness: 15%) 100%);
      box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.4),
                  0 0 0 0.15vw color.adjust($white, $alpha: -0.6),
                  0 0 1vh color.adjust($main_1, $alpha: -0.3);
    }
    
    &:active {
      transform: scale(0.95);
      box-shadow: 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.3);
    }
  }
  
  &::-moz-range-thumb {
    width: clamp(1rem, 1.5vw, 1.2rem);
    height: clamp(1rem, 1.5vw, 1.2rem);
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border: 0.1vw solid color.adjust($white, $alpha: -0.8);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.5);
    transition: all 0.2s ease;
    
    &:hover {
      background: linear-gradient(135deg, color.adjust($main_1, $lightness: 15%) 0%, color.adjust($main_2, $lightness: 15%) 100%);
      border-color: color.adjust($white, $alpha: -0.6);
    }
  }
}

.zoom-value {
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.4);
  min-width: clamp(2.5rem, 4vw, 3rem);
  text-align: right;
  font-weight: 500;
  font-family: monospace;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: clamp(0.3rem, 0.5vw, 0.4rem);
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1vw, 0.8rem);
  background: color.adjust($gray, $lightness: 20%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  font-weight: 500;
  color: $white;
  transition: all 0.3s ease;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.8);
}

.tool-btn:hover {
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  border-color: color.adjust($main_1, $alpha: -0.3);
  color: $white;
  transform: translateY(-0.1vh);
  box-shadow: 0 0.4vh 1vh color.adjust($main_1, $alpha: -0.5);
}

.tool-btn:active {
  transform: translateY(0);
  box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.6);
}

.tool-icon {
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
}

.spacer {
  flex: 1;
}

.info-group {
  display: flex;
  gap: 12px;
}

.info-text {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
}

.network-canvas {
  display: block;
  cursor: default;
  user-select: none;
}

.network-canvas.panning {
  cursor: move;
}

.node-label {
  font-size: 11px;
  font-weight: 500;
  pointer-events: none;
  user-select: none;
}

.node-layer-number {
  pointer-events: none;
  user-select: none;
}

.layer-legend {
  display: flex;
  gap: 1.6vw;
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.8rem, 1.5vw, 1rem);
  background: linear-gradient(145deg, color.adjust($gray, $lightness: 10%), color.adjust($gray, $lightness: 6%));
  border-top: 1px solid color.adjust($white, $alpha: -0.95);
  justify-content: center;
  flex-shrink: 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.6vw;
  font-size: clamp(0.7rem, 0.9vw, 0.8rem);
}

.legend-icon {
  width: clamp(0.8rem, 1.4vw, 1rem);
  height: clamp(0.8rem, 1.4vw, 1rem);
  flex-shrink: 0;
}

.legend-label {
  color: color.adjust($white, $alpha: -0.3);
}
</style>