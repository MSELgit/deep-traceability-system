<template>
  <div class="stakeholder-matrix">
    <div class="actions">
      <button class="action-btn stakeholder-btn" @click="showStakeholderDialog = true">
        <FontAwesomeIcon :icon="['fas', 'plus']" />
        Add Stakeholder
      </button>
      <button class="action-btn need-btn" @click="showNeedDialog = true">
        <FontAwesomeIcon :icon="['fas', 'plus']" />
        Add Need
      </button>
      
      <div class="download-buttons">
        <button class="download-btn image" @click="downloadMatrixAsImage" title="Download as Image">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M10.5 8.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
            <path d="M2 4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-1.172a2 2 0 0 1-1.414-.586l-.828-.828A2 2 0 0 0 9.172 2H6.828a2 2 0 0 0-1.414.586l-.828.828A2 2 0 0 1 3.172 4H2zm.5 2a.5.5 0 1 1 0-1 .5.5 0 0 1 0 1zm9 2.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0z"/>
          </svg>
          Image
        </button>
        <button class="download-btn excel" @click="downloadMatrixAsExcel" title="Download as Excel">
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

    <div v-if="stakeholders.length > 0 && needs.length > 0" class="matrix-container">
      <table class="matrix-table">
        <thead>
          <tr>
            <th class="corner-cell">
              <div>Stakeholders</div>
              <div class="separator">\</div>
              <div>Needs</div>
            </th>
            <th v-for="stakeholder in stakeholders" :key="stakeholder.id" class="stakeholder-header">
              <div class="header-content">
                <span>{{ stakeholder.name }}</span>
                <span v-if="stakeholder.category" class="category-tag">
                  {{ stakeholder.category }}
                </span>
                <div class="votes-control">
                  <label>Votes:</label>
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
                    title="Edit"
                  >
                    <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
                  </button>
                  <button 
                    class="icon-btn danger" 
                    @click="deleteStakeholder(stakeholder.id)"
                    title="Delete"
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
                    title="Edit"
                  >
                    <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
                  </button>
                  <button 
                    class="icon-btn danger" 
                    @click="deleteNeed(need.id)"
                    title="Delete"
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
              :class="getRelationshipClass(stakeholder.id, need.id)"
              @click="toggleRelation(stakeholder.id, need.id)"
            >
              <div class="cell-content" :class="getRelationshipContentClass(stakeholder.id, need.id)">
                {{ getRelationshipSymbol(stakeholder.id, need.id) }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-matrix">
      <p>Add stakeholders and needs to create a matrix</p>
    </div>

    <!-- Add/Edit Stakeholder Dialog -->
    <div v-if="showStakeholderDialog" class="modal-overlay" @click="showStakeholderDialog = false">
      <div class="modal-content" @click.stop>
        <h3>{{ editingStakeholder ? 'Edit Stakeholder' : 'Add Stakeholder' }}</h3>
        <form @submit.prevent="saveStakeholder">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="newStakeholder.name" type="text" required />
          </div>
          <div class="form-group">
            <label>Category</label>
            <input v-model="newStakeholder.category" type="text" placeholder="e.g., Energy Industry" />
          </div>
          <div class="form-group">
            <label>{{ editingStakeholder ? 'Votes' : 'Initial Votes' }}</label>
            <input v-model.number="newStakeholder.votes" type="number" min="0" value="100" />
          </div>
          <div class="form-actions">
            <button type="button" @click="closeStakeholderDialog">
              Cancel
            </button>
            <button type="submit" class="primary">
              {{ editingStakeholder ? 'Update' : 'Add' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add/Edit Need Dialog -->
    <div v-if="showNeedDialog" class="modal-overlay" @click="showNeedDialog = false">
      <div class="modal-content" @click.stop>
        <h3>{{ editingNeed ? 'Edit Need' : 'Add Need' }}</h3>
        <form @submit.prevent="saveNeed">
          <div class="form-group">
            <label>Need Name *</label>
            <input v-model="newNeed.name" type="text" required />
          </div>
          <div class="form-group">
            <label>Category</label>
            <input v-model="newNeed.category" type="text" placeholder="e.g., Power Generation" />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newNeed.description" rows="3"></textarea>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeNeedDialog">
              Cancel
            </button>
            <button type="submit" class="primary">
              {{ editingNeed ? 'Update' : 'Add' }}
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
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

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

function getRelationshipWeight(stakeholderId: string, needId: string): number {
  const relation = stakeholderNeedRelations.value.find(
    r => r.stakeholder_id === stakeholderId && r.need_id === needId
  )
  return relation?.relationship_weight || 0
}

function hasRelation(stakeholderId: string, needId: string): boolean {
  return getRelationshipWeight(stakeholderId, needId) > 0
}

function getRelationshipSymbol(stakeholderId: string, needId: string): string {
  const weight = getRelationshipWeight(stakeholderId, needId)
  if (weight === 1.0) return '○'
  if (weight === 0.5) return '△'
  return ''
}

function getRelationshipClass(stakeholderId: string, needId: string): string {
  const weight = getRelationshipWeight(stakeholderId, needId)
  if (weight === 1.0) return 'active full-weight'
  if (weight === 0.5) return 'active half-weight'
  return ''
}

function getRelationshipContentClass(stakeholderId: string, needId: string): string {
  const weight = getRelationshipWeight(stakeholderId, needId)
  if (weight === 1.0) return 'full-weight-text'
  if (weight === 0.5) return 'half-weight-text'
  return ''
}

async function toggleRelation(stakeholderId: string, needId: string) {
  const currentWeight = getRelationshipWeight(stakeholderId, needId)
  
  if (currentWeight === 0) {
    // 空白 → 緑○ (1.0)
    await projectStore.addStakeholderNeedRelation(stakeholderId, needId, 1.0)
  } else if (currentWeight === 1.0) {
    // 緑○ → 黄△ (0.5)
    await projectStore.updateStakeholderNeedRelation(stakeholderId, needId, 0.5)
  } else if (currentWeight === 0.5) {
    // 黄△ → 空白 (削除)
    await projectStore.removeStakeholderNeedRelation(stakeholderId, needId)
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
    alert(editingStakeholder.value ? 'Failed to update stakeholder' : 'Failed to add stakeholder')
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
    alert(editingNeed.value ? 'Failed to update need' : 'Failed to add need')
  }
}

async function updateStakeholderVotes(stakeholder: any) {
  try {
    await projectStore.updateStakeholder(stakeholder.id, {
      name: stakeholder.name,
      category: stakeholder.category,
      votes: stakeholder.votes
    })
  } catch (error) {
    alert('Failed to update votes')
  }
}

async function deleteStakeholder(id: string) {
  if (confirm('Delete this stakeholder?')) {
    try {
      await projectStore.deleteStakeholder(id)
    } catch (error) {
      alert('Failed to delete stakeholder')
    }
  }
}

async function deleteNeed(id: string) {
  if (confirm('Delete this need?')) {
    try {
      await projectStore.deleteNeed(id)
    } catch (error) {
      alert('Failed to delete need')
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
      alert('Matrix table not found')
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
        alert('Failed to create image data')
        return
      }
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Stakeholder_Analysis_${new Date().toISOString().slice(0, 10)}.png`
      link.click()
      URL.revokeObjectURL(url)
    }, 'image/png', 0.95)
    
  } catch (error) {
    console.error('Image generation error:', error)
    alert(`Failed to generate image: ${error}`)
  }
}

// Excelダウンロード機能
function downloadMatrixAsExcel() {
  // ワークブックを作成
  const wb = XLSX.utils.book_new()
  
  // マトリクスデータを配列に変換
  const matrixData: (string | number)[][] = []
  
  // Header row 1: corner cell + stakeholder names
  const headerRow: (string | number)[] = ['Needs']
  stakeholders.value.forEach(sh => {
    const header = sh.category 
      ? `${sh.name} (${sh.category}) - ${sh.votes} votes`
      : `${sh.name} - ${sh.votes} votes`
    headerRow.push(header)
  })
  matrixData.push(headerRow)
  
  // Data rows: each need
  needs.value.forEach(need => {
    const row: (string | number)[] = []
    const needCell = need.category
      ? `${need.name} (${need.category})`
      : need.name
    row.push(needCell)
    
    // Relationship with each stakeholder
    stakeholders.value.forEach(sh => {
      const symbol = getRelationshipSymbol(sh.id, need.id)
      row.push(symbol)
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
  
  XLSX.utils.book_append_sheet(wb, ws, 'Stakeholder Analysis')
  
  // Download file
  const filename = `Stakeholder_Analysis_${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, filename)
}
</script>

<style scoped lang="scss">
@import '../../style/color';
.stakeholder-matrix {
  padding: 2vh;
}

.actions {
  display: flex;
  gap: 1vw;
  margin-bottom: 3vh;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  padding: 1.5vh 1.5vw;
  border-radius: 0.5vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  color: $white;
}

.stakeholder-btn {
  background: linear-gradient(135deg, $main_3, darken($main_3, 10%));
}

.stakeholder-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh transparentize($main_3, 0.6);
  background: linear-gradient(135deg, lighten($main_3, 5%), $main_3);
}

.need-btn {
  background: linear-gradient(135deg, $main_2, darken($main_2, 10%));
}

.need-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh transparentize($main_2, 0.6);
  background: linear-gradient(135deg, lighten($main_2, 5%), $main_2);
}

.download-buttons {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  padding: 1.2vh 1.2vw;
  background: $white;
  border: 1px solid darken($white, 12%);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 0.95vw, 0.9rem);
  font-weight: 500;
  color: lighten($black, 10%);
  transition: all 0.2s ease;
}

.download-btn:hover {
  background: lighten($white, 3%);
  border-color: transparentize($black, 0.3);
}

.download-btn.image:hover {
  color: $sub_6;
  border-color: $sub_6;
}

.download-btn.excel:hover {
  color: $sub_4;
  border-color: $sub_4;
}

.matrix-container {
  overflow-x: auto;
  border-radius: 1vw;
  box-shadow: 0 0.5vh 2vh transparentize($black, 0.5);
  background: $white;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  background: $white;
  min-width: 800px;
}

.corner-cell {
  background: lighten($white, 2%);
  padding: 0;
  font-weight: 600;
  border: 1px solid darken($white, 10%);
  width: 260px;
  height: 60px;
  position: relative;
  overflow: hidden;
  color: $black;
}

.corner-cell::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(to top right, transparent 49.5%, transparentize($black, 0.4) 49.5%, transparentize($black, 0.4) 50.5%, transparent 50.5%);
}

