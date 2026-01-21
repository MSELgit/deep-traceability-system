<template>
  <div class="network-demo">
    <div class="demo-controls">
      <div class="iteration-selector">
        <label>WL Iterations:</label>
        <select v-model="selectedIterations" class="iteration-select">
          <option v-for="i in 4" :key="i" :value="i">{{ i }}</option>
        </select>
      </div>
      <button class="control-btn" @click="calculateSingleIteration" :disabled="!networks.length">
        Calculate Selected Iteration
      </button>
      <button class="control-btn primary" @click="calculateAllIterations" :disabled="!networks.length">
        Calculate All Iterations
      </button>
    </div>

    <!-- Network List -->
    <div class="networks-grid">
      <div v-for="(network, index) in networks" :key="index" class="network-card">
        <div class="network-header">
          <h3>Pattern {{ index + 1 }}: {{ network.name }}</h3>
          <span class="network-stats">
            Nodes: {{ network.structure.nodes.length }}, 
            Edges: {{ network.structure.edges.length }}
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

    <!-- Iteration Selection Tabs (shown only when all iterations calculated) -->
    <div v-if="isAllIterationsMode && Object.keys(allIterationResults).length > 0" class="iteration-tabs">
      <button 
        v-for="iter in [1,2,3,4]" 
        :key="iter"
        @click="selectIteration(iter)"
        :class="['tab-btn', { active: selectedIterations === iter }]"
      >
Iteration {{ iter }}
      </button>
    </div>

    <!-- Computation Results -->
    <div v-if="computationResults" class="computation-results">
      <!-- WLカーネル計算結果 -->
      <div class="result-section">
        <h3>WL Kernel Computation Results ({{ computationResults.wlIterations }} iterations)</h3>
        <div class="debug-info">
          <div class="debug-item">
            <span class="label">Node Label Count:</span> {{ computationResults.labelCount }}
          </div>
        </div>
        
        <!-- カーネル行列 -->
        <div class="matrix-container">
          <h4>Kernel Matrix K</h4>
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
        <h3>Distance Matrix</h3>
        <div class="debug-info">
          <div class="debug-item">
            <span class="label">Distance Formula:</span> d(i,j) = √(K[i,i] + K[j,j] - 2K[i,j])
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
        <h3>MDS Computation Results</h3>
        <div class="method-selector">
          <label>
            <input type="radio" v-model="selectedMethod" value="mds_polar" @change="recalculate" />
            MDS→Polar
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
                <th>Method</th>
                <th>Euclidean Stress</th>
                <th>Circular Stress</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>MDS→Polar</td>
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
                <th>Pattern</th>
                <th>Group</th>
                <th>X Coordinate</th>
                <th>Y Coordinate</th>
                <th>θ (degrees)</th>
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
        <h3>Angle Changes by Iteration Count</h3>
        <div class="iteration-comparison-table">
          <table class="data-table">
            <thead>
              <tr>
                <th>Pattern</th>
                <th>Group</th>
                <th v-for="iter in [1,2,3,4]" :key="iter">Iteration {{ iter }}</th>
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

      <!-- Visualization -->
      <div class="result-section">
        <h3>Coordinate Plot</h3>
        <div class="legend">
          <div class="legend-item" v-for="(group, idx) in groupNames" :key="idx">
            <span class="legend-color" :style="{ backgroundColor: groupColors[idx] }"></span>
            <span class="legend-label">{{ group }}</span>
          </div>
        </div>
        <div class="plots-container">
          <!-- XY Scatter Plot -->
          <div class="plot-wrapper">
            <div class="plot-header">
              <h4>XY Coordinate Scatter Plot</h4>
              <button class="camera-btn" @click="downloadScatterPlot" title="Download XY Scatter Plot">
                <FontAwesomeIcon :icon="['fas', 'camera']" />
              </button>
            </div>
            <svg ref="scatterPlotSvg" class="scatter-plot" viewBox="-320 -320 640 640">
              <!-- Grid -->
              <g class="grid">
                <line x1="-300" y1="0" x2="300" y2="0" stroke="#ddd" />
                <line x1="0" y1="-300" x2="0" y2="300" stroke="#ddd" />
                <circle cx="0" cy="0" r="100" fill="none" stroke="#eee" />
                <circle cx="0" cy="0" r="200" fill="none" stroke="#eee" />
                <circle cx="0" cy="0" r="300" fill="none" stroke="#eee" />
              </g>
              <!-- Data Points -->
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

          <!-- Circular Coordinates -->
          <div class="plot-wrapper">
            <div class="plot-header">
              <h4>Circular Coordinate Layout</h4>
              <button class="camera-btn" @click="downloadCircularPlot" title="Download Circular Plot">
                <FontAwesomeIcon :icon="['fas', 'camera']" />
              </button>
            </div>
            <svg ref="circularPlotSvg" class="circular-plot" viewBox="-320 -320 640 640">
              <!-- Circle and Angle Guides -->
              <g class="grid">
                <circle cx="0" cy="0" r="250" fill="none" stroke="#ddd" stroke-width="2" />
                <!-- Angle Markers -->
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
              <!-- Data Points -->
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
import { ref, onMounted, nextTick } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import NetworkViewer from '../network/NetworkViewer.vue';
import type { NetworkStructure, NetworkNode, NetworkEdge } from '../../types/project';
import { CONFIG } from '../../config/environment';

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

