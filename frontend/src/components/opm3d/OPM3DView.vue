<template>
  <div class="network-viewer">
    <div class="network-viewer-wrapper">
      <div class="properties-panel">
        <div class="panel-header">
          <h3>Details</h3>
        </div>
        
        <div v-if="selectedNode" class="property-section">
          <h4>Selected Node</h4>
          <div class="property-grid">
            <div class="property-row">
              <label>Label</label>
              <input 
                v-if="canEditNodeLabel"
                v-model="nodeEditData.label"
                @keyup.enter="updateNodeWithReset"
                type="text" 
                class="property-input"
                placeholder="Enter node name"
              />
              <div 
                v-else 
                class="property-value readonly"
                title="Performance nodes cannot be edited"
              >
                {{ selectedNode.label }}
                <span class="readonly-hint">(Read-only)</span>
              </div>
            </div>
            <div class="property-row">
              <label>Layer</label>
              <div class="property-badge" :style="{ 
                backgroundColor: LAYER_COLORS[selectedNode.layer],
                color: 'white'
              }">
                Layer {{ selectedNode.layer }}
              </div>
            </div>
            <div class="property-row">
              <label>Type</label>
              <div class="property-value">{{ selectedNode.type }}</div>
            </div>
          </div>
          
          <div class="coordinate-info">
            <h5>3D Coordinates</h5>
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
            
            <div class="movement-controls">
              <h5>Node Movement</h5>
              <div class="directional-pad">
                <button class="direction-btn up" @click="moveNode('up')" title="Move up">
                  <FontAwesomeIcon :icon="['fas', 'chevron-up']" />
                </button>
                <div class="middle-row">
                  <button class="direction-btn left" @click="moveNode('left')" title="Move left">
                    <FontAwesomeIcon :icon="['fas', 'chevron-left']" />
                  </button>
                  <div class="center-space"></div>
                  <button class="direction-btn right" @click="moveNode('right')" title="Move right">
                    <FontAwesomeIcon :icon="['fas', 'chevron-right']" />
                  </button>
                </div>
                <button class="direction-btn down" @click="moveNode('down')" title="Move down">
                  <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
                </button>
              </div>
            </div>
            
            <div class="update-buttons">
              <template v-if="hasNodeChanges">
                <button 
                  class="update-btn primary" 
                  @click="updateNodeWithReset"
                >
                  Update
                </button>
                <button 
                  class="update-btn secondary" 
                  @click="cancelNodeChanges"
                >
                  Cancel
                </button>
              </template>
              
              <template v-else>
                <button 
                  class="update-btn danger" 
                  @click="deleteNodeWithConfirm"
                  :disabled="isPerformanceNode(selectedNode)"
                >
                  Delete
                </button>
                <button 
                  class="update-btn secondary" 
                  @click="clearSelection"
                >
                  Cancel
                </button>
              </template>
            </div>
          </div>
        </div>
        
        <div v-else-if="selectedEdge" class="property-section">
          <h4>Selected Edge</h4>
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
              <select 
                v-model="edgeEditData.weight"
                class="property-select"
              >
                <option :value="3">3 (Strong positive relationship)</option>
                <option :value="1">1 (Weak positive relationship)</option>
                <option :value="0.33">0.33 (Very weak positive relationship)</option>
                <option :value="0">0 (No relationship)</option>
                <option :value="-0.33">-0.33 (Very weak negative relationship)</option>
                <option :value="-1">-1 (Weak negative relationship)</option>
                <option :value="-3">-3 (Strong negative relationship)</option>
              </select>
            </div>
            <div class="property-row">
              <div class="update-buttons">
                <template v-if="edgeEditData.weight !== (selectedEdge.weight || 0)">
                  <button 
                    class="update-btn primary" 
                    @click="updateEdgeWeightWithReset"
                  >
                    Update
                  </button>
                  <button 
                    class="update-btn secondary" 
                    @click="cancelEdgeChanges"
                  >
                    Cancel
                  </button>
                </template>
                
                <template v-else>
                  <button 
                    class="update-btn danger" 
                    @click="deleteEdgeWithConfirm"
                  >
                    Delete
                  </button>
                  <button 
                    class="update-btn secondary" 
                    @click="clearSelection"
                  >
                    Cancel
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="selectedCase" class="add-panel">
          <div class="add-section">
            <h5>Add Node</h5>
            <div class="add-form">
              <div class="form-group">
                <label>Layer:</label>
                <select v-model="newNodeData.layer" class="form-select">
                  <option value="">-- Select Layer --</option>
                  <option value="2">Properties</option>
                  <option value="3">Variables</option>
                  <option value="4">Objects/Environment</option>
                </select>
              </div>
              <div class="form-group">
                <label>Name:</label>
                <input 
                  v-model="newNodeData.label" 
                  type="text" 
                  class="form-input"
                  placeholder="Enter node name"
                  @keyup.enter="addNode"
                />
              </div>
              <button 
                class="add-btn" 
                @click="addNode"
                :disabled="!canAddNode"
              >
                <FontAwesomeIcon :icon="['fas', 'plus']" /> Add Node
              </button>
            </div>
          </div>
          
          <div class="section-divider"></div>
          
          <div class="add-section">
            <h5>Add Edge</h5>
            <div class="add-form">
              <div class="form-group">
                <label>Source Node:</label>
                <select v-model="newEdgeData.sourceId" class="form-select">
                  <option value="">-- Select Source Node --</option>
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
                <label>End Node:</label>
                <select v-model="newEdgeData.targetId" class="form-select">
                  <option value="">-- Select End Node --</option>
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
                <label>Weight:</label>
                <select v-model="newEdgeData.weight" class="form-select">
                  <option value="">-- Select Weight --</option>
                  <option :value="3">3 (Strong positive relationship)</option>
                  <option :value="1">1 (Weak positive relationship)</option>
                  <option :value="0.33">0.33 (Very weak positive relationship)</option>
                  <option :value="0">0 (No relationship)</option>
                  <option :value="-0.33">-0.33 (Very weak negative relationship)</option>
                  <option :value="-1">-1 (Weak negative relationship)</option>
                  <option :value="-3">-3 (Strong negative relationship)</option>
                </select>
              </div>
              <button 
                class="add-btn" 
                @click="addEdge"
                :disabled="!canAddEdge"
              >
                <FontAwesomeIcon :icon="['fas', 'plus']" /> Add Edge
              </button>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-selection">
          <p>Please select a design case</p>
        </div>
      </div>

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
        
        <!-- Camera button for 3D OPM -->
        <button 
          v-if="selectedCase"
          class="opm3d-camera-btn" 
          @click="downloadOPM3DImage" 
          title="Download 3D OPM Network"
        >
          <FontAwesomeIcon :icon="['fas', 'camera']" />
        </button>
        
        <div v-else class="empty-state">
          <div class="empty-icon">
            <FontAwesomeIcon :icon="['fas', 'hexagon-nodes']" />
          </div>
          <h3>3D Network Viewer</h3>
          <p>Select a design case to display the 3D network</p>
        </div>
      </div>

      <div class="controls-panel">
        <div class="panel-header">
          <h3>3D Display Settings</h3>
        </div>
        
        <div class="controls-section">
          <div class="control-group">
            <label class="control-label">Design Case:</label>
            <select v-model="selectedCaseId" class="control-selector">
              <option value="">-- Select Design Case --</option>
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
            <label class="control-label">Visible Layers:</label>
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
            <label class="control-label">Layer Spacing:</label>
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
            <label class="control-label">Plane Size:</label>
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
            Reset View
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

