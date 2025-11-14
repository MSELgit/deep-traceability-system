<template>
  <div class="mountain-view">
    <!-- Overlay: Makes background non-clickable when panels are expanded -->
    <div 
      v-if="leftPanelState !== 'closed' || rightPanelOpen"
      class="overlay"
      @click="closeAllPanels"
    ></div>

    <!-- Left Panel -->
    <div 
      class="left-panel" 
      :class="{ 
        'open-level-1': leftPanelState === 'level1',
        'open-level-2': leftPanelState === 'level2'
      }">
      <!-- Preview when closed -->
      <div v-if="leftPanelState === 'closed'" class="panel-preview left">
        <div class="preview-header">
          <div class="preview-title">Design Cases</div>
        </div>
        
        <!-- Peak elevation display -->
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
        
        <!-- Open button (right edge center) -->
        <button class="panel-expand-btn right" @click="toggleLeftPanel">
          <span class="expand-icon">›</span>
        </button>
      </div>

      <!-- Level 1: Design case list -->
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
      
      <!-- Level 2: Create/Edit form -->
      <DesignCaseForm
        v-if="leftPanelState === 'level2'"
        :design-case="editingCase"
        :performances="leafPerformances"
        @save="handleSave"
        @cancel="closeForm"
      />
    </div>

    <!-- Center: 3D Mountain -->
    <div class="mountain-canvas">
      <div ref="threeContainer" class="three-container"></div>
      
      <!-- Camera button for 3D mountain -->
      <button class="mountain-camera-btn" @click="downloadMountainImage" title="Download 3D Mountain">
        <FontAwesomeIcon :icon="['fas', 'camera']" />
      </button>
      
      <!-- Recalculation button -->
      <div class="recalculate-panel">
        <button 
          class="recalculate-btn" 
          @click="handleRecalculate"
          :disabled="isRecalculating"
        >
          <template v-if="isRecalculating">Recalculating...</template>
          <template v-else><FontAwesomeIcon :icon="['fas', 'rotate-right']" /> Recalculate Coordinates</template>
        </button>
        <span v-if="recalculateMessage" class="recalculate-message">{{ recalculateMessage }}</span>
      </div>
    </div>

    <!-- Right Panel -->
    <div class="right-panel" :class="{ 'open': rightPanelOpen }">
      <!-- Preview when closed -->
      <div v-if="!rightPanelOpen" class="panel-preview right">
        <div class="preview-header">
          <div class="preview-title">Details</div>
        </div>
        
        <!-- Open button (left edge center) -->
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

// Props definition
const props = defineProps<{
  isActive?: boolean;
}>();

const projectStore = useProjectStore();
const { currentProject } = storeToRefs(projectStore);

// UI state
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

// Design case list
const designCases = computed(() => {
  const cases = currentProject.value?.design_cases || [];
  return cases;
});

// Sort performances by tree structure (depth-first search)
const sortPerformancesByTree = (performances: ProjectPerformance[]): ProjectPerformance[] => {
  if (!performances || performances.length === 0) return [];
  
  // Create parent-child relationship map
  const childrenMap = new Map<string | null, ProjectPerformance[]>();
  performances.forEach(perf => {
    const parentId = perf.parent_id || null;
    if (!childrenMap.has(parentId)) {
      childrenMap.set(parentId, []);
    }
    childrenMap.get(parentId)!.push(perf);
  });
  
  // Sort each group by name
  childrenMap.forEach((children) => {
    children.sort((a, b) => a.name.localeCompare(b.name));
  });
  
  // Build order with depth-first search
  const result: ProjectPerformance[] = [];
  const traverse = (parentId: string | null) => {
    const children = childrenMap.get(parentId) || [];
    children.forEach(child => {
      result.push(child);
      traverse(child.id);
    });
  };
  
  traverse(null); // Start from root
  return result;
};

