<template>
  <div class="project-list">
    <div class="container">
      <div class="page-header-section">
        <h1>Projects</h1>
        <div class="header-actions">
          <button class="secondary" @click="showImportDialog = true">
            <FontAwesomeIcon :icon="['fas', 'file-import']" />
            Import
          </button>
          <button class="primary" @click="showCreateDialog = true">
            <FontAwesomeIcon :icon="['fas', 'plus']" />
            New Project
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading projects...</p>
      </div>

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
              <span class="meta-label">Created:</span>
              <span>{{ formatDate(project.created_at) }}</span>
            </div>
          </div>
          <div class="project-card-actions">
            <button 
              class="icon-button export" 
              @click.stop="exportProject(project.id)"
              title="Export project"
            >
              <FontAwesomeIcon :icon="['fas', 'share-from-square']" />
            </button>
            <button 
              class="icon-button delete" 
              @click.stop="deleteProject(project.id, project.name)"
              title="Delete project"
            >
              <FontAwesomeIcon :icon="['fas', 'trash']" />
            </button>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">
          <FontAwesomeIcon :icon="['fas', 'folder-open']" />
        </div>
        <h3>No Projects Yet</h3>
        <p>Create your first project to get started</p>
        <button class="primary" @click="showCreateDialog = true">
          <FontAwesomeIcon :icon="['fas', 'plus']" />
          Create Project
        </button>
      </div>

      <!-- File Select Dialog -->
      <div v-if="showImportDialog" class="modal-overlay" @click="showImportDialog = false">
        <div class="modal-content" @click.stop>
          <h2>Import Project</h2>
          <div class="import-area">
            <input
              type="file"
              @change="handleFileSelect"
              accept=".json"
              ref="fileInput"
              style="display: none"
            />
            <FontAwesomeIcon :icon="['fas', 'cloud-upload-alt']" class="import-icon" />
            <button
              class="import-button"
              @click="fileInput?.click()"
              :disabled="isLoadingPreview"
            >
              {{ isLoadingPreview ? 'Analyzing...' : 'Select File' }}
            </button>
            <p class="import-help">Choose a project file (.json) to import</p>
          </div>
          <div class="form-actions">
            <button type="button" @click="showImportDialog = false" :disabled="isLoadingPreview">
              Cancel
            </button>
          </div>
        </div>
      </div>

      <!-- Import Preview Dialog -->
      <ImportPreviewDialog
        v-if="showPreviewDialog && importPreview"
        :visible="showPreviewDialog"
        :preview="importPreview"
        @confirm="confirmImport"
        @cancel="cancelImport"
      />

      <div v-if="showCreateDialog" class="modal-overlay" @click="showCreateDialog = false">
        <div class="modal-content" @click.stop>
          <h2>New Project</h2>
          <form @submit.prevent="createNewProject">
            <div class="form-group">
              <label>Project Name *</label>
              <input 
                v-model="newProjectName" 
                type="text" 
                placeholder="e.g., Offshore Wind Power System"
                required
              />
            </div>
            <div class="form-group">
              <label>Description</label>
              <textarea 
                v-model="newProjectDescription" 
                rows="3"
                placeholder="Brief description of your project (optional)"
              ></textarea>
            </div>
            <div class="form-actions">
              <button type="button" @click="showCreateDialog = false">
                Cancel
              </button>
              <button type="submit" class="primary" :disabled="!newProjectName">
                Create Project
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
import { projectApi, type ImportPreviewResponse } from '../utils/api'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import ImportPreviewDialog from '../components/common/ImportPreviewDialog.vue'

const router = useRouter()
const projectStore = useProjectStore()
const { projects, loading } = storeToRefs(projectStore)

const showCreateDialog = ref(false)
const showImportDialog = ref(false)
const showPreviewDialog = ref(false)
const isLoadingPreview = ref(false)
const newProjectName = ref('')
const newProjectDescription = ref('')
const fileInput = ref<HTMLInputElement>()

// Import preview state
const importPreview = ref<ImportPreviewResponse | null>(null)
const pendingImportData = ref<any>(null)

