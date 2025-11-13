<template>
  <div class="mountain-view">
    <!-- オーバーレイ: パネル展開時に背景をクリック不可にする -->
    <div 
      v-if="leftPanelState !== 'closed' || rightPanelOpen"
      class="overlay"
      @click="closeAllPanels"
    ></div>

    <!-- 左パネル -->
    <div 
      class="left-panel" 
      :class="{ 
        'open-level-1': leftPanelState === 'level1',
        'open-level-2': leftPanelState === 'level2'
      }">
      <!-- 閉じている時のプレビュー -->
      <div v-if="leftPanelState === 'closed'" class="panel-preview left">
        <div class="preview-header">
          <div class="preview-title">設計案</div>
        </div>
        
        <!-- 頂点標高表示 -->
        <div v-if="H_max !== null" class="preview-h-max">
          <span class="preview-h-max-label">H<sub>max</sub>:</span>
          <span class="preview-h-max-value">{{ H_max.toFixed(1) }}</span>
        </div>
        
        
        <div class="preview-list">
          <div 
            v-for="(designCase, index) in sortedDesignCases.slice(0, 5)" 
            :key="designCase.id"
            class="preview-item"
          >
            <span class="color-indicator" :style="{ background: designCase.color }"></span>
            <span class="preview-item-name">{{ designCase.name }}</span>
            <span v-if="designCase.mountain_position" class="preview-item-height">
              {{ designCase.mountain_position.H.toFixed(1) }}
            </span>
          </div>
          <div v-if="sortedDesignCases.length > 5" class="preview-more">
            +{{ sortedDesignCases.length - 5 }} more
          </div>
        </div>
        
        <!-- 開くボタン（右端中央） -->
        <button class="panel-expand-btn right" @click="toggleLeftPanel">
          <span class="expand-icon">›</span>
        </button>
      </div>

      <!-- レベル1: 設計案一覧 -->
      <DesignCaseList
        v-if="leftPanelState === 'level1'"
        :design-cases="sortedDesignCases"
        :sort-by="sortBy"
        :h-max="H_max"
        @toggle-panel="toggleLeftPanel"
        @create="openCreateForm"
        @edit="openEditForm"
        @copy="handleCopy"
        @delete="handleDelete"
        @focus="handleFocus"
        @sort-change="handleSortChange"
      />
      
      <!-- レベル2: 作成・編集フォーム -->
      <DesignCaseForm
        v-if="leftPanelState === 'level2'"
        :design-case="editingCase"
        :performances="leafPerformances"
        @save="handleSave"
        @cancel="closeForm"
      />
    </div>

    <!-- 中央: 3D山 -->
    <div class="mountain-canvas">
      <div ref="threeContainer" class="three-container"></div>
      
      <!-- 再計算ボタン -->
      <div class="recalculate-panel">
        <button 
          class="recalculate-btn" 
          @click="handleRecalculate"
          :disabled="isRecalculating"
        >
          <template v-if="isRecalculating">再計算中...</template>
          <template v-else><FontAwesomeIcon :icon="['fas', 'rotate-right']" /> 座標を再計算</template>
        </button>
        <span v-if="recalculateMessage" class="recalculate-message">{{ recalculateMessage }}</span>
      </div>
    </div>

    <!-- 右パネル -->
    <div class="right-panel" :class="{ 'open': rightPanelOpen }">
      <!-- 閉じている時のプレビュー -->
      <div v-if="!rightPanelOpen" class="panel-preview right">
        <div class="preview-header">
          <div class="preview-title">詳細</div>
        </div>
        
        <!-- 開くボタン（左端中央） -->
        <button 
          v-if="selectedCase"
          class="panel-expand-btn left" 
          @click="rightPanelOpen = true"
        >
          <span class="expand-icon">‹</span>
        </button>
      </div>

      <DesignCaseDetail
        v-if="selectedCase && rightPanelOpen"
        :design-case="selectedCase"
        :performances="leafPerformances"
        :performance-h-max="performance_h_max"
        @close="closeRightPanel"
        @edit="openEditForm"
        @copy="handleCopy"
        @delete="handleDelete"
        @color-change="handleColorChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useProjectStore } from '../../stores/projectStore';
import { storeToRefs } from 'pinia';
import type { DesignCase, DesignCaseCreate, Performance as ProjectPerformance } from '../../types/project';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import DesignCaseList from './DesignCaseList.vue';
import DesignCaseForm from './DesignCaseForm.vue';
import DesignCaseDetail from './DesignCaseDetail.vue';

