<template>
  <div class="network-viewer">
    <!-- メインコンテンツ -->
    <div class="network-viewer-wrapper">
      <!-- プロパティパネル -->
      <div class="properties-panel">
        <div class="panel-header">
          <h3>詳細情報</h3>
        </div>
        
        <div v-if="selectedNode" class="property-section">
          <h4>選択中のノード</h4>
          <div class="property-grid">
            <div class="property-row">
              <label>ラベル</label>
              <input 
                v-if="canEditNodeLabel"
                v-model="nodeEditData.label"
                @keyup.enter="updateNodeWithReset"
                type="text" 
                class="property-input"
                placeholder="ノード名を入力"
              />
              <div 
                v-else 
                class="property-value readonly"
                title="性能ノードは編集できません"
              >
                {{ selectedNode.label }}
                <span class="readonly-hint">(編集不可)</span>
              </div>
            </div>
            <div class="property-row">
              <label>レイヤー</label>
              <div class="property-badge" :style="{ 
                backgroundColor: LAYER_COLORS[selectedNode.layer],
                color: 'white'
              }">
                Layer {{ selectedNode.layer }}
              </div>
            </div>
            <div class="property-row">
              <label>タイプ</label>
              <div class="property-value">{{ selectedNode.type }}</div>
            </div>
          </div>
          
          <div class="coordinate-info">
            <h5>3D座標</h5>
            <div class="coordinate-grid">
              <div class="coordinate-item">
                <span class="coordinate-label">X:</span>
                <span class="coordinate-value">{{ nodeEditData.x3d?.toFixed(2) ?? 'N/A' }}</span>
              </div>
              <div class="coordinate-item">
                <span class="coordinate-label">Y:</span>
                <span class="coordinate-value">{{ nodeEditData.y3d?.toFixed(2) ?? 'N/A' }}</span>
              </div>
            </div>
            
            <!-- 十字キーでの移動コントロール -->
            <div class="movement-controls">
              <h5>ノード移動</h5>
              <div class="directional-pad">
                <button class="direction-btn up" @click="moveNode('up')" title="上に移動">
                  <FontAwesomeIcon :icon="['fas', 'chevron-up']" />
                </button>
                <div class="middle-row">
                  <button class="direction-btn left" @click="moveNode('left')" title="左に移動">
                    <FontAwesomeIcon :icon="['fas', 'chevron-left']" />
                  </button>
                  <div class="center-space"></div>
                  <button class="direction-btn right" @click="moveNode('right')" title="右に移動">
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" />
                  </button>
                </div>
                <button class="direction-btn down" @click="moveNode('down')" title="下に移動">
                  <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
                </button>
              </div>
            </div>
            
            <!-- 更新ボタンを一番下に移動 -->
            <div class="update-buttons">
              <!-- ノードに変更がある場合：更新ボタンとキャンセルボタン -->
              <template v-if="hasNodeChanges">
                <button 
                  class="update-btn primary" 
                  @click="updateNodeWithReset"
                >
                  更新
                </button>
                <button 
                  class="update-btn secondary" 
                  @click="cancelNodeChanges"
                >
                  キャンセル
                </button>
              </template>
              
              <!-- 変更がない場合：削除ボタンとキャンセルボタン -->
              <template v-else>
                <button 
                  class="update-btn danger" 
                  @click="deleteNodeWithConfirm"
                  :disabled="isPerformanceNode(selectedNode)"
                >
                  削除
                </button>
                <button 
                  class="update-btn secondary" 
                  @click="clearSelection"
                >
                  キャンセル
                </button>
              </template>
            </div>
          </div>
        </div>
        
        <div v-else-if="selectedEdge" class="property-section">
          <h4>選択中のエッジ</h4>
          <div class="property-grid">
            <div class="property-row">
              <label>From</label>
              <div class="property-value small">{{ getNodeLabel(selectedEdge.source_id) }}</div>
            </div>
            <div class="property-row">
              <label>To</label>
              <div class="property-value small">{{ getNodeLabel(selectedEdge.target_id) }}</div>
            </div>
            <div class="property-row">
              <label>重み</label>
              <select 
                v-model="edgeEditData.weight"
                class="property-select"
              >
                <option :value="3">3 (強い正の関係)</option>
                <option :value="1">1 (弱い正の関係)</option>
                <option :value="0.33">0.33 (非常に弱い正の関係)</option>
                <option :value="0">0 (無関係)</option>
                <option :value="-0.33">-0.33 (非常に弱い負の関係)</option>
                <option :value="-1">-1 (弱い負の関係)</option>
                <option :value="-3">-3 (強い負の関係)</option>
              </select>
            </div>
            <div class="property-row">
              <div class="update-buttons">
                <!-- エッジに変更がある場合：更新ボタンとキャンセルボタン -->
                <template v-if="edgeEditData.weight !== (selectedEdge.weight || 0)">
                  <button 
                    class="update-btn primary" 
                    @click="updateEdgeWeightWithReset"
                  >
                    更新
                  </button>
                  <button 
                    class="update-btn secondary" 
                    @click="cancelEdgeChanges"
                  >
                    キャンセル
                  </button>
                </template>
                
                <!-- 変更がない場合：削除ボタンとキャンセルボタン -->
                <template v-else>
                  <button 
                    class="update-btn danger" 
                    @click="deleteEdgeWithConfirm"
                  >
                    削除
                  </button>
                  <button 
                    class="update-btn secondary" 
                    @click="clearSelection"
                  >
                    キャンセル
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="selectedCase" class="add-panel">
          <!-- ノード追加セクション -->
          <div class="add-section">
            <h5>ノード追加</h5>
            <div class="add-form">
              <div class="form-group">
                <label>レイヤー:</label>
                <select v-model="newNodeData.layer" class="form-select">
                  <option value="">-- レイヤーを選択 --</option>
                  <option value="2">特性</option>
                  <option value="3">変数</option>
                  <option value="4">モノ・環境</option>
                </select>
              </div>
              <div class="form-group">
                <label>名前:</label>
                <input 
                  v-model="newNodeData.label" 
                  type="text" 
                  class="form-input"
                  placeholder="ノード名を入力"
                  @keyup.enter="addNode"
                />
              </div>
              <button 
                class="add-btn" 
                @click="addNode"
                :disabled="!canAddNode"
              >
                <FontAwesomeIcon :icon="['fas', 'plus']" /> ノード追加
              </button>
            </div>
          </div>
          
          <div class="section-divider"></div>
          
          <!-- エッジ追加セクション -->
          <div class="add-section">
            <h5>エッジ追加</h5>
            <div class="add-form">
              <div class="form-group">
                <label>開始ノード:</label>
                <select v-model="newEdgeData.sourceId" class="form-select">
                  <option value="">-- 開始ノードを選択 --</option>
                  <option 
                    v-for="node in availableNodes" 
                    :key="node.id" 
                    :value="node.id"
                  >
                    {{ node.label }} (Layer {{ node.layer }})
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>終了ノード:</label>
                <select v-model="newEdgeData.targetId" class="form-select">
                  <option value="">-- 終了ノードを選択 --</option>
                  <option 
                    v-for="node in availableNodes" 
                    :key="node.id" 
                    :value="node.id"
                    :disabled="node.id === newEdgeData.sourceId"
                  >
                    {{ node.label }} (Layer {{ node.layer }})
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>重み:</label>
                <select v-model="newEdgeData.weight" class="form-select">
                  <option value="">-- 重みを選択 --</option>
                  <option :value="3">3 (強い正の関係)</option>
                  <option :value="1">1 (弱い正の関係)</option>
                  <option :value="0.33">0.33 (非常に弱い正の関係)</option>
                  <option :value="0">0 (無関係)</option>
                  <option :value="-0.33">-0.33 (非常に弱い負の関係)</option>
                  <option :value="-1">-1 (弱い負の関係)</option>
                  <option :value="-3">-3 (強い負の関係)</option>
                </select>
              </div>
              <button 
                class="add-btn" 
                @click="addEdge"
                :disabled="!canAddEdge"
              >
                <FontAwesomeIcon :icon="['fas', 'plus']" /> エッジ追加
              </button>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-selection">
          <p>設計案を選択してください</p>
        </div>
      </div>

      <!-- 3Dキャンバス -->
      <div class="canvas-container">
        <OPM3DScene
          v-if="selectedCase"
          ref="sceneRef"
          :network="selectedCase.network"
          :visible-layers="visibleLayers"
          :layer-spacing="layerSpacing"
          :layer-colors="LAYER_COLORS"
          :plane-size="planeSize"
          @node-selected="handleNodeSelected"
          @edge-selected="handleEdgeSelected"
        />
        <div v-else class="empty-state">
          <div class="empty-icon">
            <FontAwesomeIcon :icon="['fas', 'hexagon-nodes']" />
          </div>
          <h3>3D Network Viewer</h3>
          <p>設計案を選択して3Dネットワークを表示してください</p>
        </div>
      </div>

      <!-- コントロールパネル -->
      <div class="controls-panel">
        <div class="panel-header">
          <h3>3D表示設定</h3>
        </div>
        
        <div class="controls-section">
          <div class="control-group">
            <label class="control-label">設計案:</label>
            <select v-model="selectedCaseId" class="control-selector">
              <option value="">-- 設計案を選択 --</option>
              <option 
                v-for="designCase in designCases" 
                :key="designCase.id" 
                :value="designCase.id"
              >
                {{ designCase.name }}
              </option>
            </select>
          </div>
          
          <div class="control-group">
            <label class="control-label">表示レイヤー:</label>
            <div class="layer-toggles">
              <button 
                v-for="layer in layers"
                :key="layer.id"
                class="layer-toggle"
                :class="{ active: visibleLayers.includes(layer.id) }"
                @click="toggleLayer(layer.id)"
                :style="{ borderColor: layer.color }"
              >
                {{ layer.label }}
              </button>
            </div>
          </div>
          
          <div class="control-group">
            <label class="control-label">レイヤー間隔:</label>
            <div class="slider-control">
              <input 
                type="range" 
                v-model.number="layerSpacing" 
                min="3" 
                max="15" 
                step="0.5"
                class="control-slider"
              />
              <span class="slider-value">{{ layerSpacing }}</span>
            </div>
          </div>
          
          <div class="control-group">
            <label class="control-label">平面サイズ:</label>
            <div class="slider-control">
              <input 
                type="range" 
                v-model.number="planeSize" 
                :min="planeSizeRange.min" 
                :max="planeSizeRange.max" 
                step="1"
                class="control-slider"
              />
              <span class="slider-value">{{ planeSize }}</span>
            </div>
          </div>
          
          <button class="reset-button" @click="resetView">
            <FontAwesomeIcon :icon="['fas', 'rotate-right']" />
            ビューをリセット
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useProjectStore } from '../../stores/projectStore';
import { storeToRefs } from 'pinia';
import type { NetworkNode, NetworkEdge } from '../../types/project';
import OPM3DScene from './OPM3DScene.vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { networkApi } from '../../utils/api';

