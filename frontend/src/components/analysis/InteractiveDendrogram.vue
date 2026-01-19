<template>
  <div class="interactive-dendrogram">
    <div class="dendrogram-header">
      <div class="threshold-info">
        <span class="info-item">h={{ currentHeight.toFixed(2) }}</span>
        <span class="info-item">k={{ currentClusters }}</span>
        <span class="info-item" :class="silhouetteClass">
          Sil={{ currentSilhouette !== null ? currentSilhouette.toFixed(2) : '-' }}
        </span>
      </div>
      <div class="header-buttons">
        <button class="icon-btn" @click="downloadImage" title="Download PNG">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </button>
        <button class="optimize-btn" @click="optimizeThreshold" title="Silhouette最大化">
          Optimize
        </button>
      </div>
    </div>
    <div ref="dendrogramContainer" class="dendrogram-svg-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import * as d3 from 'd3';

interface DendrogramNode {
  id: number;
  label: string;
  is_leaf: boolean;
  height: number;
  children: number[];
}

interface SilhouettePoint {
  height: number;
  n_clusters: number;
  silhouette: number | null;
}

interface DendrogramData {
  nodes: DendrogramNode[];
  n_leaves: number;
  labels: string[];
  max_height: number;
  silhouette_curve: SilhouettePoint[];
  optimal_height: number | null;
}

const props = defineProps<{
  data: DendrogramData;
  width?: number;
  height?: number;
}>();

const emit = defineEmits<{
  (e: 'threshold-change', height: number, clusters: number[]): void;
}>();

const dendrogramContainer = ref<HTMLElement | null>(null);
const currentHeight = ref(0.5);
const currentClusters = ref(1);
const currentSilhouette = ref<number | null>(null);

const silhouetteClass = computed(() => {
  if (currentSilhouette.value === null) return '';
  if (currentSilhouette.value > 0.7) return 'excellent';
  if (currentSilhouette.value > 0.5) return 'good';
  if (currentSilhouette.value > 0.25) return 'fair';
  return 'poor';
});

function optimizeThreshold() {
  if (props.data.optimal_height !== null) {
    currentHeight.value = props.data.optimal_height;
    updateFromHeight(currentHeight.value);
    renderDendrogram();
  }
}