// プロップ定義
const props = defineProps<{
  isActive?: boolean;
}>();

const route = useRoute();
const projectStore = useProjectStore();
const { currentProject } = storeToRefs(projectStore);

// UI状態
const leftPanelState = ref<'closed' | 'level1' | 'level2'>('closed');
const rightPanelOpen = ref(false);
const selectedCase = ref<DesignCase | null>(null);
const editingCase = ref<DesignCase | null>(null);
const sortBy = ref<'height-desc' | 'height-asc' | 'date-desc' | 'date-asc' | 'name'>('height-desc');
const isRecalculating = ref(false);
const recalculateMessage = ref('');
const H_max = ref<number | null>(null);
const performance_h_max = ref<{ [key: string]: number }>({});

// Three.js
const threeContainer = ref<HTMLElement>();
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let controls: OrbitControls;
let mountainMesh: THREE.Mesh;
const casePoints = new Map<string, THREE.Mesh>();

// 設計案一覧
const designCases = computed(() => {
  const cases = currentProject.value?.design_cases || [];
  return cases;
});

// ツリー構造の順序で性能をソート（深さ優先探索）
const sortPerformancesByTree = (performances: ProjectPerformance[]): ProjectPerformance[] => {
  if (!performances || performances.length === 0) return [];
  
  // 親子関係のマップを作成
  const childrenMap = new Map<string | null, ProjectPerformance[]>();
  performances.forEach(perf => {
    const parentId = perf.parent_id || null;
    if (!childrenMap.has(parentId)) {
      childrenMap.set(parentId, []);
    }
    childrenMap.get(parentId)!.push(perf);
  });
  
  // 各グループを名前順にソート
  childrenMap.forEach((children) => {
    children.sort((a, b) => a.name.localeCompare(b.name));
  });
  
  // 深さ優先探索で順序を構築
  const result: ProjectPerformance[] = [];
  const traverse = (parentId: string | null) => {
    const children = childrenMap.get(parentId) || [];
    children.forEach(child => {
      result.push(child);
      traverse(child.id);
    });
  };
  
  traverse(null); // ルートから開始
  return result;
};

// 末端性能一覧（ツリー順）
const leafPerformances = computed(() => {
  const allPerfs = currentProject.value?.performances || [];
  const sorted = sortPerformancesByTree(allPerfs);
  return sorted.filter(p => p.is_leaf);
});

// ソート済み設計案
const sortedDesignCases = computed(() => {
  const cases = [...designCases.value];
  
  switch (sortBy.value) {
    case 'height-desc':
      return cases.sort((a, b) => (b.mountain_position?.H || 0) - (a.mountain_position?.H || 0));
    case 'height-asc':
      return cases.sort((a, b) => (a.mountain_position?.H || 0) - (b.mountain_position?.H || 0));
    case 'date-desc':
      return cases.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    case 'date-asc':
      return cases.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    case 'name':
      return cases.sort((a, b) => a.name.localeCompare(b.name));
    default:
      return cases;
  }
});

onMounted(() => {
  initThreeJS();
  // watcherで自動的にロード・再計算されるため、ここでは不要
});

// タブがアクティブになったときに再計算を実行
watch(() => props.isActive, async (isActive, wasActive) => {
  // 非アクティブ → アクティブに変わったとき
  if (isActive && !wasActive && currentProject.value) {
    await handleRecalculate();
    updateMountainView();
  }
});

// H_maxを取得
async function fetchHMax() {
  if (!currentProject.value) return;
  
  try {
    const response = await fetch(
      `http://localhost:8000/api/projects/${currentProject.value.id}/h-max`
    );
    
    if (response.ok) {
      const data = await response.json();
      H_max.value = data.H_max;
      performance_h_max.value = data.performance_h_max || {};
    }
  } catch (error) {
    console.error('H_max取得エラー:', error);
  }
}

// プロジェクトが変更されたらH_maxを更新し、必要なら自動再計算
watch(() => currentProject.value?.id, async (newId) => {
  if (!newId) return;
  
  await fetchHMax();
  
  // プロジェクトロード後、設計案の座標チェック
  await loadAndRenderCases();
  
  // 座標未計算の設計案があれば自動再計算
  if (designCases.value.length > 0) {
    const hasUnpositionedCases = designCases.value.some(dc => !dc.mountain_position);
    if (hasUnpositionedCases) {
      await handleRecalculate();
    }
  }
}, { immediate: true });

