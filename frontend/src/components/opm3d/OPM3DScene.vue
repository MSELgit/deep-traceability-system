<template>
  <div ref="containerRef" class="scene-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { NetworkStructure, NetworkNode, NetworkEdge } from '../../types/project';

const props = defineProps<{
  network: NetworkStructure;
  visibleLayers: number[];
  layerSpacing: number;
  layerColors: { [key: number]: string };
  planeSize?: number;
}>();

const emit = defineEmits<{
  nodeSelected: [node: NetworkNode | null];
  edgeSelected: [edge: NetworkEdge | null];
}>();

const containerRef = ref<HTMLDivElement>();

// Three.js objects
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let controls: OrbitControls;
let raycaster: THREE.Raycaster;
let mouse: THREE.Vector2;

// ノードメッシュのマップ
const nodeMeshes = new Map<string, THREE.Mesh>();
const edgeLines = new Map<string, THREE.Mesh>();

// 3D座標のマップ
const node3DPositions = new Map<string, { x3d: number; y3d: number }>();

// グリッド配置の設定
const GRID_CONFIG = {
  CELL_SIZE: 2,
  DEFAULT_LAYER_Z: {
    1: 15,
    2: 10,
    3: 5,
    4: 0,
  }
};

onMounted(() => {
  initThreeJS();
  initializeNode3DPositions();
  renderNetwork();
  animate();
});

onUnmounted(() => {
  if (renderer) {
    renderer.dispose();
  }
  if (controls) {
    controls.dispose();
  }
});

// ネットワークが変更されたら再描画
watch(() => props.network, () => {
  initializeNode3DPositions();
  renderNetwork();
}, { deep: true });

// レイヤー表示が変更されたら再描画
watch(() => props.visibleLayers, () => {
  renderNetwork();
}, { deep: true });

// レイヤー間隔が変更されたら再描画
watch(() => props.layerSpacing, () => {
  renderNetwork();
});

// 平面サイズが変更されたら再描画
watch(() => props.planeSize, () => {
  renderNetwork();
});

function initThreeJS() {
  if (!containerRef.value) return;

  // シーン
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf5f5f5);

  // カメラ
  const width = containerRef.value.clientWidth;
  const height = containerRef.value.clientHeight;
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
  camera.position.set(20, 20, 20);

  // レンダラー
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  containerRef.value.appendChild(renderer.domElement);

  // コントロール
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  // ライト
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
  directionalLight.position.set(10, 20, 10);
  scene.add(directionalLight);

  // レイキャスター（クリック検出用）
  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();

  // クリックイベント
  renderer.domElement.addEventListener('click', onCanvasClick);

  // リサイズ対応
  window.addEventListener('resize', onWindowResize);
}