.corner-cell > div:first-child {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 13px;
  color: $black;
}

.corner-cell > div:last-child {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 13px;
  color: $black;
}

.corner-cell .separator {
  display: none;
}

.stakeholder-header {
  background: $main_1;
  color: $white;
  padding: 12px;
  border: 1px solid darken($main_1, 10%);
  min-width: 140px;
  font-weight: 600;
  vertical-align: middle;
}

.stakeholder-header span {
  color: $white;
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
  color: $white;
  margin: 3px 0;
}

.votes-control input {
  width: 55px;
  padding: 4px 6px;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 4px;
  color: $white;
}

.votes-control label {
  font-size : 10px;
  color: $white;
}

.need-header {
  background: lighten($white, 3%);
  padding: 12px;
  border: 1px solid darken($white, 10%);
  min-width: 260px;
  color: $black;
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
  color: $black;
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
  background: darken($white, 8%);
  color: $black;
  padding: 2px 8px;
  min-width: 50px;
}

.need-header .action-buttons {
  flex-direction: column;
  gap: 2px;
}

.matrix-cell {
  border: 1px solid darken($white, 10%);
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.2s;
  min-width: 80px;
  min-height: 50px;
  background: $white;
}

.matrix-cell:hover {
  background: lighten($white, 1%);
}