onUnmounted(() => {
  if (renderer) {
    renderer.dispose();
  }
});

// 設計案が変更されたら再描画
watch(designCases, () => {
  updateMountainView();
}, { deep: true });



function initThreeJS() {
  if (!threeContainer.value) return;

  // シーン
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf5f5f5);

  // カメラ
  camera = new THREE.PerspectiveCamera(
    60,
    threeContainer.value.clientWidth / threeContainer.value.clientHeight,
    0.1,
    1000
  );
  camera.position.set(15, 15, 15);

  // レンダラー
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(threeContainer.value.clientWidth, threeContainer.value.clientHeight);
  threeContainer.value.appendChild(renderer.domElement);

  // コントロール
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 5;
  controls.maxDistance = 50;

  // ライト
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
  directionalLight.position.set(10, 20, 10);
  scene.add(directionalLight);

  // 半球状の山
  const geometry = new THREE.SphereGeometry(10, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2);
  const material = new THREE.MeshPhongMaterial({
    color: 0xadff2f,
    transparent: true,
    opacity: 0.2,

    side: THREE.DoubleSide
  });
  mountainMesh = new THREE.Mesh(geometry, material);
  mountainMesh.rotation.x = 0; // 半球を上向きに
  scene.add(mountainMesh);
  const peakGeometry = new THREE.SphereGeometry(0.3, 16, 16);
  const peakMaterial = new THREE.MeshPhongMaterial({
    color: 0xff4444,
    emissive: 0xff0000,
    emissiveIntensity: 0.3
  });
  const peakPoint = new THREE.Mesh(peakGeometry, peakMaterial);
  peakPoint.position.set(0, 10, 0);
  scene.add(peakPoint);

  // グリッド
  const gridHelper = new THREE.GridHelper(30, 30, 0xcccccc, 0xeeeeee);
  scene.add(gridHelper);

  // リサイズ対応
  window.addEventListener('resize', onWindowResize);

  // アニメーションループ
  animate();
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

function onWindowResize() {
  if (!threeContainer.value) return;
  
  camera.aspect = threeContainer.value.clientWidth / threeContainer.value.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(threeContainer.value.clientWidth, threeContainer.value.clientHeight);
}

async function loadAndRenderCases() {
  if (!currentProject.value) return;
  
  await projectStore.loadDesignCases();
  updateMountainView();
}

function updateMountainView() {
  casePoints.forEach(mesh => scene.remove(mesh));
  casePoints.clear();
  const energies = designCases.value
    .filter(dc => dc.mountain_position && dc.utility_vector)
    .map(dc => Object.values(dc.utility_vector!).reduce((sum: number, val) => sum + (val as number), 0));
  
  const minEnergy = Math.min(...energies) || 0;
  const maxEnergy = Math.max(...energies) || 1;
  const energyRange = maxEnergy - minEnergy || 1;

  // 各設計案をポイントとして配置
  designCases.value.forEach((designCase: DesignCase) => {
    if (!designCase.mountain_position) {
      return;
    }
    
    // エネルギーを計算（utility_vectorの合計値）
    let energy = 0;
    if (designCase.utility_vector) {
      energy = Object.values(designCase.utility_vector).reduce((sum: number, val) => sum + (val as number), 0);
    }
    
    // エネルギーに基づいて球体のサイズを決定（0.2〜1.0の範囲）
    const normalizedEnergy = (energy - minEnergy) / energyRange;
    const sphereRadius = 0.35 + normalizedEnergy * 0.4;
    
    const geometry = new THREE.SphereGeometry(sphereRadius, 16, 16);
    const material = new THREE.MeshPhongMaterial({
      color: designCase.color || '#3357FF',
      emissive: designCase.color || '#3357FF',
      emissiveIntensity: 0.2
    });
    const mesh = new THREE.Mesh(geometry, material);
    
    mesh.position.set(
      designCase.mountain_position.x,
      designCase.mountain_position.y,
      designCase.mountain_position.z
    );
    
    mesh.userData = { caseId: designCase.id, energy: energy };
    scene.add(mesh);
    casePoints.set(designCase.id, mesh);
  });
  // 各設計案の高さに半径R ^2 = R_mountain^2 - y^2 となる平面（円）となるレイヤーを配置
  designCases.value.forEach((designCase: DesignCase) => {
    if (!designCase.mountain_position) return;
    
    const y = designCase.mountain_position.y;
    const hemisphereRadius = 10; // 山の半径
    const rSquared = hemisphereRadius ** 2 - y ** 2;
    const r = Math.sqrt(Math.max(0, rSquared));
    
    const circleGeometry = new THREE.CircleGeometry(r, 32);
    const circleMaterial = new THREE.MeshBasicMaterial({
      color: designCase.color || '#3357FF',
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.1
    });
    const circleMesh = new THREE.Mesh(circleGeometry, circleMaterial);
    circleMesh.rotation.x = -Math.PI / 2; // 水平に配置
    circleMesh.position.set(0, y, 0);
    scene.add(circleMesh);
  });

  
  // クリックイベント
  setupClickHandler();
}