function downloadImage() {
  if (!dendrogramContainer.value) return;

  const svgElement = dendrogramContainer.value.querySelector('svg');
  if (!svgElement) return;

  // SVGをクローンして修正
  const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;

  // viewBoxから実際のサイズを取得
  const viewBox = svgElement.getAttribute('viewBox');
  let svgWidth = 800;
  let svgHeight = 400;
  if (viewBox) {
    const parts = viewBox.split(' ').map(Number);
    svgWidth = parts[2] || 800;
    svgHeight = parts[3] || 400;
  }

  // 固定サイズを設定
  clonedSvg.setAttribute('width', String(svgWidth));
  clonedSvg.setAttribute('height', String(svgHeight));
  clonedSvg.removeAttribute('viewBox');
  clonedSvg.style.width = `${svgWidth}px`;
  clonedSvg.style.height = `${svgHeight}px`;

  // 白背景の矩形を最初に追加
  const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bgRect.setAttribute('x', '0');
  bgRect.setAttribute('y', '0');
  bgRect.setAttribute('width', '100%');
  bgRect.setAttribute('height', '100%');
  bgRect.setAttribute('fill', '#ffffff');
  clonedSvg.insertBefore(bgRect, clonedSvg.firstChild);

  // 色の調整（クラスタ色は維持、グレー系のみ調整）
  clonedSvg.querySelectorAll('line').forEach(line => {
    const currentStroke = line.getAttribute('stroke');
    // グレー (#666) の線は濃いグレーに変更
    if (currentStroke === '#666' || currentStroke === '#666666') {
      line.setAttribute('stroke', '#999999');
    }
    // 閾値線とクラスタ色はそのまま維持
  });

  // Y軸のテキストと線
  clonedSvg.querySelectorAll('.y-axis text').forEach(text => {
    text.setAttribute('fill', '#333333');
  });
  clonedSvg.querySelectorAll('.y-axis line, .y-axis path').forEach(el => {
    el.setAttribute('stroke', '#cccccc');
  });

  // ラベルテキストはクラスタ色を維持（d3.schemeCategory10は白背景でも視認可能）

  // SVGをシリアライズ
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(clonedSvg);

  // Canvasに描画してPNGに変換
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const img = new Image();
  const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svgBlob);

  img.onload = () => {
    // 高解像度で出力（2倍）
    const scale = 2;
    canvas.width = svgWidth * scale;
    canvas.height = svgHeight * scale;
    ctx.scale(scale, scale);
    ctx.drawImage(img, 0, 0, svgWidth, svgHeight);

    // ダウンロード
    const link = document.createElement('a');
    link.download = `dendrogram_k${currentClusters.value}_sil${currentSilhouette.value?.toFixed(2) || '0'}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();

    URL.revokeObjectURL(url);
  };

  img.src = url;
}

function findSilhouetteForHeight(height: number): { n_clusters: number; silhouette: number | null } {
  const curve = props.data.silhouette_curve;
  if (!curve || curve.length === 0) {
    return { n_clusters: 1, silhouette: null };
  }

  // Find the appropriate point in the curve
  for (let i = curve.length - 1; i >= 0; i--) {
    if (height >= curve[i].height) {
      return { n_clusters: curve[i].n_clusters, silhouette: curve[i].silhouette };
    }
  }
  return { n_clusters: curve[0].n_clusters, silhouette: curve[0].silhouette };
}

function updateFromHeight(height: number) {
  const result = findSilhouetteForHeight(height);
  currentClusters.value = result.n_clusters;
  currentSilhouette.value = result.silhouette;

  // Compute cluster assignments
  const clusters = computeClustersAtHeight(height);
  emit('threshold-change', height, clusters);
}

function computeClustersAtHeight(threshold: number): number[] {
  const nodes = props.data.nodes;
  const n = props.data.n_leaves;
  const clusters = new Array(n).fill(-1);
  let clusterIdx = 0;

  // Find which internal nodes are "cut" (below threshold)
  const activeRoots: number[] = [];

  function findActiveRoots(nodeId: number): void {
    const node = nodes[nodeId];
    if (node.is_leaf) {
      activeRoots.push(nodeId);
      return;
    }
    if (node.height >= threshold) {
      // This merge is above threshold, so children are separate
      for (const childId of node.children) {
        findActiveRoots(childId);
      }
    } else {
      // This merge is below threshold, keep as single cluster
      activeRoots.push(nodeId);
    }
  }

  // Start from root (last node)
  const rootId = nodes.length - 1;
  findActiveRoots(rootId);

  // Assign cluster indices
  function assignCluster(nodeId: number, cluster: number): void {
    const node = nodes[nodeId];
    if (node.is_leaf) {
      clusters[nodeId] = cluster;
    } else {
      for (const childId of node.children) {
        assignCluster(childId, cluster);
      }
    }
  }

  for (const rootId of activeRoots) {
    assignCluster(rootId, clusterIdx++);
  }

  return clusters;
}

function renderDendrogram() {
  if (!dendrogramContainer.value || !props.data) return;

  const container = dendrogramContainer.value;
  container.innerHTML = '';

  // コンテナの実際のサイズを取得
  const containerRect = container.getBoundingClientRect();
  const containerWidth = containerRect.width || 400;
  const containerHeight = containerRect.height || 300;

  // ラベル用に下部マージンを大きめに
  const margin = { top: 15, right: 30, bottom: 80, left: 45 };
  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - margin.top - margin.bottom;

  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${containerWidth} ${containerHeight}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // Build tree structure from nodes
  const nodes = props.data.nodes;
  const n = props.data.n_leaves;
  const maxHeight = props.data.max_height;

  // Scale for height (y-axis, inverted so 0 is at bottom)
  const yScale = d3.scaleLinear()
    .domain([0, maxHeight * 1.1])
    .range([height, 0]);

  // Compute x positions for leaves
  const leafPositions: Map<number, number> = new Map();
  const leafWidth = width / n;

  // Get leaf order from dendrogram structure
  function getLeafOrder(nodeId: number): number[] {
    const node = nodes[nodeId];
    if (node.is_leaf) {
      return [nodeId];
    }
    const result: number[] = [];
    for (const childId of node.children) {
      result.push(...getLeafOrder(childId));
    }
    return result;
  }

  const rootId = nodes.length - 1;
  const leafOrder = getLeafOrder(rootId);
  leafOrder.forEach((leafId, idx) => {
    leafPositions.set(leafId, (idx + 0.5) * leafWidth);
  });

  // Compute x position for each node
  const nodePositions: Map<number, number> = new Map();

  function computeNodePosition(nodeId: number): number {
    if (leafPositions.has(nodeId)) {
      const pos = leafPositions.get(nodeId)!;
      nodePositions.set(nodeId, pos);
      return pos;
    }
    const node = nodes[nodeId];
    const childPositions = node.children.map(cid => computeNodePosition(cid));
    const pos = d3.mean(childPositions)!;
    nodePositions.set(nodeId, pos);
    return pos;
  }

  computeNodePosition(rootId);

  // Get current clusters for coloring
  const clusterAssignments = computeClustersAtHeight(currentHeight.value);
  const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

  // Function to get cluster color for a node
  function getNodeCluster(nodeId: number): number {
    const node = nodes[nodeId];
    if (node.is_leaf) {
      return clusterAssignments[nodeId];
    }
    // For internal nodes, use the cluster of first leaf descendant
    function getFirstLeaf(nid: number): number {
      const n = nodes[nid];
      if (n.is_leaf) return nid;
      return getFirstLeaf(n.children[0]);
    }
    return clusterAssignments[getFirstLeaf(nodeId)];
  }

  // Draw links
  for (const node of nodes) {
    if (!node.is_leaf && node.children.length >= 2) {
      const x = nodePositions.get(node.id)!;
      const y = yScale(node.height);

      for (const childId of node.children) {
        const childX = nodePositions.get(childId)!;
        const childNode = nodes[childId];
        const childY = yScale(childNode.height);
        const cluster = getNodeCluster(childId);
        const color = node.height < currentHeight.value ? colorScale(String(cluster)) : '#666';

        // Vertical line from child
        g.append('line')
          .attr('x1', childX)
          .attr('y1', childY)
          .attr('x2', childX)
          .attr('y2', y)
          .attr('stroke', color)
          .attr('stroke-width', 2);

        // Horizontal line to parent
        g.append('line')
          .attr('x1', childX)
          .attr('y1', y)
          .attr('x2', x)
          .attr('y2', y)
          .attr('stroke', color)
          .attr('stroke-width', 2);
      }
    }
  }

  // Draw leaf labels
  for (let i = 0; i < n; i++) {
    const node = nodes[i];
    const x = leafPositions.get(i)!;
    const cluster = clusterAssignments[i];

    g.append('text')
      .attr('x', x)
      .attr('y', height + 15)
      .attr('text-anchor', 'start')
      .attr('transform', `rotate(45, ${x}, ${height + 15})`)
      .attr('font-size', '10px')
      .attr('fill', colorScale(String(cluster)))
      .text(node.label.replace(/^P\d+_/, ''));
  }

  // Draw threshold line (draggable)
  const thresholdY = yScale(currentHeight.value);

  const thresholdLine = g.append('line')
    .attr('class', 'threshold-line')
    .attr('x1', -10)
    .attr('y1', thresholdY)
    .attr('x2', width + 10)
    .attr('y2', thresholdY)
    .attr('stroke', '#ff6b6b')
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '5,5')
    .style('cursor', 'ns-resize');

  const thresholdHandle = g.append('rect')
    .attr('x', -15)
    .attr('y', thresholdY - 8)
    .attr('width', width + 30)
    .attr('height', 16)
    .attr('fill', 'transparent')
    .style('cursor', 'ns-resize');

  // Drag behavior
  const drag = d3.drag<SVGRectElement, unknown>()
    .on('drag', (event) => {
      const newY = Math.max(0, Math.min(height, event.y));
      const newHeight = yScale.invert(newY);
      currentHeight.value = Math.max(0, Math.min(maxHeight * 1.1, newHeight));

      thresholdLine.attr('y1', newY).attr('y2', newY);
      thresholdHandle.attr('y', newY - 8);

      updateFromHeight(currentHeight.value);
    })
    .on('end', () => {
      renderDendrogram();
    });

  thresholdHandle.call(drag);

  // Y-axis
  const yAxis = d3.axisLeft(yScale).ticks(5);
  g.append('g')
    .attr('class', 'y-axis')
    .call(yAxis);

  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -height / 2)
    .attr('y', -35)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#999')
    .text('Distance');
}

onMounted(() => {
  if (props.data) {
    currentHeight.value = props.data.optimal_height || props.data.max_height / 2;
    updateFromHeight(currentHeight.value);
    renderDendrogram();
  }
});

watch(() => props.data, (newData) => {
  if (newData) {
    currentHeight.value = newData.optimal_height || newData.max_height / 2;
    updateFromHeight(currentHeight.value);
    renderDendrogram();
  }
}, { deep: true });
</script>

<style scoped lang="scss">
@use '../../style/color' as *;
@use 'sass:color';

.interactive-dendrogram {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  height: 100%;
}

.dendrogram-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 4px;
}

.threshold-info {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.7rem;

  .info-item {
    color: color.adjust($white, $alpha: -0.3);
    font-family: monospace;

    &.excellent { color: #4CAF50; }
    &.good { color: #8BC34A; }
    &.fair { color: #FFC107; }
    &.poor { color: #FF5722; }
  }
}

.header-buttons {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.icon-btn {
  padding: 0.2rem;
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.8);
  border-radius: 3px;
  color: color.adjust($white, $alpha: -0.3);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: color.adjust($gray, $lightness: 20%);
    color: $white;
  }
}

.optimize-btn {
  padding: 0.2rem 0.5rem;
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  border: none;
  border-radius: 3px;
  color: $white;
  font-size: 0.65rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba($main_1, 0.4);
  }
}

.dendrogram-svg-container {
  flex: 1;
  background: color.adjust($gray, $lightness: 5%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 6px;
  overflow: hidden;
  min-height: 0;

  :deep(svg) {
    display: block;
    width: 100%;
    height: 100%;

    .y-axis {
      text {
        fill: #999;
        font-size: 10px;
      }
      line, path {
        stroke: #555;
      }
    }

    .threshold-line {
      pointer-events: none;
    }
  }
}
</style>