const layers = [
  { id: 1, label: 'Performance', color: '#4CAF50' },
  { id: 2, label: 'Properties', color: '#2196F3' },
  { id: 3, label: 'Variables', color: '#FFC107' },
  { id: 4, label: 'Objects/Environment', color: '#9C27B0' }
];

const LAYER_COLORS: { [key: number]: string } = {
  1: '#4CAF50',
  2: '#2196F3',
  3: '#FFC107',
  4: '#9C27B0'
};

const sceneRef = ref<InstanceType<typeof OPM3DScene>>();

const designCases = computed(() => currentProject.value?.design_cases || []);

const selectedCaseId = ref<string>('');
const selectedCase = computed(() => 
  designCases.value.find(dc => dc.id === selectedCaseId.value)
);

const visibleLayers = ref<number[]>([1, 2, 3, 4]);

const layerSpacing = ref<number>(5);

const planeSize = ref<number>(30);


const planeSizeRange = computed(() => {
  if (!selectedCase.value) {
    return { min: 20, max: 60 };
  }
  
  const nodeCount = selectedCase.value.network.nodes.length;
  const minSize = Math.max(20, Math.ceil(Math.sqrt(nodeCount)) * 4);
  const maxSize = Math.max(minSize + 20, 80);
  
  return { min: minSize, max: maxSize };
});

