<template>
  <div class="project-detail">
    <div class="container">
      <!-- Loading -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading project...</p>
      </div>

      <!-- Project Info -->
      <div v-else-if="currentProject">
        <div class="project-header">
          <div>
            <h1>{{ currentProject.name }}</h1>
            <p v-if="currentProject.description" class="description">
              {{ currentProject.description }}
            </p>
          </div>
          <div class="project-actions">
            <button 
              class="icon-button export" 
              @click="exportProject"
              title="Export project"
            >
              <FontAwesomeIcon :icon="['fas', 'share-from-square']" />
              Export
            </button>
          </div>
        </div>

        <!-- Tab Navigation -->
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="{ active: activeTab === tab.key }"
            @click="handleTabChange(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- タブコンテンツ -->
        <div class="tab-content">
          <!-- ステークホルダー分析 -->
          <div v-show="activeTab === 'stakeholders'">
            <StakeholderMatrix />
          </div>

          <!-- 性能管理 -->
          <div v-show="activeTab === 'performances'">
            <PerformanceManagement />
          </div>

          <!-- ニーズ×性能マトリクス -->
          <div v-show="activeTab === 'matrix'">
            <NeedPerformanceMatrix @navigate-to-performance="activeTab = 'performances'" />
          </div>

          <!-- 山の可視化（設計案管理を含む） -->
          <div v-show="activeTab === 'mountain'">
            <MountainView :is-active="activeTab === 'mountain'" />
          </div>

          <!-- 2-axis Evaluation (Multiple Views) -->
          <div v-show="activeTab === 'twoaxis'" class="two-axis-placeholder">
            <div v-if="energyCalculated">
              <div class="twoaxis-multiview-header">
                <button class="add-view-btn" @click="addTwoAxisView">
                  <FontAwesomeIcon :icon="['fas', 'plus']" />
                  Add New View
                </button>
              </div>
              <div class="twoaxis-multiview-row">
                <TwoAxisEvaluation
                  v-for="view in twoAxisViews"
                  :key="view.id"
                  :viewId="view.id"
                  :designCases="currentProject?.design_cases || []"
                  :performances="currentProject?.performances || []"
                  :initialX="view.x_axis"
                  :initialY="view.y_axis"
                  :onRemove="removeTwoAxisView"
                  @axis-change="handleAxisChange"
                />
              </div>
            </div>
            <div v-else class="loading">
              <div class="spinner"></div>
              <p>Calculating energy...</p>
            </div>
          </div>

          <!-- Dashboard -->
          <div v-show="activeTab === 'dashboard'">
            <div v-if="energyCalculated">
              <DesignCaseDashboard
                :projectId="(route.params.id as string)"
                :designCases="currentProject?.design_cases || []"
                :performances="currentProject?.performances || []"
              />
            </div>
            <div v-else class="loading">
              <div class="spinner"></div>
              <p>Calculating energy...</p>
            </div>
          </div>

          <!-- 立体OPM -->
          <div v-show="activeTab === 'opm3d'">
            <OPM3DView />
          </div>

          <!-- ネットワークデモ -->
          <div v-show="activeTab === 'demo'">
            <NetworkDemo ref="networkDemoRef" />
          </div>

          <!-- 比較 -->
          <div v-show="activeTab === 'compare'">
            <ComparisonView />
          </div>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error">
        <p>Failed to load project</p>
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '../stores/projectStore'
import { storeToRefs } from 'pinia'
import { projectApi, calculationApi } from '../utils/api'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import StakeholderMatrix from '../components/stakeholder/StakeholderMatrix.vue'
import PerformanceManagement from '../components/performance/PerformanceManagement.vue'
import NeedPerformanceMatrix from '../components/matrix/NeedPerformanceMatrix.vue'
import NetworkDemo from '../components/demo/NetworkDemo.vue'
import MountainView from '../components/mountain/MountainView.vue'
import OPM3DView from '../components/opm3d/OPM3DView.vue'
import ComparisonView from '../components/comparison/ComparisonView.vue'

import TwoAxisEvaluation from '../components/twoaxis/TwoAxisEvaluation.vue'
import DesignCaseDashboard from '../components/dashboard/DesignCaseDashboard.vue'


const route = useRoute()
const projectStore = useProjectStore()
const { currentProject, loading, error } = storeToRefs(projectStore)

const activeTab = ref('stakeholders')
const networkDemoRef = ref<InstanceType<typeof NetworkDemo> | null>(null);
const energyCalculated = ref(false)

