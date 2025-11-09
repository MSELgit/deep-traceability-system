<template>
  <div class="stakeholder-matrix">
    <div class="section-header">
      <h2>ステークホルダー分析</h2>
      <p class="section-description">
        関係者とニーズを登録し、それぞれの関心事をマトリクスで管理します<br>
        ただしステークホルダーとニーズの両方が登録されている場合にマトリクスが表示されます
      </p>
    </div>

    <div class="actions">
      <button class="primary" @click="showStakeholderDialog = true">
        + ステークホルダー追加
      </button>
      <button class="secondary" @click="showNeedDialog = true">
        + ニーズ追加
      </button>
      
      <div class="download-buttons">
        <button class="download-btn image" @click="downloadMatrixAsImage" title="画像としてダウンロード">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M10.5 8.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
            <path d="M2 4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-1.172a2 2 0 0 1-1.414-.586l-.828-.828A2 2 0 0 0 9.172 2H6.828a2 2 0 0 0-1.414.586l-.828.828A2 2 0 0 1 3.172 4H2zm.5 2a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm9 2.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0z"/>
          </svg>
          画像
        </button>
        <button class="download-btn excel" @click="downloadMatrixAsExcel" title="Excelファイルとしてダウンロード">
          <svg width="16" height="16" viewBox="0 0 48 48">
            <defs>
              <linearGradient id="excel-gradient" x1="5.822" y1="11.568" x2="20.178" y2="36.432" gradientUnits="userSpaceOnUse">
                <stop offset="0" stop-color="#18884f"/>
                <stop offset=".5" stop-color="#117e43"/>
                <stop offset="1" stop-color="#0b6631"/>
              </linearGradient>
            </defs>
            <path d="M29 23l-17-3v22.167A1.833 1.833 0 0 0 13.833 44h29.334A1.833 1.833 0 0 0 45 42.167V34z" fill="#185c37"/>
            <path d="M29 4H13.833A1.833 1.833 0 0 0 12 5.833V14l17 10 9 3 7-3V14z" fill="#21a366"/>
            <path fill="#107c41" d="M12 14h17v10H12z"/>
            <rect x="2" y="13" width="22" height="22" rx="1.833" fill="url(#excel-gradient)"/>
            <path d="M7.677 29.958l3.856-5.975L8 18.041h2.842l1.928 3.8c.178.361.3.629.366.806h.025q.19-.432.4-.839l2.061-3.765h2.609l-3.623 5.907 3.715 6.008h-2.776l-2.227-4.171a3.5 3.5 0 0 1-.266-.557h-.033a2.638 2.638 0 0 1-.258.54l-2.293 4.188z" fill="#fff"/>
          </svg>
          Excel
        </button>
      </div>
    </div>

    <!-- マトリクステーブル（列=ステークホルダー、行=ニーズ） -->
    <div v-if="stakeholders.length > 0 && needs.length > 0" class="matrix-container">
      <table class="matrix-table">
        <thead>
          <tr>
            <th class="corner-cell">
              <div>ステークホルダー</div>
              <div class="separator">\</div>
              <div>ニーズ</div>
            </th>
            <th v-for="stakeholder in stakeholders" :key="stakeholder.id" class="stakeholder-header">
              <div class="header-content">
                <span>{{ stakeholder.name }}</span>
                <span v-if="stakeholder.category" class="category-tag">
                  {{ stakeholder.category }}
                </span>
                <div class="votes-control">
                  <label>票数:</label>
                  <input
                    type="number"
                    v-model.number="stakeholder.votes"
                    @change="updateStakeholderVotes(stakeholder)"
                    min="0"
                    step="10"
                  />
                </div>
                <div class="action-buttons">
                  <button 
                    class="icon-btn edit" 
                    @click="editStakeholder(stakeholder)"
                    title="編集"
                  >
                    <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
                  </button>
                  <button 
                    class="icon-btn danger" 
                    @click="deleteStakeholder(stakeholder.id)"
                    title="削除"
                  >
                    <FontAwesomeIcon :icon="['fas', 'trash']" />
                  </button>
                </div>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="need in needs" :key="need.id">
            <td class="need-header">
              <div class="need-info">
                <span class="need-name">{{ need.name }}</span>
                <span v-if="need.category" class="category-tag">
                  {{ need.category }}
                </span>
                <div class="action-buttons">
                  <button 
                    class="icon-btn edit" 
                    @click="editNeed(need)"
                    title="編集"
                  >
                    <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
                  </button>
                  <button 
                    class="icon-btn danger" 
                    @click="deleteNeed(need.id)"
                    title="削除"
                  >
                    <FontAwesomeIcon :icon="['fas', 'trash']" />
                  </button>
                </div>
              </div>
            </td>
            <td 
              v-for="stakeholder in stakeholders" 
              :key="stakeholder.id"
              class="matrix-cell"
              :class="{ active: hasRelation(stakeholder.id, need.id) }"
              @click="toggleRelation(stakeholder.id, need.id)"
            >
              <div class="cell-content">
                {{ hasRelation(stakeholder.id, need.id) ? '○' : '' }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 空状態 -->
    <div v-else class="empty-matrix">
      <p>ステークホルダーとニーズを追加してマトリクスを作成してください</p>
    </div>

    <!-- ステークホルダー追加/編集ダイアログ -->
    <div v-if="showStakeholderDialog" class="modal-overlay" @click="showStakeholderDialog = false">
      <div class="modal-content" @click.stop>
        <h3>{{ editingStakeholder ? 'ステークホルダー編集' : 'ステークホルダー追加' }}</h3>
        <form @submit.prevent="saveStakeholder">
          <div class="form-group">
            <label>名前 *</label>
            <input v-model="newStakeholder.name" type="text" required />
          </div>
          <div class="form-group">
            <label>カテゴリ</label>
            <input v-model="newStakeholder.category" type="text" placeholder="例: エネルギー業界" />
          </div>
          <div class="form-group">
            <label>{{ editingStakeholder ? '票数' : '初期票数' }}</label>
            <input v-model.number="newStakeholder.votes" type="number" min="0" value="100" />
          </div>
          <div class="form-actions">
            <button type="button" @click="closeStakeholderDialog">
              キャンセル
            </button>
            <button type="submit" class="primary">
              {{ editingStakeholder ? '更新' : '追加' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ニーズ追加/編集ダイアログ -->
    <div v-if="showNeedDialog" class="modal-overlay" @click="showNeedDialog = false">
      <div class="modal-content" @click.stop>
        <h3>{{ editingNeed ? 'ニーズ編集' : 'ニーズ追加' }}</h3>
        <form @submit.prevent="saveNeed">
          <div class="form-group">
            <label>ニーズ名 *</label>
            <input v-model="newNeed.name" type="text" required />
          </div>
          <div class="form-group">
            <label>カテゴリ</label>
            <input v-model="newNeed.category" type="text" placeholder="例: 発電性" />
          </div>
          <div class="form-group">
            <label>説明</label>
            <textarea v-model="newNeed.description" rows="3"></textarea>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeNeedDialog">
              キャンセル
            </button>
            <button type="submit" class="primary">
              {{ editingNeed ? '更新' : '追加' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useProjectStore } from '../../stores/projectStore'
import { storeToRefs } from 'pinia'
import * as XLSX from 'xlsx'

const projectStore = useProjectStore()
const { stakeholders, needs, stakeholderNeedRelations } = storeToRefs(projectStore)

const showStakeholderDialog = ref(false)
const showNeedDialog = ref(false)
const editingStakeholder = ref<any>(null)
const editingNeed = ref<any>(null)

const newStakeholder = ref({
  name: '',
  category: '',
  votes: 100
})

const newNeed = ref({
  name: '',
  category: '',
  description: ''
})

function hasRelation(stakeholderId: string, needId: string): boolean {
  return stakeholderNeedRelations.value.some(
    r => r.stakeholder_id === stakeholderId && r.need_id === needId
  )
}

async function toggleRelation(stakeholderId: string, needId: string) {
  if (hasRelation(stakeholderId, needId)) {
    await projectStore.removeStakeholderNeedRelation(stakeholderId, needId)
  } else {
    await projectStore.addStakeholderNeedRelation(stakeholderId, needId)
  }
}

function editStakeholder(stakeholder: any) {
  editingStakeholder.value = stakeholder
  newStakeholder.value = {
    name: stakeholder.name,
    category: stakeholder.category || '',
    votes: stakeholder.votes || 100
  }
  showStakeholderDialog.value = true
}

function editNeed(need: any) {
  editingNeed.value = need
  newNeed.value = {
    name: need.name,
    category: need.category || '',
    description: need.description || ''
  }
  showNeedDialog.value = true
}

function closeStakeholderDialog() {
  showStakeholderDialog.value = false
  editingStakeholder.value = null
  newStakeholder.value = { name: '', category: '', votes: 100 }
}

function closeNeedDialog() {
  showNeedDialog.value = false
  editingNeed.value = null
  newNeed.value = { name: '', category: '', description: '' }
}

async function saveStakeholder() {
  try {
    if (editingStakeholder.value) {
      // 編集モード
      await projectStore.updateStakeholder(editingStakeholder.value.id, newStakeholder.value)
    } else {
      // 追加モード
      await projectStore.addStakeholder(newStakeholder.value)
    }
    closeStakeholderDialog()
  } catch (error) {
    alert(editingStakeholder.value ? 'ステークホルダーの更新に失敗しました' : 'ステークホルダーの追加に失敗しました')
  }
}

async function saveNeed() {
  try {
    if (editingNeed.value) {
      // 編集モード
      await projectStore.updateNeed(editingNeed.value.id, newNeed.value)
    } else {
      // 追加モード
      await projectStore.addNeed(newNeed.value)
    }
    closeNeedDialog()
  } catch (error) {
    alert(editingNeed.value ? 'ニーズの更新に失敗しました' : 'ニーズの追加に失敗しました')
  }
}

async function updateStakeholderVotes(stakeholder: any) {
  try {
    await projectStore.updateStakeholder(stakeholder.id, {
      name: stakeholder.name,
      votes: stakeholder.votes
    })
  } catch (error) {
    alert('票数の更新に失敗しました')
  }
}

async function deleteStakeholder(id: string) {
  if (confirm('このステークホルダーを削除しますか？')) {
    try {
      await projectStore.deleteStakeholder(id)
    } catch (error) {
      alert('ステークホルダーの削除に失敗しました')
    }
  }
}

async function deleteNeed(id: string) {
  if (confirm('このニーズを削除しますか？')) {
    try {
      await projectStore.deleteNeed(id)
    } catch (error) {
      alert('ニーズの削除に失敗しました')
    }
  }
}

// 画像ダウンロード機能
async function downloadMatrixAsImage() {
  try {
    // html2canvasを動的インポート
    const html2canvas = (await import('html2canvas')).default as any
    
    // マトリクステーブルを取得
    const matrixTable = document.querySelector('.matrix-table') as HTMLElement
    if (!matrixTable) {
      alert('マトリクステーブルが見つかりません')
      return
    }
    
    // 画像化
    const canvas = await html2canvas(matrixTable, {
      scale: 2,
      backgroundColor: '#ffffff',
      logging: false,
      useCORS: true,
      allowTaint: true
    })
    
    // ダウンロード
    canvas.toBlob((blob: Blob | null) => {
      if (!blob) {
        alert('画像データの作成に失敗しました')
        return
      }
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `ステークホルダー分析_${new Date().toISOString().slice(0, 10)}.png`
      link.click()
      URL.revokeObjectURL(url)
    }, 'image/png', 0.95)
    
  } catch (error) {
    console.error('画像生成エラー:', error)
    alert(`画像の生成に失敗しました: ${error}`)
  }
}

// Excelダウンロード機能
function downloadMatrixAsExcel() {
  // ワークブックを作成
  const wb = XLSX.utils.book_new()
  
  // マトリクスデータを配列に変換
  const matrixData: (string | number)[][] = []
  
  // ヘッダー行1: 角セル + ステークホルダー名
  const headerRow: (string | number)[] = ['ニーズ']
  stakeholders.value.forEach(sh => {
    const header = sh.category 
      ? `${sh.name} (${sh.category}) - ${sh.votes}票`
      : `${sh.name} - ${sh.votes}票`
    headerRow.push(header)
  })
  matrixData.push(headerRow)
  
  // データ行: 各ニーズ
  needs.value.forEach(need => {
    const row: (string | number)[] = []
    const needCell = need.category
      ? `${need.name} (${need.category})`
      : need.name
    row.push(needCell)
    
    // 各ステークホルダーとの関係
    stakeholders.value.forEach(sh => {
      row.push(hasRelation(sh.id, need.id) ? '○' : '')
    })
    
    matrixData.push(row)
  })
  
  // ワークシートを作成
  const ws = XLSX.utils.aoa_to_sheet(matrixData)
  
  // 列幅を自動調整
  const columnWidths = matrixData[0].map((_, colIndex) => {
    const maxLength = Math.max(
      ...matrixData.map(row => {
        const cell = row[colIndex]
        return cell ? String(cell).length : 0
      })
    )
    return { wch: Math.min(maxLength + 2, 30) }
  })
  ws['!cols'] = columnWidths
  
  XLSX.utils.book_append_sheet(wb, ws, 'ステークホルダー分析')
  
  // ファイルをダウンロード
  const filename = `ステークホルダー分析_${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, filename)
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
  align-items: center;
}

.download-buttons {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #495057;
  transition: all 0.2s ease;
}

.download-btn:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.download-btn.image:hover {
  color: #0866cc;
  border-color: #0866cc;
}

.download-btn.excel:hover {
  color: #107c41;
  border-color: #107c41;
}

.matrix-container {
  overflow-x: auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  min-width: 800px;
}

.corner-cell {
  background: #f5f5f5;
  padding: 0;
  font-weight: 600;
  border: 1px solid #ddd;
  width: 260px;
  height: 60px;
  position: relative;
  overflow: hidden;
}

.corner-cell::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(to top right, transparent 49.5%, #999 49.5%, #999 50.5%, transparent 50.5%);
}

.corner-cell > div:first-child {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 13px;
}

.corner-cell > div:last-child {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 13px;
}

.corner-cell .separator {
  display: none;
}

.stakeholder-header {
  background: #667eea;
  color: white;
  padding: 12px;
  border: 1px solid #5568d3;
  min-width: 120px;
  font-weight: 600;
  vertical-align: middle;
}

.header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 20px;
}

.votes-control {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: white;
  margin: 3px 0;
}

.votes-control label {
  font-size : 10px;
}

.votes-control input {
  width: 55px;
  padding: 4px 6px;
  font-size: 13px;
}

.need-header {
  background: #f8f9fa;
  padding: 12px;
  border: 1px solid #ddd;
  min-width: 260px;
}

.need-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.need-name {
  font-weight: 600;
  font-size: 13px;
  min-width: 134.75px;
}

.category-tag {
  background: rgba(255, 255, 255, 0.3);
  padding: 3px 15px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: normal;
  min-width: 85px;
  text-align: center;
}

.need-header .category-tag {
  background: #e0e0e0;
  color: #333;
  padding: 2px 8px;
  min-width: 50px;
}

.need-header .action-buttons {
  flex-direction: column;
  gap: 2px;
}

.matrix-cell {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.2s;
  min-width: 80px;
  min-height: 50px;
}

.matrix-cell:hover {
  background: #f0f0f0;
}

.matrix-cell.active {
  background: #d4edda;
}

.cell-content {
  font-size: 20px;
  font-weight: bold;
  color: #28a745;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.icon-btn {
  padding: 4px 8px;
  font-size: 13px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  opacity: 0.8;
  color: white;
}

.icon-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

.need-header .icon-btn {
  border-color: #ddd;
  color: #333;
}

.icon-btn.edit:hover {
  background: #e3f2fd;
  border-color: #2196f3;
  color: #2196f3;
}

.need-header .icon-btn.edit:hover {
  background: #e3f2fd;
  border-color: #2196f3;
  color: #2196f3;
}

.icon-btn.danger:hover {
  background: #fee;
  border-color: #e74c3c;
  color: #e74c3c;
}

.empty-matrix {
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
  max-width: 500px;
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

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>