<template>
  <div class="project-detail">
    <div class="container">
      <!-- ローディング -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <!-- プロジェクト情報 -->
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
              class="icon-button" 
              @click="exportProject"
              title="プロジェクトをエクスポート"
            >
              <FontAwesomeIcon :icon="['fas', 'share-from-square']" />
              エクスポート
            </button>
          </div>
        </div>

        <!-- タブナビゲーション -->
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

          <!-- 2軸評価（複数ビュー管理） -->
          <div v-show="activeTab === 'twoaxis'">
            <div v-if="energyCalculated">
              <div class="twoaxis-multiview-header">
                <button class="add-view-btn" @click="addTwoAxisView">＋ 新しいビューを追加</button>
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
              <p>エネルギーを計算中...</p>
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
        </div>
      </div>

      <!-- エラー -->
      <div v-else-if="error" class="error">
        <p>❌ プロジェクトの読み込みに失敗しました</p>
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

import TwoAxisEvaluation from '../components/twoaxis/TwoAxisEvaluation.vue'


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
    console.error('2軸プロットの保存に失敗:', error);
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
  { key: 'stakeholders', label: 'ステークホルダー' },
  { key: 'performances', label: '性能管理' },
  { key: 'matrix', label: 'マトリクス' },
  { key: 'mountain', label: '山の可視化' },
  { key: 'twoaxis', label: '2軸評価' },
  { key: 'opm3d', label: '立体OPM' },
  { key: 'demo', label: 'ネットワークデモ' },
];

function handleTabChange(tabKey: string) {
  activeTab.value = tabKey;
  if (tabKey === 'demo') {
    nextTick(() => {
      setTimeout(() => {
        if (networkDemoRef.value && typeof networkDemoRef.value.resetAllViewers === 'function') {
          networkDemoRef.value.resetAllViewers();
        } else {
          console.warn('networkDemoRef.value が利用できません');
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
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `project_${currentProject.value.id}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('プロジェクトのエクスポートに失敗:', error)
    alert('プロジェクトのエクスポートに失敗しました')
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
    console.error('プロジェクトの読み込みに失敗:', e)
  }
})
</script>

<style scoped>
.twoaxis-multiview-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.add-view-btn {
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 18px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.add-view-btn:hover {
  background: #5a67d8;
}
.twoaxis-multiview-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  align-items: stretch;
}
.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.project-header h1 {
  font-size: 32px;
  color: #333;
  margin-bottom: 8px;
}

.description {
  color: #666;
  font-size: 16px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  border-bottom: 2px solid #e0e0e0;
  overflow-x: auto;
}

.tabs button {
  padding: 12px 24px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: 16px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tabs button:hover {
  color: #333;
  background: rgba(102, 126, 234, 0.05);
}

.tabs button.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.tab-content {
  min-height: 400px;
}

.two-axis-placeholder {
  padding: 16px;
}

.placeholder-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.error {
  text-align: center;
  padding: 40px;
  color: #e74c3c;
}

.project-actions {
  display: flex;
  gap: 12px;
}

.icon-button {
  padding: 10px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.icon-button:hover {
  background: #5a67d8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 立体OPM */
.opm3d-container {
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
  min-height: 600px;
}

.opm3d-container h3 {
  font-size: 24px;
  margin-bottom: 12px;
  color: #333;
}

.opm3d-container p {
  color: #666;
  margin-bottom: 24px;
}
</style>