const selectedNode = ref<NetworkNode | null>(null);
const selectedEdge = ref<NetworkEdge | null>(null);

const nodeEditData = ref<{label: string, x3d: number | null, y3d: number | null}>({label: '', x3d: null, y3d: null});
const edgeEditData = ref<{weight: number}>({weight: 0});

const newNodeData = ref<{layer: string, label: string}>({layer: '', label: ''});
const newEdgeData = ref<{sourceId: string, targetId: string, weight: string}>({sourceId: '', targetId: '', weight: ''});


const originalNodePosition = ref<{x3d: number | null, y3d: number | null}>({x3d: null, y3d: null});

const canEditNodeLabel = computed(() => {
  if (!selectedNode.value) return false;
  return selectedNode.value.layer !== 1;
});

const hasNodeChanges = computed(() => {
  if (!selectedNode.value) return false;
  const labelChanged = canEditNodeLabel.value && nodeEditData.value.label.trim() !== selectedNode.value.label;
  const xChanged = nodeEditData.value.x3d !== null && nodeEditData.value.x3d !== originalNodePosition.value.x3d;
  const yChanged = nodeEditData.value.y3d !== null && nodeEditData.value.y3d !== originalNodePosition.value.y3d;
  return labelChanged || xChanged || yChanged;
});

const availableNodes = computed(() => {
  return selectedCase.value?.network.nodes || [];
});

const canAddNode = computed(() => {
  return newNodeData.value.layer && newNodeData.value.label.trim();
});

const canAddEdge = computed(() => {
  return newEdgeData.value.sourceId && 
         newEdgeData.value.targetId && 
         newEdgeData.value.sourceId !== newEdgeData.value.targetId &&
         newEdgeData.value.weight !== '';
});

watch(selectedCase, (newCase) => {
  if (newCase) {
    const range = planeSizeRange.value;
    planeSize.value = Math.min(Math.max(planeSize.value, range.min), range.max);
    
    setTimeout(() => {
      initializeExisting3DPositions();
    }, 100);
  }
});

function toggleLayer(layerId: number) {
  const index = visibleLayers.value.indexOf(layerId);
  if (index === -1) {
    visibleLayers.value.push(layerId);
  } else {
    visibleLayers.value.splice(index, 1);
  }
}

function resetView() {
  layerSpacing.value = 5;
  visibleLayers.value = [1, 2, 3, 4];
  selectedNode.value = null;
  selectedEdge.value = null;
  const range = planeSizeRange.value;
  planeSize.value = Math.floor((range.min + range.max) / 2);
}

function getNodePosition(nodeId: string) {
  return sceneRef.value?.getNodePosition?.(nodeId) || { x3d: null, y3d: null };
}

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

