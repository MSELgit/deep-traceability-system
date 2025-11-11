<template>
  <div class="network-editor">
    <!-- ツールバー -->
    <div class="toolbar">
      <div class="tool-group">
        <!-- レイヤー2, 3 のボタン -->
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
        <!-- レイヤー4: モノ -->
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'add-layer4-object' }"
          @click="selectAddNodeTool(4, 'object')"
          :style="{ borderColor: layers[3].color }"
        >
          <span class="tool-icon" :style="{ color: layers[3].color }">■</span>
          モノ
        </button>
        <!-- レイヤー4: 環境 -->
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'add-layer4-environment' }"
          @click="selectAddNodeTool(4, 'environment')"
          :style="{ borderColor: layers[3].color }"
        >
          <span class="tool-icon" :style="{ color: layers[3].color }">□</span>
          環境
        </button>
      </div>

      <div class="tool-divider"></div>

      <div class="tool-group">
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'select' }"
          @click="selectedTool = 'select'"
          title="選択モード"
        >
          <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'arrow-pointer']" /></span>
          選択
        </button>
        <button 
          class="tool-btn"
          :class="{ active: selectedTool === 'edge' }"
          @click="selectedTool = 'edge'"
          title="エッジ作成"
        >
          <span class="tool-icon">—</span>
          接続
        </button>
        <button 
          class="tool-btn danger"
          @click="deleteSelected"
          :disabled="!selectedNode && !selectedEdge"
          title="削除"
        >
          <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'trash']" /></span>
          削除
        </button>
      </div>

      <div class="tool-divider"></div>

      <div class="tool-group" style="background: #ffffcc; padding: 4px;">
        <label class="zoom-label">ズーム</label>
        <input 
          type="range" 
          v-model.number="zoom" 
          :min="minZoom" 
          max="3" 
          step="0.1"
          class="zoom-slider"
        />
        <span class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
        <button class="tool-btn" @click="resetViewWithDebug" title="全体表示">
          <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'expand']" /></span>
          全体表示
        </button>
      </div>

      <div class="tool-divider"></div>

      <div class="tool-group">
        <button class="tool-btn" @click="downloadAsImage" title="画像ダウンロード">
          <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" style="margin-right: 4px;">
            <path d="M10.5 8.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
            <path d="M2 4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-1.172a2 2 0 0 1-1.414-.586l-.828-.828A2 2 0 0 0 9.172 2H6.828a2 2 0 0 0-1.414.586l-.828.828A2 2 0 0 1 3.172 4H2zm.5 2a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm9 2.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0z"/>
          </svg>
          画像ダウンロード
        </button>
        <button class="tool-btn" @click="autoLayout" title="自動レイアウト">
          <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'align-justify']" /></span>
          整列
        </button>
        <button class="tool-btn" @click="clearAll" title="全削除">
          <span class="tool-icon"><FontAwesomeIcon :icon="['fas', 'rotate-right']" /></span>
          リセット
        </button>
      </div>
    </div>
    
    <div class="network-editor-wrapper">
      <!-- プロパティパネル（左側に常設） -->
    <div class="properties-panel">
      <h3 v-if="selectedNode">ノードのプロパティ</h3>
      <h3 v-else-if="selectedEdge">エッジのプロパティ</h3>
      <h3 v-else>プロパティ</h3>
      
      <!-- ノードのプロパティ -->
      <template v-if="selectedNode">
        <div class="property-group">
          <label>ラベル</label>
          <input
            v-model="tempNodeData.label"
            type="text"
            class="property-input"
            :disabled="isPerformanceNode(selectedNode)"
          />
        </div>

        <div class="property-group">
          <label>レイヤー</label>
          <select 
            v-model.number="tempNodeData.layer" 
            class="property-select"
            :disabled="isPerformanceNode(selectedNode)"
          >
            <option :value="1">Layer 1 - 性能</option>
            <option :value="2">Layer 2 - 特性</option>
            <option :value="3">Layer 3 - 変数</option>
            <option :value="4">Layer 4 - モノ・環境</option>
          </select>
        </div>

        <div class="property-group">
          <label>タイプ</label>
          <select 
            v-model="tempNodeData.type" 
            class="property-select"
            :disabled="isPerformanceNode(selectedNode)"
          >
            <option value="performance">性能</option>
            <option value="property">特性</option>
            <option value="variable">変数</option>
            <option value="object">モノ</option>
            <option value="environment">環境</option>
          </select>
        </div>

        <div class="property-group" v-if="tempNodeData.type === 'performance'">
          <label>性能ID</label>
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
          <label>座標</label>
          <div class="coords">
            <span>X: {{ Math.round(selectedNode.x) }}</span>
            <span>Y: {{ Math.round(selectedNode.y) }}</span>
          </div>
        </div>
        
        <div class="property-actions">
          <button class="save-btn" @click="saveNodeChanges">保存</button>
          <button class="cancel-btn" @click="cancelNodeChanges">キャンセル</button>
        </div>
      </template>

      <!-- エッジのプロパティ -->
      <template v-else-if="selectedEdge">
        <div class="property-group">
          <label>重み (因果関係の強さ)</label>
          <select 
            v-model.number="tempEdgeWeight" 
            class="property-select"
          >
            <option :value="3">+3 (強い正の因果関係)</option>
            <option :value="1">+1 (中程度の正の因果関係)</option>
            <option :value="0.33">+1/3 (弱い正の因果関係)</option>
            <option :value="0">0 (無相関)</option>
            <option :value="-0.33">-1/3 (弱い負の因果関係)</option>
            <option :value="-1">-1 (中程度の負の因果関係)</option>
            <option :value="-3">-3 (強い負の因果関係)</option>
          </select>
        </div>
        
        <div class="property-group">
          <label>接続情報</label>
          <div class="connection-info">
            <p>From: {{ getNodeById(selectedEdge.source_id)?.label }}</p>
            <p>To: {{ getNodeById(selectedEdge.target_id)?.label }}</p>
          </div>
        </div>
        
        <div class="property-actions">
          <button class="save-btn" @click="saveEdgeChanges">保存</button>
          <button class="cancel-btn" @click="cancelEdgeChanges">キャンセル</button>
        </div>
      </template>

      <!-- 何も選択されていない時 -->
      <div v-else class="property-empty">
        <p>ノードまたはエッジを選択してください</p>
      </div>
    </div>

    <!-- キャンバスエリア -->
    <div class="canvas-container" ref="canvasContainer">
        <!-- SVGキャンバス -->
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
          <!-- グリッド背景パターン定義 -->
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
            
            <!-- 矢印マーカー定義（各色用） -->
            <marker
              v-for="(color, weight) in edgeWeightColors"
              :key="`arrow-${weight}`"
              :id="`arrow-${weight}`"
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
            
            <!-- 選択時の赤い矢印 -->
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

          <!-- メインコンテンツグループ（ズーム・パン適用） - すべての要素を含む -->
          <g :transform="`scale(${zoom})`">
            <!-- グリッド背景 -->
            <rect 
              :x="0" 
              :y="0" 
              :width="canvasWidth" 
              :height="canvasHeight" 
              fill="url(#grid)" 
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

          <!-- エッジ（線） -->
          <g class="edges-layer">
            <g
              v-for="edge in network.edges"
              :key="edge.id"
              class="edge"
              :class="{ selected: selectedEdge?.id === edge.id }"
              @click.stop="selectEdge(edge)"
            >
              <!-- クリック判定用の透明な太い線 -->
              <line
                :x1="getNodeById(edge.source_id)?.x"
                :y1="getNodeById(edge.source_id)?.y"
                :x2="getNodeById(edge.target_id)?.x"
                :y2="getNodeById(edge.target_id)?.y"
                stroke="transparent"
                stroke-width="10"
                style="cursor: pointer"
              />
              <!-- 表示用の線 -->
              <line
                :x1="getNodeById(edge.source_id)?.x"
                :y1="getNodeById(edge.source_id)?.y"
                :x2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!).x : getNodeById(edge.target_id)?.x"
                :y2="getNodeById(edge.source_id) && getNodeById(edge.target_id) ? getAdjustedLineEnd(getNodeById(edge.source_id)!, getNodeById(edge.target_id)!).y : getNodeById(edge.target_id)?.y"
                :stroke="selectedEdge?.id === edge.id ? '#FF5722' : getEdgeColor(edge)"
                :stroke-width="selectedEdge?.id === edge.id ? '3' : '2'"
                stroke-linecap="round"
                :marker-end="selectedEdge?.id === edge.id ? 'url(#arrow-selected)' : `url(#arrow-${edge.weight ?? 0})`"
                style="pointer-events: none"
              />
              <!-- エッジの中点に削除ボタン -->
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

            <!-- エッジ作成中のプレビュー -->
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

          <!-- ノード -->
          <g class="nodes-layer">
            <g
              v-for="node in network.nodes"
              :key="node.id"
              class="node"
              :class="{ selected: selectedNode?.id === node.id }"
              @mousedown="startDrag($event, node)"
              @click.stop="handleNodeClick(node)"
            >
              <!-- レイヤー1: 性能（円） -->
              <circle
                v-if="node.layer === 1"
                :cx="node.x"
                :cy="node.y"
                :r="18"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- レイヤー2: 特性（正三角形、高さ36px） -->
              <polygon
                v-else-if="node.layer === 2"
                :points="getTrianglePoints(node.x, node.y)"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- レイヤー3: 変数（横長ダイヤ、高さ36px、幅54px） -->
              <polygon
                v-else-if="node.layer === 3"
                :points="getDiamondPoints(node.x, node.y)"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- レイヤー4: モノ（縦1:横2の長方形、高さ36px、幅72px） -->
              <rect
                v-else-if="node.layer === 4 && node.type === 'object'"
                :x="node.x - 36"
                :y="node.y - 18"
                :width="72"
                :height="36"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                rx="4"
                class="node-shape"
              />
              
              <!-- レイヤー4: 環境（正方形、36px × 36px） -->
              <rect
                v-else-if="node.layer === 4 && node.type === 'environment'"
                :x="node.x - 18"
                :y="node.y - 18"
                :width="36"
                :height="36"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                rx="4"
                class="node-shape"
              />
              
              <!-- フォールバック: レイヤー4でtypeが不明な場合（円） -->
              <circle
                v-else-if="node.layer === 4"
                :cx="node.x"
                :cy="node.y"
                :r="18"
                :fill="getNodeColor(node)"
                :stroke="selectedNode?.id === node.id ? '#FF5722' : '#333'"
                :stroke-width="selectedNode?.id === node.id ? '2' : '1.5'"
                class="node-shape"
              />
              
              <!-- ノードラベル -->
              <text
                :x="node.x"
                :y="node.y + 18 + 15"
                text-anchor="middle"
                class="node-label"
                :fill="selectedNode?.id === node.id ? '#FF5722' : '#333'"
              >
                {{ node.label }}
              </text>m
            </g>
          </g>
          </g> <!-- メインコンテンツグループ終了 -->
        </svg>

        <!-- ヘルプテキスト -->
        <div class="canvas-help" v-if="network.nodes.length === 0">
          <p><FontAwesomeIcon :icon="['fas', 'expand']" /> 上のツールバーから「性能」「特性」「変数」「モノ・環境」ボタンを選択</p>
          <p>キャンバスをクリックしてノードを配置</p>
        </div>
      </div>

      <!-- レイヤーガイド（右側） -->
      <div class="layer-legend">
        <h3>凡例</h3>
        <div 
          v-for="layer in layers"
          :key="layer.id"
          class="legend-item"
        >
          <span class="legend-color" :style="{ background: layer.color }"></span>
          <span class="legend-label">{{ layer.label }}</span>
        </div>
      </div>
    </div> <!-- network-editor-wrapper終了 -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import type { NetworkStructure, NetworkNode, NetworkEdge, Performance } from '../../types/project';