// Leaf performance list (tree order)
const leafPerformances = computed(() => {
  const allPerfs = currentProject.value?.performances || [];
  const sorted = sortPerformancesByTree(allPerfs);
  return sorted.filter(p => p.is_leaf);
});

// Sorted design cases
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
  // Automatically loaded and recalculated by watcher, not needed here
});

// Execute recalculation when tab becomes active
watch(() => props.isActive, async (isActive, wasActive) => {
  // When changed from inactive to active
  if (isActive && !wasActive && currentProject.value) {
    await handleRecalculate();
    updateMountainView();
  }
});

// Fetch H_max
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
    console.error('H_max fetch error:', error);
  }
}

// Update H_max when project changes and auto-recalculate if needed
watch(() => currentProject.value?.id, async (newId) => {
  if (!newId) return;
  
  await fetchHMax();
  
  // Check design case coordinates after project load
  await loadAndRenderCases();
  
  // Auto-recalculate if there are design cases without calculated coordinates
  if (designCases.value.length > 0) {
    const hasUnpositionedCases = designCases.value.some(dc => !dc.mountain_position);
    if (hasUnpositionedCases) {
      await handleRecalculate();
    }
  }
}, { immediate: true });

// Download 3D mountain as image
function downloadMountainImage() {
  if (!renderer || !scene || !camera) {
    console.error('3D scene not available');
    return;
  }

  try {
    // Render the current scene
    renderer.render(scene, camera);
    
    // Get the canvas from the renderer
    const canvas = renderer.domElement;
    
    // Create download link
    const link = document.createElement('a');
    link.download = `mountain-3d-${currentProject.value?.name || 'view'}-${new Date().toISOString().slice(0, 10)}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  } catch (error) {
    console.error('Failed to download 3D mountain:', error);
    alert('Failed to download 3D mountain');
  }
}

onUnmounted(() => {
  if (renderer) {
    renderer.dispose();
  }
});

// Redraw when design cases change
watch(designCases, () => {
  updateMountainView();
}, { deep: true });



function initThreeJS() {
  if (!threeContainer.value) return;

  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf5f5f5);

  // Camera
  camera = new THREE.PerspectiveCamera(
    60,
    threeContainer.value.clientWidth / threeContainer.value.clientHeight,
    0.1,
    1000
  );
  camera.position.set(15, 15, 15);

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(threeContainer.value.clientWidth, threeContainer.value.clientHeight);
  threeContainer.value.appendChild(renderer.domElement);

  // Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 5;
  controls.maxDistance = 50;

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
  directionalLight.position.set(10, 20, 10);
  scene.add(directionalLight);

  // Hemispherical mountain
  const geometry = new THREE.SphereGeometry(10, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2);
  const material = new THREE.MeshPhongMaterial({
    color: 0xadff2f,
    transparent: true,
    opacity: 0.2,

    side: THREE.DoubleSide
  });
  mountainMesh = new THREE.Mesh(geometry, material);
  mountainMesh.rotation.x = 0; // Orient hemisphere upward
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

  // Grid
  const gridHelper = new THREE.GridHelper(30, 30, 0xcccccc, 0xeeeeee);
  scene.add(gridHelper);

  // Resize handling
  window.addEventListener('resize', onWindowResize);

  // Animation loop
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

  // Place each design case as a point
  designCases.value.forEach((designCase: DesignCase) => {
    if (!designCase.mountain_position) {
      return;
    }
    
    // Calculate energy (sum of utility_vector values)
    let energy = 0;
    if (designCase.utility_vector) {
      energy = Object.values(designCase.utility_vector).reduce((sum: number, val) => sum + (val as number), 0);
    }
    
    // Determine sphere size based on energy (range 0.2-1.0)
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
  designCases.value.forEach((designCase: DesignCase) => {
    if (!designCase.mountain_position) return;
    
    const y = designCase.mountain_position.y;
    const hemisphereRadius = 10;
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
    circleMesh.rotation.x = -Math.PI / 2; // Place horizontally
    circleMesh.position.set(0, y, 0);
    scene.add(circleMesh);
  });

  
  // Click event
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
  
  // Log the current performance tree
  const currentPerformances = currentProject.value?.performances || [];
  
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
      
      // Zoom camera to new design case
      if (newCase && newCase.mountain_position) {
        setTimeout(() => {
          focusOnPosition(newCase.mountain_position!);
        }, 500);
      }
    }
    closeForm();
  } catch (error) {
    console.error('Save error:', error);
    alert('Failed to save');
  }
}

async function handleCopy(designCase: DesignCase) {
  try {
    const copied = await projectStore.copyDesignCase(designCase.id);

    if (copied && copied.mountain_position) {
      setTimeout(() => {
        focusOnPosition(copied.mountain_position!);
      }, 500);
    }
  } catch (error) {
    console.error('Copy error:', error);
    alert('Failed to copy');
  }
}

async function handleDelete(designCase: DesignCase) {
  if (!confirm(`Delete "${designCase.name}"? This action cannot be undone.`)) return;
  
  try {
    await projectStore.deleteDesignCase(designCase.id);
    
    // Close right panel if it was displaying this case
    if (selectedCase.value?.id === designCase.id) {
      closeRightPanel();
    }
  } catch (error) {
    console.error('Delete error:', error);
    alert('Failed to delete');
  }
}

async function handleRecalculate() {
  if (!currentProject.value) return;
  
  isRecalculating.value = true;
  recalculateMessage.value = '';
  
  try {
    // Collect network information for each design case
    const networks = designCases.value.map(designCase => {
      return {
        nodes: designCase.network?.nodes || [],
        edges: (designCase.network?.edges || []).map(edge => ({
          ...edge,
          weight: edge.weight !== undefined ? edge.weight : 0  // Default to 0 if no weight
        }))
      };
    });
    
    const response = await fetch(
      `http://localhost:8000/api/projects/${currentProject.value.id}/recalculate-mountains`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ networks })  // Send network information
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('Recalculation error details:', errorData);
      throw new Error(errorData.detail || 'Recalculation failed');
    }
    
    const result = await response.json();
    recalculateMessage.value = result.message;
    
    // Save H_max
    if (result.H_max !== undefined) {
      H_max.value = result.H_max;
    }
    
    // Reload project to reflect latest coordinates
    await projectStore.loadProject(currentProject.value.id);
    
    // Verify coordinates after reload
    await loadAndRenderCases();
    
    setTimeout(() => {
      recalculateMessage.value = '';
    }, 3000);
  } catch (error) {
    console.error('Recalculation error:', error);
    recalculateMessage.value = 'Recalculation failed';
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
  
  // Adjust camera position
  const offset = new THREE.Vector3(5, 5, 5);
  camera.position.copy(targetPos).add(offset);
}

