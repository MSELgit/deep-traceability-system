<template>
  <div class="mountain-view">
    <!-- 左パネル -->
    <div 
      class="left-panel" 
      :class="{ 
        'open-level-1': leftPanelState === 'level1',
        'open-level-2': leftPanelState === 'level2'
      }"
    >
      
      <DesignCaseForm
        v-if="leftPanelState === 'level2'"
        :design-case="editingCase"
        :performances="leafPerformances"
        @save="handleSave"
        @cancel="closeForm"
      />
      
      <button 
        v-if="leftPanelState === 'closed'"
        class="panel-toggle-btn"
        @click="toggleLeftPanel"
      >
        ☰
      </button>
    </div>

    <!-- 中央: 3D山 -->
    <div class="mountain-canvas" :class="{ 'shrink': leftPanelState !== 'closed' || rightPanelOpen }">
      <div ref="threeContainer" class="three-container"></div>
    </div>

    <!-- 右パネル -->
    <div class="right-panel" :class="{ 'open': rightPanelOpen }">
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useProjectStore } from '../stores/projectStore';
import { storeToRefs } from 'pinia';
import type { DesignCase } from '../types/project';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import DesignCaseList from '../components/mountain/DesignCaseList.vue';
import DesignCaseForm from '../components/mountain/DesignCaseForm.vue';
import DesignCaseDetail from '../components/mountain/DesignCaseDetail.vue';

const projectStore = useProjectStore();
const { designCases, leafPerformances, currentProject } = storeToRefs(projectStore);

// UI状態
const leftPanelState = ref<'closed' | 'level1' | 'level2'>('closed');
const rightPanelOpen = ref(false);
const selectedCase = ref<DesignCase | null>(null);
const editingCase = ref<DesignCase | null>(null);
const sortBy = ref<'height-desc' | 'height-asc' | 'date-desc' | 'date-asc' | 'name'>('height-desc');

// Three.js
const threeContainer = ref<HTMLElement>();
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let controls: OrbitControls;
let mountainMesh: THREE.Mesh;
const casePoints = new Map<string, THREE.Mesh>();

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
  loadAndRenderCases();
});

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
  scene.background = new THREE.Color(0xf0f0f0);

  // カメラ
  camera = new THREE.PerspectiveCamera(
    75,
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

  // ライト
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
  directionalLight.position.set(10, 20, 10);
  scene.add(directionalLight);

  // 半球（円錐）
  const geometry = new THREE.ConeGeometry(10, 15, 32);
  const material = new THREE.MeshPhongMaterial({
    color: 0xcccccc,
    transparent: true,
    opacity: 0.3,
    wireframe: true
  });
  mountainMesh = new THREE.Mesh(geometry, material);
  mountainMesh.position.y = 7.5;
  scene.add(mountainMesh);

  // グリッド
  const gridHelper = new THREE.GridHelper(30, 30);
  scene.add(gridHelper);

  // アニメーションループ
  animate();
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

async function loadAndRenderCases() {
  if (!currentProject.value) return;
  
  await projectStore.loadDesignCases();
  updateMountainView();
}

function updateMountainView() {
  // 既存のポイントを削除
  casePoints.forEach(mesh => scene.remove(mesh));
  casePoints.clear();

  // 各設計案をポイントとして配置
  designCases.value.forEach(designCase => {
    if (!designCase.mountain_position) return;

    const geometry = new THREE.SphereGeometry(0.3, 16, 16);
    const material = new THREE.MeshPhongMaterial({
      color: designCase.color || '#3357FF'
    });
    const mesh = new THREE.Mesh(geometry, material);
    
    mesh.position.set(
      designCase.mountain_position.x,
      designCase.mountain_position.y,
      designCase.mountain_position.z
    );
    
    mesh.userData = { caseId: designCase.id };
    scene.add(mesh);
    casePoints.set(designCase.id, mesh);
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
      const designCase = designCases.value.find(dc => dc.id === caseId);
      if (designCase) {
        handleCaseClick(designCase);
      }
    }
  }

  renderer.domElement.addEventListener('click', onMouseClick);
}

function handleCaseClick(designCase: DesignCase) {
  selectedCase.value = designCase;
  rightPanelOpen.value = true;
  
  // 左パネルが完全展開している場合は50%に縮小
  if (leftPanelState.value === 'level2') {
    leftPanelState.value = 'level1';
  }
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
  
  // 右パネルが開いている場合は閉じるか、50%にする
  if (rightPanelOpen.value) {
    // ここでは閉じずに50%-50%にする
  }
}

function openEditForm(designCase: DesignCase) {
  editingCase.value = designCase;
  leftPanelState.value = 'level2';
}

function closeForm() {
  leftPanelState.value = 'level1';
  editingCase.value = null;
}

async function handleSave(data: any) {
  try {
    if (editingCase.value) {
      await projectStore.updateDesignCase(editingCase.value.id, data);
    } else {
      await projectStore.createDesignCase(data);
    }
    closeForm();
  } catch (error) {
    alert('保存に失敗しました');
  }
}

async function handleCopy(designCase: DesignCase) {
  try {
    await projectStore.copyDesignCase(designCase.id);
  } catch (error) {
    alert('コピーに失敗しました');
  }
}

async function handleDelete(designCase: DesignCase) {
  if (!confirm(`「${designCase.name}」を削除しますか？`)) return;
  
  try {
    await projectStore.deleteDesignCase(designCase.id);
    
    // 右パネルで表示していた場合は閉じる
    if (selectedCase.value?.id === designCase.id) {
      closeRightPanel();
    }
  } catch (error) {
    alert('削除に失敗しました');
  }
}

function handleFocus(designCase: DesignCase) {
  if (!designCase.mountain_position) return;
  
  // カメラをアニメーション
  const targetPos = new THREE.Vector3(
    designCase.mountain_position.x,
    designCase.mountain_position.y,
    designCase.mountain_position.z
  );
  
  // TODO: アニメーション実装
  controls.target.copy(targetPos);
}

function handleSortChange(newSortBy: string) {
  sortBy.value = newSortBy as any;
}

function closeRightPanel() {
  rightPanelOpen.value = false;
  selectedCase.value = null;
}

async function handleColorChange(designCase: DesignCase, color: string) {
  try {
    await projectStore.updateDesignCaseColor(designCase.id, color);
    
    // 3Dシーンの色も更新
    const mesh = casePoints.get(designCase.id);
    if (mesh) {
      (mesh.material as THREE.MeshPhongMaterial).color.set(color);
    }
  } catch (error) {
    alert('色の変更に失敗しました');
  }
}
</script>

<style scoped>
.mountain-view {
  display: flex;
  height: 100vh;
  position: relative;
}

.left-panel {
  width: 15%;
  background: #f5f5f5;
  transition: width 0.3s ease;
  position: relative;
  overflow: hidden;
}

.left-panel.open-level-1 {
  width: 30%;
}

.left-panel.open-level-2 {
  width: 70%;
}

.mountain-canvas {
  flex: 1;
  transition: flex 0.3s ease;
}

.three-container {
  width: 100%;
  height: 100%;
}

.right-panel {
  width: 0;
  background: #fff;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transition: width 0.3s ease;
  overflow: hidden;
}

.right-panel.open {
  width: 30%;
}

.panel-toggle-btn {
  position: absolute;
  top: 20px;
  left: 20px;
  width: 40px;
  height: 40px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.panel-toggle-btn:hover {
  background: #f0f0f0;
}
</style>