const projectStore = useProjectStore();
const { currentProject } = storeToRefs(projectStore);

// レイヤー定義
const layers = [
  { id: 1, label: '性能', color: '#4CAF50' },
  { id: 2, label: '特性', color: '#2196F3' },
  { id: 3, label: '変数', color: '#FFC107' },
  { id: 4, label: 'モノ・環境', color: '#9C27B0' }
];

const LAYER_COLORS: { [key: number]: string } = {
  1: '#4CAF50',
  2: '#2196F3',
  3: '#FFC107',
  4: '#9C27B0'
};

// コンポーネント参照
const sceneRef = ref<InstanceType<typeof OPM3DScene>>();

// 設計案一覧
const designCases = computed(() => currentProject.value?.design_cases || []);

// 選択中の設計案
const selectedCaseId = ref<string>('');
const selectedCase = computed(() => 
  designCases.value.find(dc => dc.id === selectedCaseId.value)
);

// レイヤー表示制御
const visibleLayers = ref<number[]>([1, 2, 3, 4]);

// レイヤー間隔
const layerSpacing = ref<number>(5);

// 平面サイズ制御
const planeSize = ref<number>(30);


// 平面サイズの範囲計算
const planeSizeRange = computed(() => {
  if (!selectedCase.value) {
    return { min: 20, max: 60 };
  }
  
  const nodeCount = selectedCase.value.network.nodes.length;
  const minSize = Math.max(20, Math.ceil(Math.sqrt(nodeCount)) * 4);
  const maxSize = Math.max(minSize + 20, 80);
  
  return { min: minSize, max: maxSize };
});