onMounted(async () => {
  try {
    await projectStore.loadProjects()
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
})

async function createNewProject() {
  try {
    const project = await projectStore.createProject(
      newProjectName.value,
      newProjectDescription.value
    )
    newProjectName.value = ''
    newProjectDescription.value = ''
    showCreateDialog.value = false
    router.push(`/project/${project.id}`)
  } catch (error) {
    console.error('Failed to create project:', error)
    alert('Failed to create project')
  }
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

async function exportProject(projectId: string) {
  try {
    const response = await projectApi.export(projectId)
    const exportedPath = response.data._exported_path
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `project_${projectId}_${new Date().toISOString().split('T')[0]}.json`
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

async function deleteProject(projectId: string, projectName: string) {
  const confirmed = confirm(`Delete project "${projectName}"?\n\nThis action cannot be undone.`)
  if (!confirmed) return
  try {
    await projectApi.delete(projectId)
    await projectStore.loadProjects()
    alert('Project deleted successfully')
  } catch (error) {
    console.error('Failed to delete project:', error)
    alert('Failed to delete project')
  }
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  isLoadingPreview.value = true

  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const projectData = JSON.parse(e.target?.result as string)

        // Get preview first
        const previewResponse = await projectApi.importPreview(projectData)
        importPreview.value = previewResponse.data
        pendingImportData.value = projectData

        // Close file dialog and show preview dialog
        showImportDialog.value = false
        showPreviewDialog.value = true
      } catch (error) {
        console.error('Failed to analyze import:', error)
        alert('Failed to analyze import file. Please check the file format.')
      } finally {
        isLoadingPreview.value = false
        // Reset file input
        if (fileInput.value) {
          fileInput.value.value = ''
        }
      }
    }
    reader.readAsText(file)
  } catch (error) {
    console.error('Failed to read file:', error)
    alert('Failed to read file')
    isLoadingPreview.value = false
  }
}

async function confirmImport(userChoices: Record<string, any>) {
  if (!pendingImportData.value) return

  try {
    await projectApi.import(pendingImportData.value, userChoices)
    await projectStore.loadProjects()

    showPreviewDialog.value = false
    importPreview.value = null
    pendingImportData.value = null

    alert('Project imported successfully')
  } catch (error) {
    console.error('Failed to import project:', error)
    alert('Failed to import project')
  }
}

function cancelImport() {
  showPreviewDialog.value = false
  importPreview.value = null
  pendingImportData.value = null
}
</script>

<style scoped lang="scss">
@import '../style/color';

.project-list {
  min-height: calc(100vh - 120px);
  background: $black;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2vh 3vw;
}

.page-header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4vh;
  padding-bottom: 2vh;
  border-bottom: 1px solid transparentize($white, 0.95);
}

.page-header-section h1 {
  font-size: clamp(2.2rem, 3.5vw, 3rem);
  color: $white;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, $white, transparentize($white, 0.15));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-actions {
  display: flex;
  gap: 1vw;
}

.secondary {
  background: transparentize($gray, 0.5);
  color: $white;
  border: 1px solid transparentize($white, 0.8);
  padding: 1.5vh 1.5vw;
  border-radius: 0.5vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5vw;
  transition: all 0.3s ease;
}

.secondary:hover {
  background: transparentize($gray, 0.3);
  border-color: transparentize($white, 0.7);
}

.primary {
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border: none;
  padding: 1.5vh 1.5vw;
  border-radius: 0.5vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5vw;
  transition: all 0.3s ease;
}

.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh transparentize($main_2, 0.6);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

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
  border: 3px solid transparentize($white, 0.95);
  border-top-color: $main_1;
  border-right-color: $main_2;
  border-radius: 50%;
  margin: 0 auto 3vh;
  animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
  box-shadow: 0 0 2vh transparentize($main_1, 0.8);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading p {
  color: transparentize($white, 0.2);
  font-size: clamp(1rem, 1.2vw, 1.1rem);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2.5vw;
}

.project-card {
  background: linear-gradient(145deg, lighten($gray, 12%), lighten($gray, 8%));
  border: 1px solid transparentize($white, 0.85);
  border-radius: 1.2vw;
  padding: 0;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
  box-shadow: 0 0.8vh 3vh transparentize($black, 0.2);
}

