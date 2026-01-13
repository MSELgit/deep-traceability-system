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

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let controls: OrbitControls;
let raycaster: THREE.Raycaster;
let mouse: THREE.Vector2;

const renderer = ref<THREE.WebGLRenderer>();

const nodeMeshes = new Map<string, THREE.Mesh>();
const edgeLines = new Map<string, THREE.Group>();
const nodeLabels = new Map<string, THREE.Sprite>();

const node3DPositions = new Map<string, { x3d: number; y3d: number }>();
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
  if (renderer.value) {
    renderer.value.dispose();
  }
  if (controls) {
    controls.dispose();
  }
});

watch(() => props.network, () => {
  initializeNode3DPositionsPreservingExisting();
  renderNetwork();
}, { deep: true });

watch(() => props.visibleLayers, () => {
  renderNetwork();
}, { deep: true });

watch(() => props.layerSpacing, () => {
  renderNetwork();
});

watch(() => props.planeSize, () => {
  renderNetwork();
});

function initThreeJS() {
  if (!containerRef.value) return;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf5f5f5);

  const width = containerRef.value.clientWidth;
  const height = containerRef.value.clientHeight;
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 500);
  camera.position.set(30, 30, 30);

  renderer.value = new THREE.WebGLRenderer({ 
    antialias: true,
    preserveDrawingBuffer: true 
  });
  renderer.value.setSize(width, height);
  containerRef.value.appendChild(renderer.value.domElement);

  controls = new OrbitControls(camera, renderer.value.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 5;
  controls.maxDistance = 200;
  
  controls.target.set(0, 7.5, 0);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
  directionalLight.position.set(10, 20, 10);
  scene.add(directionalLight);

  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();

  renderer.value.domElement.addEventListener('click', onCanvasClick);

  window.addEventListener('resize', onWindowResize);
}

function onWindowResize() {
  if (!containerRef.value || !renderer.value) return;
  
  const width = containerRef.value.clientWidth;
  const height = containerRef.value.clientHeight;
  
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.value.setSize(width, height);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  if (renderer.value) {
    renderer.value.render(scene, camera);
  }
}

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