function setupClickHandler() {
  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();

  function onMouseClick(event: MouseEvent) {
    if (!threeContainer.value) return;

    const rect = threeContainer.value.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(Array.from(casePoints.values()));

    if (intersects.length > 0) {
      const caseId = intersects[0].object.userData.caseId;
      const designCase = designCases.value.find((dc: DesignCase) => dc.id === caseId);
      if (designCase) {
        handleCaseClick(designCase);
      }
    }
  }

  renderer.domElement.removeEventListener('click', onMouseClick);
  renderer.domElement.addEventListener('click', onMouseClick);
}

function handleCaseClick(designCase: DesignCase) {
  selectedCase.value = designCase;
  rightPanelOpen.value = true;
}

function toggleLeftPanel() {
  if (leftPanelState.value === 'closed') {
    leftPanelState.value = 'level1';
  } else if (leftPanelState.value === 'level1') {
    leftPanelState.value = 'closed';
  } else {
    leftPanelState.value = 'level1';
  }
}

function openCreateForm() {
  editingCase.value = null;
  leftPanelState.value = 'level2';
}

function openEditForm(designCase: DesignCase) {
  editingCase.value = designCase;
  leftPanelState.value = 'level2';
}

function closeForm() {
  leftPanelState.value = 'level1';
  editingCase.value = null;
}

async function handleSave(data: DesignCaseCreate) {
  try {
    if (editingCase.value) {
      await projectStore.updateDesignCase(editingCase.value.id, data);
    } else {
      const newCase = await projectStore.createDesignCase(data);
      
      // 新しい設計案にカメラをズーム
      if (newCase && newCase.mountain_position) {
        setTimeout(() => {
          focusOnPosition(newCase.mountain_position!);
        }, 500);
      }
    }
    closeForm();
  } catch (error) {
    console.error('保存エラー:', error);
    alert('保存に失敗しました');
  }
}

async function handleCopy(designCase: DesignCase) {
  try {
    const copied = await projectStore.copyDesignCase(designCase.id);
    
    // コピーした設計案にズーム
    if (copied && copied.mountain_position) {
      setTimeout(() => {
        focusOnPosition(copied.mountain_position!);
      }, 500);
    }
  } catch (error) {
    console.error('コピーエラー:', error);
    alert('コピーに失敗しました');
  }
}

async function handleDelete(designCase: DesignCase) {
  if (!confirm(`「${designCase.name}」を削除しますか？この操作は取り消せません。`)) return;
  
  try {
    await projectStore.deleteDesignCase(designCase.id);
    
    // 右パネルで表示していた場合は閉じる
    if (selectedCase.value?.id === designCase.id) {
      closeRightPanel();
    }
  } catch (error) {
    console.error('削除エラー:', error);
    alert('削除に失敗しました');
  }
}

async function handleRecalculate() {
  if (!currentProject.value) return;
  
  isRecalculating.value = true;
  recalculateMessage.value = '';
  
  try {
    // 各設計案のネットワーク情報を収集
    const networks = designCases.value.map(designCase => {
      return {
        nodes: designCase.network?.nodes || [],
        edges: (designCase.network?.edges || []).map(edge => ({
          ...edge,
          weight: edge.weight !== undefined ? edge.weight : 0  // weightがない場合は0
        }))
      };
    });
    
    const response = await fetch(
      `http://localhost:8000/api/projects/${currentProject.value.id}/recalculate-mountains`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ networks })  // ネットワーク情報を送信
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('再計算エラー詳細:', errorData);
      throw new Error(errorData.detail || '再計算に失敗しました');
    }
    
    const result = await response.json();
    recalculateMessage.value = result.message;
    
    // H_maxを保存
    if (result.H_max !== undefined) {
      H_max.value = result.H_max;
    }
    
    // プロジェクトを再取得して最新の座標を反映
    await projectStore.loadProject(currentProject.value.id);
    
    // 再取得後の座標を確認
    await loadAndRenderCases();
    
    setTimeout(() => {
      recalculateMessage.value = '';
    }, 3000);
  } catch (error) {
    console.error('再計算エラー:', error);
    recalculateMessage.value = '再計算に失敗しました';
  } finally {
    isRecalculating.value = false;
  }
}