.project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 0.4vh;
  background: linear-gradient(90deg, $main_1, $main_2);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.project-card:hover {
  transform: translateY(-0.8vh) scale(1.02);
  border-color: transparentize($main_1, 0.5);
  box-shadow: 0 1.5vh 4vh transparentize($main_1, 0.6);
  background: linear-gradient(145deg, lighten($gray, 15%), lighten($gray, 10%));
}

.project-card:hover::before {
  transform: scaleX(1);
}

.project-card-content {
  padding: 3vh 2.5vw;
  cursor: pointer;
  min-height: 18vh;
  display: flex;
  flex-direction: column;
}

.project-card h3 {
  font-size: clamp(1.2rem, 1.6vw, 1.5rem);
  margin-bottom: 1.5vh;
  color: $white;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.project-card p {
  color: transparentize($white, 0.15);
  margin-bottom: auto;
  line-height: 1.7;
  font-size: clamp(0.9rem, 1.05vw, 1rem);
  font-weight: 400;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  color: lighten($main_1, 20%);
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  margin-top: 2vh;
  padding-top: 2vh;
  border-top: 1px solid transparentize($white, 0.9);
}

.meta-label {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: transparentize($white, 0.3);
}

.project-card-actions {
  position: absolute;
  top: 2vh;
  right: 2vw;
  display: flex;
  gap: 0.8vw;
  opacity: 0.9;
  transition: opacity 0.3s ease;
}

.project-card:hover .project-card-actions {
  opacity: 1;
}

.icon-button {
  width: 40px;
  height: 40px;
  padding: 0;
  background: transparentize($black, 0.1);
  border: 1px solid transparentize($white, 0.85);
  border-radius: 0.8vw;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  color: $white;
  backdrop-filter: blur(10px);
  box-shadow: 0 0.3vh 1vh transparentize($black, 0.5);
}

.icon-button.export:hover {
  background: linear-gradient(135deg, $main_1, darken($main_1, 10%));
  border-color: $main_1;
  transform: scale(1.15) rotate(-5deg);
  color: $white;
  box-shadow: 0 0.5vh 1.5vh transparentize($main_1, 0.5);
}

.icon-button.delete:hover {
  background: linear-gradient(135deg, $sub_1, darken($sub_1, 10%));
  border-color: $sub_1;
  transform: scale(1.15) rotate(5deg);
  color: $white;
  box-shadow: 0 0.5vh 1.5vh transparentize($sub_1, 0.5);
}

.empty-state {
  text-align: center;
  padding: 12vh 2vw;
  background: linear-gradient(145deg, lighten($gray, 8%), lighten($gray, 5%));
  border-radius: 2vw;
  border: 1px solid transparentize($white, 0.9);
}

.empty-icon {
  font-size: 6vw;
  color: $main_1;
  margin-bottom: 3vh;
  opacity: 0.3;
  filter: drop-shadow(0 1vh 2vh transparentize($main_1, 0.8));
}

.empty-state h3 {
  font-size: clamp(1.8rem, 2.5vw, 2.2rem);
  color: $white;
  margin-bottom: 1.5vh;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.empty-state p {
  color: transparentize($white, 0.3);
  margin-bottom: 4vh;
  font-size: clamp(1rem, 1.2vw, 1.1rem);
  font-weight: 400;
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
  padding: 2vh 3vw;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 2vh 6vh transparentize($black, 0.5);
}

.modal-content h2 {
  margin-bottom: 2.5vh;
  font-size: clamp(1.3rem, 2vw, 1.8rem);
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

.import-area {
  padding: 4vh 3vw;
  border: 2px dashed transparentize($main_1, 0.5);
  border-radius: 0.8vw;
  text-align: center;
  margin-bottom: 2vh;
  background: transparentize($black, 0.5);
}

.import-icon {
  font-size: 3vw;
  color: $main_1;
  margin-bottom: 2vh;
  display: block;
}

.import-button {
  padding: 1vh 2vw;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.import-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh transparentize($main_2, 0.6);
}

.import-help {
  margin-top: 1.5vh;
  color: lighten($main_1, 10%);
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
}
</style>