watch(selectedEdge, (edge) => {
  if (edge) {
    edgeEditData.value.weight = edge.weight || 0;
    selectedNode.value = null;
  }
});


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
    if (selectedEdge.value) {
      edgeEditData.value.weight = selectedEdge.value.weight || 0;
    } else {
      edgeEditData.value.weight = originalWeight;
    }
  }
}

const MOVE_STEP = 2;

function moveNode(direction: 'up' | 'down' | 'left' | 'right') {
  if (!selectedNode.value) return;
  
  let currentX = nodeEditData.value.x3d;
  let currentY = nodeEditData.value.y3d;
  
  if (currentX === null || currentY === null) {
    const position = getNodePosition(selectedNode.value.id);
    currentX = position.x3d ?? 0;
    currentY = position.y3d ?? 0;
  }
  
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

async function updateNodeWithReset() {
  if (!selectedNode.value || !currentProject.value || !selectedCaseId.value) return;
  
  try {
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
    if (selectedNode.value) {
      nodeEditData.value.label = selectedNode.value.label;
      nodeEditData.value.x3d = originalNodePosition.value.x3d;
      nodeEditData.value.y3d = originalNodePosition.value.y3d;
      if (originalNodePosition.value.x3d !== null && originalNodePosition.value.y3d !== null) {
        sceneRef.value?.updateNodePosition(selectedNode.value.id, originalNodePosition.value.x3d, originalNodePosition.value.y3d);
      }
    }
  }
}

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

async function addNode() {
  if (!canAddNode.value || !currentProject.value || !selectedCaseId.value) {
    return;
  }
  
  try {
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
    
    newNodeData.value = { layer: '', label: '' };
  } catch (error) {
    console.error('❌ ノード追加エラー:', error);
    console.error('❌ エラー詳細:', JSON.stringify(error, null, 2));
    alert('ノードの追加に失敗しました');
  }
}

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
    
    newEdgeData.value = { sourceId: '', targetId: '', weight: '' };
  } catch (error) {
    console.error('❌ エッジ追加エラー:', error);
    console.error('❌ エラー詳細:', JSON.stringify(error, null, 2));
    alert('エッジの追加に失敗しました');
  }
}

function isPerformanceNode(node: NetworkNode | null): boolean {
  if (!node) return false;
  return node.layer === 1 && node.type === 'performance' && !!node.performance_id;
}

