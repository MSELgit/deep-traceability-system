<template>
  <div class="project-list">
    <div class="container">
      <div class="page-header-section">
        <h1>プロジェクト一覧</h1>
        <div class="header-actions">
          <button class="secondary" @click="showImportDialog = true">
            <FontAwesomeIcon :icon="['fas', 'file-import']" />
            インポート
          </button>
          <button class="primary" @click="showCreateDialog = true">
            + 新規プロジェクト
          </button>
        </div>
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
        >
          <div class="project-card-content" @click="router.push(`/project/${project.id}`)">
            <h3>{{ project.name }}</h3>
            <p v-if="project.description">{{ project.description }}</p>
            <div class="project-meta">
              <span>{{ formatDate(project.created_at) }}</span>
            </div>
          </div>
          <div class="project-card-actions">
            <button 
              class="icon-button" 
              @click.stop="exportProject(project.id)"
              title="エクスポート"
            >
              <FontAwesomeIcon :icon="['fas', 'share-from-square']" />
            </button>
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

      <!-- インポートダイアログ -->
      <div v-if="showImportDialog" class="modal-overlay" @click="showImportDialog = false">
        <div class="modal-content" @click.stop>
          <h2>プロジェクトをインポート</h2>
          <div class="import-area">
            <input 
              type="file" 
              @change="handleFileSelect" 
              accept=".json"
              ref="fileInput"
              style="display: none"
            />
            <button 
              class="import-button" 
              @click="fileInput?.click()"
            >
              <FontAwesomeIcon :icon="['fas', 'file-import']" />
              ファイルを選択
            </button>
            <p class="import-help">プロジェクトデータ（.json）を選択してください</p>
          </div>
          <div class="form-actions">
            <button type="button" @click="showImportDialog = false">
              キャンセル
            </button>
          </div>
        </div>
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
import { projectApi, calculationApi } from '../utils/api'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const router = useRouter()
const projectStore = useProjectStore()
const { projects, loading } = storeToRefs(projectStore)

const showCreateDialog = ref(false)
const showImportDialog = ref(false)
const newProjectName = ref('')
const newProjectDescription = ref('')
const fileInput = ref<HTMLInputElement>()

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

// プロジェクトをエクスポート
async function exportProject(projectId: string) {
  try {
    const response = await projectApi.export(projectId)
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `project_${projectId}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('プロジェクトのエクスポートに失敗:', error)
    alert('プロジェクトのエクスポートに失敗しました')
  }
}

// ファイル選択処理
async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const projectData = JSON.parse(e.target?.result as string)
        const result = await projectApi.import(projectData)
        
        // インポート後に山の座標を再計算
        // result.dataは実際のレスポンスデータ
        const importedProject = result.data as any
        if (importedProject.needs_recalculation && importedProject.id) {
          // 山の座標計算はスキップ（エラーが発生するため）
          // TODO: 山の座標計算APIのエラーを修正後に有効化
          // try {
          //   console.log('[Import] 山の座標を計算中... プロジェクトID:', importedProject.id)
          //   const mountainResult = await calculationApi.calculateMountain(importedProject.id)
          //   console.log('[Import] 山の座標計算完了:', mountainResult.data)
          //   
          //   // 少し待ってからプロジェクトリストを更新
          //   await new Promise(resolve => setTimeout(resolve, 500))
          // } catch (error) {
          //   console.error('[Import] 山の座標計算に失敗しました:', error)
          // }
        }
        
        await projectStore.loadProjects()
        showImportDialog.value = false
        alert('プロジェクトのインポートが完了しました')
      } catch (error) {
        console.error('プロジェクトのインポートに失敗:', error)
        alert('プロジェクトのインポートに失敗しました')
      }
    }
    reader.readAsText(file)
  } catch (error) {
    console.error('ファイルの読み込みに失敗:', error)
    alert('ファイルの読み込みに失敗しました')
  }
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

.header-actions {
  display: flex;
  gap: 12px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.project-card {
  background: white;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.project-card-content {
  padding: 24px;
  cursor: pointer;
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

.project-card-actions {
  position: absolute;
  top: 16px;
  right: 16px;
}

.icon-button {
  width: 36px;
  height: 36px;
  padding: 0;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-button:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
  transform: scale(1.05);
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

/* インポートエリア */
.import-area {
  padding: 40px;
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 20px;
}

.import-button {
  padding: 12px 24px;
  font-size: 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s;
}

.import-button:hover {
  background: #5a67d8;
}

.import-help {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}
</style>