function onWindowResize() {
  if (!containerRef.value) return;
  
  const width = containerRef.value.clientWidth;
  const height = containerRef.value.clientHeight;
  
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

/**
 * ノードの3D座標を初期化（グリッドベース配置）
 */
function initializeNode3DPositions() {
  const { nodes } = props.network;
  
  // 既存の座標をクリア（再配置のため）
  node3DPositions.clear();
  
  // レイヤーごとにグループ化
  const layerGroups = new Map<number, NetworkNode[]>();
  for (const node of nodes) {
    if (!layerGroups.has(node.layer)) {
      layerGroups.set(node.layer, []);
    }
    layerGroups.get(node.layer)!.push(node);
  }
  
  // 各レイヤーごとに配置
  for (const [layer, layerNodes] of layerGroups) {
    layoutNodesInLayer(layerNodes);
  }
}

/**
 * レイヤー内のノードをグリッド配置
 */
function layoutNodesInLayer(nodes: NetworkNode[]) {
  const nodeCount = nodes.length;
  
  if (nodeCount === 0) return;
  
  // 平面サイズに基づいて配置エリアを決定
  const planeSize = props.planeSize || 30;
  const usableArea = planeSize * 0.7; // 平面の70%を使用
  const maxRadius = usableArea / 2;
  
  nodes.forEach((node, index) => {
    // 既に3D座標が設定されている場合はスキップ
    if (node3DPositions.has(node.id)) {
      return;
    }
    
    let x3d, y3d;
    let attempts = 0;
    const maxAttempts = 50;
    
    // 重複を避けるポアソンディスク配置的なアプローチ
    do {
      if (nodeCount <= 4) {
        // 少数の場合：円周上に配置
        const angle = (index / nodeCount) * 2 * Math.PI;
        const radius = Math.min(maxRadius * 0.6, 8);
        x3d = Math.cos(angle) * radius;
        y3d = Math.sin(angle) * radius;
      } else if (nodeCount <= 12) {
        // 中程度の場合：同心円状に配置
        const ringSize = Math.ceil(Math.sqrt(nodeCount));
        const ring = Math.floor(index / ringSize);
        const posInRing = index % ringSize;
        const totalInRing = Math.min(ringSize, nodeCount - ring * ringSize);
        
        const radius = (ring + 1) * (maxRadius / Math.ceil(nodeCount / ringSize)) * 0.8;
        const angle = (posInRing / totalInRing) * 2 * Math.PI;
        
        // ランダムノイズを追加
        const noise = radius * 0.3;
        const angleNoise = Math.PI / 6;
        
        x3d = Math.cos(angle + (Math.random() - 0.5) * angleNoise) * 
              (radius + (Math.random() - 0.5) * noise);
        y3d = Math.sin(angle + (Math.random() - 0.5) * angleNoise) * 
              (radius + (Math.random() - 0.5) * noise);
      } else {
        // 多数の場合：ランダムだが均等に分散
        const angle = Math.random() * 2 * Math.PI;
        const radius = Math.sqrt(Math.random()) * maxRadius;
        
        x3d = Math.cos(angle) * radius;
        y3d = Math.sin(angle) * radius;
        
        // 中心付近を避ける
        if (radius < maxRadius * 0.2) {
          const minRadius = maxRadius * 0.2;
          x3d = Math.cos(angle) * minRadius;
          y3d = Math.sin(angle) * minRadius;
        }
      }
      
      attempts++;
    } while (isTooClose(x3d, y3d, node.id) && attempts < maxAttempts);
    
    node3DPositions.set(node.id, { x3d, y3d });
  });
}

// 他のノードと近すぎるかチェック
function isTooClose(x: number, y: number, currentNodeId: string): boolean {
  const minDistance = 3;
  
  for (const [nodeId, position] of node3DPositions) {
    if (nodeId === currentNodeId) continue;
    
    const dx = x - position.x3d;
    const dy = y - position.y3d;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    if (distance < minDistance) {
      return true;
    }
  }
  
  return false;
}

/**
 * ネットワークを描画
 */
function renderNetwork() {
  // 既存のメッシュをクリア
  clearScene();
  
  // レイヤー平面を描画
  renderLayerPlanes();
  
  // エッジを描画
  renderEdges();
  
  // ノードを描画
  renderNodes();
}

function clearScene() {
  // 既存のノード・エッジを削除
  nodeMeshes.forEach(mesh => scene.remove(mesh));
  edgeLines.forEach(edgeMesh => scene.remove(edgeMesh));
  nodeMeshes.clear();
  edgeLines.clear();
  
  // レイヤー平面も削除
  const objectsToRemove = scene.children.filter(
    obj => obj.userData.isLayerPlane || obj.userData.isGridHelper
  );
  objectsToRemove.forEach(obj => scene.remove(obj));
}

/**
 * レイヤー平面を描画
 */
function renderLayerPlanes() {
  const size = props.planeSize || 30;
  
  for (let layer = 1; layer <= 4; layer++) {
    // レイヤーが非表示の場合はスキップ
    if (!props.visibleLayers.includes(layer)) {
      continue;
    }
    
    const z = getLayerZ(layer);
    
    // 平面
    const planeGeometry = new THREE.PlaneGeometry(size, size);
    const planeMaterial = new THREE.MeshBasicMaterial({
      color: props.layerColors[layer],
      transparent: true,
      opacity: 0.1,
      side: THREE.DoubleSide
    });
    const plane = new THREE.Mesh(planeGeometry, planeMaterial);
    plane.position.z = z;
    plane.userData.isLayerPlane = true;
    scene.add(plane);
    
    // グリッド
    const gridHelper = new THREE.GridHelper(size, size, 0xcccccc, 0xeeeeee);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.z = z;
    gridHelper.userData.isGridHelper = true;
    scene.add(gridHelper);
  }
}

/**
 * ノードを描画
 */
function renderNodes() {
  for (const node of props.network.nodes) {
    // レイヤーが非表示の場合はスキップ
    if (!props.visibleLayers.includes(node.layer)) {
      continue;
    }
    
    const position = node3DPositions.get(node.id);
    if (!position) continue;
    
    const z = getLayerZ(node.layer);
    
    // 球体ジオメトリ
    const geometry = new THREE.SphereGeometry(0.4, 16, 16);
    const material = new THREE.MeshPhongMaterial({
      color: props.layerColors[node.layer]
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(position.x3d, position.y3d, z);
    mesh.userData.node = node;
    
    scene.add(mesh);
    nodeMeshes.set(node.id, mesh);
  }
}

/**
 * エッジを描画
 */
function renderEdges() {
  const { nodes, edges } = props.network;
  const nodeMap = new Map(nodes.map(n => [n.id, n]));
  
  for (const edge of edges) {
    const sourceNode = nodeMap.get(edge.source_id);
    const targetNode = nodeMap.get(edge.target_id);
    
    if (!sourceNode || !targetNode) continue;
    
    // 両方のノードのレイヤーが表示されている場合のみエッジを描画
    if (!props.visibleLayers.includes(sourceNode.layer) || 
        !props.visibleLayers.includes(targetNode.layer)) {
      continue;
    }
    
    const sourcePosition = node3DPositions.get(sourceNode.id);
    const targetPosition = node3DPositions.get(targetNode.id);
    
    if (!sourcePosition || !targetPosition) continue;
    
    const sourceZ = getLayerZ(sourceNode.layer);
    const targetZ = getLayerZ(targetNode.layer);
    
    const points = [
      new THREE.Vector3(sourcePosition.x3d, sourcePosition.y3d, sourceZ),
      new THREE.Vector3(targetPosition.x3d, targetPosition.y3d, targetZ)
    ];
    
    // エッジを太い円柱として作成（クリック可能にするため）
    const direction = new THREE.Vector3().subVectors(points[1], points[0]);
    const distance = direction.length();
    const geometry = new THREE.CylinderGeometry(0.05, 0.05, distance, 8);
    
    const material = new THREE.MeshBasicMaterial({
      color: getEdgeColor(edge.weight)
    });
    
    const cylinder = new THREE.Mesh(geometry, material);
    
    // 円柱を正しい位置と向きに配置
    const midpoint = new THREE.Vector3().addVectors(points[0], points[1]).multiplyScalar(0.5);
    cylinder.position.copy(midpoint);
    
    // 円柱の向きを設定
    const normalizedDirection = direction.clone().normalize();
    cylinder.lookAt(points[1]);
    cylinder.rotateX(Math.PI / 2);
    
    cylinder.userData.edge = edge;
    
    scene.add(cylinder);
    edgeLines.set(edge.id, cylinder);
  }
}

/**
 * レイヤーのZ座標を取得
 */
function getLayerZ(layer: number): number {
  const baseZ = GRID_CONFIG.DEFAULT_LAYER_Z[layer as keyof typeof GRID_CONFIG.DEFAULT_LAYER_Z];
  // レイヤー間隔を適用
  const normalizedZ = (layer - 1) * props.layerSpacing;
  return 15 - normalizedZ; // 上から下に
}

/**
 * エッジの重みから色を取得
 */
function getEdgeColor(weight?: number): number {
  const colorMap: { [key: number]: string } = {
    3: '#004563',
    1: '#588da2',
    0.33: '#c3dde2',
    0: 'silver',
    [-0.33]: '#e9c1c9',
    [-1]: '#c94c62',
    [-3]: '#9f1e35'
  };
  
  const colorHex = colorMap[weight || 0] || 'silver';
  return new THREE.Color(colorHex).getHex();
}

/**
 * レイヤー表示/非表示を更新
 */
function updateVisibility() {
  nodeMeshes.forEach((mesh, nodeId) => {
    const node = mesh.userData.node as NetworkNode;
    mesh.visible = props.visibleLayers.includes(node.layer);
  });
  
  edgeLines.forEach((line, edgeId) => {
    const edge = line.userData.edge as NetworkEdge;
    const sourceNode = props.network.nodes.find(n => n.id === edge.source_id);
    const targetNode = props.network.nodes.find(n => n.id === edge.target_id);
    
    if (sourceNode && targetNode) {
      line.visible = props.visibleLayers.includes(sourceNode.layer) && 
                     props.visibleLayers.includes(targetNode.layer);
    }
  });
}

/**
 * キャンバスクリック処理
 */
function onCanvasClick(event: MouseEvent) {
  if (!containerRef.value) return;
  
  const rect = containerRef.value.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  
  raycaster.setFromCamera(mouse, camera);
  
  // ノードとの交差判定（優先度高）
  const meshArray = Array.from(nodeMeshes.values());
  const nodeIntersects = raycaster.intersectObjects(meshArray);
  
  if (nodeIntersects.length > 0) {
    const selectedMesh = nodeIntersects[0].object as THREE.Mesh;
    const node = selectedMesh.userData.node as NetworkNode;
    emit('nodeSelected', node);
    
    // ハイライト表示
    highlightNode(selectedMesh);
    clearEdgeHighlight();
    return;
  }
  
  // エッジとの交差判定
  const lineArray = Array.from(edgeLines.values());
  const edgeIntersects = raycaster.intersectObjects(lineArray);
  
  if (edgeIntersects.length > 0) {
    const selectedEdge = edgeIntersects[0].object as THREE.Mesh;
    const edge = selectedEdge.userData.edge as NetworkEdge;
    emit('edgeSelected', edge);
    
    // ハイライト表示
    highlightEdge(selectedEdge);
    clearNodeHighlight();
    return;
  }
  
  // 何も選択されていない場合
  emit('nodeSelected', null);
  emit('edgeSelected', null);
  clearHighlight();
}

/**
 * ノードをハイライト
 */
function highlightNode(mesh: THREE.Mesh) {
  // 全ノードを通常色に戻す
  clearNodeHighlight();
  
  // 選択ノードを赤にする
  const material = mesh.material as THREE.MeshPhongMaterial;
  material.color.set(0xff0000);
}

/**
 * エッジをハイライト
 */
function highlightEdge(edgeMesh: THREE.Mesh) {
  // 全エッジを通常色に戻す
  clearEdgeHighlight();
  
  // 選択エッジを赤にする
  const material = edgeMesh.material as THREE.MeshBasicMaterial;
  material.color.set(0xff0000);
}

/**
 * ノードハイライトをクリア
 */
function clearNodeHighlight() {
  nodeMeshes.forEach((mesh) => {
    const node = mesh.userData.node as NetworkNode;
    const material = mesh.material as THREE.MeshPhongMaterial;
    material.color.set(props.layerColors[node.layer]);
  });
}

/**
 * エッジハイライトをクリア
 */
function clearEdgeHighlight() {
  edgeLines.forEach((edgeMesh) => {
    const edge = edgeMesh.userData.edge as NetworkEdge;
    const material = edgeMesh.material as THREE.MeshBasicMaterial;
    material.color.set(getEdgeColor(edge.weight));
  });
}

/**
 * 全ハイライトをクリア
 */
function clearHighlight() {
  clearNodeHighlight();
  clearEdgeHighlight();
}

/**
 * ノードの3D座標を取得（親コンポーネント用）
 */
function getNodePosition(nodeId: string) {
  return node3DPositions.get(nodeId) || { x3d: null, y3d: null };
}

// 親コンポーネントからアクセス可能にする
defineExpose({
  getNodePosition
});
</script>

<style scoped>
.scene-container {
  width: 100%;
  height: 100%;
}
</style>