// 選択中のノード/エッジ
const selectedNode = ref<NetworkNode | null>(null);
const selectedEdge = ref<NetworkEdge | null>(null);

// 編集データ
const nodeEditData = ref<{label: string, x3d: number | null, y3d: number | null}>({label: '', x3d: null, y3d: null});
const edgeEditData = ref<{weight: number}>({weight: 0});

// 新規追加データ
const newNodeData = ref<{layer: string, label: string}>({layer: '', label: ''});
const newEdgeData = ref<{sourceId: string, targetId: string, weight: string}>({sourceId: '', targetId: '', weight: ''});


// 元の座標を保持（比較用）
const originalNodePosition = ref<{x3d: number | null, y3d: number | null}>({x3d: null, y3d: null});

// 性能ノード（レイヤー1）の編集可能性チェック
const canEditNodeLabel = computed(() => {
  if (!selectedNode.value) return false;
  return selectedNode.value.layer !== 1; // 性能ノード（レイヤー1）は編集不可
});

// 編集状態管理
const hasNodeChanges = computed(() => {
  if (!selectedNode.value) return false;
  const labelChanged = canEditNodeLabel.value && nodeEditData.value.label.trim() !== selectedNode.value.label;
  const xChanged = nodeEditData.value.x3d !== null && nodeEditData.value.x3d !== originalNodePosition.value.x3d;
  const yChanged = nodeEditData.value.y3d !== null && nodeEditData.value.y3d !== originalNodePosition.value.y3d;
  return labelChanged || xChanged || yChanged;
});