.matrix-cell.active {
  background: lighten($sub_4, 40%);
}

.cell-content {
  font-size: 20px;
  font-weight: bold;
  color: $sub_4;
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
  color: $white;
}

.icon-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

.need-header .icon-btn {
  border-color: darken($white, 10%);
  color: $black;
}

.icon-btn.edit:hover {
  background: lighten($sub_6, 40%);
  border-color: $sub_6;
  color: $sub_6;
}

.need-header .icon-btn.edit:hover {
  background: lighten($sub_6, 40%);
  border-color: $sub_6;
  color: $sub_6;
}

.icon-btn.danger:hover {
  background: lighten($sub_1, 45%);
  border-color: $sub_1;
  color: $sub_1;
}

.empty-matrix {
  text-align: center;
  padding: 8vh 2vw;
  color: transparentize($white, 0.3);
  background: lighten($gray, 5%);
  border-radius: 1vw;
  border: 1px dashed transparentize($main_1, 0.7);
  font-size: clamp(0.9rem, 1.1vw, 1rem);
}

// 3択システム用のスタイル
.matrix-cell.full-weight {
  background: lighten($sub_4, 40%);
  border-color: $sub_4;
}

.matrix-cell.half-weight {
  background: lighten(#FFA500, 40%);
  border-color: #FFA500;
}

.cell-content.full-weight-text {
  color: $sub_4;
  font-weight: bold;
}

.cell-content.half-weight-text {
  color: #FFA500;
  font-weight: bold;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparentize($black, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: $gray;
  border: 1px solid transparentize($white, 0.9);
  border-radius: 1vw;
  padding: 3vh 3vw;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 2vh 6vh transparentize($black, 0.5);
}

.modal-content h3 {
  margin-bottom: 2.5vh;
  font-size: clamp(1.3rem, 1.8vw, 1.6rem);
  color: $white;
  font-weight: 600;
}

.form-group {
  margin-bottom: 2vh;
}

.form-group label {
  display: block;
  margin-bottom: 0.8vh;
  font-weight: 600;
  color: $white;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 1vh 1vw;
  background: transparentize($black, 0.3);
  border: 1px solid transparentize($white, 0.9);
  border-radius: 0.5vw;
  color: $white;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  transition: all 0.3s ease;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: $main_1;
  background: transparentize($black, 0.1);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: transparentize($main_1, 0.3);
}

.form-actions {
  display: flex;
  gap: 1vw;
  justify-content: flex-end;
  margin-top: 3vh;
}

.form-actions button {
  padding: 1vh 1.5vw;
  border-radius: 0.5vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.form-actions button[type="button"] {
  background: transparentize($gray, 0.5);
  color: $white;
  border: 1px solid transparentize($white, 0.8);
}

.form-actions button[type="button"]:hover {
  background: transparentize($gray, 0.3);
  border-color: transparentize($white, 0.7);
}
</style>