function layoutNodesInLayer(nodes: NetworkNode[]) {
  const nodeCount = nodes.length;
  
  if (nodeCount === 0) {
    return;
  }
  const planeSize = props.planeSize || 30;
  const usableArea = planeSize * 0.7;
  const maxRadius = usableArea / 2;
  nodes.forEach((node, index) => {
    if (node3DPositions.has(node.id)) {
      return;
    }
    
    let x3d, y3d;
    let attempts = 0;
    const maxAttempts = 100;

    do {
      if (nodeCount <= 4) {
        const angle = (index / nodeCount) * 2 * Math.PI;
        const radius = Math.min(maxRadius * 0.7, 10); 
        x3d = Math.cos(angle) * radius;
        y3d = Math.sin(angle) * radius;
      } else if (nodeCount <= 12) {
        const ringSize = Math.ceil(Math.sqrt(nodeCount));
        const ring = Math.floor(index / ringSize);
        const posInRing = index % ringSize;
        const totalInRing = Math.min(ringSize, nodeCount - ring * ringSize);
        
        const radius = (ring + 1) * (maxRadius / Math.ceil(nodeCount / ringSize)) * 0.8;
        const angle = (posInRing / totalInRing) * 2 * Math.PI;
        
        const noise = radius * 0.3;
        const angleNoise = Math.PI / 6;
        
        x3d = Math.cos(angle + (Math.random() - 0.5) * angleNoise) * 
              (radius + (Math.random() - 0.5) * noise);
        y3d = Math.sin(angle + (Math.random() - 0.5) * angleNoise) * 
              (radius + (Math.random() - 0.5) * noise);
      } else {
        const angle = Math.random() * 2 * Math.PI;
        const radius = Math.sqrt(Math.random()) * maxRadius;
        
        x3d = Math.cos(angle) * radius;
        y3d = Math.sin(angle) * radius;
        
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

function isTooClose(x: number, y: number, currentNodeId: string): boolean {
  const minDistance = 4;
  
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

function renderNetwork() {
  clearScene();
  
  renderLayerPlanes();
  
  renderEdges();
  
  renderNodes();
}

function clearScene() {
  nodeMeshes.forEach(mesh => scene.remove(mesh));
  edgeLines.forEach(edgeGroup => scene.remove(edgeGroup));
  nodeLabels.forEach(label => {
    scene.remove(label);
    if (label.material.map) {
      label.material.map.dispose();
    }
    label.material.dispose();
  });
  
  nodeMeshes.clear();
  edgeLines.clear();
  nodeLabels.clear();
  const objectsToRemove = scene.children.filter(
    obj => obj.userData.isLayerPlane || obj.userData.isGridHelper
  );
  objectsToRemove.forEach(obj => scene.remove(obj));
}

function renderLayerPlanes() {
  const size = props.planeSize || 30;
  
  for (let layer = 1; layer <= 4; layer++) {
    if (!props.visibleLayers.includes(layer)) {
      continue;
    }
    
    const y = getLayerY(layer);
    
    const planeGeometry = new THREE.PlaneGeometry(size, size);
    const planeMaterial = new THREE.MeshBasicMaterial({
      color: props.layerColors[layer],
      transparent: true,
      opacity: 0.1,
      side: THREE.DoubleSide
    });
    const plane = new THREE.Mesh(planeGeometry, planeMaterial);
    plane.position.y = y;
    plane.rotation.x = -Math.PI / 2;
    plane.userData.isLayerPlane = true;
    scene.add(plane);
    
    const gridHelper = new THREE.GridHelper(size, size, 0xcccccc, 0xeeeeee);
    gridHelper.position.y = y;
    gridHelper.userData.isGridHelper = true;
    scene.add(gridHelper);
  }
}

function renderNodes() {
  for (const node of props.network.nodes) {
    if (!props.visibleLayers.includes(node.layer)) {
      continue;
    }
    
    const position = node3DPositions.get(node.id);
    if (!position) continue;
    
    const y = getLayerY(node.layer);
    
    const geometry = new THREE.SphereGeometry(0.4, 16, 16);
    const material = new THREE.MeshPhongMaterial({
      color: props.layerColors[node.layer]
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(position.x3d, y, -position.y3d);
    mesh.userData.node = node;
    
    scene.add(mesh);
    nodeMeshes.set(node.id, mesh);
    
    const label = createNodeLabel(node.label, '#000');
    label.position.set(position.x3d, y + 0.75, -position.y3d);
    label.userData.nodeId = node.id;
    
    scene.add(label);
    nodeLabels.set(node.id, label);
  }
}

function renderEdges() {
  const { nodes, edges } = props.network;
  const nodeMap = new Map(nodes.map(n => [n.id, n]));
  
  for (const edge of edges) {
    const sourceNode = nodeMap.get(edge.source_id);
    const targetNode = nodeMap.get(edge.target_id);
    
    if (!sourceNode || !targetNode) continue;
    
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
    
    const direction = new THREE.Vector3().subVectors(points[1], points[0]);
    const distance = direction.length();
    
    const nodeRadius = 1.5;
    const adjustedDistance = distance - nodeRadius;
    
    const edgeGroup = new THREE.Group();
    
    const arrowLength = Math.min(adjustedDistance * 0.15, 1.0);
    const cylinderLength = adjustedDistance;
    const cylinderGeometry = new THREE.CylinderGeometry(0.05, 0.05, cylinderLength, 8);
    const material = new THREE.MeshBasicMaterial({
      color: getEdgeColor(edge.weight)
    });
    const cylinder = new THREE.Mesh(cylinderGeometry, material);
    
    const arrowRadius = 0.15;
    const arrowGeometry = new THREE.ConeGeometry(arrowRadius, arrowLength, 8);
    const arrowMaterial = new THREE.MeshBasicMaterial({
      color: getEdgeColor(edge.weight)
    });
    const arrowHead = new THREE.Mesh(arrowGeometry, arrowMaterial);
    
    cylinder.position.set(0, -(arrowLength * 0.5), 0);
    
    const arrowOffset = cylinderLength * 0.5;
    arrowHead.position.set(0, arrowOffset, 0);
    
    edgeGroup.add(cylinder);
    edgeGroup.add(arrowHead);
    
    const normalizedDirection = direction.clone().normalize();
    const sourceOffset = normalizedDirection.clone().multiplyScalar(nodeRadius);
    const adjustedStart = points[0].clone().add(sourceOffset);
    const adjustedEnd = points[1].clone().sub(normalizedDirection.clone().multiplyScalar(nodeRadius));
    
    const adjustedMidpoint = new THREE.Vector3().addVectors(adjustedStart, adjustedEnd).multiplyScalar(0.5);
    edgeGroup.position.copy(adjustedMidpoint);
    
    edgeGroup.lookAt(adjustedEnd);
    edgeGroup.rotateX(Math.PI / 2);
    
    edgeGroup.userData.edge = edge;
    cylinder.userData.edge = edge;
    arrowHead.userData.edge = edge;
    
    scene.add(edgeGroup);
    edgeLines.set(edge.id, edgeGroup);
  }
}

function getLayerY(layer: number): number {
  const baseY = GRID_CONFIG.DEFAULT_LAYER_Y[layer as keyof typeof GRID_CONFIG.DEFAULT_LAYER_Y];
  
  if (baseY !== undefined) {
    return baseY;
  }
  return 15 - (layer - 1) * 5;
}

function createNodeLabel(text: string, color: string = '#000'): THREE.Sprite {
  const dpr = window.devicePixelRatio || 1;
  const resolution = Math.min(dpr * 2, 4);
  
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d')!;
  
  const fontSize = 24 * resolution;
  const fontFamily = 'Arial, sans-serif';
  context.font = `bold ${fontSize}px ${fontFamily}`;
  
  const metrics = context.measureText(text);
  const textWidth = metrics.width;
  const textHeight = fontSize;
  
  const padding = 8 * resolution;
  canvas.width = textWidth + padding * 2;
  canvas.height = textHeight + padding * 2;
  
  canvas.style.width = `${canvas.width / resolution}px`;
  canvas.style.height = `${canvas.height / resolution}px`;
  
  context.clearRect(0, 0, canvas.width, canvas.height);

  context.scale(resolution, resolution);
  context.font = `bold ${24}px ${fontFamily}`;
  context.fillStyle = color;
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  
  context.imageSmoothingEnabled = true;
  if (context.imageSmoothingQuality) {
    context.imageSmoothingQuality = 'high';
  }
  
  context.fillText(text, (canvas.width / resolution) / 2, (canvas.height / resolution) / 2);
  
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  
  const material = new THREE.SpriteMaterial({ 
    map: texture,
    transparent: true,
    alphaTest: 0.1,
    depthTest: false
  });
  
  const sprite = new THREE.Sprite(material);
  
  const scale = 0.8;
  const aspectRatio = textWidth / textHeight;
  sprite.scale.set(scale * aspectRatio, scale, 1);
  
  return sprite;
}

function getEdgeColor(weight?: number): number {
  // Edge weight colors supporting both old (0.33) and new (±5) formats
  const colorMap: { [key: number]: string } = {
    5: '#002040',      // Strong positive (new discrete_7)
    3: '#004563',      // Moderate-strong positive
    1: '#588da2',      // Moderate positive
    0.33: '#c3dde2',   // Weak positive (legacy)
    0: 'silver',       // No correlation
    [-0.33]: '#e9c1c9', // Weak negative (legacy)
    [-1]: '#c94c62',   // Moderate negative
    [-3]: '#9f1e35',   // Moderate-strong negative
    [-5]: '#6f0020'    // Strong negative (new discrete_7)
  };

  const colorHex = colorMap[weight || 0] || 'silver';
  return new THREE.Color(colorHex).getHex();
}

function onCanvasClick(event: MouseEvent) {
  if (!containerRef.value) return;
  
  const rect = containerRef.value.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  
  raycaster.setFromCamera(mouse, camera);
  
  const meshArray = Array.from(nodeMeshes.values());
  const nodeIntersects = raycaster.intersectObjects(meshArray);
  
  if (nodeIntersects.length > 0) {
    const selectedMesh = nodeIntersects[0].object as THREE.Mesh;
    const node = selectedMesh.userData.node as NetworkNode;
    emit('nodeSelected', node);
    
    highlightNode(selectedMesh);
    clearEdgeHighlight();
    return;
  }
  
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
      
        highlightEdge(selectedObject);
      clearNodeHighlight();
      return;
    }
  }
  
  emit('nodeSelected', null);
  emit('edgeSelected', null);
  clearHighlight();
}

function highlightNode(mesh: THREE.Mesh) {
  clearNodeHighlight();
  
  const material = mesh.material as THREE.MeshPhongMaterial;
  material.color.set(0xff0000);
}

function highlightEdge(selectedObject: THREE.Object3D) {
  clearEdgeHighlight();
  
  const edge = selectedObject.userData.edge as NetworkEdge;
  if (edge) {
    edgeLines.forEach(edgeGroup => {
      if (edgeGroup.userData.edge?.id === edge.id) {
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

function clearNodeHighlight() {
  nodeMeshes.forEach((mesh) => {
    const node = mesh.userData.node as NetworkNode;
    const material = mesh.material as THREE.MeshPhongMaterial;
    material.color.set(props.layerColors[node.layer]);
  });
}

function clearEdgeHighlight() {
  edgeLines.forEach((edgeGroup) => {
    const edge = edgeGroup.userData.edge as NetworkEdge;
    const color = getEdgeColor(edge.weight);
    
    edgeGroup.children.forEach(child => {
      if (child instanceof THREE.Mesh) {
        const material = child.material as THREE.MeshBasicMaterial;
        material.color.set(color);
      }
    });
  });
}

function clearEdges() {
  edgeLines.forEach((edgeGroup) => {
    scene.remove(edgeGroup);
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

function clearHighlight() {
  clearNodeHighlight();
  clearEdgeHighlight();
}

function getNodePosition(nodeId: string) {
  return node3DPositions.get(nodeId) || { x3d: null, y3d: null };
}

function updateNodePosition(nodeId: string, x3d: number, y3d: number) {
  node3DPositions.set(nodeId, { x3d, y3d });
  
  const nodeObject = nodeMeshes.get(nodeId);
  const labelObject = nodeLabels.get(nodeId);
  
  if (nodeObject) {
    const node = nodeObject.userData.node as NetworkNode;
    const layerY = getLayerY(node.layer);
    
    nodeObject.position.x = x3d;
    nodeObject.position.y = layerY; 
    nodeObject.position.z = -y3d;
    
    if (labelObject) {
      labelObject.position.x = x3d;
      labelObject.position.y = layerY + 0.75; 
      labelObject.position.z = -y3d;
    }
  }
  
  clearEdges();
  renderEdges();
}

function updateNodeLabel(nodeId: string, newLabel: string) {
  const labelObject = nodeLabels.get(nodeId);
  
  if (labelObject) {
    scene.remove(labelObject);
    if (labelObject.material.map) {
      labelObject.material.map.dispose();
    }
    labelObject.material.dispose();
    
    const newLabelSprite = createNodeLabel(newLabel, '#000');
    
    newLabelSprite.position.copy(labelObject.position);
    newLabelSprite.userData.nodeId = nodeId;
    
    scene.add(newLabelSprite);
    nodeLabels.set(nodeId, newLabelSprite);
  } else {
    console.warn(`⚠️ Label object not found: ${nodeId}`);
  }
}

function setNodePosition(nodeId: string, x3d: number, y3d: number) {
  node3DPositions.set(nodeId, { x3d, y3d });
  
  const nodeObject = nodeMeshes.get(nodeId);
  const labelObject = nodeLabels.get(nodeId);
  
  if (nodeObject) {
    const node = nodeObject.userData.node as NetworkNode;
    const layerY = getLayerY(node.layer);
    
    nodeObject.position.x = x3d;
    nodeObject.position.y = layerY; 
    nodeObject.position.z = -y3d; 
    
    if (labelObject) {
      labelObject.position.x = x3d;
      labelObject.position.y = layerY + 0.75; 
      labelObject.position.z = -y3d; 
    }
  }
}

function setMultipleNodePositions(nodePositions: Array<{id: string, x3d: number, y3d: number}>) {
  nodePositions.forEach(nodeData => {
    setNodePosition(nodeData.id, nodeData.x3d, nodeData.y3d);
  });
  
  clearEdges();
  renderEdges();
}


defineExpose({
  getNodePosition,
  updateNodePosition,
  updateNodeLabel,
  setNodePosition,
  setMultipleNodePositions,
  clearHighlight,
  highlightNode,
  highlightEdge,
  nodeMeshes,
  edgeLines,
  renderer,
  scene: () => scene,
  camera: () => camera,
});
</script>

<style scoped>
.scene-container {
  width: 100%;
  height: 100%;
}
</style>