// 2軸ビュー管理
interface TwoAxisView {
  id: string;
  x_axis: string;
  y_axis: string;
}
const twoAxisViews = ref<TwoAxisView[]>([]);

// 2軸プロットをバックエンドに保存
async function saveTwoAxisPlots() {
  if (!currentProject.value) return;
  
  try {
    await projectApi.updateTwoAxisPlots(currentProject.value.id, twoAxisViews.value);
  } catch (error) {
    console.error('Failed to save 2-axis plots:', error);
  }
}

function addTwoAxisView() {
  const perfs = currentProject.value?.performances || [];
  const x = perfs[0]?.id || '';
  const y = perfs[1]?.id || perfs[0]?.id || '';
  const newView: TwoAxisView = {
    id: `view-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
    x_axis: x,
    y_axis: y
  };
  twoAxisViews.value.push(newView);
  saveTwoAxisPlots();
}

function removeTwoAxisView(id: string | number) {
  twoAxisViews.value = twoAxisViews.value.filter(v => v.id !== id);
  saveTwoAxisPlots();
}

// 2軸プロットの初期化
async function initializeTwoAxisPlots() {
  if (!currentProject.value) return;
  
  // プロジェクトから保存された設定を読み込む
  if (currentProject.value.two_axis_plots && currentProject.value.two_axis_plots.length > 0) {
    twoAxisViews.value = currentProject.value.two_axis_plots;
  } else if (twoAxisViews.value.length === 0) {
    // 保存された設定がない場合は新規作成
    addTwoAxisView();
  }
}

// 軸変更時の処理
function handleAxisChange(viewId: string, axis: 'x' | 'y', value: string) {
  const view = twoAxisViews.value.find(v => v.id === viewId);
  if (view) {
    if (axis === 'x') {
      view.x_axis = value;
    } else {
      view.y_axis = value;
    }
    saveTwoAxisPlots();
  }
}

const tabs = [
  { key: 'stakeholders', label: 'Stakeholders' },
  { key: 'performances', label: 'Performance' },
  { key: 'matrix', label: 'Matrix' },
  { key: 'mountain', label: 'Mountain View' },
  { key: 'twoaxis', label: '2-axis' },
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'opm3d', label: '3D OPM' },
  { key: 'demo', label: 'WL Kernel' },
  { key: 'compare', label: '比較' },
];

function handleTabChange(tabKey: string) {
  activeTab.value = tabKey;
  if (tabKey === 'demo') {
    nextTick(() => {
      setTimeout(() => {
        if (networkDemoRef.value && typeof networkDemoRef.value.resetAllViewers === 'function') {
          networkDemoRef.value.resetAllViewers();
        } else {
          console.warn('networkDemoRef.value is not available');
        }
      }, 200); // 200msに増やして確実にレンダリング完了を待つ
    });
  }
}

// プロジェクトをエクスポート
async function exportProject() {
  if (!currentProject.value) return

  try {
    const response = await projectApi.export(currentProject.value.id)
    const exportedPath = response.data._exported_path
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `project_${currentProject.value.id}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    if (exportedPath) {
      alert(`エクスポート完了\nサーバー保存先: ${exportedPath}`)
    }
  } catch (error) {
    console.error('Failed to export project:', error)
    alert('Failed to export project')
  }
}

onMounted(async () => {
  const projectId = route.params.id as string
  try {
    await projectStore.loadProject(projectId)
    // 設計案一覧取得後にエネルギーをAPIで取得して設計案にマージ
    if (currentProject.value && currentProject.value.design_cases?.length) {
      const energyResults = await calculationApi.calculateEnergy(projectId)
      // case_idで設計案にマージ
      for (const energy of energyResults.data) {
        const dc = currentProject.value.design_cases.find(d => d.id === energy.case_id)
        if (dc) {
          dc.energy = {
            total_energy: energy.total_energy,
            partial_energies: energy.partial_energies
          }
        }
      }
    }
    energyCalculated.value = true
    // 2軸プロットの初期化
    await initializeTwoAxisPlots()
  } catch (e) {
    console.error('Failed to load project:', e)
  }
})
</script>

<style scoped lang="scss">
@use 'sass:color';
@use '../style/color' as *;
.project-detail {
  min-height: 100vh;
  background: $black;
  color: $white;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2vh 3vw;
}

