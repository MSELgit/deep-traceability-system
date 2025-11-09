<template>
  <div class="network-viewer-wrapper">
      <!-- ツールバー -->
      <div class="viewer-toolbar">
        <div class="tool-group">
          <label v-if="!hideToolbar" class="zoom-label">ズーム</label>
          <input  v-if="!hideToolbar"
            type="range" 
            v-model.number="zoom" 
            :min="minZoom" 
            max="3" 
            step="0.1"
            class="zoom-slider"
          />
          <span v-if="!hideToolbar" class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
          <button v-if="!hideToolbar" class="tool-btn" @click="resetView" title="全体表示">
            <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'expand']" /></span>
            全体表示
          </button>
          <button class="tool-btn" @click="downloadAsImage" title="ダウンロード">
            <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
              <path d="M10.5 8.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
              <path d="M2 4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-1.172a2 2 0 0 1-1.414-.586l-.828-.828A2 2 0 0 0 9.172 2H6.828a2 2 0 0 0-1.414.586l-.828.828A2 2 0 0 1 3.172 4H2zm.5 2a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm9 2.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0z"/>
            </svg>
            画像ダウンロード
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
      <!-- グリッド背景パターン定義 -->
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
        
        <!-- 矢印マーカー定義（各色用） -->
        <marker
          v-for="(color, weight) in edgeWeightColors"
          :key="`arrow-${weight}`"
          :id="`arrow-viewer-${weight}`"
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

      <!-- メインコンテンツグループ（ズーム適用） - すべての要素を含む -->
      <g :transform="`scale(${zoom})`">
        <!-- グリッド背景 -->
        <rect 
          :x="0" 
          :y="0" 
          :width="canvasWidth" 
          :height="canvasHeight" 
          fill="url(#grid-viewer)" 
        />

        <!-- レイヤー背景（4段分割） -->
        <g class="layer-backgrounds">
          <!-- 性能レイヤー（1段目: Y=0-200） -->
          <rect 
            :x="0" 
            :y="0" 
            :width="canvasWidth" 
            :height="200"
            :fill="layers[0].color"
            opacity="0.1"
          />
          <!-- 特性レイヤー（2段目: Y=200-400） -->
          <rect 
            :x="0" 
            :y="200" 
            :width="canvasWidth" 
            :height="200"
            :fill="layers[1].color"
            opacity="0.1"
          />
          <!-- 変数レイヤー（3段目: Y=400-600） -->
          <rect 
            :x="0" 
            :y="400" 
            :width="canvasWidth" 
            :height="200"
            :fill="layers[2].color"
            opacity="0.1"
          />
          <!-- モノ・環境レイヤー（4段目: Y=600-800） -->
          <rect 
            :x="0" 
            :y="600" 
            :width="canvasWidth" 
            :height="200"
            :fill="layers[3].color"
            opacity="0.1"
          />
        </g>

      <!-- エッジ -->
      <g class="edges-layer">
        <line
          v-for="edge in network.edges"
          :key="edge.id"
          :x1="getNodeById(edge.source_id)?.x"
          :y1="getNodeById(edge.source_id)?.y"
          :x2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!).x : getNodeById(edge.target_id)?.x"
          :y2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!).y : getNodeById(edge.target_id)?.y"
          :stroke="getEdgeColor(edge)"
          stroke-width="1.5"
          stroke-linecap="round"
          :marker-end="`url(#arrow-viewer-${edge.weight ?? 0})`"
        />
      </g>

      <!-- ノード -->
      <g class="nodes-layer">
        <g
          v-for="node in network.nodes"
          :key="node.id"
          class="node"
        >
          <!-- レイヤー1: 性能（円） -->
          <circle
            v-if="node.layer === 1"
            :cx="node.x"
            :cy="node.y"
            :r="18"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
          />
          
          <!-- レイヤー2: 特性（正三角形、高さ36px） -->
          <polygon
            v-else-if="node.layer === 2"
            :points="getTrianglePoints(node.x, node.y)"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
          />
          
          <!-- レイヤー3: 変数（横長ダイヤ、高さ36px、幅54px） -->
          <polygon
            v-else-if="node.layer === 3"
            :points="getDiamondPoints(node.x, node.y)"
            :fill="getNodeColor(node)"
            stroke="#333"
            stroke-width="1.5"
          />
          
          <!-- レイヤー4: モノ（縦1:横2の長方形、高さ36px、幅72px） -->
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
          
          <!-- レイヤー4: 環境（正方形、36px × 36px） -->
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
          
          <!-- フォールバック: レイヤー4でtypeが不明な場合（円） -->
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
      </g> <!-- メインコンテンツグループ終了 -->
    </svg>
    </div> <!-- canvas-container終了 -->
    </div> <!-- network-viewer終了 -->

    <!-- レイヤーガイド（ネットワーク表示エリアの外） -->
    <div class="layer-legend">
      <div 
        v-for="layer in layers"
        :key="layer.id"
        class="legend-item"
      >
        <span class="legend-color" :style="{ background: layer.color }"></span>
        <span class="legend-label">{{ layer.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import type { NetworkStructure, NetworkNode, Performance } from '../../types/project';

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

// ズーム・パン状態
const zoom = ref(1);
const minZoom = ref(0.3);
const panX = ref(0);
const panY = ref(0);
const isPanning = ref(false);
const panStart = ref({ x: 0, y: 0 });

const svgCanvas = ref<SVGSVGElement>();
const viewerContainer = ref<HTMLDivElement>();

const layers = [
  { id: 1, label: '性能', color: '#4CAF50' },
  { id: 2, label: '特性', color: '#2196F3' },
  { id: 3, label: '変数', color: '#FFC107' },
  { id: 4, label: 'モノ・環境', color: '#9C27B0' }
];

// エッジの重みと色の対応
const edgeWeightColors = {
  3: '#004563',      // 強い正の因果関係
  1: '#588da2',      // 中程度の正の因果関係
  0.33: '#c3dde2',   // 弱い正の因果関係
  0: 'silver',       // 無相関
  [-0.33]: '#e9c1c9', // 弱い負の因果関係
  [-1]: '#c94c62',   // 中程度の負の因果関係
  [-3]: '#9f1e35'    // 強い負の因果関係
};

// エッジの色を取得
function getEdgeColor(edge: any): string {
  const weight = edge.weight ?? 0;
  return edgeWeightColors[weight as keyof typeof edgeWeightColors] || 'silver';
}

// ノード形状計算関数
// 正三角形の座標（高さ36px、上向き）
function getTrianglePoints(cx: number, cy: number): string {
  const height = 36;
  const halfBase = height / Math.sqrt(3); // 底辺の半分 ≈ 20.8
  return `${cx},${cy - height/2} ${cx - halfBase},${cy + height/2} ${cx + halfBase},${cy + height/2}`;
}

// 横長ダイヤの座標（高さ36px、幅54px）
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

// エッジの終点を調整（矢印がノードと重ならないように）
function getAdjustedLineEnd(source: NetworkNode, target: NetworkNode): { x: number, y: number } {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  
  // ノードの半径（形状に応じて調整）
  let targetRadius = 18; // デフォルト（円）
  
  if (target.layer === 2) { // 三角形
    targetRadius = 20;
  } else if (target.layer === 3) { // ダイヤ
    targetRadius = 24;
  } else if (target.layer === 4 && target.type === 'object') { // 長方形
    targetRadius = 36;
  } else if (target.layer === 4 && target.type === 'environment') { // 正方形
    targetRadius = 18;
  }
  
  // 矢印の分だけさらに短くする
  const adjustment = targetRadius + 10;
  const ratio = (distance - adjustment) / distance;
  
  return {
    x: source.x + dx * ratio,
    y: source.y + dy * ratio
  };
}

// ズーム・パン機能
function resetView() {
  
  if (props.network.nodes.length === 0) {
    zoom.value = 1;
    minZoom.value = 0.3;
    panX.value = 0;
    panY.value = 0;
    return;
  }

  // SVGキャンバスが準備できているか確認
  if (!svgCanvas.value) {
    console.warn('  ⚠️ SVGキャンバスが準備できていません');
    return;
  }

  // キャンバス全体のサイズを使用（ノードの配置に関わらず）
  const contentWidth = canvasWidth.value; // 1200
  const contentHeight = canvasHeight.value; // 800
  
  // 実際の表示領域のサイズを取得（canvas-containerのサイズ）
  const container = viewerContainer.value?.querySelector('.canvas-container') as HTMLElement;
  if (!container) {
    console.warn('  ⚠️ canvas-containerが見つかりません');
    return;
  }
  const rect = container.getBoundingClientRect();
  const viewWidth = rect.width;
  const viewHeight = rect.height;
  
  // 親要素のサイズも確認
  const viewerRect = viewerContainer.value?.getBoundingClientRect();
  const wrapperElement = viewerContainer.value?.parentElement;
  const wrapperRect = wrapperElement?.getBoundingClientRect();
  
  // viewSizeが0の場合は処理をスキップ
  if (viewWidth === 0 || viewHeight === 0) {
    return;
  }
  
  // スクロールバーの幅を考慮して計算（約17px）
  const scrollbarSize = 0;
  const effectiveWidth = viewWidth - scrollbarSize;
  const effectiveHeight = viewHeight - scrollbarSize;
  
  // コンテンツが表示領域に収まるズーム比率を計算
  const zoomX = effectiveWidth / contentWidth;
  const zoomY = effectiveHeight / contentHeight;
  const calculatedZoom = Math.min(zoomX, zoomY); // 少し余白を追加
  
  // 異常な値をチェック
  if (calculatedZoom <= 0 || !isFinite(calculatedZoom)) {
    console.warn('  ⚠️ 異常なズーム値:', calculatedZoom);
    zoom.value = 1;
    minZoom.value = 0.3;
    return;
  }
  
  zoom.value = calculatedZoom;
  
  // 計算されたズーム値を最小値として設定
  minZoom.value = Math.max(0.1, Math.floor(zoom.value * 10) / 10);
  
  // スクロールをリセット
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

// リサイズハンドラーを保持
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

<style scoped>
.network-viewer-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
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
  padding: 8px 12px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  gap: 12px;
  flex-shrink: 0;
}

.tool-group {
  display: flex;
  gap: 6px;
  align-items: center;
}

.zoom-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.zoom-slider {
  width: 100px;
  height: 6px;
  cursor: pointer;
}

.zoom-value {
  font-size: 11px;
  color: #666;
  min-width: 40px;
  text-align: right;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #f5f5f5;
  border-color: #999;
}

.tool-icon {
  font-size: 14px;
}

.spacer {
  flex: 1;
}

.info-group {
  display: flex;
  gap: 12px;
}

.info-text {
  font-size: 12px;
  color: #666;
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
  gap: 16px;
  padding: 8px 16px;
  background: white;
  border-top: 1px solid #e0e0e0;
  justify-content: center;
  flex-shrink: 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-label {
  color: #666;
}
</style>