function handleSortChange(newSortBy: string) {
  sortBy.value = newSortBy as any;
}

function closeRightPanel() {
  rightPanelOpen.value = false;
  selectedCase.value = null;
}

function closeAllPanels() {
  // Don't close if left panel level 2 (form) is open (prevent accidental closing)
  if (leftPanelState.value === 'level2') {
    return;
  }
  
  leftPanelState.value = 'closed';
  closeRightPanel();
}

async function handleColorChange(designCase: DesignCase, color: string) {
  try {
    await projectStore.updateDesignCaseColor(designCase.id, color);
    
    // Update color in 3D scene
    const mesh = casePoints.get(designCase.id);
    if (mesh) {
      (mesh.material as THREE.MeshPhongMaterial).color.set(color);
      (mesh.material as THREE.MeshPhongMaterial).emissive.set(color);
    }
  } catch (error) {
    console.error('Color change error:', error);
    alert('Failed to change color');
  }
}
</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

// カスタムスクロールバースタイル
@mixin custom-scrollbar {
  &::-webkit-scrollbar {
    width: 0.8vw;
    height: 0.8vw;
  }
  
  &::-webkit-scrollbar-track {
    background: color.adjust($gray, $lightness: 5%);
    border-radius: 0.4vw;
  }
  
  &::-webkit-scrollbar-thumb {
    background: color.adjust($main_1, $alpha: -0.5);
    border-radius: 0.4vw;
    transition: background 0.3s ease;
    
    &:hover {
      background: color.adjust($main_1, $alpha: -0.3);
    }
    
    &:active {
      background: $main_1;
    }
  }
  
  // Firefox
  scrollbar-width: thin;
  scrollbar-color: color.adjust($main_1, $alpha: -0.5) color.adjust($gray, $lightness: 5%);
}

