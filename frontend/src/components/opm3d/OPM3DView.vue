<template>
  <div class="network-viewer">
    <!-- ツールバー -->
    <div class="toolbar">
      <div class="toolbar-group">
        <label class="tool-label">設計案:</label>
        <select v-model="selectedCaseId" class="case-selector">
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
      
      <div class="tool-divider"></div>
      
      <div class="toolbar-group">
        <button 
          v-for="layer in layers"
          :key="layer.id"
          class="tool-btn layer-btn"
          :class="{ active: visibleLayers.includes(layer.id) }"
          @click="toggleLayer(layer.id)"
        >
          <span 
            class="layer-color-dot" 
            :style="{ backgroundColor: layer.color }"
          ></span>
          {{ layer.label }}
        </button>
      </div>
      
      <div class="tool-divider"></div>
      
      <div class="toolbar-group">
        <label class="tool-label">間隔:</label>
        <div class="zoom-control">
          <input 
            type="range" 
            v-model.number="layerSpacing" 
            min="3" 
            max="15" 
            step="0.5"
            class="zoom-slider"
          />
          <span class="zoom-value">{{ layerSpacing }}</span>
        </div>
      </div>
      
      <div class="tool-divider"></div>
      
      <div class="toolbar-group">
        <label class="tool-label">平面サイズ:</label>
        <div class="zoom-control">
          <input 
            type="range" 
            v-model.number="planeSize" 
            :min="planeSizeRange.min" 
            :max="planeSizeRange.max" 
            step="1"
            class="zoom-slider"
          />
          <span class="zoom-value">{{ planeSize }}</span>
        </div>
      </div>
      
      
      <div class="tool-divider"></div>
      
      <div class="toolbar-group">
        <button class="tool-btn" @click="resetView">
          <span class="tool-icon">
            <FontAwesomeIcon :icon="['fas', 'rotate-right']" />
          </span>
          リセット
        </button>
      </div>
    </div>

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
              <div class="property-value">{{ selectedNode.label }}</div>
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
            <div class="property-row">
              <label>ID</label>
              <div class="property-value small">{{ selectedNode.id }}</div>
            </div>
          </div>
          
          <div class="coordinate-info">
            <h5>3D座標</h5>
            <div class="coordinate-grid">
              <div class="coordinate-item">
                <span class="coordinate-label">X:</span>
                <span class="coordinate-value">{{ getNodePosition(selectedNode.id)?.x3d?.toFixed(2) ?? 'N/A' }}</span>
              </div>
              <div class="coordinate-item">
                <span class="coordinate-label">Y:</span>
                <span class="coordinate-value">{{ getNodePosition(selectedNode.id)?.y3d?.toFixed(2) ?? 'N/A' }}</span>
              </div>
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
              <label>Weight</label>
              <div class="property-value">{{ selectedEdge.weight }}</div>
            </div>
            <div class="property-row">
              <label>ID</label>
              <div class="property-value small">{{ selectedEdge.id }}</div>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-selection">
          <div class="empty-icon">
            <FontAwesomeIcon :icon="['fas', 'arrow-pointer']" />
          </div>
          <p>ノードまたはエッジを選択してください</p>
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

      <!-- レイヤー凡例 -->
      <div class="layer-legend">
        <div class="panel-header">
          <h3>レイヤー凡例</h3>
        </div>
        
        <div class="legend-items">
          <div 
            v-for="layer in layers"
            :key="layer.id"
            class="legend-item"
            :class="{ disabled: !visibleLayers.includes(layer.id) }"
          >
            <div 
              class="legend-color"
              :style="{ backgroundColor: layer.color }"
            ></div>
            <div class="legend-info">
              <div class="legend-name">{{ layer.label }}</div>
              <div class="legend-count">
                {{ getLayerNodeCount(layer.id) }} ノード
              </div>
            </div>
          </div>
        </div>
        
        <div class="panel-divider"></div>
        
        <div class="statistics">
          <h4>統計情報</h4>
          <div class="stat-item">
            <span class="stat-label">総ノード数:</span>
            <span class="stat-value">{{ selectedCase?.network.nodes.length || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">総エッジ数:</span>
            <span class="stat-value">{{ selectedCase?.network.edges.length || 0 }}</span>
          </div>
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

// 設計案変更時に平面サイズをリセット
watch(selectedCase, (newCase) => {
  if (newCase) {
    const range = planeSizeRange.value;
    planeSize.value = Math.min(Math.max(planeSize.value, range.min), range.max);
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

// レイヤーのノード数取得
function getLayerNodeCount(layerId: number) {
  if (!selectedCase.value) return 0;
  return selectedCase.value.network.nodes.filter(node => node.layer === layerId).length;
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

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.tool-divider {
  width: 1px;
  height: 24px;
  background: #e0e0e0;
  margin: 0 4px;
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

.tool-btn:hover {
  background: #f5f5f5;
  border-color: #999;
}

.tool-btn.active {
  background: #E3F2FD;
  border-color: #2196F3;
  color: #2196F3;
}

.layer-btn {
  white-space: nowrap;
}

.layer-color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.2);
}

.case-selector {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  min-width: 200px;
}

.zoom-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zoom-slider {
  width: 100px;
}

.zoom-value {
  min-width: 25px;
  font-size: 13px;
  font-weight: 600;
  color: #666;
}

.tool-icon {
  display: flex;
  align-items: center;
  font-size: 14px;
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

/* レイヤー凡例 */
.layer-legend {
  width: 250px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow-y: auto;
  flex-shrink: 0;
}

.legend-items {
  padding: 0 20px 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  transition: opacity 0.2s;
}

.legend-item.disabled {
  opacity: 0.4;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid rgba(0,0,0,0.1);
  flex-shrink: 0;
}

.legend-info {
  flex: 1;
}

.legend-name {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}

.legend-count {
  font-size: 11px;
  color: #888;
}

.panel-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 16px 0;
}

.statistics {
  padding: 0 20px 20px;
}

.statistics h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 13px;
  color: #666;
}

.stat-value {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  font-family: monospace;
}
</style>