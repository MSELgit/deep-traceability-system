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
import StakeholderMatrix from '../components/stakeholder/StakeholderMatrix.vue'
import PerformanceManagement from '../components/performance/PerformanceManagement.vue'
import NeedPerformanceMatrix from '../components/matrix/NeedPerformanceMatrix.vue'
import NetworkDemo from '../components/demo/NetworkDemo.vue'
import MountainView from '../components/mountain/MountainView.vue'


const route = useRoute()
const projectStore = useProjectStore()
const { currentProject, loading, error } = storeToRefs(projectStore)

const activeTab = ref('stakeholders')
const networkDemoRef = ref<InstanceType<typeof NetworkDemo> | null>(null);

const tabs = [
  { key: 'stakeholders', label: 'ステークホルダー' },
  { key: 'performances', label: '性能管理' },
  { key: 'matrix', label: 'マトリクス' },
  { key: 'mountain', label: '山の可視化' },
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

onMounted(async () => {
  const projectId = route.params.id as string
  try {
    await projectStore.loadProject(projectId)
  } catch (e) {
    console.error('プロジェクトの読み込みに失敗:', e)
  }
})
</script>

<style scoped>
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

.error {
  text-align: center;
  padding: 40px;
  color: #e74c3c;
}
</style>