const props = defineProps<{
  modelValue: NetworkStructure;
  performances: Performance[];
}>();

const emit = defineEmits<{
  'update:modelValue': [value: NetworkStructure];
}>();

// キャンバスサイズ
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

// 内部状態
const network = ref<NetworkStructure>({
  nodes: [],
  edges: []
});

// 更新中フラグ（循環参照防止）
const isUpdating = ref(false);

// ツール選択
const selectedTool = ref<string>('select');
const selectedNode = ref<NetworkNode | null>(null);
const selectedEdge = ref<NetworkEdge | null>(null);

// ドラッグ状態
const isDragging = ref(false);
const dragNode = ref<NetworkNode | null>(null);
const dragOffset = ref({ x: 0, y: 0 });

// エッジ作成状態
const edgeStart = ref<NetworkNode | null>(null);
const tempEdgeEnd = ref<{ x: number; y: number } | null>(null);

// プロパティ編集用の一時データ
const tempNodeData = ref({
  label: '',
  layer: 1 as 1 | 2 | 3 | 4,
  type: 'property' as NetworkNode['type'],
  performance_id: undefined as string | undefined
});
const tempEdgeWeight = ref<3 | 1 | 0.33 | 0 | -0.33 | -1 | -3>(0);

const svgCanvas = ref<SVGSVGElement>();
const canvasContainer = ref<HTMLDivElement>();