// 利用可能なノード一覧（エッジ作成用）
const availableNodes = computed(() => {
  return selectedCase.value?.network.nodes || [];
});

// ノード追加の可否
const canAddNode = computed(() => {
  return newNodeData.value.layer && newNodeData.value.label.trim();
});

// エッジ追加の可否
const canAddEdge = computed(() => {
  return newEdgeData.value.sourceId && 
         newEdgeData.value.targetId && 
         newEdgeData.value.sourceId !== newEdgeData.value.targetId &&
         newEdgeData.value.weight !== '';
});

// 設計案変更時の処理
watch(selectedCase, (newCase) => {
  if (newCase) {
    const range = planeSizeRange.value;
    planeSize.value = Math.min(Math.max(planeSize.value, range.min), range.max);
    
    // 保存済みの3D座標を復元
    setTimeout(() => {
      initializeExisting3DPositions();
    }, 100); // 3Dシーンの初期化待ち
  }
});

// レイヤー切り替え
function toggleLayer(layerId: number) {
  const index = visibleLayers.value.indexOf(layerId);
  if (index === -1) {
    visibleLayers.value.push(layerId);
  } else {
    visibleLayers.value.splice(index, 1);
  }
}

// ビューリセット
function resetView() {
  layerSpacing.value = 5;
  visibleLayers.value = [1, 2, 3, 4];
  selectedNode.value = null;
  selectedEdge.value = null;
  const range = planeSizeRange.value;
  planeSize.value = Math.floor((range.min + range.max) / 2);
}

// ノード位置取得
function getNodePosition(nodeId: string) {
  return sceneRef.value?.getNodePosition?.(nodeId) || { x3d: null, y3d: null };
}

// ノードラベル取得
function getNodeLabel(nodeId: string) {
  const node = selectedCase.value?.network.nodes.find(n => n.id === nodeId);
  return node?.label || nodeId;
}


function handleNodeSelected(node: NetworkNode | null) {
  selectedNode.value = node;
  if (node) {
    selectedEdge.value = null;
  }
}

function handleEdgeSelected(edge: NetworkEdge | null) {
  selectedEdge.value = edge;
  if (edge) {
    selectedNode.value = null;
  }
}

// ========== 編集機能 ==========

watch(selectedNode, (node) => {
  if (node) {
    nodeEditData.value.label = node.label;
    const position = getNodePosition(node.id);
    nodeEditData.value.x3d = position.x3d;
    nodeEditData.value.y3d = position.y3d;
    originalNodePosition.value.x3d = position.x3d;
    originalNodePosition.value.y3d = position.y3d;
    selectedEdge.value = null;
  }
});

// エッジ選択時に編集データを初期化
watch(selectedEdge, (edge) => {
  if (edge) {
    edgeEditData.value.weight = edge.weight || 0;
    selectedNode.value = null;
  }
});