// Loading
.loading {
  text-align: center;
  padding: 15vh 2vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 3px solid color.adjust($white, $alpha: -0.95);
  border-top-color: $main_1;
  border-right-color: $main_2;
  border-radius: 50%;
  margin: 0 auto 3vh;
  animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
  box-shadow: 0 0 2vh color.adjust($main_1, $alpha: -0.8);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading p {
  color: color.adjust($white, $alpha: -0.2);
  font-size: clamp(1rem, 1.2vw, 1.1rem);
  font-weight: 500;
  letter-spacing: 0.02em;
}

// Two-axis view header
.twoaxis-multiview-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 2vh;
}

.add-view-btn {
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border: none;
  border-radius: 0.8vw;
  padding: 1.2vh 2vw;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.8vw;
}

.add-view-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh color.adjust($main_2, $alpha: -0.6);
}
.twoaxis-multiview-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: clamp(1rem, 2vw, 1.5rem);
  align-items: start;
}
.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4vh;
  padding-bottom: 2vh;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
}

.project-header h1 {
  font-size: clamp(2.2rem, 3.5vw, 3rem);
  color: $white;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, $white, color.adjust($white, $alpha: -0.15));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.description {
  color: color.adjust($white, $alpha: -0.3);
  font-size: clamp(0.95rem, 1.2vw, 1.1rem);
  line-height: 1.6;
}

.tabs {
  display: flex;
  gap: 1vw;
  margin-bottom: 4vh;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  overflow-x: auto;
  padding-bottom: 0;
}

.tabs button {
  padding: 1.5vh 2vw;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  font-weight: 600;
  color: color.adjust($white, $alpha: -0.4);
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  position: relative;
}

.tabs button:hover {
  color: $white;
  background: color.adjust($gray, $alpha: -0.8);
}

.tabs button.active {
  color: $white;
  border-bottom-color: $main_1;
}

.tabs button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, $main_1, $main_2);
}

.tab-content {
  min-height: 60vh;
  background: color.scale($black, $lightness: 2%);
  border-radius: 1vw;
  padding: 2vh;
}

.two-axis-placeholder {
  padding: 2vh;
}

.placeholder-card {
  background: color.scale($gray, $lightness: 8%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 1vw;
  padding: 3vh;
  box-shadow: 0 0.5vh 2vh color.adjust($black, $alpha: -0.5);
}

.error {
  text-align: center;
  padding: 10vh;
  background: color.scale($gray, $lightness: 5%);
  border-radius: 1vw;
  border: 1px solid color.adjust($sub_1, $alpha: -0.7);
}

.error p:first-child {
  font-size: clamp(1.2rem, 1.5vw, 1.4rem);
  color: $sub_1;
  margin-bottom: 2vh;
  font-weight: 600;
}

.error p:last-child {
  color: color.adjust($white, $alpha: -0.3);
  font-size: clamp(0.9rem, 1.1vw, 1rem);
}

.project-actions {
  display: flex;
  gap: 1vw;
}

.icon-button {
  padding: 1.2vh 2vw;
  background: color.adjust($black, $alpha: -0.1);
  color: $white;
  border: 1px solid color.adjust($white, $alpha: -0.85);
  border-radius: 0.8vw;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.8vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  backdrop-filter: blur(10px);
}

.icon-button.export:hover {
  background: linear-gradient(135deg, $main_1, color.scale($main_1, $lightness: -10%));
  border-color: $main_1;
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 1.5vh color.adjust($main_1, $alpha: -0.5);
}

// 3D OPM
.opm3d-container {
  padding: 3vh;
  background: color.scale($gray, $lightness: 5%);
  border-radius: 1vw;
  min-height: 60vh;
}

.opm3d-container h3 {
  font-size: clamp(1.3rem, 1.8vw, 1.6rem);
  margin-bottom: 1.5vh;
  color: $white;
  font-weight: 700;
}

.opm3d-container p {
  color: color.adjust($white, $alpha: -0.3);
  margin-bottom: 3vh;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
}

// Responsive
@media (max-width: 1200px) {
  .twoaxis-multiview-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .project-header {
    flex-direction: column;
    gap: 2vh;
  }
  
  .tabs {
    gap: 0.5vw;
    overflow-x: scroll;
    -webkit-overflow-scrolling: touch;
  }
  
  .tabs button {
    padding: 1.5vh 3vw;
    font-size: 0.9rem;
  }
  
  .twoaxis-multiview-row {
    grid-template-columns: 1fr;
  }
}
</style>