function handleFocus(designCase: DesignCase) {
  if (!designCase.mountain_position) return;
  focusOnPosition(designCase.mountain_position);
}

function focusOnPosition(position: { x: number; y: number; z: number }) {
  const targetPos = new THREE.Vector3(position.x, position.y, position.z);
  controls.target.copy(targetPos);
  
  // カメラ位置も調整
  const offset = new THREE.Vector3(5, 5, 5);
  camera.position.copy(targetPos).add(offset);
}

function handleSortChange(newSortBy: string) {
  sortBy.value = newSortBy as any;
}

function selectCaseFromDebug(designCase: DesignCase) {
  selectedCase.value = designCase;
  rightPanelOpen.value = true;
  
  // 座標がある場合はフォーカスも
  if (designCase.mountain_position) {
    focusOnPosition(designCase.mountain_position);
  }
}

function closeRightPanel() {
  rightPanelOpen.value = false;
  selectedCase.value = null;
}

function closeAllPanels() {
  // 左パネルのレベル2(フォーム)が開いている場合は閉じない(誤操作防止)
  if (leftPanelState.value === 'level2') {
    return;
  }
  
  leftPanelState.value = 'closed';
  closeRightPanel();
}

async function handleColorChange(designCase: DesignCase, color: string) {
  try {
    await projectStore.updateDesignCaseColor(designCase.id, color);
    
    // 3Dシーンの色も更新
    const mesh = casePoints.get(designCase.id);
    if (mesh) {
      (mesh.material as THREE.MeshPhongMaterial).color.set(color);
      (mesh.material as THREE.MeshPhongMaterial).emissive.set(color);
    }
  } catch (error) {
    console.error('色変更エラー:', error);
    alert('色の変更に失敗しました');
  }
}
</script>

<style scoped>
.mountain-view {
  display: flex;
  height: calc(100vh - 200px);
  position: relative;
  background: #fafafa;
}

/* オーバーレイ: パネル展開時に背景を暗くして操作を制限 */
.overlay {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  z-index: 10;
  transition: opacity 0.3s ease;
}

.left-panel {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 15%;
  background: #ffffff;
  border-right: 1px solid #e0e0e0;
  transition: all 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 11;
}

.left-panel.open-level-1 {
  width: 30%;

}

.left-panel.open-level-2 {
  width: 50%;
}

.mountain-canvas {
  position: absolute;
  left: 15%;
  top: 0;
  width: 70%;
  height: 100%;
}

.three-container {
  width: 100%;
  height: 100%;
}

.right-panel {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  width: 15%;
  background: #ffffff;
  border-left: 1px solid #e0e0e0;
  transition: all 0.3s ease;
  overflow: hidden;
  z-index: 10;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0);

}

.right-panel.open {
  width: 50%;
  transform: translateX(0);
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15);
}

/* パネルプレビュー（閉じている時） */
.panel-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  position: relative;
  overflow: hidden;
}

.panel-preview.left {
  align-items: flex-start;
}

.panel-preview.right {
  align-items: flex-end;
}

.preview-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  width: 100%;
}

.preview-icon {
  font-size: 32px;
  filter: grayscale(0.3);
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-bottom: 24px;
}

.preview-count {
  font-size: 36px;
  font-weight: 700;
  color: #3357FF;
  line-height: 1;
}

.preview-label {
  font-size: 11px;
  color: #999;
}

.preview-hint {
  font-size: 13px;
  color: #999;
  text-align: center;
  line-height: 1.4;
}

.preview-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

/* 閉じた状態での頂点標高表示 */
.preview-h-max {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  margin: 0 8px 12px 8px;
}

.preview-h-max-label {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.95;
}