// SVG要素のref
const scatterPlotSvg = ref<SVGSVGElement>();
const circularPlotSvg = ref<SVGSVGElement>();

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
const groupNames = ['Linear', 'Tree', 'Star', 'Mesh', 'Sparse'];
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
    name: 'Linear',
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
    name: 'Linear+1',
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
    name: 'Linear-W',
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
    name: 'Tree',
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
    name: 'Tree+1',
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
    name: 'Star',
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
    name: 'Star+1',
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
    name: 'Star-2',
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
    name: 'Mesh',
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
    name: 'Mesh-3',
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
    name: 'Mesh-W',
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
    name: 'Sparse',
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
    name: 'Sparse+2',
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
    name: 'Sparse+1N',
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
    const response = await fetch(`${CONFIG.apiBaseUrl}/mds/compute_network_comparison`, {
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

// Download scatter plot as image
function downloadScatterPlot() {
  if (!scatterPlotSvg.value) {
    console.error('Scatter plot SVG not available');
    return;
  }
  downloadSvgAsImage(scatterPlotSvg.value, 'scatter-plot');
}

// Download circular plot as image
function downloadCircularPlot() {
  if (!circularPlotSvg.value) {
    console.error('Circular plot SVG not available');
    return;
  }
  downloadSvgAsImage(circularPlotSvg.value, 'circular-plot');
}

// Helper function to download SVG as PNG image
function downloadSvgAsImage(svgElement: SVGSVGElement, plotType: string) {
  try {
    // Clone SVG to avoid modifying the original
    const svgClone = svgElement.cloneNode(true) as SVGSVGElement;
    
    // Set dimensions for proper scaling
    const width = 640;
    const height = 640;
    svgClone.setAttribute('width', String(width));
    svgClone.setAttribute('height', String(height));
    
    // Convert SVG to data URL
    const svgData = new XMLSerializer().serializeToString(svgClone);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    
    // Create Image object and load SVG
    const img = new Image();
    img.onload = () => {
      // Create canvas
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      // Fill background
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw SVG
      ctx.drawImage(img, 0, 0);
      
      // Download
      const link = document.createElement('a');
      const method = selectedMethod.value;
      const iterations = selectedIterations.value;
      link.download = `mds-${plotType}-${method}-iter${iterations}-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      
      // Cleanup
      URL.revokeObjectURL(svgUrl);
    };
    
    img.onerror = () => {
      console.error('Failed to convert SVG');
      alert('Failed to download plot');
      URL.revokeObjectURL(svgUrl);
    };
    
    img.src = svgUrl;
  } catch (error) {
    console.error('Failed to generate plot image:', error);
    alert('Failed to download plot');
  }
}

onMounted(() => {
  generateNetworks();
});
</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

.network-demo {
  padding: 2vh;
}

.demo-controls {
  display: flex;
  gap: clamp(1rem, 2vw, 1.5rem);
  margin-bottom: clamp(1.5rem, 3vh, 2rem);
  flex-wrap: wrap;
  align-items: center;
}

.iteration-selector {
  display: flex;
  align-items: center;
  gap: clamp(0.75rem, 1.5vw, 1rem);
  padding: clamp(0.75rem, 1.5vh, 1rem) clamp(1rem, 2vw, 1.25rem);
  background: linear-gradient(135deg, color.adjust($main_1, $alpha: -0.8, $lightness: 20%), color.adjust($main_2, $alpha: -0.8, $lightness: 20%));
  border: 1px solid color.adjust($main_1, $alpha: -0.7);
  border-radius: 0.6vw;
  box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.7);
}

.iteration-selector label {
  font-size: clamp(0.9rem, 1.2vw, 1rem);
  font-weight: 600;
  color: $white;
  text-shadow: 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.5);
}

.iteration-select {
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(0.75rem, 1.5vw, 1rem);
  background: $white;
  border: 2px solid color.adjust($main_1, $alpha: -0.3);
  border-radius: 0.4vw;
  color: $black;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.7);

  &:hover {
    background: color.adjust($white, $lightness: -5%);
    border-color: $main_1;
    box-shadow: 0 0.4vh 1vh color.adjust($main_1, $alpha: -0.5);
  }

  &:focus {
    outline: none;
    background: $white;
    border-color: $main_1;
    box-shadow: 0 0 0 0.2vw color.adjust($main_1, $alpha: -0.6), 0 0.4vh 1vh color.adjust($main_1, $alpha: -0.5);
  }

  option {
    background: $white;
    color: $black;
    font-weight: 500;
  }
}

.control-btn {
  display: flex;
  align-items: center;
  gap: clamp(0.4rem, 0.8vw, 0.6rem);
  padding: clamp(0.75rem, 1.5vh, 1rem) clamp(1.25rem, 2.5vw, 1.75rem);
  background: linear-gradient(135deg, color.adjust($gray, $lightness: 20%) 0%, color.adjust($gray, $lightness: 15%) 100%);
  border: 2px solid color.adjust($white, $alpha: -0.85);
  border-radius: 0.6vw;
  cursor: pointer;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  font-weight: 600;
  color: $white;
  transition: all 0.3s ease;
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.6);

  &:hover {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: color.adjust($main_1, $alpha: -0.3);
    transform: translateY(-0.1vh);
    box-shadow: 0 0.4vh 1vh color.adjust($main_1, $alpha: -0.5);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.6);
  }

  &:disabled {
    background: color.adjust($gray, $lightness: 5%);
    color: color.adjust($white, $alpha: -0.6);
    cursor: not-allowed;
    border-color: color.adjust($white, $alpha: -0.95);
    transform: none;
    box-shadow: none;
  }

  &.primary {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: $main_1;

    &:hover {
      background: linear-gradient(135deg, lighten($main_1, 10%) 0%, lighten($main_2, 10%) 100%);
      box-shadow: 0 0.5vh 1.2vh color.adjust($main_1, $alpha: -0.4);
    }
  }
}

.networks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(clamp(18rem, 30vw, 20rem), 1fr));
  gap: clamp(1rem, 2vw, 1.5rem);
  margin-bottom: clamp(2rem, 4vh, 2.5rem);
}

.network-card {
  background: lighten($gray, 8%);
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.8vw;
  overflow: hidden;
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.5);
}

.network-header {
  padding: clamp(1rem, 2vh, 1.25rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.network-header h3 {
  font-size: clamp(0.9rem, 1.2vw, 1rem);
  font-weight: 600;
  color: $white;
  margin: 0;
}

.network-stats {
  font-size: clamp(0.75rem, 0.9vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.4);
}

.network-viewer-container {
  position: relative;
  overflow: hidden;
  background: white;
}

.computation-results {
  margin-top: clamp(2rem, 4vh, 2.5rem);
}

.iteration-tabs {
  display: flex;
  gap: clamp(0.5rem, 1vw, 0.75rem);
  margin-bottom: clamp(1.5rem, 3vh, 2rem);
  justify-content: center;
  flex-wrap: wrap;
}

.tab-btn {
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(1rem, 2vw, 1.5rem);
  background: color.adjust($gray, $lightness: 10%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  color: color.adjust($white, $alpha: -0.3);
  transition: all 0.3s ease;

  &.active {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: $main_1;
    color: $white;
    box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.5);
  }

  &:hover:not(.active) {
    background: color.adjust($gray, $lightness: 15%);
    border-color: color.adjust($main_1, $alpha: -0.5);
    color: $white;
  }
}

.result-section {
  background: lighten($gray, 8%);
  padding: clamp(1.5rem, 3vh, 2rem);
  border-radius: 0.8vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
  margin-bottom: clamp(1.5rem, 3vh, 2rem);
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.5);
}

.result-section h3 {
  font-size: clamp(1.2rem, 1.6vw, 1.4rem);
  margin-bottom: clamp(1rem, 2vh, 1.25rem);
  color: $white;
  font-weight: 600;
}

.result-section h4 {
  font-size: clamp(1rem, 1.3vw, 1.1rem);
  margin: clamp(1rem, 2vh, 1.25rem) 0 clamp(0.75rem, 1.5vh, 1rem);
  color: color.adjust($white, $alpha: -0.2);
  font-weight: 500;
}

.debug-info {
  background: color.adjust($gray, $lightness: 15%);
  padding: clamp(0.75rem, 1.5vh, 1rem);
  border-radius: 0.6vw;
  margin-bottom: clamp(1rem, 2vh, 1.25rem);
  font-family: monospace;
  font-size: clamp(0.75rem, 0.9vw, 0.8rem);
  border: 1px solid color.adjust($white, $alpha: -0.95);
  box-shadow: inset 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.9);
}

.debug-item {
  margin: clamp(0.3rem, 0.6vh, 0.5rem) 0;
}

.debug-item .label {
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.3);
}

.matrix-container {
  overflow-x: auto;
  margin-bottom: clamp(1.25rem, 2.5vh, 1.5rem);
  border-radius: 0.6vw;
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.7);
}

.data-matrix {
  border-collapse: collapse;
  font-size: clamp(0.75rem, 0.9vw, 0.8rem);
  min-width: 100%;
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.6vw;
  overflow: hidden;
}

.data-matrix th,
.data-matrix td {
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1.2vw, 0.8rem);
  text-align: center;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.data-matrix th {
  background: linear-gradient(135deg, $main_1 0%, color.adjust($main_1, $lightness: 10%) 100%);
  font-weight: 600;
  color: $white;
}

.data-matrix td {
  background: color.adjust($gray, $lightness: 12%);
  font-family: monospace;
  color: $white;
}

.data-matrix td.diagonal {
  background: color.adjust($gray, $lightness: 20%);
  font-weight: 600;
  color: color.adjust($white, $lightness: 10%);
}

.kernel-matrix td {
  color: lighten(#28a745, 20%);
}

.distance-matrix td {
  color: lighten(#dc3545, 15%);
}

.coordinates-table {
  margin-top: 16px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: clamp(0.75rem, 0.9vw, 0.8rem);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.6vw;
  overflow: hidden;
}

.data-table th,
.data-table td {
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1.2vw, 0.8rem);
  text-align: left;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.data-table th {
  background: linear-gradient(135deg, $main_1 0%, color.adjust($main_1, $lightness: 10%) 100%);
  font-weight: 600;
  color: $white;
}

.data-table td {
  background: color.adjust($gray, $lightness: 12%);
  color: $white;
}

.data-table tr:hover td {
  background: color.adjust($main_1, $alpha: -0.8, $lightness: 25%);
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
  gap: clamp(1rem, 2vw, 1.25rem);
  margin-bottom: clamp(1rem, 2vh, 1.25rem);
  padding: clamp(0.75rem, 1.5vh, 1rem);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.6vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
  box-shadow: inset 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.9);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: clamp(1rem, 2vw, 1.25rem);
  height: clamp(1rem, 2vw, 1.25rem);
  border-radius: 0.3vw;
  border: 2px solid color.adjust($white, $alpha: -0.2);
}

.legend-label {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  color: $white;
}

.plots-container {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.plot-wrapper {
  flex: 1;
  min-width: clamp(20rem, 40vw, 25rem);
}

.plot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: clamp(0.6rem, 1.2vh, 0.75rem);
  padding: 0 clamp(0.5rem, 1vw, 0.75rem);
}

.plot-header h4 {
  margin: 0;
  font-size: clamp(0.9rem, 1.2vw, 1rem);
  color: $white;
  font-weight: 600;
}

.plot-header .camera-btn {
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  padding: clamp(0.3rem, 0.6vh, 0.5rem) clamp(0.5rem, 1vw, 0.75rem);
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: $white;
  transition: all 0.3s ease;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.8);

  &:hover {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: color.adjust($main_1, $alpha: -0.3);
    transform: translateY(-0.05vh);
    box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.5);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.6);
  }
}

.scatter-plot,
.circular-plot {
  width: 100%;
  height: auto;
  max-width: clamp(25rem, 50vw, 31.25rem);
  margin: 0 auto;
  display: block;
  background: white;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.6vw;
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.7);
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
  margin: clamp(0.5rem, 1vh, 0.75rem) 0;
  display: flex;
  gap: clamp(0.75rem, 1.5vw, 1rem);
  flex-wrap: wrap;
  padding: clamp(0.75rem, 1.5vh, 1rem);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.6vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.method-selector label {
  display: flex;
  align-items: center;
  gap: clamp(0.3rem, 0.6vw, 0.4rem);
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  color: $white;
}

.method-selector input[type="radio"] {
  accent-color: $main_1;
  transform: scale(1.2);
}

.comparison-results {
  margin: clamp(0.75rem, 1.5vh, 1rem) 0;
  padding: clamp(0.75rem, 1.5vh, 1rem);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.6vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
  box-shadow: inset 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.9);
}

.comparison-results table {
  width: 100%;
  border-collapse: collapse;
  margin-top: clamp(0.5rem, 1vh, 0.75rem);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.6vw;
  overflow: hidden;
}

.comparison-results th,
.comparison-results td {
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1.2vw, 0.8rem);
  text-align: left;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.comparison-results th {
  background: linear-gradient(135deg, $main_1 0%, color.adjust($main_1, $lightness: 10%) 100%);
  font-weight: 600;
  color: $white;
}

.comparison-results td {
  color: $white;
  font-family: monospace;
}

.comparison-results tbody tr:hover td {
  background: color.adjust($main_1, $alpha: -0.8, $lightness: 25%);
}
</style>