// エッジ重み更新
async function updateEdgeWeight() {
  if (!selectedEdge.value || !currentProject.value || !selectedCaseId.value) {
    console.warn('⚠️ Missing required data for edge update');
    return;
  }
  
  const originalWeight = selectedEdge.value.weight || 0;
  
  if (edgeEditData.value.weight === originalWeight) {
    return;
  }
  try {
    await networkApi.updateEdge(
      currentProject.value.id,
      selectedCaseId.value,
      selectedEdge.value.id,
      { weight: edgeEditData.value.weight as NetworkEdge['weight'] }
    );
    if (selectedEdge.value) {
      selectedEdge.value.weight = edgeEditData.value.weight as NetworkEdge['weight'];
    }
  } catch (error) {
    console.error('❌ エッジ重み更新エラー:', error);
    // 元の値に戻す（selectedEdgeがnullでないことを確認）
    if (selectedEdge.value) {
      edgeEditData.value.weight = selectedEdge.value.weight || 0;
    } else {
      edgeEditData.value.weight = originalWeight;
    }
  }
}

// ノード移動（十字キー）
const MOVE_STEP = 2; // 移動ステップ

function moveNode(direction: 'up' | 'down' | 'left' | 'right') {
  if (!selectedNode.value) return;
  
  // 現在の編集中の座標を使用（初期値がない場合は実際の座標を使用）
  let currentX = nodeEditData.value.x3d;
  let currentY = nodeEditData.value.y3d;
  
  if (currentX === null || currentY === null) {
    const position = getNodePosition(selectedNode.value.id);
    currentX = position.x3d ?? 0;
    currentY = position.y3d ?? 0;
  }
  
  // TypeScriptのnullチェックのため明示的に数値型に変換
  const safeCurrentX: number = currentX ?? 0;
  const safeCurrentY: number = currentY ?? 0;
  
  let newX = safeCurrentX;
  let newY = safeCurrentY;
  
  switch (direction) {
    case 'up':
      newY += MOVE_STEP;
      break;
    case 'down':
      newY -= MOVE_STEP;
      break;
    case 'left':
      newX -= MOVE_STEP;
      break;
    case 'right':
      newX += MOVE_STEP;
      break;
  }
  
  nodeEditData.value.x3d = newX;
  nodeEditData.value.y3d = newY;
  sceneRef.value?.updateNodePosition(selectedNode.value.id, newX, newY);
}

// ========== 更新とリセット関数 ==========

// ノード更新（ラベルと座標を統合）
async function updateNodeWithReset() {
  if (!selectedNode.value || !currentProject.value || !selectedCaseId.value) return;
  
  try {
    // ラベルの更新（性能ノード以外）
    if (canEditNodeLabel.value && nodeEditData.value.label.trim() !== selectedNode.value.label) {
      await networkApi.updateNode(
        currentProject.value.id,
        selectedCaseId.value,
        selectedNode.value.id,
        { label: nodeEditData.value.label.trim() }
      );
      
      const newLabel = nodeEditData.value.label.trim();
      selectedNode.value.label = newLabel;
      sceneRef.value?.updateNodeLabel(selectedNode.value.id, newLabel);
    }
    
    // 3D座標の更新
    const xChanged = nodeEditData.value.x3d !== null && nodeEditData.value.x3d !== originalNodePosition.value.x3d;
    const yChanged = nodeEditData.value.y3d !== null && nodeEditData.value.y3d !== originalNodePosition.value.y3d;
    
    if (xChanged || yChanged) {
      await networkApi.updateNode3DPosition(
        currentProject.value.id,
        selectedCaseId.value,
        selectedNode.value.id,
        nodeEditData.value.x3d!,
        nodeEditData.value.y3d!
      );
    }
    
    clearSelection();
    
  } catch (error) {
    console.error('❌ ノード更新エラー:', error);
    // エラー時は元の値に戻す
    if (selectedNode.value) {
      nodeEditData.value.label = selectedNode.value.label;
      nodeEditData.value.x3d = originalNodePosition.value.x3d;
      nodeEditData.value.y3d = originalNodePosition.value.y3d;
      // 3Dシーンの表示も元に戻す
      if (originalNodePosition.value.x3d !== null && originalNodePosition.value.y3d !== null) {
        sceneRef.value?.updateNodePosition(selectedNode.value.id, originalNodePosition.value.x3d, originalNodePosition.value.y3d);
      }
    }
  }
}