.preview-h-max-value {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  padding: 4px 8px 4px 4px;
  border-radius: 4px;
  transition: background 0.2s;
  margin-right: 24px; /* 開くボタンと被らないように */
}

.preview-item:hover {
  background: #f5f5f5;
}

.color-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.preview-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0; /* flexboxで省略を有効にする */
}

.preview-item-height {
  font-size: 10px;
  font-weight: 700;
  color: #667eea;
  flex-shrink: 0;
  min-width: 30px;
  text-align: right;
}

.preview-more {
  font-size: 10px;
  color: #999;
  text-align: center;
  padding: 4px;
  font-style: italic;
}

.instruction-icon {
  font-size: 28px;
  animation: pointDown 1.5s ease-in-out infinite;
}

@keyframes pointDown {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(5px); }
}

.instruction-text {
  font-size: 11px;
  color: #666;
  text-align: center;
  line-height: 1.4;
}

/* パネル展開ボタン（右端/左端中央） */
.panel-expand-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  z-index: 25;
}

.panel-expand-btn.right {
  right: -0px;
}

.panel-expand-btn.left {
  left: -16px;
  border-radius: 12px 0 0 12px;
}

.panel-expand-btn:hover {
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
  transform: translateY(-50%) scale(1.05);
}

.panel-expand-btn .expand-icon {
  font-size: 24px;
  font-weight: bold;
  color: white;
  line-height: 1;
}

.panel-expand-btn:hover .expand-icon {
  animation: slideHint 0.6s ease-in-out infinite;
}

@keyframes slideHint {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(3px); }
}

/* 再計算パネル */
.recalculate-panel {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 8;
}

.recalculate-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #3357FF 0%, #5577FF 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(51, 87, 255, 0.3);
}

.recalculate-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #2247EE 0%, #4467EE 100%);
  box-shadow: 0 4px 12px rgba(51, 87, 255, 0.4);
  transform: translateY(-1px);
}

.recalculate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.recalculate-message {
  font-size: 13px;
  color: #2d8659;
  background: rgba(45, 134, 89, 0.1);
  padding: 8px 16px;
  border-radius: 6px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 性能ごとの部分標高最大値デバッグ表示 */
.performance-h-max-debug {
  position: absolute;
  bottom: 80px;
  left: 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 300px;
  z-index: 5;
}

.performance-h-max-debug h4 {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #666;
  font-weight: 600;
}

.performance-h-max-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.performance-h-max-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.performance-h-max-item .perf-name {
  color: #333;
  font-weight: 500;
  flex: 1;
}

.performance-h-max-item .perf-h-max {
  color: #667eea;
  font-weight: 700;
  margin-left: 12px;
}

/* デバッグ用座標表示 */
.debug-coordinates {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px 16px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 400px;
  max-width: 600px;
  z-index: 5;
}

.debug-coordinates h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #666;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 6px;
}

.debug-coordinates .h-max-info {
  font-size: 12px;
  color: #2563eb;
  font-weight: 600;
  margin-bottom: 8px;
  padding: 6px 10px;
  background: #eff6ff;
  border-radius: 4px;
  border-left: 3px solid #2563eb;
}

.debug-coordinates .performance-headers {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 10px;
  overflow-x: auto;
}

.debug-coordinates .header-label {
  font-weight: 600;
  color: #333;
  margin-right: 4px;
}

.debug-coordinates .perf-header {
  padding: 2px 4px;
  background: #e3f2fd;
  border-radius: 3px;
  color: #1976d2;
  font-weight: 500;
  white-space: nowrap;
}

.debug-coordinates .no-cases {
  color: #999;
  font-size: 12px;
  text-align: center;
  padding: 8px;
}

.debug-coordinates .case-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.debug-coordinates .case-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 12px;
  gap: 4px;
}

.debug-coordinates .case-item:hover {
  background: #f5f5f5;
}

.debug-coordinates .case-item.no-position {
  opacity: 0.5;
}

.debug-coordinates .case-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.debug-coordinates .color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.debug-coordinates .coordinates {
  font-family: 'Courier New', monospace;
  color: #666;
  font-size: 11px;
}

.debug-coordinates .performance-values {
  font-family: 'Courier New', monospace;
  color: #FF8C00;
  font-size: 10px;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

.debug-coordinates .partial-heights {
  font-family: 'Courier New', monospace;
  color: #3357FF;
  font-size: 10px;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}
</style>