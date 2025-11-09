<template>
  <div class="project-list">
    <div class="container">
      <div class="page-header-section">
        <h1>プロジェクト一覧</h1>
        <button class="primary" @click="showCreateDialog = true">
          + 新規プロジェクト
        </button>
      </div>

      <!-- ローディング -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <!-- プロジェクトリスト -->
      <div v-else-if="projects.length > 0" class="projects-grid">
        <div 
          v-for="project in projects" 
          :key="project.id"
          class="project-card"
          @click="router.push(`/project/${project.id}`)"
        >
          <h3>{{ project.name }}</h3>
          <p v-if="project.description">{{ project.description }}</p>
          <div class="project-meta">
            <span>📅 {{ formatDate(project.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 空状態 -->
      <div v-else class="empty-state">
        <div class="empty-icon">📂</div>
        <h3>プロジェクトがまだありません</h3>
        <p>新規プロジェクトを作成して始めましょう</p>
        <button class="primary" @click="showCreateDialog = true">
          プロジェクトを作成
        </button>
      </div>

      <!-- 作成ダイアログ -->
      <div v-if="showCreateDialog" class="modal-overlay" @click="showCreateDialog = false">
        <div class="modal-content" @click.stop>
          <h2>新規プロジェクト作成</h2>
          <form @submit.prevent="createNewProject">
            <div class="form-group">
              <label>プロジェクト名 *</label>
              <input 
                v-model="newProjectName" 
                type="text" 
                placeholder="例: 洋上風力発電システム"
                required
              />
            </div>
            <div class="form-group">
              <label>説明（任意）</label>
              <textarea 
                v-model="newProjectDescription" 
                rows="3"
                placeholder="プロジェクトの概要を入力してください"
              ></textarea>
            </div>
            <div class="form-actions">
              <button type="button" @click="showCreateDialog = false">
                キャンセル
              </button>
              <button type="submit" class="primary" :disabled="!newProjectName">
                作成
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/projectStore'
import { storeToRefs } from 'pinia'

const router = useRouter()
const projectStore = useProjectStore()
const { projects, loading } = storeToRefs(projectStore)

const showCreateDialog = ref(false)
const newProjectName = ref('')
const newProjectDescription = ref('')

onMounted(async () => {
  try {
    await projectStore.loadProjects()
  } catch (error) {
    console.error('プロジェクトの読み込みに失敗:', error)
  }
})

async function createNewProject() {
  try {
    const project = await projectStore.createProject(
      newProjectName.value,
      newProjectDescription.value
    )
    
    // リセット
    newProjectName.value = ''
    newProjectDescription.value = ''
    showCreateDialog.value = false
    
    // 新規プロジェクトの詳細ページに遷移
    router.push(`/project/${project.id}`)
  } catch (error) {
    console.error('プロジェクトの作成に失敗:', error)
    alert('プロジェクトの作成に失敗しました')
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.page-header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.page-header-section h1 {
  font-size: 32px;
  color: #333;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.project-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.project-card h3 {
  font-size: 20px;
  margin-bottom: 12px;
  color: #333;
}

.project-card p {
  color: #666;
  margin-bottom: 16px;
  line-height: 1.5;
}

.project-meta {
  color: #999;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 24px;
  color: #333;
  margin-bottom: 12px;
}

.empty-state p {
  color: #666;
  margin-bottom: 24px;
}

/* モーダル */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 32px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-content h2 {
  margin-bottom: 24px;
  font-size: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}
</style>