.mountain-view {
  display: flex;
  height: calc(100vh - 200px);
  position: relative;
  background: $black;
}

/* Overlay: Darkens background and restricts interaction when panels are expanded */
.overlay {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 10;
  transition: opacity 0.3s ease;
}

.left-panel {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 15%;
  background: lighten($gray, 8%);
  transition: all 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 11;
}

.left-panel.open-level-1 {
  width: 30%;
  box-shadow: 0 0 2vh color.adjust($black, $alpha: -0.5);
}

.left-panel.open-level-2 {
  width: 50%;
  box-shadow: 0 0 2vh color.adjust($black, $alpha: -0.5);
}

.mountain-canvas {
  position: absolute;
  left: 15%;
  top: 0;
  width: 70%;
  height: 100%;
  background: $black;
}

.mountain-camera-btn {
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
  background: lighten($gray, 8%);
  transition: all 0.3s ease;
  overflow: hidden;
  z-index: 10;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0);

}

.right-panel.open {
  width: 50%;
  transform: translateX(0);
  box-shadow: -0.5vw 0 2vh color.adjust($black, $alpha: -0.5);
}

.panel-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(0.75rem, 1.5vw, 1rem);
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
  gap: 0.5vh;
  margin-bottom: 2vh;
  width: 100%;
}

.preview-icon {
  font-size: clamp(1.8rem, 3vw, 2rem);
  color: color.adjust($white, $alpha: -0.7);
}

.preview-title {
  font-size: clamp(0.7rem, 1vw, 0.8rem);
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.4);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.preview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5vh;
  margin-bottom: 2.5vh;
}

.preview-count {
  font-size: clamp(2rem, 4vw, 2.5rem);
  font-weight: 700;
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
}

.preview-label {
  font-size: clamp(0.65rem, 0.9vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.6);
}

.preview-hint {
  font-size: clamp(0.75rem, 1vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.5);
  text-align: center;
  line-height: 1.4;
}

.preview-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.8vh;
  overflow: hidden;
}

/* Peak elevation display when closed */
.preview-h-max {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(0.75rem, 1.5vw, 1rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  border-radius: 0.5vw;
  margin: 0 0.8vw 1.5vh 0.8vw;
  box-shadow: 0 0.5vh 1.5vh color.adjust($main_1, $alpha: -0.6);
}

.preview-h-max-label {
  font-size: clamp(0.65rem, 0.9vw, 0.75rem);
  font-weight: 600;
  opacity: 0.95;
}

.preview-h-max-value {
  font-size: clamp(1.1rem, 1.8vw, 1.3rem);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  font-size: clamp(0.65rem, 0.9vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.3);
  white-space: nowrap;
  overflow: hidden;
  padding: 0.5vh 0.8vw 0.5vh 0.5vw;
  border-radius: 0.3vw;
  transition: all 0.2s;
  margin-right: 2vw; /* Avoid overlap with expand button */
}

.preview-item:hover {
  background: color.adjust($gray, $lightness: 15%);
  transform: translateX(0.2vw);
}

.color-indicator {
  width: 0.8vw;
  height: 0.8vw;
  min-width: 8px;
  min-height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.preview-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0; /* Enable text truncation in flexbox */
}

.preview-item-height {
  font-size: clamp(0.6rem, 0.8vw, 0.7rem);
  font-weight: 700;
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  flex-shrink: 0;
  min-width: 2.5vw;
  text-align: right;
}

.preview-more {
  font-size: clamp(0.6rem, 0.8vw, 0.7rem);
  color: color.adjust($white, $alpha: -0.6);
  text-align: center;
  padding: 0.5vh;
  font-style: italic;
}

.instruction-icon {
  font-size: clamp(1.5rem, 2.5vw, 2rem);
  color: color.adjust($white, $alpha: -0.5);
  animation: pointDown 1.5s ease-in-out infinite;
}

@keyframes pointDown {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(0.5vh); }
}