async function deleteNodeWithConfirm() {
  if (!selectedNode.value || !currentProject.value || !selectedCaseId.value) return;
  
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

function downloadOPM3DImage() {
  if (!sceneRef.value) {
    console.error('3D scene not available');
    return;
  }

  try {
    const sceneComponent = sceneRef.value as any;
    const renderer = sceneComponent.renderer;
    
    if (!renderer || !renderer.domElement) {
      console.error('Renderer or canvas not available');
      return;
    }
    const scene = sceneComponent.scene?.();
    const camera = sceneComponent.camera?.();
    
    if (!scene || !camera) {
      console.error('Scene or camera not available');
      return;
    }
    renderer.render(scene, camera);

    const canvas = renderer.domElement;
    const link = document.createElement('a');
    const caseName = selectedCase.value?.name || 'OPM3D';
    const timestamp = new Date().toISOString().slice(0, 10);
    link.download = `3D-OPM-${caseName}-${timestamp}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    
    console.log('3D OPM image downloaded successfully');
  } catch (error) {
    console.error('Failed to download 3D OPM image:', error);
    alert('Failed to download image');
  }
}

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



</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

.network-viewer {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);

  padding: 2vh;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}


.network-viewer-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.properties-panel {
  width: clamp(200px, 15vw, 250px);
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 1vw 0 0 1vw;
  box-shadow: 0 0.5vh 2vh color.adjust($black, $alpha: -0.5);
  overflow-y: auto;
  flex-shrink: 0;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.panel-header {
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1.25rem, 2.5vw, 1.75rem) clamp(0.75rem, 1.5vh, 1rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
}

.panel-header h3 {
  margin: 0;
  font-size: clamp(0.95rem, 1.2vw, 1.1rem);
  font-weight: 600;
  color: $white;
}

.property-section {
  padding: clamp(1.25rem, 2.5vh, 1.75rem);
}

.property-section h4 {
  margin: 0 0 clamp(1rem, 2vh, 1.5rem) 0;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  font-weight: 600;
  color: $white;
}

.property-grid {
  display: flex;
  flex-direction: column;
  gap: clamp(0.75rem, 1.5vh, 1rem);
}

.property-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: clamp(0.5rem, 1vh, 0.75rem);
}

.property-row label {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: $white;
  font-weight: 500;
  min-width: clamp(60px, 12vw, 80px);
}

.property-value {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: $white;
  font-weight: 500;
  text-align: right;
  max-width: clamp(150px, 30vw, 200px);
  word-break: break-all;
}

.property-value.small {
  font-size: clamp(0.7rem, 0.85vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.3);
}

.property-value.readonly {
  background: color.adjust($gray, $lightness: 5%);
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.5rem, 1vw, 0.7rem);
  border-radius: 0.4vw;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
}

.readonly-hint {
  font-size: clamp(0.65rem, 0.8vw, 0.7rem);
  color: color.adjust($white, $alpha: -0.4);
  margin-left: clamp(0.5rem, 1vw, 0.75rem);
  font-style: italic;
}

.property-badge {
  padding: clamp(0.25rem, 0.5vh, 0.3rem) clamp(0.5rem, 1vw, 0.7rem);
  border-radius: 0.3vw;
  font-size: clamp(0.7rem, 0.85vw, 0.75rem);
  font-weight: 600;
  text-transform: uppercase;
}

.coordinate-info {
  margin-top: clamp(1rem, 2vh, 1.5rem);
  padding: clamp(0.75rem, 1.5vh, 1rem);
  background: color.adjust($gray, $lightness: 5%);
  border-radius: 0.6vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.coordinate-info h5 {
  margin: 0 0 clamp(0.5rem, 1vh, 0.75rem) 0;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  color: $white;
  text-transform: uppercase;
}

.coordinate-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(0.5rem, 1vw, 0.75rem);
  margin-bottom: clamp(0.75rem, 1.5vh, 1rem);
}

.coordinate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1.2vw, 0.8rem);
  background: color.adjust($gray, $lightness: 10%);
  border-radius: 0.4vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.coordinate-label {
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: $white;
  font-weight: 600;
}

.coordinate-value {
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.3);
  font-weight: 600;
  font-family: monospace;
}

.empty-selection {
  padding: clamp(2.5rem, 5vh, 3rem) clamp(1.25rem, 2.5vw, 1.75rem);
  text-align: center;
}

.empty-icon {
  font-size: clamp(1.5rem, 3vw, 2rem);
  margin-bottom: clamp(0.5rem, 1vh, 0.75rem);
  color: color.adjust($white, $alpha: -0.4);
}

.empty-selection p {
  margin: 0;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: color.adjust($white, $alpha: -0.4);
}

.canvas-container {
  flex: 1;
  background: $black;
  box-shadow: 0 0.5vh 2vh color.adjust($black, $alpha: -0.5);
  overflow: hidden;
  position: relative;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: color.adjust($white, $alpha: -0.3);
  text-align: center;
}

.empty-state .empty-icon {
  font-size: clamp(3rem, 5vw, 4rem);
  margin-bottom: clamp(1rem, 2vh, 1.5rem);
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 clamp(0.5rem, 1vh, 0.75rem) 0;
  font-size: clamp(1.2rem, 1.8vw, 1.5rem);
  font-weight: 600;
  color: $white;
}

.empty-state p {
  margin: 0;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
}

.controls-panel {
  width: clamp(200px, 15vw, 250px);
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 0 1vw 1vw 0;
  box-shadow: 0 0.5vh 2vh color.adjust($black, $alpha: -0.5);
  overflow-y: auto;
  flex-shrink: 0;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.controls-section {
  padding: clamp(1.25rem, 2.5vh, 1.75rem);
}

.control-group {
  margin-bottom: clamp(0.95rem, 1.9vh, 1.3rem);
}

.control-group:last-child {
  margin-bottom: 0;
}

.control-label {
  display: block;
  margin-bottom: clamp(0.5rem, 1vh, 0.75rem);
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: $white;
  font-weight: 500;
}

.control-selector {
  width: 100%;
  padding: clamp(0.5rem, 1vh, 0.7rem) clamp(0.75rem, 1.5vw, 1rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  background: color.adjust($gray, $lightness: 15%);
  color: $white;
  transition: all 0.3s ease;

  &:hover {
    background: color.adjust($gray, $lightness: 20%);
    border-color: color.adjust($main_1, $alpha: -0.5);
  }

  &:focus {
    outline: none;
    background: color.adjust($gray, $lightness: 20%);
    border-color: $main_1;
    box-shadow: 0 0 0 0.15vw color.adjust($main_1, $alpha: -0.7);
  }

  option {
    background: color.adjust($gray, $lightness: 15%);
    color: $white;
  }
}

.layer-toggles {
  display: flex;
  flex-wrap: wrap;
  flex-direction: column;
  gap: clamp(0.4rem, 0.8vh, 0.6rem);
}

.layer-toggle {
  display: flex;
  align-items: center;
  gap: clamp(0.4rem, 0.8vw, 0.6rem);
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1.2vw, 0.8rem) clamp(0.4rem, 0.8vh, 0.6rem) clamp(2rem, 4vw, 2.5rem);
  background: color.adjust($black, $lightness: 15%);
  border: 2px solid color.adjust($gray, $lightness: 25%);
  border-radius: 0.4vw;
  cursor: pointer;
  font-size: clamp(0.7rem, 0.85vw, 0.75rem);
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.4);
  transition: all 0.3s ease;
  flex: 1;
  min-width: 0;
  opacity: 0.6;
  transform: scale(0.98);
  position: relative;
  text-decoration: line-through;

  &::before {
    content: '✗';
    position: absolute;
    right: clamp(0.3rem, 0.6vw, 0.4rem);
    top: 50%;
    transform: translateY(-50%);
    font-size: clamp(0.6rem, 0.75vw, 0.7rem);
    font-weight: bold;
    color: color.adjust($white, $alpha: -0.3);
    opacity: 0.7;
  }
}

.layer-toggle:hover {
  background: color.adjust($black, $lightness: 20%);
  border-color: color.adjust($gray, $lightness: 35%);
  opacity: 0.8;
}

.layer-toggle.active {
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  border: 2px solid $white;
  color: $white;
  opacity: 1;
  transform: scale(1);
  text-decoration: none;
  box-shadow: 
    0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.5),
    inset 0 0.1vh 0.2vh rgba(255, 255, 255, 0.3);
  position: relative;

  &::before {
    content: '✓';
    position: absolute;
    right: clamp(0.3rem, 0.6vw, 0.4rem);
    top: 50%;
    transform: translateY(-50%);
    font-size: clamp(0.6rem, 0.75vw, 0.7rem);
    font-weight: bold;
    color: $white;
    opacity: 0.9;
  }

  &:hover {
    background: linear-gradient(135deg, color.adjust($main_1, $lightness: 10%) 0%, color.adjust($main_2, $lightness: 10%) 100%);
    transform: scale(1.02);
    box-shadow: 
      0 0.4vh 1vh color.adjust($main_1, $alpha: -0.4),
      inset 0 0.1vh 0.2vh rgba(255, 255, 255, 0.4);
  }
}

.slider-control {
  display: flex;
  align-items: center;
  gap: clamp(0.5rem, 1vw, 0.75rem);
}

.control-slider {
  flex: 1;
  min-width: 0;
  
  &::-webkit-slider-track {
    background: color.adjust($gray, $lightness: 20%);
    border-radius: 0.2vw;
  }
  
  &::-webkit-slider-thumb {
    background: $main_1;
    border-radius: 50%;
    cursor: pointer;
  }
  
  &::-moz-range-track {
    background: color.adjust($gray, $lightness: 20%);
    border-radius: 0.2vw;
  }
  
  &::-moz-range-thumb {
    background: $main_1;
    border: none;
    border-radius: 50%;
    cursor: pointer;
  }
}

.slider-value {
  min-width: clamp(30px, 6vw, 40px);
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.3);
}

.reset-button {
  width: 100%;
  padding: clamp(0.6rem, 1.2vh, 0.8rem) clamp(0.8rem, 1.6vw, 1rem);
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  color: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(0.4rem, 0.8vw, 0.6rem);
  transition: all 0.3s ease;
  margin-top: clamp(0.75rem, 1.5vh, 1rem);
}

.reset-button:hover {
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  border-color: $main_1;
  transform: translateY(-0.1vh);
  box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.5);
}

.panel-divider {
  height: 1px;
  background: color.adjust($white, $alpha: -0.95);
  margin: clamp(1rem, 2vh, 1.5rem) 0;
}


.property-input {
  width: 100%;
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.5rem, 1vw, 0.7rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  background: color.adjust($gray, $lightness: 15%);
  color: $white;
  transition: all 0.3s ease;
}

.property-input:focus {
  outline: none;
  border-color: $main_1;
  box-shadow: 0 0 0 0.15vw color.adjust($main_1, $alpha: -0.7);
  background: color.adjust($gray, $lightness: 20%);
}

.property-select {
  width: 100%;
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.5rem, 1vw, 0.7rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  background: color.adjust($gray, $lightness: 15%);
  color: $white;
  cursor: pointer;
  transition: all 0.3s ease;

  option {
    background: color.adjust($gray, $lightness: 15%);
    color: $white;
  }
}

.property-select:focus {
  outline: none;
  border-color: $main_1;
  box-shadow: 0 0 0 0.15vw color.adjust($main_1, $alpha: -0.7);
  background: color.adjust($gray, $lightness: 20%);
}


.movement-controls {
  margin-top: clamp(1rem, 2vh, 1.5rem);
  padding-top: clamp(0.75rem, 1.5vh, 1rem);
  border-top: 1px solid color.adjust($white, $alpha: -0.95);
}

.movement-controls h5 {
  margin: 0 0 clamp(0.75rem, 1.5vh, 1rem) 0;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  color: $white;
}

.directional-pad {
  display: grid;
  grid-template-areas:
    ". up ."
    "left center right"
    ". down .";
  grid-template-columns: 1fr 1fr 1fr;
  gap: clamp(0.3rem, 0.6vw, 0.4rem);
  max-width: 120px;
  margin: 0 auto clamp(0.75rem, 1.5vh, 1rem);
}

.direction-btn {
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.3vw;
  padding: clamp(0.4rem, 0.8vh, 0.6rem);
  color: $white;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &.up {
    grid-area: up;
  }

  &.down {
    grid-area: down;
  }

  &.left {
    grid-area: left;
  }

  &.right {
    grid-area: right;
  }

  &:hover {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: $main_1;
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }
}

.middle-row {
  display: contents;
}

.center-space {
  grid-area: center;
}


.update-buttons {
  display: flex;
  gap: clamp(0.5rem, 1vw, 0.75rem);
  width: 100%;
  margin-top: clamp(1rem, 2vh, 1.5rem);
  padding-top: clamp(0.75rem, 1.5vh, 1rem);
  border-top: 1px solid color.adjust($white, $alpha: -0.95);
}

.update-btn {
  flex: 1;
  padding: clamp(0.5rem, 1vh, 0.7rem) clamp(0.75rem, 1.5vw, 1rem);
  border: none;
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(0.4rem, 0.8vw, 0.6rem);
  transition: all 0.3s ease;
}

.update-btn.primary {
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;

  &:hover:not(:disabled) {
    transform: translateY(-0.1vh);
    box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.5);
  }

  &:disabled {
    background: color.adjust($gray, $lightness: 10%);
    color: color.adjust($white, $alpha: -0.5);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
}

.update-btn.secondary {
  background: color.adjust($gray, $lightness: 15%);
  color: $white;
  border: 1px solid color.adjust($white, $alpha: -0.9);

  &:hover {
    background: color.adjust($gray, $lightness: 20%);
    border-color: color.adjust($main_1, $alpha: -0.5);
  }
}

.update-btn.danger {
  background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
  color: $white;

  &:hover:not(:disabled) {
    transform: translateY(-0.1vh);
    box-shadow: 0 0.3vh 0.8vh rgba(211, 47, 47, 0.5);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
}


.add-panel {
  padding: clamp(1rem, 2vh, 1.5rem);
}

.add-panel .panel-header h4 {
  margin: 0 0 clamp(1rem, 2vh, 1.5rem) 0;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  font-weight: 600;
  color: $white;
}

.add-section h5 {
  margin: 0 0 clamp(0.4rem, 0.8vh, 0.6rem) 0;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  color: $white;
  display: flex;
  align-items: center;
}

.section-divider {
  height: 1px;
  background: color.adjust($white, $alpha: -0.95);
  margin: clamp(0.75rem, 1.5vh, 1rem) 0;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: clamp(0.5rem, 1vh, 0.75rem);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: clamp(0.25rem, 0.5vh, 0.4rem);
}

.form-group label {
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: $white;
  font-weight: 500;
}

.form-select,
.form-input {
  width: 100%;
  padding: clamp(0.5rem, 1vh, 0.7rem) clamp(0.6rem, 1.2vw, 0.8rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  background: color.adjust($gray, $lightness: 15%);
  color: $white;
  transition: all 0.3s ease;

  &:hover {
    background: color.adjust($gray, $lightness: 20%);
    border-color: color.adjust($main_1, $alpha: -0.5);
  }

  &:focus {
    outline: none;
    border-color: $main_1;
    box-shadow: 0 0 0 0.15vw color.adjust($main_1, $alpha: -0.7);
    background: color.adjust($gray, $lightness: 20%);
  }

  option {
    background: color.adjust($gray, $lightness: 15%);
    color: $white;

    &:disabled {
      color: color.adjust($white, $alpha: -0.6);
    }
  }
}

.add-btn {
  padding: clamp(0.5rem, 1vh, 0.7rem) clamp(0.75rem, 1.5vw, 1rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  border: none;
  border-radius: 0.4vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(0.4rem, 0.8vw, 0.6rem);
  transition: all 0.3s ease;
  margin-top: clamp(0.5rem, 1vh, 0.75rem);

  &:hover:not(:disabled) {
    transform: translateY(-0.1vh);
    box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.5);
  }

  &:disabled {
    background: color.adjust($gray, $lightness: 10%);
    color: color.adjust($white, $alpha: -0.5);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
}

.opm3d-camera-btn {
  position: absolute;
  top: clamp(1rem, 2vh, 1.25rem);
  right: clamp(1rem, 2vw, 1.25rem);
  background: color.adjust($gray, $lightness: 20%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(0.7rem, 1.2vw, 1rem);
  cursor: pointer;
  font-size: clamp(1rem, 1.3vw, 1.1rem);
  color: $white;
  transition: all 0.3s ease;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.8);
  z-index: 10;

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
}

</style>