// レイヤー定義
const layers = [
  { id: 1, label: '性能', color: '#4CAF50', type: 'performance' },
  { id: 2, label: '特性', color: '#2196F3', type: 'property' },
  { id: 3, label: '変数', color: '#FFC107', type: 'variable' },
  { id: 4, label: 'モノ・環境', color: '#9C27B0', type: 'object' }
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

const edgeWeightLabels = {
  3: '+3 (強い正の因果関係)',
  1: '+1 (中程度の正の因果関係)',
  0.33: '+1/3 (弱い正の因果関係)',
  0: '0 (無相関)',
  [-0.33]: '-1/3 (弱い負の因果関係)',
  [-1]: '-1 (中程度の負の因果関係)',
  [-3]: '-3 (強い負の因果関係)'
};

// エッジの色を取得
function getEdgeColor(edge: NetworkEdge): string {
  const weight = edge.weight ?? 0;
  return edgeWeightColors[weight] || 'silver';
}

// キャンバスのカーソルスタイル（computed）
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

// 初期化
onMounted(() => {
  if (props.modelValue) {
    network.value = JSON.parse(JSON.stringify(props.modelValue));
    
    // 既存のエッジにweightがない場合はデフォルト値を設定
    network.value.edges.forEach(edge => {
      if (edge.weight === undefined) {
        edge.weight = 0; // デフォルトは無相関
      }
    });
  }
  if (network.value.nodes.length === 0) {
    ensurePerformanceNodes(false); // emitしない
  } else {
    ensurePerformanceNodes(false); // emitしない
  }
  
  // ノードがあれば全体表示
  if (network.value.nodes.length > 0) {
    nextTick(() => resetView());
  }
});

// 監視
watch(() => props.modelValue, (newVal, oldVal) => {
  
  // 自分自身の更新による変更は無視
  if (isUpdating.value) {
    return;
  }
  
  if (newVal) {
    // 新しいデータをコピー
    network.value = JSON.parse(JSON.stringify(newVal));
    
    // 既存のエッジにweightがない場合はデフォルト値を設定
    network.value.edges.forEach(edge => {
      if (edge.weight === undefined) {
        edge.weight = 0; // デフォルトは無相関
      }
    });
  }
}, { deep: true });

// 性能データの変更を監視
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

// 性能ノードが存在することを保証
function ensurePerformanceNodes(shouldEmit: boolean = true) {
  if (props.performances.length === 0) {
    return;
  }
  
  const leafPerfs = props.performances.filter(p => p.is_leaf);
  
  // 既存の性能ノードIDを取得
  const existingPerfIds = new Set(
    network.value.nodes
      .filter(n => n.type === 'performance' && n.performance_id)
      .map(n => n.performance_id)
  );
  const startX = 100;
  const startY = 100; // レイヤー1の中央
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

// デバッグ情報を出力するヘルパー
function logResetViewDebug() {
  network.value.nodes.forEach(node => {
  });
}

// ノード色を取得
function getNodeColor(node: NetworkNode): string {
  const layer = layers.find(l => l.id === node.layer);
  return layer?.color || '#999';
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

// ノードIDから取得
function getNodeById(id: string): NetworkNode | undefined {
  return network.value.nodes.find(n => n.id === id);
}

// SVG座標をワールド座標に変換（ズーム考慮）
function screenToWorld(screenX: number, screenY: number): { x: number; y: number } {
  return {
    x: screenX / zoom.value,
    y: screenY / zoom.value
  };
}

// 性能ノードかどうか判定
function isPerformanceNode(node: NetworkNode | null): boolean {
  if (!node) return false;
  return node.type === 'performance' && !!node.performance_id;
}

// タイプ変更時の処理
function handleTypeChange() {
  if (!selectedNode.value) return;
  
  // タイプに応じてレイヤーを自動設定
  const typeLayerMap: Record<string, 1 | 2 | 3 | 4> = {
    'performance': 1,
    'property': 2,
    'variable': 3,
    'object': 4,
    'condition': 4
  };
  
  const newLayer = typeLayerMap[selectedNode.value.type];
  if (newLayer) {
    selectedNode.value.layer = newLayer;
  }
  
  emitUpdate();
}

// ノード選択時に一時データを初期化
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

// エッジ選択時に一時データを初期化
function updateTempEdgeData() {
  if (selectedEdge.value) {
    tempEdgeWeight.value = (selectedEdge.value.weight ?? 0) as 3 | 1 | 0.33 | 0 | -0.33 | -1 | -3;
  }
}

// ノードの変更を保存
function saveNodeChanges() {
  if (!selectedNode.value) return;
  
  // 変更を適用
  selectedNode.value.label = tempNodeData.value.label;
  selectedNode.value.layer = tempNodeData.value.layer;
  selectedNode.value.type = tempNodeData.value.type;
  selectedNode.value.performance_id = tempNodeData.value.performance_id;
  
  // タイプに応じてレイヤーを自動設定
  const typeLayerMap: Record<string, 1 | 2 | 3 | 4> = {
    'performance': 1,
    'property': 2,
    'variable': 3,
    'object': 4,
    'environment': 4
  };
  
  const newLayer = typeLayerMap[tempNodeData.value.type];
  if (newLayer) {
    selectedNode.value.layer = newLayer;
  }
  
  emitUpdate();
  selectedNode.value = null; // 選択を解除
}

// ノードの変更をキャンセル
function cancelNodeChanges() {
  selectedNode.value = null;
}

// エッジの変更を保存
function saveEdgeChanges() {
  if (!selectedEdge.value) return;
  
  selectedEdge.value.weight = tempEdgeWeight.value;
  emitUpdate();
  selectedEdge.value = null; // 選択を解除
}

// エッジの変更をキャンセル
function cancelEdgeChanges() {
  selectedEdge.value = null;
}

// ノード追加ツール選択
function selectAddNodeTool(layerId: number, nodeType?: string) {
  if (layerId === 4 && nodeType) {
    selectedTool.value = `add-layer4-${nodeType}`;
  } else {
    selectedTool.value = `add-layer${layerId}`;
  }
  selectedNode.value = null;
  selectedEdge.value = null;
}

// キャンバスクリック
function handleCanvasClick(event: MouseEvent) {
  // パン中は無視
  if (isPanning.value) return;
  
  const rect = svgCanvas.value!.getBoundingClientRect();
  const screenX = event.clientX - rect.left;
  const screenY = event.clientY - rect.top;
  
  // ワールド座標に変換
  const { x, y } = screenToWorld(screenX, screenY);

  // ノード追加モード
  if (selectedTool.value.startsWith('add-layer')) {
    // レイヤー4の場合はモノ/環境を判定
    if (selectedTool.value === 'add-layer4-object') {
      addNode(x, y, 4, 'object');
    } else if (selectedTool.value === 'add-layer4-environment') {
      addNode(x, y, 4, 'environment');
    } else {
      const layerId = parseInt(selectedTool.value.replace('add-layer', ''));
      addNode(x, y, layerId);
    }
  }
  // 選択解除
  else if (selectedTool.value === 'select') {
    selectedNode.value = null;
    selectedEdge.value = null;
  }
}

// ノード追加
function addNode(x: number, y: number, layer: number, nodeType?: string) {
  const layerInfo = layers.find(l => l.id === layer);
  
  // レイヤーに応じたY座標範囲（キャンバス800を4分割）
  const layerYStart = (layer - 1) * 200;
  const layerYEnd = layer * 200;
  
  // Y座標をレイヤーの範囲内に制限
  let adjustedY = y;
  if (y < layerYStart) {
    adjustedY = layerYStart + 50;
  } else if (y > layerYEnd) {
    adjustedY = layerYEnd - 50;
  }
  
  // typeを決定
  let type: NetworkNode['type'];
  if (nodeType) {
    type = nodeType as NetworkNode['type'];
  } else {
    type = layerInfo?.type as NetworkNode['type'] || 'property';
  }
  
  // labelを決定
  let label: string;
  if (layer === 4) {
    if (type === 'object') {
      label = `モノ ${network.value.nodes.filter(n => n.layer === 4 && n.type === 'object').length + 1}`;
    } else if (type === 'environment') {
      label = `環境 ${network.value.nodes.filter(n => n.layer === 4 && n.type === 'environment').length + 1}`;
    } else {
      label = `${layerInfo?.label || 'ノード'} ${network.value.nodes.filter(n => n.layer === layer).length + 1}`;
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
  
  // 追加後は選択モードに戻る
  selectedTool.value = 'select';
  selectedNode.value = newNode;
  updateTempNodeData(); // 一時データを更新
}

// ノードクリック
function handleNodeClick(node: NetworkNode) {
  if (selectedTool.value === 'select') {
    selectedNode.value = node;
    selectedEdge.value = null;
    updateTempNodeData(); // 一時データを更新
  } else if (selectedTool.value === 'edge') {
    // エッジ作成開始
    if (!edgeStart.value) {
      edgeStart.value = node;
    } else {
      // エッジ作成完了
      createEdge(edgeStart.value, node);
      edgeStart.value = null;
      tempEdgeEnd.value = null;
    }
  }
}

// エッジ作成
function createEdge(from: NetworkNode, to: NetworkNode) {
  if (from.id === to.id) return;
  
  // 既存チェック
  const exists = network.value.edges.some(
    e => (e.source_id === from.id && e.target_id === to.id) ||
         (e.source_id === to.id && e.target_id === from.id)
  );
  
  if (exists) {
    alert('このエッジは既に存在します');
    return;
  }

  const newEdge: NetworkEdge = {
    id: `edge-${Date.now()}`,
    source_id: from.id,
    target_id: to.id,
    type: 'type1',
    weight: 0 // デフォルトは無相関
  };

  network.value.edges.push(newEdge);
  emitUpdate();
  
  // エッジを自動選択してプロパティを表示
  selectedTool.value = 'select';
  selectedEdge.value = newEdge;
  selectedNode.value = null;
  updateTempEdgeData(); // 一時データを更新
}

// エッジ選択
function selectEdge(edge: NetworkEdge) {
  if (selectedTool.value === 'select') {
    selectedEdge.value = edge;
    selectedNode.value = null;
    updateTempEdgeData(); // 一時データを更新
  }
}

// エッジ削除
function deleteEdge(edge: NetworkEdge) {
  network.value.edges = network.value.edges.filter(e => e.id !== edge.id);
  selectedEdge.value = null;
  emitUpdate();
}

// マウス移動（エッジプレビュー）
function handleCanvasMouseMove(event: MouseEvent) {
  if (selectedTool.value === 'edge' && edgeStart.value) {
    const rect = svgCanvas.value!.getBoundingClientRect();
    const screenX = event.clientX - rect.left;
    const screenY = event.clientY - rect.top;
    const world = screenToWorld(screenX, screenY);
    tempEdgeEnd.value = { x: world.x, y: world.y };
  }
}

// ドラッグ開始
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

// ドラッグ中
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
  dragNode.value.x = Math.max(nodeRadius, Math.min(maxX - nodeRadius, dragNode.value.x));
  dragNode.value.y = Math.max(nodeRadius, Math.min(maxY - nodeRadius, dragNode.value.y));
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
  
  for (let layer = 1; layer <= 4; layer++) {
    if (layer === 4) {
      // レイヤー4は特別な処理：モノを左半分、環境を右半分に配置
      const objectNodes = network.value.nodes.filter(n => n.layer === 4 && n.type === 'object');
      const envNodes = network.value.nodes.filter(n => n.layer === 4 && n.type === 'environment');
      
      const yCenter = layerCenterY[layer - 1];
      const halfWidth = canvasWidth.value / 2;
      
      // モノを左半分に配置
      if (objectNodes.length > 0) {
        const objectSpacing = halfWidth / (objectNodes.length + 1);
        objectNodes.forEach((node, index) => {
          node.x = objectSpacing * (index + 1);
          node.y = yCenter;
        });
      }
      
      // 環境を右半分に配置
      if (envNodes.length > 0) {
        const envSpacing = halfWidth / (envNodes.length + 1);
        envNodes.forEach((node, index) => {
          node.x = halfWidth + envSpacing * (index + 1);
          node.y = yCenter;
        });
      }
    } else {
      // レイヤー1-3は従来通り
      const layerNodes = network.value.nodes.filter(n => n.layer === layer);
      
      if (layerNodes.length === 0) continue;
      
      // このレイヤーの中央Y座標
      const yCenter = layerCenterY[layer - 1];
      
      // ノードを横一列に配置
      const spacing = canvasWidth.value / (layerNodes.length + 1);
      
      layerNodes.forEach((node, index) => {
        node.x = spacing * (index + 1);
        node.y = yCenter;
      });
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

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDragMove);
  document.removeEventListener('mouseup', handleDragEnd);
  document.removeEventListener('mousemove', handlePanMove);
  document.removeEventListener('mouseup', handlePanEnd);
});
</script>

<style scoped>
.network-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.network-editor-wrapper {
  display: flex;
  flex-direction: row;
  flex: 1;
  gap: 12px;
  overflow: hidden;
  min-height: 0; /* flexboxで縮小可能にする */
}

.toolbar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  gap: 12px;
  overflow-x: auto;
  flex-wrap: nowrap;
  flex-shrink: 0; /* ツールバーは縮まないように */
}

.tool-group {
  display: flex;
  gap: 6px;
  align-items: center;
}

.zoom-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.zoom-slider {
  width: 120px;
  height: 6px;
  cursor: pointer;
}

.zoom-value {
  font-size: 12px;
  color: #666;
  min-width: 45px;
  text-align: right;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.tool-btn:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #999;
}

.tool-btn.active {
  background: #E3F2FD;
  border-color: #2196F3;
  color: #2196F3;
}

.tool-btn.danger {
  color: #f44336;
}

.tool-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.tool-icon {
  font-size: 16px;
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
  background: white;
  border-radius: 8px;
  min-width: 0; /* flexboxで必要 */
}

.layer-legend {
  display: flex;
  flex-direction: column;
  width: 250px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow-y: auto;
  flex-shrink: 0;
}

.layer-legend h3 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
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

.network-canvas {
  display: block;
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
  font-size: 13px;
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
  stroke: #FF5722 !important;
  stroke-width: 3 !important;
}

.canvas-help {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #999;
  pointer-events: none;
}

.canvas-help p {
  margin: 8px 0;
  font-size: 14px;
}

.properties-panel {
  width: 250px;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow-y: auto;
  flex-shrink: 0;
}

.properties-panel h3 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
}

.property-group {
  margin-bottom: 12px;
}

.property-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.property-input,
.property-select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.coords {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.connection-info {
  background: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  font-size: 13px;
}

.connection-info p {
  margin: 4px 0;
  color: #666;
}

.property-empty {
  color: #999;
  text-align: center;
  padding: 40px 20px;
}

.property-empty p {
  font-size: 14px;
}

.property-actions {
  display: flex;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
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