.instruction-text {
  font-size: clamp(0.65rem, 0.9vw, 0.75rem);
  color: color.adjust($white, $alpha: -0.5);
  text-align: center;
  line-height: 1.4;
}

/* Panel expand button (right/left edge center) */
.panel-expand-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: clamp(1.8rem, 3vw, 2.2rem);
  height: clamp(4rem, 8vh, 5rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0.5vh 1.5vh color.adjust($main_1, $alpha: -0.6);
  transition: all 0.3s ease;
  z-index: 25;
}

.panel-expand-btn.right {
  right: 0;
  border-radius: 0.8vw 0 0 0.8vw;
}

.panel-expand-btn.left {
  left: -1vw;
  border-radius: 0.8vw 0 0 0.8vw;
}

.panel-expand-btn:hover {
  box-shadow: 0 0.8vh 2.5vh color.adjust($main_1, $alpha: -0.4);
  transform: translateY(-50%) scale(1.05);
}

.panel-expand-btn .expand-icon {
  font-size: clamp(1.2rem, 2vw, 1.5rem);
  font-weight: bold;
  color: $white;
  line-height: 1;
}

.panel-expand-btn:hover .expand-icon {
  animation: slideHint 0.6s ease-in-out infinite;
}

@keyframes slideHint {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(0.3vw); }
}

/* Recalculation panel */
.recalculate-panel {
  position: absolute;
  bottom: 2vh;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 1vw;
  z-index: 8;
}

.recalculate-btn {
  padding: clamp(0.6rem, 1.2vh, 0.8rem) clamp(1rem, 2vw, 1.5rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  border: none;
  border-radius: 0.5vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0.3vh 1vh color.adjust($main_1, $alpha: -0.7);
}

.recalculate-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, lighten($main_1, 10%) 0%, lighten($main_2, 10%) 100%);
  box-shadow: 0 0.5vh 1.5vh color.adjust($main_1, $alpha: -0.5);
  transform: translateY(-0.1vh);
}

.recalculate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.recalculate-message {
  font-size: clamp(0.75rem, 1vw, 0.85rem);
  color: $sub_1;
  background: color.adjust($sub_1, $alpha: -0.9);
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(0.8rem, 1.5vw, 1rem);
  border-radius: 0.4vw;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-0.5vh); }
  to { opacity: 1; transform: translateY(0); }
}

/* Debug display for partial height max values per performance */
.performance-h-max-debug {
  position: absolute;
  bottom: 8vh;
  left: 2vw;
  background: color.adjust($gray, $lightness: 12%);
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.5vw;
  padding: clamp(0.75rem, 1.5vh, 1rem) clamp(1rem, 1.5vw, 1.25rem);
  box-shadow: 0 0.3vh 1vh color.adjust($black, $alpha: -0.5);
  max-width: 20vw;
  z-index: 5;
}

.performance-h-max-debug h4 {
  margin: 0 0 1vh 0;
  font-size: clamp(0.7rem, 1vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.4);
  font-weight: 600;
}

.performance-h-max-list {
  display: flex;
  flex-direction: column;
  gap: 0.5vh;
}

.performance-h-max-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: clamp(0.65rem, 0.9vw, 0.75rem);
  padding: 0.5vh 0.8vw;
  background: color.adjust($black, $alpha: -0.8);
  border-radius: 0.3vw;
}

