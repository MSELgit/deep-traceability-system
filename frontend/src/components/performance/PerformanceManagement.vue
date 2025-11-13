<template>
  <div class="performance-management">
    <div class="section-header">
      <h2>Performance Management</h2>
    </div>
    <div class="actions">
      <button class="primary" @click="showAddDialog = true">
        <FontAwesomeIcon :icon="['fas', 'plus']" />
        Add Performance
      </button>
      <button class="secondary" @click="downloadPerformanceTree" v-if="performanceTree.length > 0">
        Download Tree
      </button>
    </div>
    <PerformanceTree 
      v-if="performanceTree.length > 0"
      :performances="performanceTree"
      @add-child="openAddChildDialog"
      @edit="editPerformance"
      @delete="deletePerformance"
    />
    <div v-else class="empty-state">
      <p>Add performances to define system evaluation metrics</p>
    </div>
    <div v-if="showAddDialog || editingPerformance" class="modal-overlay" @click="closeDialog">
      <div class="modal-content" @click.stop>
        <h3>{{ editingPerformance ? 'Edit Performance' : 'Add Performance' }}</h3>
        <form @submit.prevent="savePerformance">
          <div class="form-group">
            <label>Performance Name *</label>
            <input 
              v-model="formData.name" 
              type="text" 
              required
              placeholder="e.g., Power Generation Efficiency"
            />
          </div>

          <div class="form-group" v-if="parentPerformance">
            <label>Parent Performance</label>
            <input 
              :value="parentPerformance.name" 
              type="text" 
              disabled
            />
          </div>

          <div class="form-group">
            <label>Unit</label>
            <input 
              v-model="formData.unit" 
              type="text"
              placeholder="e.g., kW, km/h, kg"
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea 
              v-model="formData.description" 
              rows="3"
              placeholder="Detailed description of this performance"
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="button" @click="closeDialog">
              Cancel
            </button>
            <button type="submit" class="primary">
              {{ editingPerformance ? 'Update' : 'Add' }}
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
import PerformanceTree from './PerformanceTree.vue'
import type { Performance } from '../../types/project'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

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
  showAddDialog.value = true
}

async function savePerformance() {
  try {
    if (editingPerformance.value) {
      await projectStore.updatePerformance(editingPerformance.value.id, {
        name: formData.value.name,
        unit: formData.value.unit,
        description: formData.value.description
      })
    } else {
      await projectStore.addPerformance(formData.value)
    }
    closeDialog()
  } catch (error) {
    alert('Failed to save performance')
  }
}

async function deletePerformance(performance: Performance) {
  if (confirm(`Delete "${performance.name}"? All child elements will also be deleted.`)) {
    try {
      await projectStore.deletePerformance(performance.id)
    } catch (error) {
      console.error('Delete error:', error)
      alert('Failed to delete performance')
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

function performanceTreeToText(performances: Performance[], indent: string = ''): string {
  let result = ''
  
  performances.forEach((perf, index) => {
    const isLast = index === performances.length - 1
    const connector = isLast ? '└─ ' : '├─ '
    const childIndent = indent + (isLast ? '   ' : '│  ')
    let line = `${indent}${connector}${perf.name}`
    if (perf.unit) {
      line += ` [${perf.unit}]`
    }
    if (!perf.is_leaf) {
      line += ' (parent)'
    }
    result += line + '\n'
    if (perf.description) {
      const descLines = perf.description.split('\n')
      descLines.forEach(descLine => {
        result += `${childIndent}  ${descLine}\n`
      })
    }
    if ((perf as any).children && (perf as any).children.length > 0) {
      result += performanceTreeToText((perf as any).children, childIndent)
    }
  })
  
  return result
}

function downloadPerformanceTree() {
  const project = projectStore.currentProject
  if (!project || performanceTree.value.length === 0) {
    return
  }
  let content = `Performance Tree Structure\n`
  content += `Project: ${project.name}\n`
  content += `Generated: ${new Date().toLocaleString('en-US')}\n`
  content += `=${'='.repeat(60)}\n\n`
  content += performanceTreeToText(performanceTree.value)

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

<style scoped lang="scss">
@import '../../style/color';
.performance-management {
  padding: 2vh;
}

.section-header {
  margin-bottom: 3vh;
}

.section-header h2 {
  font-size: clamp(1.5rem, 2vw, 1.8rem);
  color: $white;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.section-description {
  color: transparentize($white, 0.4);
  font-size: clamp(0.85rem, 1vw, 0.95rem);
}

.actions {
  display: flex;
  gap: 1vw;
  margin-bottom: 3vh;
}

.primary, .secondary {
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

.primary {
  background: linear-gradient(135deg, $main_1, $main_2);
}

.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh transparentize($main_2, 0.6);
}

.secondary {
  background: transparentize($gray, 0.3);
  border: 1px solid transparentize($white, 0.8);
}

.secondary:hover {
  background: transparentize($gray, 0.1);
  border-color: transparentize($white, 0.7);
  transform: translateY(-2px);
}

.empty-state {
  text-align: center;
  padding: 8vh 2vw;
  color: transparentize($white, 0.3);
  background: lighten($gray, 5%);
  border-radius: 1vw;
  border: 1px dashed transparentize($main_1, 0.7);
  font-size: clamp(0.9rem, 1.1vw, 1rem);
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
  max-width: 600px;
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

.form-group input[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 0.8vw;
}

.help-text {
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: transparentize($white, 0.4);
  margin-top: 0.5vh;
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