// エッジ重み更新（リセット付き）
async function updateEdgeWeightWithReset() {
  await updateEdgeWeight();
  clearSelection();
}

function clearSelection() {
  selectedNode.value = null;
  selectedEdge.value = null;
  nodeEditData.value = { label: '', x3d: null, y3d: null };
  originalNodePosition.value = { x3d: null, y3d: null };
  edgeEditData.value.weight = 0;
  sceneRef.value?.clearHighlight?.();
}

// ========== ノード・エッジ追加機能 ==========

// ノード追加
// ノード追加
async function addNode() {
  if (!canAddNode.value || !currentProject.value || !selectedCaseId.value) {
    return;
  }
  
  try {
    // レイヤーに応じたタイプを決定
    const layerTypeMap: { [key: number]: 'property' | 'variable' | 'object' } = {
      2: 'property',
      3: 'variable',
      4: 'object'
    };
    
    const layer = parseInt(newNodeData.value.layer);
    const nodeData = {
      label: newNodeData.value.label.trim(),
      type: layerTypeMap[layer],
      layer: layer as 1 | 2 | 3 | 4
    };
    const response = await networkApi.createNode(
      currentProject.value.id,
      selectedCaseId.value,
      nodeData
    );
    const newNode = response.data;
    if (selectedCase.value) {
      selectedCase.value.network.nodes = [
        ...selectedCase.value.network.nodes,
        newNode
      ];
      await new Promise(resolve => setTimeout(resolve, 100));
      selectedNode.value = newNode;
      const nodeMesh = sceneRef.value?.nodeMeshes?.get(newNode.id);
      if (nodeMesh) {
        sceneRef.value?.highlightNode?.(nodeMesh);
      } else {
        console.warn('⚠️ ノードメッシュが見つかりません:', newNode.id);
      }
    } else {
      console.warn('⚠️ selectedCase.value が null です');
    }
    
    // フォームをリセット
    newNodeData.value = { layer: '', label: '' };
  } catch (error) {
    console.error('❌ ノード追加エラー:', error);
    console.error('❌ エラー詳細:', JSON.stringify(error, null, 2));
    alert('ノードの追加に失敗しました');
  }
}

// エッジ追加
// エッジ追加
async function addEdge() {
  if (!canAddEdge.value || !currentProject.value || !selectedCaseId.value) {
    return;
  }
  
  try {
    const edgeData = {
      source_id: newEdgeData.value.sourceId,
      target_id: newEdgeData.value.targetId,
      weight: parseFloat(newEdgeData.value.weight) as NetworkEdge['weight']
    };
    const response = await networkApi.createEdge(
      currentProject.value.id,
      selectedCaseId.value,
      edgeData
    );
    const newEdge = response.data;
    if (selectedCase.value) {
      selectedCase.value.network.edges = [
        ...selectedCase.value.network.edges,
        newEdge
      ];
      await new Promise(resolve => setTimeout(resolve, 100));
      selectedEdge.value = newEdge;
      const edgeGroup = sceneRef.value?.edgeLines?.get(newEdge.id);
      if (edgeGroup) {
        sceneRef.value?.highlightEdge?.(edgeGroup);
      } else {
        console.warn('⚠️ エッジグループが見つかりません:', newEdge.id);
      }
    }
    
    // フォームをリセット
    newEdgeData.value = { sourceId: '', targetId: '', weight: '' };
  } catch (error) {
    console.error('❌ エッジ追加エラー:', error);
    console.error('❌ エラー詳細:', JSON.stringify(error, null, 2));
    alert('エッジの追加に失敗しました');
  }
}

// 性能ノードかどうかの判定関数（既存）
function isPerformanceNode(node: NetworkNode | null): boolean {
  if (!node) return false;
  return node.layer === 1 && node.type === 'performance' && !!node.performance_id;
}