.performance-h-max-item .perf-name {
  color: color.adjust($white, $alpha: -0.3);
  font-weight: 500;
  flex: 1;
}

.performance-h-max-item .perf-h-max {
  color: $main_2;
  font-weight: 700;
  margin-left: 1vw;
}

/* Debug coordinate display */
.debug-coordinates {
  position: absolute;
  bottom: 2vh;
  left: 50%;
  transform: translateX(-50%);
  background: color.adjust($gray, $lightness: 12%);
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.5vw;
  padding: clamp(0.75rem, 1.5vh, 1rem) clamp(1rem, 1.5vw, 1.25rem);
  max-height: 20vh;
  overflow-y: auto;
  box-shadow: 0 0.3vh 1vh color.adjust($black, $alpha: -0.5);
  min-width: 30vw;
  max-width: 40vw;
  z-index: 5;
}

.debug-coordinates h4 {
  margin: 0 0 1vh 0;
  font-size: clamp(0.75rem, 1vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  padding-bottom: 0.5vh;
}

.debug-coordinates .h-max-info {
  font-size: clamp(0.7rem, 0.95vw, 0.8rem);
  color: $main_2;
  font-weight: 600;
  margin-bottom: 1vh;
  padding: 0.6vh 1vw;
  background: color.adjust($main_1, $alpha: -0.9);
  border-radius: 0.3vw;
  border-left: 0.3vw solid $main_2;
}

.debug-coordinates .performance-headers {
  display: flex;
  gap: 0.4vw;
  margin-bottom: 1vh;
  padding: 0.5vh 0.8vw;
  background: color.adjust($black, $alpha: -0.8);
  border-radius: 0.3vw;
  font-size: clamp(0.6rem, 0.85vw, 0.7rem);
  overflow-x: auto;
}

.debug-coordinates .header-label {
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.3);
  margin-right: 0.4vw;
}

.debug-coordinates .perf-header {
  padding: 0.2vh 0.4vw;
  background: color.adjust($main_1, $alpha: -0.8);
  border-radius: 0.2vw;
  color: $main_2;
  font-weight: 500;
  white-space: nowrap;
}

.debug-coordinates .no-cases {
  color: color.adjust($white, $alpha: -0.6);
  font-size: clamp(0.7rem, 0.95vw, 0.8rem);
  text-align: center;
  padding: 1vh;
}

.debug-coordinates .case-list {
  display: flex;
  flex-direction: column;
  gap: 0.6vh;
}

.debug-coordinates .case-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.8vh;
  border-radius: 0.3vw;
  cursor: pointer;
  transition: all 0.2s;
  font-size: clamp(0.7rem, 0.95vw, 0.8rem);
  gap: 0.4vh;
}

.debug-coordinates .case-item:hover {
  background: color.adjust($gray, $lightness: 15%);
  transform: translateX(0.2vw);
}

.debug-coordinates .case-item.no-position {
  opacity: 0.5;
}

.debug-coordinates .case-name {
  display: flex;
  align-items: center;
  gap: 0.6vw;
  font-weight: 500;
  color: color.adjust($white, $alpha: -0.2);
}

.debug-coordinates .color-dot {
  width: 1vw;
  height: 1vw;
  min-width: 10px;
  min-height: 10px;
  border-radius: 50%;
  border: 1px solid color.adjust($white, $alpha: -0.9);
}

.debug-coordinates .coordinates {
  font-family: 'Courier New', monospace;
  color: color.adjust($white, $alpha: -0.4);
  font-size: clamp(0.65rem, 0.9vw, 0.75rem);
}

.debug-coordinates .performance-values {
  font-family: 'Courier New', monospace;
  color: $sub_3;
  font-size: clamp(0.6rem, 0.85vw, 0.7rem);
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

.debug-coordinates .partial-heights {
  font-family: 'Courier New', monospace;
  color: $main_2;
  font-size: clamp(0.6rem, 0.85vw, 0.7rem);
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}
</style>