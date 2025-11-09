<template>
  <div class="network-demo">
    <div class="demo-controls">
      <div class="iteration-selector">
        <label>WL反復回数:</label>
        <select v-model="selectedIterations" class="iteration-select">
          <option v-for="i in 4" :key="i" :value="i">{{ i }}回</option>
        </select>
      </div>
      <button class="control-btn" @click="calculateSingleIteration" :disabled="!networks.length">
        選択反復回数で計算
      </button>
      <button class="control-btn primary" @click="calculateAllIterations" :disabled="!networks.length">
        全反復回数で計算
      </button>
    </div>

    <!-- ネットワーク一覧 -->
    <div class="networks-grid">
      <div v-for="(network, index) in networks" :key="index" class="network-card">
        <div class="network-header">
          <h3>パターン {{ index + 1 }}: {{ network.name }}</h3>
          <span class="network-stats">
            ノード: {{ network.structure.nodes.length }}, 
            エッジ: {{ network.structure.edges.length }}
          </span>
        </div>
        <div class="network-viewer-container">
          <NetworkViewer
            :ref="el => setViewerRef(el, index)"
            :network="network.structure"
            :performances="[]"
            :hide-toolbar="true"
          />
        </div>
      </div>
    </div>

    <!-- 反復回数選択タブ（全反復計算時のみ表示） -->
    <div v-if="isAllIterationsMode && Object.keys(allIterationResults).length > 0" class="iteration-tabs">
      <button 
        v-for="iter in [1,2,3,4]" 
        :key="iter"
        @click="selectIteration(iter)"
        :class="['tab-btn', { active: selectedIterations === iter }]"
      >
        反復{{ iter }}回
      </button>
    </div>

    <!-- 計算結果表示 -->
    <div v-if="computationResults" class="computation-results">
      <!-- WLカーネル計算結果 -->
      <div class="result-section">
        <h3>WLカーネル計算結果 (反復{{ computationResults.wlIterations }}回)</h3>
        <div class="debug-info">
          <div class="debug-item">
            <span class="label">ノードラベル数:</span> {{ computationResults.labelCount }}
          </div>
        </div>
        
        <!-- カーネル行列 -->
        <div class="matrix-container">
          <h4>カーネル行列 K</h4>
          <table class="data-matrix kernel-matrix">
            <thead>
              <tr>
                <th></th>
                <th v-for="i in networks.length" :key="i">{{ i }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in computationResults.kernelMatrix" :key="i">
                <th>{{ i + 1 }}</th>
                <td v-for="(val, j) in row" :key="j" :class="{ diagonal: i === j }">
                  {{ val.toFixed(3) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 距離行列表示 -->
      <div class="result-section">
        <h3>距離行列</h3>
        <div class="debug-info">
          <div class="debug-item">
            <span class="label">距離計算式:</span> d(i,j) = √(K[i,i] + K[j,j] - 2K[i,j])
          </div>
        </div>
        <div class="matrix-container">
          <table class="data-matrix distance-matrix">
            <thead>
              <tr>
                <th></th>
                <th v-for="i in networks.length" :key="i">{{ i }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in distanceMatrix" :key="i">
                <th>{{ i + 1 }}</th>
                <td v-for="(dist, j) in row" :key="j" :class="{ diagonal: i === j }">
                  {{ dist.toFixed(3) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- MDS座標 -->
      <div class="result-section">
        <h3>MDS計算結果</h3>
        <div class="method-selector">
          <label>
            <input type="radio" v-model="selectedMethod" value="mds_polar" @change="recalculate" />
            MDS→極座標
          </label>
          <label>
            <input type="radio" v-model="selectedMethod" value="circular_mds" @change="recalculate" />
            Circular MDS
          </label>
        </div>
        <!-- 比較結果の表示 -->
        <div v-if="computationResults.comparisonResults" class="comparison-results">
          <table>
            <thead>
              <tr>
                <th>手法</th>
                <th>ユークリッドストレス</th>
                <th>円環ストレス</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>MDS→極座標</td>
                <td>{{ computationResults.comparisonResults.mds_polar.stress.toFixed(4) }}</td>
                <td>{{ computationResults.comparisonResults.mds_polar.circular_stress.toFixed(4) }}</td>
              </tr>
              <tr>
                <td>Circular MDS</td>
                <td>-</td>
                <td>{{ computationResults.comparisonResults.circular_mds.circular_stress.toFixed(4) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="coordinates-table">
          <table class="data-table">
            <thead>
              <tr>
                <th>パターン</th>
                <th>グループ</th>
                <th>X座標</th>
                <th>Y座標</th>
                <th>θ (度)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(coord, i) in computationResults.coordinates" :key="i">
                <td>{{ networks[i].name }}</td>
                <td>
                  <span class="group-badge" :style="{ backgroundColor: getColorByIndex(i) }">
                    {{ getGroupName(i) }}
                  </span>
                </td>
                <td>{{ coord.x.toFixed(3) }}</td>
                <td>{{ coord.y.toFixed(3) }}</td>
                <td>{{ coord.theta.toFixed(1) }}°</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 反復回数比較（全反復計算時のみ表示） -->
      <div v-if="isAllIterationsMode && Object.keys(allIterationResults).length > 0" class="result-section">
        <h3>反復回数による角度変化</h3>
        <div class="iteration-comparison-table">
          <table class="data-table">
            <thead>
              <tr>
                <th>パターン</th>
                <th>グループ</th>
                <th v-for="iter in [1,2,3,4]" :key="iter">反復{{ iter }}回</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(network, i) in networks" :key="i">
                <td>{{ network.name }}</td>
                <td>
                  <span class="group-badge" :style="{ backgroundColor: getColorByIndex(i) }">
                    {{ getGroupName(i) }}
                  </span>
                </td>
                <td v-for="iter in [1,2,3,4]" :key="iter">
                  <span v-if="allIterationResults[iter]">
                    {{ allIterationResults[iter].coordinates[i].theta.toFixed(1) }}°
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 可視化 -->
      <div class="result-section">
        <h3>座標プロット</h3>
        <div class="legend">
          <div class="legend-item" v-for="(group, idx) in groupNames" :key="idx">
            <span class="legend-color" :style="{ backgroundColor: groupColors[idx] }"></span>
            <span class="legend-label">{{ group }}</span>
          </div>
        </div>
        <div class="plots-container">
          <!-- XY散布図 -->
          <div class="plot-wrapper">
            <h4>XY座標散布図</h4>
            <svg class="scatter-plot" viewBox="-320 -320 640 640">
              <!-- グリッド -->
              <g class="grid">
                <line x1="-300" y1="0" x2="300" y2="0" stroke="#ddd" />
                <line x1="0" y1="-300" x2="0" y2="300" stroke="#ddd" />
                <circle cx="0" cy="0" r="100" fill="none" stroke="#eee" />
                <circle cx="0" cy="0" r="200" fill="none" stroke="#eee" />
                <circle cx="0" cy="0" r="300" fill="none" stroke="#eee" />
              </g>
              <!-- データ点 -->
              <g class="data-points">
                <circle
                  v-for="(coord, i) in computationResults.xyCoordinates"
                  :key="i"
                  :cx="coord.x * 250"
                  :cy="-coord.y * 250"
                  r="8"
                  :fill="getColorByIndex(i)"
                  :stroke="getColorByIndex(i)"
                  stroke-width="2"
                  :opacity="0.8"
                />
                <text
                  v-for="(coord, i) in computationResults.xyCoordinates"
                  :key="`label-${i}`"
                  :x="coord.x * 250 + 12"
                  :y="-coord.y * 250 + 5"
                  font-size="12"
                  fill="#333"
                >
                  {{ i + 1 }}
                </text>
              </g>
            </svg>
          </div>

          <!-- 円環座標図 -->
          <div class="plot-wrapper">
            <h4>円環座標配置</h4>
            <svg class="circular-plot" viewBox="-320 -320 640 640">
              <!-- 円と角度ガイド -->
              <g class="grid">
                <circle cx="0" cy="0" r="250" fill="none" stroke="#ddd" stroke-width="2" />
                <!-- 角度マーカー -->
                <g v-for="angle in [0, 45, 90, 135, 180, 225, 270, 315]" :key="angle">
                  <line
                    :x1="240 * Math.cos(angle * Math.PI / 180)"
                    :y1="240 * Math.sin(angle * Math.PI / 180)"
                    :x2="260 * Math.cos(angle * Math.PI / 180)"
                    :y2="260 * Math.sin(angle * Math.PI / 180)"
                    stroke="#999"
                    stroke-width="2"
                  />
                  <text
                    :x="280 * Math.cos(angle * Math.PI / 180)"
                    :y="280 * Math.sin(angle * Math.PI / 180)"
                    text-anchor="middle"
                    dominant-baseline="middle"
                    font-size="12"
                    fill="#666"
                  >
                    {{ angle }}°
                  </text>
                </g>
              </g>
              <!-- データ点 -->
              <g class="data-points">
                <circle
                  v-for="(coord, i) in computationResults.circularCoordinates"
                  :key="i"
                  :cx="coord.x"
                  :cy="coord.y"
                  r="10"
                  :fill="getColorByIndex(i)"
                  :stroke="getColorByIndex(i)"
                  stroke-width="2"
                  :opacity="0.8"
                />
                <text
                  v-for="(coord, i) in computationResults.circularCoordinates"
                  :key="`label-${i}`"
                  :x="coord.x"
                  :y="coord.y - 15"
                  text-anchor="middle"
                  font-size="12"
                  font-weight="bold"
                  fill="#333"
                >
                  {{ i + 1 }}
                </text>
                <text
                  v-for="(coord, i) in computationResults.circularCoordinates"
                  :key="`name-${i}`"
                  :x="coord.x"
                  :y="coord.y + 25"
                  text-anchor="middle"
                  font-size="10"
                  fill="#666"
                >
                  {{ networks[i].name }}
                </text>
              </g>
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import NetworkViewer from '../network/NetworkViewer.vue';
import type { NetworkStructure, NetworkNode, NetworkEdge } from '../../types/project';

defineExpose({
  resetAllViewers
});

interface DemoNetwork {
  name: string;
  structure: NetworkStructure;
}

interface ComputationResults {
  wlIterations: number;
  labelCount: number;
  kernelMatrix: number[][];
  distanceMatrix: number[][];
  coordinates: Array<{x: number, y: number, theta: number}>;
  xyCoordinates: Array<{x: number, y: number}>;
  circularCoordinates: Array<{x: number, y: number}>;
  mdsStress?: number;
  circular_stress?: number;
  comparisonResults?: {
    mds_polar: { stress: number, circular_stress: number },
    circular_mds: { stress: number, circular_stress: number },
  };
}

const networks = ref<DemoNetwork[]>([]);
const distanceMatrix = ref<number[][] | null>(null);
const computationResults = ref<ComputationResults | null>(null);
const selectedIterations = ref(1);
const allIterationResults = ref<{[key: number]: ComputationResults}>({});
const selectedMethod = ref<'mds_polar' | 'circular_mds'>('circular_mds');
const isAllIterationsMode = ref(false);

// NetworkViewerのref配列
const networkViewers = ref<Array<InstanceType<typeof NetworkViewer> | null>>([]);

// ref配列を設定する関数
function setViewerRef(el: any, index: number) {
  if (el) {
    networkViewers.value[index] = el;
  }
}

// 全てのNetworkViewerに対してresetViewを実行
function resetAllViewers() {
  nextTick(() => {
    let successCount = 0;
    
    networkViewers.value.forEach((viewer, index) => {
      if (viewer && typeof viewer.resetView === 'function') {
        try {
          viewer.resetView();
          successCount++;
        } catch (error) {
          console.warn(`NetworkViewer ${index + 1} のリセットに失敗:`, error);
        }
      }
    });
  });
}

// グループ名と色の定義
const groupNames = ['線形', 'ツリー', 'スター', 'メッシュ', '疎'];
const groupColors = [
  '#FF6B6B',  // 線形：赤系
  '#4ECDC4',  // ツリー：青緑系
  '#45B7D1',  // スター：青系
  '#FFA07A',  // メッシュ：オレンジ系
  '#98D8C8'   // 疎：緑系
];

// ノードID生成
let nodeIdCounter = 0;
const generateNodeId = () => `node-${++nodeIdCounter}`;

// エッジID生成
let edgeIdCounter = 0;
const generateEdgeId = () => `edge-${++edgeIdCounter}`;

// インデックスからグループ番号を取得（0-4）
function getGroupIndex(index: number): number {
  return Math.floor(index / 3);
}

// インデックスからグループ名を取得
function getGroupName(index: number): string {
  return groupNames[getGroupIndex(index)];
}

// インデックスから色を取得（5色でグループ分け）
function getColorByIndex(index: number): string {
  return groupColors[getGroupIndex(index)];
}

// 15種類のネットワークパターン生成（5基本パターン × 3バリエーション）
function generateNetworks() {
  networks.value = [];
  networks.value.push(generateLinearNetwork());
  networks.value.push(generateLinearNetworkV1());
  networks.value.push(generateLinearNetworkV2());
  networks.value.push(generateTreeNetwork());
  networks.value.push(generateTreeNetworkV1());
  networks.value.push(generateTreeNetworkV2());
  networks.value.push(generateStarNetwork());
  networks.value.push(generateStarNetworkV1());
  networks.value.push(generateStarNetworkV2());
  networks.value.push(generateMeshNetwork());
  networks.value.push(generateMeshNetworkV1());
  networks.value.push(generateMeshNetworkV2());
  networks.value.push(generateSparseNetwork());
  networks.value.push(generateSparseNetworkV1());
  networks.value.push(generateSparseNetworkV2());
  distanceMatrix.value = null;
  computationResults.value = null;
}

// パターン1: 線形ネットワーク
function generateLinearNetwork(): DemoNetwork {
  const nodes: NetworkNode[] = [];
  const edges: NetworkEdge[] = [];

  // 各レイヤーに2つずつノードを配置
  for (let layer = 1; layer <= 4; layer++) {
    for (let i = 0; i < 2; i++) {
      const nodeId = generateNodeId();
      nodes.push({
        id: nodeId,
        layer: layer as 1 | 2 | 3 | 4,
        type: getNodeTypeByLayer(layer),
        label: `L${layer}-${i + 1}`,
        x: 300 + i * 600,
        y: layer * 200 - 100,
        performance_id: layer === 1 ? nodeId : undefined
      });
    }
  }

  // レイヤー間を順次接続
  for (let i = 0; i < 3; i++) {
    edges.push({
      id: generateEdgeId(),
      source_id: nodes[i * 2].id,
      target_id: nodes[(i + 1) * 2].id,
      type: 'type1',
      weight: 3 as const
    });
    edges.push({
      id: generateEdgeId(),
      source_id: nodes[i * 2 + 1].id,
      target_id: nodes[(i + 1) * 2 + 1].id,
      type: 'type1',
      weight: 1 as const
    });
  }

  return {
    name: '線形',
    structure: { nodes, edges }
  };
}

// パターン1-1: 線形ネットワーク（ノード追加）
function generateLinearNetworkV1(): DemoNetwork {
  const base = generateLinearNetwork();
  const { nodes, edges } = base.structure;
  
  // レイヤー3に1ノード追加
  const newNodeId = generateNodeId();
  nodes.push({
    id: newNodeId,
    layer: 3,
    type: 'variable',
    label: 'L3-3',
    x: 600,
    y: 500
  });
  
  // 既存のレイヤー2ノードから接続
  edges.push({
    id: generateEdgeId(),
    source_id: nodes[3].id, // L2-2
    target_id: newNodeId,
    type: 'type1',
    weight: 0.33 as const
  });
  
  return {
    name: '線形+1',
    structure: { nodes, edges }
  };
}

// パターン1-2: 線形ネットワーク（重み変更）
function generateLinearNetworkV2(): DemoNetwork {
  const base = generateLinearNetwork();
  const { nodes, edges } = base.structure;
  
  // 最初のエッジの重みを3から1に変更
  if (edges[0]) {
    edges[0].weight = 1 as const;
  }
  
  // 2番目のエッジの重みを1から-1に変更
  if (edges[1]) {
    edges[1].weight = -1 as const;
  }
  
  return {
    name: '線形W',
    structure: { nodes, edges }
  };
}

// パターン2: ツリー構造
function generateTreeNetwork(): DemoNetwork {
  const nodes: NetworkNode[] = [];
  const edges: NetworkEdge[] = [];

  // レイヤー1: 1ノード
  const root = generateNodeId();
  nodes.push({
    id: root,
    layer: 1,
    type: 'performance',
    label: 'Root',
    x: 600,
    y: 100,
    performance_id: root
  });

  // レイヤー2: 2ノード
  const layer2Nodes = [];
  for (let i = 0; i < 2; i++) {
    const nodeId = generateNodeId();
    layer2Nodes.push(nodeId);
    nodes.push({
      id: nodeId,
      layer: 2,
      type: 'property',
      label: `L2-${i + 1}`,
      x: 400 + i * 400,
      y: 300
    });
    edges.push({
      id: generateEdgeId(),
      source_id: root,
      target_id: nodeId,
      type: 'type1',
      weight: 3 as const
    });
  }

  // レイヤー3: 4ノード
  const layer3Nodes = [];
  for (let i = 0; i < 4; i++) {
    const nodeId = generateNodeId();
    layer3Nodes.push(nodeId);
    nodes.push({
      id: nodeId,
      layer: 3,
      type: 'variable',
      label: `L3-${i + 1}`,
      x: 200 + i * 267,
      y: 500
    });
    edges.push({
      id: generateEdgeId(),
      source_id: layer2Nodes[Math.floor(i / 2)],
      target_id: nodeId,
      type: 'type2',
      weight: 1 as const
    });
  }

  // レイヤー4: 4ノード
  for (let i = 0; i < 4; i++) {
    const nodeId = generateNodeId();
    const nodeType = i % 2 === 0 ? 'object' : 'environment';
    nodes.push({
      id: nodeId,
      layer: 4,
      type: nodeType as 'object' | 'environment',
      label: `L4-${i + 1}`,
      x: 200 + i * 267,
      y: 700
    });
    edges.push({
      id: generateEdgeId(),
      source_id: layer3Nodes[i],
      target_id: nodeId,
      type: 'type3',
      weight: 0.33 as const
    });
  }

  return {
    name: 'ツリー',
    structure: { nodes, edges }
  };
}

// パターン2-1: ツリー構造（ノード追加）
function generateTreeNetworkV1(): DemoNetwork {
  const base = generateTreeNetwork();
  const { nodes, edges } = base.structure;
  
  // レイヤー2に1ノード追加
  const newNodeId = generateNodeId();
  nodes.push({
    id: newNodeId,
    layer: 2,
    type: 'property',
    label: 'L2-3',
    x: 600,
    y: 300
  });
  
  // ルートから接続
  edges.push({
    id: generateEdgeId(),
    source_id: nodes[0].id, // Root
    target_id: newNodeId,
    type: 'type1',
    weight: 1 as const
  });
  
  return {
    name: 'ツリー+1',
    structure: { nodes, edges }
  };
}

// パターン2-2: ツリー構造（重み変更）
function generateTreeNetworkV2(): DemoNetwork {
  const base = generateTreeNetwork();
  
  // 深いコピーを作成して、参照の問題を避ける
  return {
    name: base.name,
    structure: {
      nodes: base.structure.nodes.map(n => ({ ...n })),
      edges: base.structure.edges.map(e => ({ ...e }))
    }
  };
}

// パターン3: スター型
function generateStarNetwork(): DemoNetwork {
  const nodes: NetworkNode[] = [];
  const edges: NetworkEdge[] = [];

  // 中心ノード（レイヤー3の変数）
  const center = generateNodeId();
  nodes.push({
    id: center,
    layer: 3,
    type: 'variable',
    label: 'Center',
    x: 600,
    y: 500
  });

  // 周辺ノード
  const surroundingNodes = [
    // レイヤー1（性能）
    { x: 400, y: 100, layer: 1, type: 'performance' },
    { x: 800, y: 100, layer: 1, type: 'performance' },
    // レイヤー2（特性）
    { x: 300, y: 300, layer: 2, type: 'property' },
    { x: 600, y: 300, layer: 2, type: 'property' },
    { x: 900, y: 300, layer: 2, type: 'property' },
    // レイヤー4（モノ・環境）
    { x: 300, y: 700, layer: 4, type: 'object' },
    { x: 600, y: 700, layer: 4, type: 'environment' },
    { x: 900, y: 700, layer: 4, type: 'object' }
  ];

  surroundingNodes.forEach((node, i) => {
    const nodeId = generateNodeId();
    nodes.push({
      id: nodeId,
      layer: node.layer as 1 | 2 | 3 | 4,
      type: node.type as 'performance' | 'property' | 'variable' | 'object' | 'environment',
      label: `${node.type.charAt(0).toUpperCase()}${i + 1}`,
      x: node.x,
      y: node.y,
      performance_id: node.layer === 1 ? nodeId : undefined
    });

    // 重みを交互に設定
    const weights = [3, 1, 0.33, 0, -0.33, -1, -3, 3] as const;
    
    // レイヤーの順序に基づいて接続方向を決定
    const isSourceHigher = node.layer < 3;
    edges.push({
      id: generateEdgeId(),
      source_id: isSourceHigher ? nodeId : center,
      target_id: isSourceHigher ? center : nodeId,
      type: 'type1',
      weight: weights[i]
    });
  });

  return {
    name: 'スター',
    structure: { nodes, edges }
  };
}

// パターン3-1: スター型（ノード追加）
function generateStarNetworkV1(): DemoNetwork {
  const base = generateStarNetwork();
  const { nodes, edges } = base.structure;
  
  // レイヤー3に周辺ノードを1つ追加
  const newNodeId = generateNodeId();
  nodes.push({
    id: newNodeId,
    layer: 3,
    type: 'variable',
    label: 'V2',
    x: 300,
    y: 500
  });
  
  // 中心から接続（双方向なので適切な方向で）
  edges.push({
    id: generateEdgeId(),
    source_id: nodes[0].id, // Center
    target_id: newNodeId,
    type: 'type1',
    weight: 0.33 as const
  });
  
  return {
    name: 'スター+1',
    structure: { nodes, edges }
  };
}

// パターン3-2: スター型（エッジ削除）
function generateStarNetworkV2(): DemoNetwork {
  const base = generateStarNetwork();
  const { nodes, edges } = base.structure;
  
  // 最後の2つのエッジを削除（接続数を減らす）
  edges.splice(-2, 2);
  
  return {
    name: 'スター-2',
    structure: { nodes, edges }
  };
}

// パターン4: メッシュ型
function generateMeshNetwork(): DemoNetwork {
  const nodes: NetworkNode[] = [];
  const edges: NetworkEdge[] = [];

  // 各レイヤーに3つずつノードを配置
  const nodesByLayer: { [key: number]: string[] } = {};
  
  for (let layer = 1; layer <= 4; layer++) {
    nodesByLayer[layer] = [];
    for (let i = 0; i < 3; i++) {
      const nodeId = generateNodeId();
      nodesByLayer[layer].push(nodeId);
      nodes.push({
        id: nodeId,
        layer: layer as 1 | 2 | 3 | 4,
        type: getNodeTypeByLayer(layer),
        label: `L${layer}-${i + 1}`,
        x: 200 + i * 400,
        y: layer * 200 - 100,
        performance_id: layer === 1 ? nodeId : undefined
      });
    }
  }

  // レイヤー間を密に接続
  const weights = [3, 1, 0.33, 0, -0.33] as const;
  for (let layer = 1; layer < 4; layer++) {
    nodesByLayer[layer].forEach((sourceId, i) => {
      nodesByLayer[layer + 1].forEach((targetId, j) => {
        edges.push({
          id: generateEdgeId(),
          source_id: sourceId,
          target_id: targetId,
          type: 'type1',
          weight: weights[(i + j) % weights.length]
        });
      });
    });
  }

  return {
    name: 'メッシュ',
    structure: { nodes, edges }
  };
}

// パターン4-1: メッシュ型（エッジ削除）
function generateMeshNetworkV1(): DemoNetwork {
  const base = generateMeshNetwork();
  const { nodes, edges } = base.structure;
  
  // 斜めの接続を3つ削除（構造を少し単純化）
  const indicesToRemove = [2, 5, 8]; // 特定のインデックス
  for (let i = indicesToRemove.length - 1; i >= 0; i--) {
    if (edges[indicesToRemove[i]]) {
      edges.splice(indicesToRemove[i], 1);
    }
  }
  
  return {
    name: 'メッシュ-3',
    structure: { nodes, edges }
  };
}

// パターン4-2: メッシュ型（重み変更）
function generateMeshNetworkV2(): DemoNetwork {
  const base = generateMeshNetwork();
  const { nodes, edges } = base.structure;
  
  // いくつかのエッジの重みを負に変更
  if (edges[1]) edges[1].weight = -1 as const;
  if (edges[4]) edges[4].weight = -0.33 as const;
  if (edges[7]) edges[7].weight = -3 as const;
  
  return {
    name: 'メッシュW',
    structure: { nodes, edges }
  };
}

// パターン5: 疎なネットワーク
function generateSparseNetwork(): DemoNetwork {
  const nodes: NetworkNode[] = [];
  const edges: NetworkEdge[] = [];

  // 多くのノードで少ない接続
  for (let layer = 1; layer <= 4; layer++) {
    const count = layer === 1 ? 3 : layer === 4 ? 3 : 4;
    for (let i = 0; i < count; i++) {
      const nodeId = generateNodeId();
      nodes.push({
        id: nodeId,
        layer: layer as 1 | 2 | 3 | 4,
        type: getNodeTypeByLayer(layer),
        label: `L${layer}-${i + 1}`,
        x: 150 + (i * 1200 / count),
        y: layer * 200 - 100,
        performance_id: layer === 1 ? nodeId : undefined
      });
    }
  }

  // 最小限の接続のみ
  for (let i = 0; i < nodes.length - 1; i++) {
    const source = nodes[i];
    const target = nodes[i + 1];
    
    if (source.layer < target.layer && target.layer - source.layer === 1) {
      edges.push({
        id: generateEdgeId(),
        source_id: source.id,
        target_id: target.id,
        type: 'type1',
        weight: i % 2 === 0 ? 1 : 0.33
      });
    }
  }

  return {
    name: '疎',
    structure: { nodes, edges }
  };
}

// パターン5-1: 疎なネットワーク（エッジ追加）
function generateSparseNetworkV1(): DemoNetwork {
  const base = generateSparseNetwork();
  const { nodes, edges } = base.structure;
  
  // レイヤー1→レイヤー3に直接接続を1つ追加
  edges.push({
    id: generateEdgeId(),
    source_id: nodes[0].id, // L1-1
    target_id: nodes[5].id, // L3-2
    type: 'type2',
    weight: 3 as const
  });
  
  // レイヤー2→レイヤー4に直接接続を1つ追加
  edges.push({
    id: generateEdgeId(),
    source_id: nodes[4].id, // L2-2
    target_id: nodes[10].id, // L4-1
    type: 'type3',
    weight: -1 as const
  });
  
  return {
    name: '疎+2',
    structure: { nodes, edges }
  };
}

// パターン5-2: 疎なネットワーク（ノード追加）
function generateSparseNetworkV2(): DemoNetwork {
  const base = generateSparseNetwork();
  const { nodes, edges } = base.structure;
  
  // レイヤー2に1ノード追加
  const newNodeId = generateNodeId();
  nodes.push({
    id: newNodeId,
    layer: 2,
    type: 'property',
    label: 'L2-5',
    x: 1050,
    y: 300
  });
  
  // 既存のノードから接続
  edges.push({
    id: generateEdgeId(),
    source_id: nodes[2].id, // L1-3
    target_id: newNodeId,
    type: 'type1',
    weight: 0.33 as const
  });
  
  return {
    name: '疎+1N',
    structure: { nodes, edges }
  };
}

// レイヤーに応じたノードタイプを取得
function getNodeTypeByLayer(layer: number): 'performance' | 'property' | 'variable' | 'object' | 'environment' {
  switch (layer) {
    case 1: return 'performance';
    case 2: return 'property';
    case 3: return 'variable';
    case 4: return 'object';
    default: return 'variable';
  }
}

async function calculateDistances(iterations: number): Promise<ComputationResults> {
  const networkStructures = networks.value.map(n => ({
    nodes: n.structure.nodes,
    edges: n.structure.edges
  }));
  
  try {
    const response = await fetch('http://localhost:8000/api/mds/compute_network_comparison', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        networks: networkStructures,
        iterations: iterations,
        method: selectedMethod.value,
        n_init: 500,
        compare_methods: true
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // 座標データの準備（度数法）
    const coordinates = data.coordinates.map((coord: number[], i: number) => ({
      x: coord[0],
      y: coord[1],
      theta: (Math.atan2(coord[1], coord[0]) * 180 / Math.PI + 360) % 360
    }));
    
    return {
      wlIterations: data.wl_iterations,
      labelCount: data.label_count,
      kernelMatrix: data.kernel_matrix,
      distanceMatrix: data.distance_matrix,
      coordinates: coordinates,
      xyCoordinates: data.coordinates.map((c: number[]) => ({ x: c[0], y: c[1] })),
      circularCoordinates: data.circular_coordinates.map((c: number[]) => ({ x: c[0], y: c[1] })),
      mdsStress: data.stress,
      circular_stress: data.circular_stress,
      comparisonResults: data.comparison
    };
    
  } catch (error) {
    console.error('計算エラー:', error);
    throw error;
  }
}

// 単体計算（選択された反復回数のみ）
async function calculateSingleIteration() {
  isAllIterationsMode.value = false;
  allIterationResults.value = {};
  
  computationResults.value = await calculateDistances(selectedIterations.value);
  distanceMatrix.value = computationResults.value.distanceMatrix;
}

// 全ての反復回数で計算
async function calculateAllIterations() {
  isAllIterationsMode.value = true;
  allIterationResults.value = {};
  
  for (let iter = 1; iter <= 4; iter++) {
    allIterationResults.value[iter] = await calculateDistances(iter);
  }
  
  // 選択された反復回数の結果を表示
  computationResults.value = allIterationResults.value[selectedIterations.value];
  distanceMatrix.value = computationResults.value.distanceMatrix;
}

// 手法変更時の再計算
async function recalculate() {
  if (isAllIterationsMode.value) {
    await calculateAllIterations();
  } else {
    await calculateSingleIteration();
  }
}

// 反復回数を選択（全反復モード時のみ）
function selectIteration(iter: number) {
  selectedIterations.value = iter;
  if (allIterationResults.value[iter]) {
    computationResults.value = allIterationResults.value[iter];
    distanceMatrix.value = computationResults.value.distanceMatrix;
  }
}

onMounted(() => {
  generateNetworks();
});
</script>

<style scoped>
.network-demo {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.demo-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 30px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.control-btn:hover:not(:disabled) {
  background: #f0f0f0;
  border-color: #999;
}

.control-btn.primary {
  background: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.control-btn.primary:hover:not(:disabled) {
  background: #45a049;
  border-color: #45a049;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.networks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 2fr));
  gap: 20px;
  margin-bottom: 40px;
}

.network-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.network-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.network-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.network-stats {
  font-size: 12px;
  color: #666;
}

.network-viewer-container {
  position: relative;
  overflow: hidden;
}

.computation-results {
  margin-top: 40px;
}

.result-section {
  background: white;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  margin-bottom: 24px;
}

.result-section h3 {
  font-size: 20px;
  margin-bottom: 16px;
  color: #333;
}

.result-section h4 {
  font-size: 16px;
  margin: 16px 0 12px;
  color: #555;
}

.debug-info {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-family: monospace;
  font-size: 13px;
}

.debug-item {
  margin: 4px 0;
}

.debug-item .label {
  font-weight: 600;
  color: #495057;
}

.matrix-container {
  overflow-x: auto;
  margin-bottom: 20px;
}

.data-matrix {
  border-collapse: collapse;
  font-size: 12px;
  min-width: 100%;
}

.data-matrix th,
.data-matrix td {
  padding: 6px 10px;
  text-align: center;
  border: 1px solid #dee2e6;
}

.data-matrix th {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.data-matrix td {
  background: white;
  font-family: monospace;
}

.data-matrix td.diagonal {
  background: #e9ecef;
  font-weight: 600;
}

.kernel-matrix td {
  color: #28a745;
}

.distance-matrix td {
  color: #dc3545;
}

.coordinates-table {
  margin-top: 16px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 10px 12px;
  text-align: left;
  border: 1px solid #dee2e6;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.data-table td {
  background: white;
}

.data-table tr:hover td {
  background: #f8f9fa;
}

.group-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.legend {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 2px solid #333;
}

.legend-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.plots-container {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.plot-wrapper {
  flex: 1;
  min-width: 400px;
}

.plot-wrapper h4 {
  text-align: center;
  margin-bottom: 12px;
  font-size: 16px;
  color: #333;
}

.scatter-plot,
.circular-plot {
  width: 100%;
  height: auto;
  max-width: 500px;
  margin: 0 auto;
  display: block;
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.iteration-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.iteration-selector label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.iteration-select {
  padding: 6px 12px;
  border: 2px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.iteration-tabs {
  display: flex;
  gap: 8px;
  margin: 20px 0;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.tab-btn {
  padding: 8px 16px;
  border: 2px solid #ddd;
  background: white;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f0f0f0;
}

.tab-btn.active {
  background: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.method-selector {
  margin: 10px 0;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.method-selector label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.comparison-results {
  margin: 15px 0;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 5px;
}

.comparison-results table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.comparison-results th,
.comparison-results td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.comparison-results th {
  background: #e9ecef;
  font-weight: bold;
}

.comparison-results tbody tr:hover {
  background: #f5f5f5;
}
</style>