// ノード削除（確認ダイアログ付き）
async function deleteNodeWithConfirm() {
  if (!selectedNode.value || !currentProject.value || !selectedCaseId.value) return;
  
  // 性能ノードは削除不可
  if (isPerformanceNode(selectedNode.value)) {
    alert('性能ノードは削除できません');
    return;
  }
  
  if (!confirm(`「${selectedNode.value.label}」を削除しますか？\n関連するエッジも削除されます。`)) {
    return;
  }
  
  try {
    await networkApi.deleteNode(
      currentProject.value.id,
      selectedCaseId.value,
      selectedNode.value.id
    );
    if (selectedCase.value) {
      const nodeId = selectedNode.value.id;
      selectedCase.value.network.nodes = selectedCase.value.network.nodes.filter(
        n => n.id !== nodeId
      );
      selectedCase.value.network.edges = selectedCase.value.network.edges.filter(
        e => e.source_id !== nodeId && e.target_id !== nodeId
      );
    }
    clearSelection();
    
  } catch (error) {
    console.error('❌ ノード削除エラー:', error);
    alert('ノードの削除に失敗しました');
  }
}

async function deleteEdgeWithConfirm() {
  if (!selectedEdge.value || !currentProject.value || !selectedCaseId.value) return;
  
  const sourceNode = selectedCase.value?.network.nodes.find(n => n.id === selectedEdge.value!.source_id);
  const targetNode = selectedCase.value?.network.nodes.find(n => n.id === selectedEdge.value!.target_id);
  const edgeLabel = `${sourceNode?.label || '?'} → ${targetNode?.label || '?'}`;
  
  if (!confirm(`エッジ「${edgeLabel}」を削除しますか？`)) {
    return;
  }
  try {
    await networkApi.deleteEdge(
      currentProject.value.id,
      selectedCaseId.value,
      selectedEdge.value.id
    );
    if (selectedCase.value) {
      selectedCase.value.network.edges = selectedCase.value.network.edges.filter(
        e => e.id !== selectedEdge.value!.id
      );
    }
    clearSelection();
    
  } catch (error) {
    console.error('❌ エッジ削除エラー:', error);
    alert('エッジの削除に失敗しました');
  }
}

function cancelNodeChanges() {
  if (selectedNode.value) {
    nodeEditData.value.label = selectedNode.value.label;
    nodeEditData.value.x3d = originalNodePosition.value.x3d;
    nodeEditData.value.y3d = originalNodePosition.value.y3d;
    if (originalNodePosition.value.x3d !== null && originalNodePosition.value.y3d !== null) {
      sceneRef.value?.updateNodePosition(
        selectedNode.value.id, 
        originalNodePosition.value.x3d, 
        originalNodePosition.value.y3d
      );
    }
  }
}

function cancelEdgeChanges() {
  if (selectedEdge.value) {
    edgeEditData.value.weight = selectedEdge.value.weight || 0;
  }
}

// ========== 初期化とリセット ==========

// ページリロード時に3D座標を保持するための初期化改善
function initializeExisting3DPositions() {
  if (!selectedCase.value) return;
  
  const nodesToRestore: Array<{id: string, label: string, x3d: number, y3d: number}> = [];
  
  selectedCase.value.network.nodes.forEach(node => {
    if ((node as any).x3d !== undefined && (node as any).y3d !== undefined && 
        (node as any).x3d !== null && (node as any).y3d !== null) {
      nodesToRestore.push({
        id: node.id,
        label: node.label,
        x3d: (node as any).x3d,
        y3d: (node as any).y3d
      });
    }
  });
  
  if (nodesToRestore.length > 0) {
    sceneRef.value?.setMultipleNodePositions?.(nodesToRestore);
  }
}


// 設計案変更時の処理
watch(selectedCase, (newCase) => {
  if (newCase) {
    const range = planeSizeRange.value;
    planeSize.value = Math.min(Math.max(planeSize.value, range.min), range.max);
    
    // 保存済みの3D座標を復元
    setTimeout(() => {
      initializeExisting3DPositions();
      
    }, 100); // 3Dシーンの初期化待ち
  }
});

</script>

<style scoped>
/* メインレイアウト */
.network-viewer {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  background: #f5f5f5;
}

/* ツールバー */
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}


/* メインコンテンツエリア */
.network-viewer-wrapper {
  display: flex;
  flex: 1;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}

/* プロパティパネル */
.properties-panel {
  width: 250px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow-y: auto;
  flex-shrink: 0;
}

.panel-header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.property-section {
  padding: 20px;
}

.property-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.property-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.property-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.property-row label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.property-value {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  text-align: right;
  max-width: 150px;
  word-break: break-all;
}

.property-value.small {
  font-size: 11px;
  color: #888;
}

