<template>
  <div class="performance-management">
    <div class="section-header">
      <h2>性能管理</h2>
      <p class="section-description">
        システムの性能を階層的に定義します。HHI分析により、詳細化すべき性能が明確になります。
      </p>
    </div>

    <div class="actions">
      <button class="primary" @click="showAddDialog = true">
        + 性能を追加
      </button>
      <button class="secondary" @click="downloadPerformanceTree" v-if="performanceTree.length > 0">
        ツリー構造をダウンロード
      </button>
    </div>

    <!-- 性能ツリー -->
    <PerformanceTree 
      v-if="performanceTree.length > 0"
      :performances="performanceTree"
      @add-child="openAddChildDialog"
      @edit="editPerformance"
      @delete="deletePerformance"
    />

    <!-- 空状態 -->
    <div v-else class="empty-state">
      <p>性能を追加してシステムの評価指標を定義してください</p>
    </div>

    <!-- 追加/編集ダイアログ -->
    <div v-if="showAddDialog || editingPerformance" class="modal-overlay" @click="closeDialog">
      <div class="modal-content" @click.stop>
        <h3>{{ editingPerformance ? '性能を編集' : '性能を追加' }}</h3>
        <form @submit.prevent="savePerformance">
          <div class="form-group">
            <label>性能名 *</label>
            <input 
              v-model="formData.name" 
              type="text" 
              required
              placeholder="例: 発電効率"
            />
          </div>

          <div class="form-group" v-if="parentPerformance">
            <label>親性能</label>
            <input 
              :value="parentPerformance.name" 
              type="text" 
              disabled
            />
          </div>

          <div class="form-group">
            <label>単位</label>
            <input 
              v-model="formData.unit" 
              type="text"
              placeholder="例: kW, km/h, kg"
            />
          </div>

          <div class="form-group">
            <label>説明</label>
            <textarea 
              v-model="formData.description" 
              rows="3"
              placeholder="この性能の詳細説明"
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="button" @click="closeDialog">
              キャンセル
            </button>
            <button type="submit" class="primary">
              {{ editingPerformance ? '更新' : '追加' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useProjectStore } from '../../stores/projectStore'
import { storeToRefs } from 'pinia'
import PerformanceTree from './PerformanceTree.vue'
import type { Performance } from '../../types/project'

const projectStore = useProjectStore()
const { performanceTree } = storeToRefs(projectStore)

const showAddDialog = ref(false)
const editingPerformance = ref<Performance | null>(null)
const parentPerformance = ref<Performance | null>(null)

const formData = ref({
  name: '',
  unit: '',
  description: '',
  parent_id: undefined as string | undefined,
  level: 0
})

function openAddChildDialog(parent: Performance) {
  parentPerformance.value = parent
  formData.value = {
    name: '',
    unit: '',
    description: '',
    parent_id: parent.id,
    level: parent.level + 1
  }
  showAddDialog.value = true
}

function editPerformance(performance: Performance) {
  editingPerformance.value = performance
  formData.value = {
    name: performance.name,
    unit: performance.unit || '',
    description: performance.description || '',
    parent_id: performance.parent_id,
    level: performance.level
  }
}

async function savePerformance() {
  try {
    if (editingPerformance.value) {
      // 更新
      await projectStore.updatePerformance(editingPerformance.value.id, {
        name: formData.value.name,
        unit: formData.value.unit,
        description: formData.value.description
      })
    } else {
      // 新規追加
      await projectStore.addPerformance(formData.value)
    }
    closeDialog()
  } catch (error) {
    alert('性能の保存に失敗しました')
  }
}

async function deletePerformance(performance: Performance) {
  if (confirm(`「${performance.name}」を削除しますか？子要素がある場合はすべて削除されます。`)) {
    try {
      await projectStore.deletePerformance(performance.id)
    } catch (error) {
      console.error('削除エラー:', error)
      alert('性能の削除に失敗しました')
    }
  }
}

function closeDialog() {
  showAddDialog.value = false
  editingPerformance.value = null
  parentPerformance.value = null
  formData.value = {
    name: '',
    unit: '',
    description: '',
    parent_id: undefined,
    level: 0
  }
}

// ツリー構造をテキスト形式に変換
function performanceTreeToText(performances: Performance[], indent: string = ''): string {
  let result = ''
  
  performances.forEach((perf, index) => {
    const isLast = index === performances.length - 1
    const connector = isLast ? '└─ ' : '├─ '
    const childIndent = indent + (isLast ? '   ' : '│  ')
    
    // 性能情報を整形
    let line = `${indent}${connector}${perf.name}`
    if (perf.unit) {
      line += ` [${perf.unit}]`
    }
    if (!perf.is_leaf) {
      line += ' (親性能)'
    }
    result += line + '\n'
    
    // 説明がある場合は追加
    if (perf.description) {
      const descLines = perf.description.split('\n')
      descLines.forEach(descLine => {
        result += `${childIndent}  ${descLine}\n`
      })
    }
    
    // 子要素を再帰的に処理
    if ((perf as any).children && (perf as any).children.length > 0) {
      result += performanceTreeToText((perf as any).children, childIndent)
    }
  })
  
  return result
}

// ツリー構造をダウンロード
function downloadPerformanceTree() {
  const project = projectStore.currentProject
  if (!project || performanceTree.value.length === 0) {
    return
  }
  
  // テキスト生成
  let content = `性能ツリー構造\n`
  content += `プロジェクト: ${project.name}\n`
  content += `生成日時: ${new Date().toLocaleString('ja-JP')}\n`
  content += `=${'='.repeat(60)}\n\n`
  content += performanceTreeToText(performanceTree.value)
  
  // ダウンロード
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `performance-tree-${project.name}-${Date.now()}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.section-header {
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.section-description {
  color: #666;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.actions button.secondary {
  background-color: #6c757d;
}

.actions button.secondary:hover {
  background-color: #5a6268;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  background: #f8f9fa;
  border-radius: 8px;
}

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
  padding: 24px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-bottom: 20px;
  font-size: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  font-size: 14px;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
}

.help-text {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
