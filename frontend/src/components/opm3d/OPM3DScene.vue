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
const edgeLines = new Map<string, THREE.Group>();
const nodeLabels = new Map<string, THREE.Sprite>();

// 3D座標のマップ
const node3DPositions = new Map<string, { x3d: number; y3d: number }>();

// グリッド配置の設定（Y軸を上方向に変更）
const GRID_CONFIG = {
  CELL_SIZE: 2,
  DEFAULT_LAYER_Y: {
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

// ネットワークが変更されたら再描画（既存の3D座標は保持）
watch(() => props.network, () => {
  initializeNode3DPositionsPreservingExisting();
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
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 500);
  camera.position.set(30, 30, 30); // 山の可視化と同様の位置

  // レンダラー
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  containerRef.value.appendChild(renderer.domElement);

  // コントロール（山の可視化と同様のシンプル設定）
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 5;
  controls.maxDistance = 200;
  
  // ターゲットをレイヤー2と3の中間（Y=7.5）に設定
  controls.target.set(0, 7.5, 0);

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
  
  node3DPositions.clear();
  
  const layerGroups = new Map<number, NetworkNode[]>();
  for (const node of nodes) {
    if (!layerGroups.has(node.layer)) {
      layerGroups.set(node.layer, []);
    }
    layerGroups.get(node.layer)!.push(node);
  }
  
  for (const [layer, layerNodes] of layerGroups) {
    layoutNodesInLayer(layerNodes);
  }
}

/**
 * 既存の3D座標を保持しながらノードの3D座標を初期化
 */
function initializeNode3DPositionsPreservingExisting() {
  const { nodes } = props.network;
  const existingPositions = new Map(node3DPositions);
  node3DPositions.clear();
  
  const layerGroups = new Map<number, NetworkNode[]>();
  for (const node of nodes) {
    if (!layerGroups.has(node.layer)) {
      layerGroups.set(node.layer, []);
    }
    layerGroups.get(node.layer)!.push(node);
  }
  
  for (const [layer, layerNodes] of layerGroups) {
    for (const node of layerNodes) {
      const existingPosition = existingPositions.get(node.id);
      if (existingPosition) {
        node3DPositions.set(node.id, existingPosition);
      } else if ((node as any).x3d !== undefined && (node as any).y3d !== undefined && 
                 (node as any).x3d !== null && (node as any).y3d !== null) {
        node3DPositions.set(node.id, { x3d: (node as any).x3d, y3d: (node as any).y3d });
      } else {
        layoutNodesInLayer([node]);
      }
    }
  }
}

/**
 * レイヤー内のノードをグリッド配置
 */
function layoutNodesInLayer(nodes: NetworkNode[]) {
  const nodeCount = nodes.length;
  
  if (nodeCount === 0) {
    return;
  }
  
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
    const maxAttempts = 100; // 試行回数を増加
    
    // 重複を避けるポアソンディスク配置的なアプローチ
    do {
      if (nodeCount <= 4) {
        // 少数の場合：円周上に配置（半径を調整）
        const angle = (index / nodeCount) * 2 * Math.PI;
        const radius = Math.min(maxRadius * 0.7, 10); // 半径を増加
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
        
        // 中心付近を避ける（最小半径を増加）
        if (radius < maxRadius * 0.3) {
          const minRadius = maxRadius * 0.3;
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
  const minDistance = 4; // 最小距離を増加
  
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
  // 既存のノード・エッジ・ラベルを削除
  nodeMeshes.forEach(mesh => scene.remove(mesh));
  edgeLines.forEach(edgeGroup => scene.remove(edgeGroup));
  nodeLabels.forEach(label => {
    scene.remove(label);
    // テクスチャとマテリアルを破棄
    if (label.material.map) {
      label.material.map.dispose();
    }
    label.material.dispose();
  });
  
  nodeMeshes.clear();
  edgeLines.clear();
  nodeLabels.clear();
  
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
    
    const y = getLayerY(layer);
    
    // 平面
    const planeGeometry = new THREE.PlaneGeometry(size, size);
    const planeMaterial = new THREE.MeshBasicMaterial({
      color: props.layerColors[layer],
      transparent: true,
      opacity: 0.1,
      side: THREE.DoubleSide
    });
    const plane = new THREE.Mesh(planeGeometry, planeMaterial);
    plane.position.y = y;
    plane.rotation.x = -Math.PI / 2; // X軸周りに-90度回転してXZ平面（水平）にする
    plane.userData.isLayerPlane = true;
    scene.add(plane);
    
    // グリッド
    const gridHelper = new THREE.GridHelper(size, size, 0xcccccc, 0xeeeeee);
    // Y軸が上方向の場合、GridHelperはデフォルトでXZ平面に配置されるので回転不要
    gridHelper.position.y = y;
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
    
    const y = getLayerY(node.layer);
    
    // 球体ジオメトリ
    const geometry = new THREE.SphereGeometry(0.4, 16, 16);
    const material = new THREE.MeshPhongMaterial({
      color: props.layerColors[node.layer]
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(position.x3d, y, -position.y3d); // 2D座標のy3dを反転してZ軸にマッピング
    mesh.userData.node = node;
    
    scene.add(mesh);
    nodeMeshes.set(node.id, mesh);
    
    // ノードラベルを作成
    const label = createNodeLabel(node.label, '#000');
    label.position.set(position.x3d, y + 0.75, -position.y3d); // 2D座標のy3dを反転してZ軸にマッピング
    label.userData.nodeId = node.id;
    
    scene.add(label);
    nodeLabels.set(node.id, label);
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
    
    const sourceY = getLayerY(sourceNode.layer);
    const targetY = getLayerY(targetNode.layer);
    
    const points = [
      new THREE.Vector3(sourcePosition.x3d, sourceY, -sourcePosition.y3d),
      new THREE.Vector3(targetPosition.x3d, targetY, -targetPosition.y3d)
    ];
    
    // エッジを太い円柱として作成（クリック可能にするため）
    const direction = new THREE.Vector3().subVectors(points[1], points[0]);
    const distance = direction.length();
    
    // ノードの半径を考慮して矢印の終点を調整
    const nodeRadius = 1.5; // SphereGeometryの半径と一致
    const adjustedDistance = distance - nodeRadius; // ターゲットノードの表面で停止
    
    // エッジグループを作成（円柱+矢印先端）
    const edgeGroup = new THREE.Group();
    
    // 1. 円柱（エッジ本体）
    const arrowLength = Math.min(adjustedDistance * 0.15, 1.0); // 矢印の長さ（最大1.0）
    const cylinderLength = adjustedDistance; // 円柱の長さ
    const cylinderGeometry = new THREE.CylinderGeometry(0.05, 0.05, cylinderLength, 8);
    const material = new THREE.MeshBasicMaterial({
      color: getEdgeColor(edge.weight)
    });
    const cylinder = new THREE.Mesh(cylinderGeometry, material);
    
    // 2. 円錐（矢印先端）
    const arrowRadius = 0.15; // 矢印の太さ
    const arrowGeometry = new THREE.ConeGeometry(arrowRadius, arrowLength, 8);
    const arrowMaterial = new THREE.MeshBasicMaterial({
      color: getEdgeColor(edge.weight)
    });
    const arrowHead = new THREE.Mesh(arrowGeometry, arrowMaterial);
    
    // 円柱の位置設定（始点から中央へ）
    cylinder.position.set(0, -(arrowLength * 0.5), 0);
    
    // 矢印の位置設定（ターゲットノードの表面で停止）
    const arrowOffset = cylinderLength * 0.5;
    arrowHead.position.set(0, arrowOffset, 0);
    
    // グループに追加
    edgeGroup.add(cylinder);
    edgeGroup.add(arrowHead);
    
    // グループ全体の位置と向きを設定（ソースノードの表面から開始）
    const normalizedDirection = direction.clone().normalize();
    const sourceOffset = normalizedDirection.clone().multiplyScalar(nodeRadius);
    const adjustedStart = points[0].clone().add(sourceOffset);
    const adjustedEnd = points[1].clone().sub(normalizedDirection.clone().multiplyScalar(nodeRadius));
    
    const adjustedMidpoint = new THREE.Vector3().addVectors(adjustedStart, adjustedEnd).multiplyScalar(0.5);
    edgeGroup.position.copy(adjustedMidpoint);
    
    // グループ全体の向きを設定
    edgeGroup.lookAt(adjustedEnd);
    edgeGroup.rotateX(Math.PI / 2);
    
    // クリック検出用のメタデータ
    edgeGroup.userData.edge = edge;
    cylinder.userData.edge = edge; // 円柱部分もクリック可能
    arrowHead.userData.edge = edge; // 矢印部分もクリック可能
    
    scene.add(edgeGroup);
    edgeLines.set(edge.id, edgeGroup);
  }
}

/**
 * レイヤーのY座標を取得（Y軸が上方向）
 */
function getLayerY(layer: number): number {
  const baseY = GRID_CONFIG.DEFAULT_LAYER_Y[layer as keyof typeof GRID_CONFIG.DEFAULT_LAYER_Y];
  
  // デフォルト位置を使用（レイヤー間隔プロパティは無視）
  if (baseY !== undefined) {
    return baseY;
  }
  
  // fallback: レイヤー番号から計算
  return 15 - (layer - 1) * 5; // 固定間隔5
}

/**
 * ノードラベル用のスプライトを作成
 */
function createNodeLabel(text: string, color: string = '#000'): THREE.Sprite {
  // 高解像度対応の係数
  const dpr = window.devicePixelRatio || 1;
  const resolution = Math.min(dpr * 2, 4); // 最大4倍まで
  
  // キャンバスでテキストを描画
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d')!;
  
  // フォント設定（高解像度対応）
  const fontSize = 24 * resolution;
  const fontFamily = 'Arial, sans-serif';
  context.font = `bold ${fontSize}px ${fontFamily}`;
  
  // テキストサイズを測定
  const metrics = context.measureText(text);
  const textWidth = metrics.width;
  const textHeight = fontSize;
  
  // キャンバスサイズを設定（パディング込み、高解像度対応）
  const padding = 8 * resolution;
  canvas.width = textWidth + padding * 2;
  canvas.height = textHeight + padding * 2;
  
  // 高解像度設定
  canvas.style.width = `${canvas.width / resolution}px`;
  canvas.style.height = `${canvas.height / resolution}px`;
  
  // 背景を透明に設定
  context.clearRect(0, 0, canvas.width, canvas.height);
  
  // テキスト描画の設定（高解像度対応）
  context.scale(resolution, resolution);
  context.font = `bold ${24}px ${fontFamily}`; // 元のサイズで指定
  context.fillStyle = color;
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  
  // アンチエイリアス設定
  context.imageSmoothingEnabled = true;
  if (context.imageSmoothingQuality) {
    context.imageSmoothingQuality = 'high';
  }
  
  // テキストを描画
  context.fillText(text, (canvas.width / resolution) / 2, (canvas.height / resolution) / 2);
  
  // テクスチャとマテリアルを作成
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  
  const material = new THREE.SpriteMaterial({ 
    map: texture,
    transparent: true,
    alphaTest: 0.1,
    depthTest: false  // 常に手前に表示
  });
  
  const sprite = new THREE.Sprite(material);
  
  // スプライトのサイズを調整（3D空間でのサイズ）
  const scale = 0.8;
  const aspectRatio = textWidth / textHeight;
  sprite.scale.set(scale * aspectRatio, scale, 1);
  
  return sprite;
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
  
  edgeLines.forEach((edgeGroup) => {
    const edge = edgeGroup.userData.edge as NetworkEdge;
    const sourceNode = props.network.nodes.find(n => n.id === edge.source_id);
    const targetNode = props.network.nodes.find(n => n.id === edge.target_id);
    
    if (sourceNode && targetNode) {
      edgeGroup.visible = props.visibleLayers.includes(sourceNode.layer) && 
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
  
  // エッジとの交差判定（グループ内のオブジェクトも含む）
  const edgeObjects: THREE.Object3D[] = [];
  edgeLines.forEach(edgeGroup => {
    edgeObjects.push(edgeGroup);
    edgeGroup.children.forEach(child => edgeObjects.push(child));
  });
  const edgeIntersects = raycaster.intersectObjects(edgeObjects);
  
  if (edgeIntersects.length > 0) {
    const selectedObject = edgeIntersects[0].object;
    const edge = selectedObject.userData.edge as NetworkEdge;
    if (edge) {
      emit('edgeSelected', edge);
      
      // ハイライト表示
      highlightEdge(selectedObject);
      clearNodeHighlight();
      return;
    }
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
function highlightEdge(selectedObject: THREE.Object3D) {
  // 全エッジを通常色に戻す
  clearEdgeHighlight();
  
  // 選択されたオブジェクトがエッジグループの子要素の場合、そのグループ全体をハイライト
  const edge = selectedObject.userData.edge as NetworkEdge;
  if (edge) {
    edgeLines.forEach(edgeGroup => {
      if (edgeGroup.userData.edge?.id === edge.id) {
        // グループ内の全ての子要素を赤にする
        edgeGroup.children.forEach(child => {
          if (child instanceof THREE.Mesh) {
            const material = child.material as THREE.MeshBasicMaterial;
            material.color.set(0xff0000);
          }
        });
      }
    });
  }
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
  edgeLines.forEach((edgeGroup) => {
    const edge = edgeGroup.userData.edge as NetworkEdge;
    const color = getEdgeColor(edge.weight);
    
    // グループ内の全ての子要素を元の色に戻す
    edgeGroup.children.forEach(child => {
      if (child instanceof THREE.Mesh) {
        const material = child.material as THREE.MeshBasicMaterial;
        material.color.set(color);
      }
    });
  });
}

/**
 * 全てのエッジをシーンから削除
 */
function clearEdges() {
  edgeLines.forEach((edgeGroup) => {
    scene.remove(edgeGroup);
    // グループ内の全ての子要素のジオメトリとマテリアルを破棄
    edgeGroup.children.forEach(child => {
      if (child instanceof THREE.Mesh) {
        child.geometry.dispose();
        if (Array.isArray(child.material)) {
          child.material.forEach(mat => mat.dispose());
        } else {
          child.material.dispose();
        }
      }
    });
  });
  edgeLines.clear();
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

/**
 * ノードの3D座標を更新（親コンポーネント用）
 */
function updateNodePosition(nodeId: string, x3d: number, y3d: number) {
  // マップを更新
  node3DPositions.set(nodeId, { x3d, y3d });
  
  // nodeMeshesマップからノードオブジェクトを取得
  const nodeObject = nodeMeshes.get(nodeId);
  const labelObject = nodeLabels.get(nodeId);
  
  if (nodeObject) {
    // ノードのレイヤーを取得してY座標も正しく設定
    const node = nodeObject.userData.node as NetworkNode;
    const layerY = getLayerY(node.layer);
    
    nodeObject.position.x = x3d;
    nodeObject.position.y = layerY; // レイヤーのY座標
    nodeObject.position.z = -y3d; // 2D座標のy3dを反転してZ軸にマッピング
    
    // ラベルの位置も更新
    if (labelObject) {
      labelObject.position.x = x3d;
      labelObject.position.y = layerY + 0.75; // ノードの上に配置
      labelObject.position.z = -y3d; // 2D座標のy3dを反転してZ軸にマッピング
    }
  }
  
  // エッジを再描画（古いエッジを削除してから新しいエッジを描画）
  clearEdges();
  renderEdges();
}

/**
 * ノードラベルを更新（親コンポーネント用）
 */
function updateNodeLabel(nodeId: string, newLabel: string) {
  const labelObject = nodeLabels.get(nodeId);
  
  if (labelObject) {
    // 古いラベルを削除
    scene.remove(labelObject);
    if (labelObject.material.map) {
      labelObject.material.map.dispose();
    }
    labelObject.material.dispose();
    
    // 新しいラベルを作成
    const newLabelSprite = createNodeLabel(newLabel, '#000');
    
    // 位置を復元
    newLabelSprite.position.copy(labelObject.position);
    newLabelSprite.userData.nodeId = nodeId;
    
    // シーンに追加してマップを更新
    scene.add(newLabelSprite);
    nodeLabels.set(nodeId, newLabelSprite);
  } else {
    console.warn(`⚠️ ラベルオブジェクトが見つかりません: ${nodeId}`);
  }
}

/**
 * 保存済み座標を設定（リロード時の復元用）
 */
function setNodePosition(nodeId: string, x3d: number, y3d: number) {
  node3DPositions.set(nodeId, { x3d, y3d });
  
  const nodeObject = nodeMeshes.get(nodeId);
  const labelObject = nodeLabels.get(nodeId);
  
  if (nodeObject) {
    // ノードのレイヤーを取得してY座標も正しく設定
    const node = nodeObject.userData.node as NetworkNode;
    const layerY = getLayerY(node.layer);
    
    nodeObject.position.x = x3d;
    nodeObject.position.y = layerY; // レイヤーのY座標
    nodeObject.position.z = -y3d; // 2D座標のy3dを反転してZ軸にマッピング
    
    if (labelObject) {
      labelObject.position.x = x3d;
      labelObject.position.y = layerY + 0.75; // ノードの上に配置
      labelObject.position.z = -y3d; // 2D座標のy3dを反転してZ軸にマッピング
    }
  }
}

/**
 * 一括でノード座標を設定し、最後にエッジを再描画（復元処理用）
 */
function setMultipleNodePositions(nodePositions: Array<{id: string, x3d: number, y3d: number}>) {
  nodePositions.forEach(nodeData => {
    setNodePosition(nodeData.id, nodeData.x3d, nodeData.y3d);
  });
  
  clearEdges();
  renderEdges();
}


// 親コンポーネントからアクセス可能にする
defineExpose({
  getNodePosition,
  updateNodePosition,
  updateNodeLabel,
  setNodePosition, // 新しく追加
  setMultipleNodePositions, // 一括設定用
  clearHighlight,
  highlightNode,
  highlightEdge,
  nodeMeshes,
  edgeLines,
});
</script>

<style scoped>
.scene-container {
  width: 100%;
  height: 100%;
}
</style>