.property-value.readonly {
  background: #f8f8f8;
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  font-size: 12px;
}

.readonly-hint {
  font-size: 10px;
  color: #999;
  margin-left: 8px;
}

.property-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.coordinate-info {
  margin-top: 16px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.coordinate-info h5 {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
}

.coordinate-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.coordinate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.coordinate-label {
  font-size: 12px;
  color: #888;
  font-weight: 500;
}

.coordinate-value {
  font-size: 12px;
  color: #333;
  font-weight: 600;
  font-family: monospace;
}

.empty-selection {
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.empty-selection p {
  margin: 0;
  font-size: 13px;
  color: #999;
}

/* キャンバスエリア */
.canvas-container {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  position: relative;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  text-align: center;
}

.empty-state .empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #666;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* コントロールパネル */
.controls-panel {
  width: 280px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow-y: auto;
  flex-shrink: 0;
}

.controls-section {
  padding: 20px;
}

.control-group {
  margin-bottom: 15px;
}

.control-group:last-child {
  margin-bottom: 0;
}

.control-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.control-selector {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  background: white;
}

.layer-toggles {
  display: flex;
  flex-wrap: wrap;
  flex-direction: column;
  gap: 6px;
}

.layer-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 10px;
  transition: all 0.2s;
  flex: 1;
  min-width: 0;
}

.layer-toggle:hover {
  background: #f5f5f5;
  border-color: #999;
}

.layer-toggle.active {
  background: #E3F2FD;
  border-color: #2196F3;
  color: #2196F3;
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-slider {
  flex: 1;
  min-width: 0;
}

.slider-value {
  min-width: 30px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
}

.reset-button {
  width: 100%;
  padding: 10px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
  margin-top: 12px;
}

.reset-button:hover {
  background: #e3f2fd;
  border-color: #2196F3;
  color: #2196F3;
}

.panel-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 16px 0;
}

/* ========== 編集フォーム ========== */

.property-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  background: white;
  transition: border-color 0.2s;
}

.property-input:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.property-select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  background: white;
  cursor: pointer;
}

.property-select:focus {
  outline: none;
  border-color: #2196F3;
}

/* ========== 十字キーコントロール ========== */

.movement-controls {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.movement-controls h5 {
  margin: 0 0 12px 0;
  font-size: 12px;
  font-weight: 600;
  color: #555;
}

.directional-pad {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.direction-btn {
  width: 32px;
  height: 32px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.direction-btn:hover {
  background: #e3f2fd;
  border-color: #2196F3;
  color: #2196F3;
}

.direction-btn:active {
  background: #bbdefb;
  transform: scale(0.95);
}

.middle-row {
  display: flex;
  gap: 4px;
  align-items: center;
}

.center-space {
  width: 32px;
  height: 32px;
}

/* ========== 更新ボタン ========== */

.update-buttons {
  display: flex;
  gap: 8px;
  width: 100%;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.update-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
}

.update-btn.primary {
  background: #2196F3;
  color: white;
}

.update-btn.primary:hover:not(:disabled) {
  background: #1976D2;
}

.update-btn.primary:disabled {
  background: #ccc;
  color: #888;
  cursor: not-allowed;
}

.update-btn.secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
}

.update-btn.secondary:hover {
  background: #eeeeee;
  border-color: #999;
}

/* ========== ノード・エッジ追加パネル ========== */

.add-panel {
  padding: 16px;
}

.add-panel .panel-header h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.add-section h5 {
  margin: 0 0 6px 0;
  font-size: 13px;
  font-weight: 600;
  color: #555;
  display: flex;
  align-items: center;
}

.section-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 12px 0;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.form-select,
.form-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  background: white;
  transition: border-color 0.2s;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.form-select option:disabled {
  color: #ccc;
}

.add-btn {
  padding: 8px 12px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
  margin-top: 8px;
}

.add-btn:hover:not(:disabled) {
  background: #45a049;
}

.add-btn:disabled {
  background: #ccc;
  color: #888;
  cursor: not-allowed;
}

.update-btn.danger {
  background: #f44336;
  color: white;
  border-color: #f44336;
}

.update-btn.danger:hover:not(:disabled) {
  background: #d32f2f;
  border-color: #d32f2f;
}

.update-btn.danger:disabled {
  background: #ccc;
  color: #888;
  cursor: not-allowed;
}
</style>