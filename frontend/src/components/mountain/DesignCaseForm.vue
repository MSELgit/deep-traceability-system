<template>
  <div class="design-case-form">
    <div class="form-header">
      <h2>{{ isEdit ? 'Edit Design Case' : 'Create New Design Case' }}</h2>
      <button class="back-btn" @click="$emit('cancel')">← Back</button>
    </div>

    <div class="form-content">
      <!-- Performance mismatch warning -->
      <div v-if="isEdit && !isEditable" class="performance-mismatch-warning">
        <div class="warning-icon"><FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" /></div>
        <div class="warning-content">
          <div class="warning-title">Cannot Edit</div>
          <div class="warning-message">
            The performance tree has been modified since this design case was created. Edit is disabled (view only).
          </div>
        </div>
      </div>

      <!-- Basic Information -->
      <section class="form-section">
        <h3>Basic Information</h3>
        
        <div class="form-group">
          <label>Name <span class="required">*</span></label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="e.g., Design Case 1"
            class="form-input"
            :disabled="isEdit && !isEditable"
          />
        </div>

        <div class="form-group">
          <label>Description</label>
          <textarea
            v-model="formData.description"
            placeholder="Enter description for this design case..."
            class="form-textarea"
            rows="3"
            :disabled="isEdit && !isEditable"
          ></textarea>
        </div>

        <div class="form-group">
          <label>Display Color</label>
          <div class="color-picker-wrapper">
            <input
              v-model="formData.color"
              type="color"
              class="color-input"
              :disabled="isEdit && !isEditable"
            />
            <span class="color-value">{{ formData.color }}</span>
          </div>
        </div>
      </section>

      <!-- Performance Value Input -->
      <section class="form-section">
        <h3>Enter Performance Values</h3>

        <div class="performance-table">
          <div class="table-header">
            <div class="col-performance">Performance</div>
            <div class="col-value">Value</div>
            <div class="col-unit">Unit</div>
          </div>

          <div
            v-for="perf in displayPerformances"
            :key="perf.id"
            class="table-row"
          >
            <div class="col-performance">
              <span class="perf-name">{{ perf.name }}</span>
            </div>

            <div class="col-value">
              <!-- For discrete values: Select box -->
              <select
                v-if="isDiscretePerformance(perf.id)"
                v-model="formData.performance_values[perf.id]"
                class="value-select"
                :disabled="isEdit && !isEditable"
              >
                <option value="" disabled>Please select</option>
                <option
                  v-for="option in getDiscreteOptions(perf.id)"
                  :key="option"
                  :value="option"
                >
                  {{ option }}
                </option>
              </select>
              
              <!-- For continuous values: Number input + unit -->
              <div v-else class="value-input-wrapper">
                <input
                  v-model.number="formData.performance_values[perf.id]"
                  type="number"
                  step="any"
                  class="value-input"
                  :placeholder="'Enter value'"
                  :disabled="isEdit && !isEditable"
                />
              </div>
            </div>
            <div class="col-unit">
              <span class="unit-text">{{ perf.unit || '-' }}</span>
            </div>
          </div>

          <div v-if="displayPerformances.length === 0" class="empty-performances">
            <p>No performances defined</p>
            <p class="empty-hint">Please create performances in the "Performance Management" tab first</p>
          </div>
        </div>

        <!-- Input Status -->
        <div class="input-status" :class="{ complete: isAllPerformancesFilled }">
          <span v-if="isAllPerformancesFilled" class="status-icon">✓</span>
          <span v-else class="status-icon"><FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" /></span>
          {{ filledCount }} / {{ displayPerformances.length }} filled
        </div>
      </section>

      <!-- ★ Network Display Section -->
      <section class="form-section network-section">
        <div class="section-header-with-action">
          <div>
            <h3><FontAwesomeIcon :icon="['fas', 'hexagon-nodes']" /> Network Structure</h3>
          </div>
          <button 
            class="edit-network-btn" 
            @click="showNetworkEditor = true"
            :disabled="isEdit && !isEditable"
          >
            <FontAwesomeIcon :icon="['fas', 'pen-to-square']" /> Edit
          </button>
        </div>
        
        <div class="network-viewer-wrapper">
          <NetworkViewer
            :network="formData.network"
            :performances="performances"
          />
        </div>
        <!--<p>{{ formData.network }}</p>-->
      </section>
    </div>

    <!-- Footer -->
    <div class="form-footer">
      <button class="btn-cancel" @click="$emit('cancel')">Cancel</button>
      <button 
        class="btn-save" 
        @click="handleSave"
        :disabled="!isValid"
      >
        {{ isEdit ? 'Update' : 'Create' }}
      </button>
    </div>

    <!-- Network Edit Modal -->
    <div v-if="showNetworkEditor" class="network-editor-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Edit Network</h2>
          <div class="modal-header-actions">
            <button class="save-network-btn" @click="handleNetworkSave" :disabled="!isValid">
              <FontAwesomeIcon :icon="['fas', 'floppy-disk']" /> Save and Close
            </button>
            <button class="close-btn" @click="showNetworkEditor = false">✕</button>
          </div>
        </div>
        <div class="modal-body">
          <!-- SCC Warning Banner -->
          <SCCWarningBanner
            v-if="showSccWarning"
            :scc-result="sccResult"
            :show-info="false"
            @continue="handleSccContinue"
            @dismiss="handleSccDismiss"
          />

          <!-- SCC Checking Indicator -->
          <div v-if="sccChecking" class="scc-checking">
            <div class="spinner"></div>
            <span>Checking for loops...</span>
          </div>

          <NetworkEditor
            v-model="formData.network"
            :performances="performances"
            :weight-mode="formData.weight_mode"
            @update:weight-mode="formData.weight_mode = $event"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, inject } from 'vue';
import type { DesignCase, Performance, DesignCaseCreate, NeedPerformanceRelation, UtilityFunction, NetworkStructure, WeightMode } from '../../types/project';
import { migrateNetworkEdges, needsEdgeMigration } from '../../types/project';
import { useProjectStore } from '../../stores/projectStore';
import { storeToRefs } from 'pinia';
import NetworkEditor from '../network/NetworkEditor.vue';
import NetworkViewer from '../network/NetworkViewer.vue';
import SCCWarningBanner from '../analysis/SCCWarningBanner.vue';
import { sccApi } from '../../utils/api';
import type { SCCAnalysisResult } from '../../utils/api';
import { isDesignCaseEditable, getPerformanceMismatchMessage, createPerformanceIdMapping, remapNetworkPerformanceIds } from '../../utils/performanceComparison';

const props = defineProps<{
  designCase: DesignCase | null;
  performances: Performance[];  // Current performance tree (used when creating new)
}>();

const showNetworkEditor = ref(false);

// SCC analysis state
const sccResult = ref<SCCAnalysisResult | null>(null);
const sccChecking = ref(false);
const showSccWarning = ref(false);

// Control scroll by monitoring network editor modal show/hide
watch(showNetworkEditor, (isOpen) => {
  if (isOpen) {
    // Disable scroll when modal opens
    document.body.style.overflow = 'hidden';
  } else {
    // Re-enable scroll when modal closes
    document.body.style.overflow = '';
  }
});

// Re-enable scroll when component is unmounted
onUnmounted(() => {
  document.body.style.overflow = '';
});
const emit = defineEmits<{
  save: [data: DesignCaseCreate];
  cancel: [];
}>();

const projectStore = useProjectStore();
const { currentProject } = storeToRefs(projectStore);

const isEdit = computed(() => props.designCase !== null);

// Sort performances by tree structure (depth-first search)
const sortPerformancesByTree = (performances: any[]): any[] => {
  if (!performances || performances.length === 0) return [];
  
  // Create parent-child relationship map
  const childrenMap = new Map<string | null, any[]>();
  performances.forEach(perf => {
    const parentId = perf.parent_id || null;
    if (!childrenMap.has(parentId)) {
      childrenMap.set(parentId, []);
    }
    childrenMap.get(parentId)!.push(perf);
  });
  
  // Sort each group by name
  childrenMap.forEach((children) => {
    children.sort((a, b) => a.name.localeCompare(b.name));
  });
  
  // Build order with depth-first search
  const result: any[] = [];
  const traverse = (parentId: string | null) => {
    const children = childrenMap.get(parentId) || [];
    children.forEach(child => {
      result.push(child);
      traverse(child.id);
    });
  };
  
  traverse(null); // Start from root
  return result;
};

// Performance list to display (snapshot when editing, current leaf performances when creating)
const displayPerformances = computed(() => {
  if (isEdit.value && props.designCase?.performance_snapshot) {
    // Edit mode: Extract only leaf performances from snapshot (snapshot is already sorted)
    return props.designCase.performance_snapshot.filter(p => p.is_leaf);
  } else {
    // Create mode: Use current leaf performances (already sorted)
    return props.performances;
  }
});

// Performance tree consistency check
const isEditable = computed(() => {
  // Create mode is always editable
  if (!isEdit.value) return true;
  
  // In edit mode, check performance_snapshot consistency
  const designCase = props.designCase;
  
  if (!designCase || !designCase.performance_snapshot || designCase.performance_snapshot.length === 0) {
    // Editable if no snapshot (backward compatibility)
    return true;
  }
  
  // Get all performances (both leaf and parent)
  const allCurrentPerformances = currentProject.value?.performances || [];
  
  // Compare all performance tree with saved snapshot
  const result = isDesignCaseEditable(allCurrentPerformances, designCase.performance_snapshot);
  
  return result;
});

// Performance mismatch detail message
const performanceMismatchWarning = computed(() => {
  if (!isEdit.value || isEditable.value) return '';
  
  const designCase = props.designCase;
  if (!designCase || !designCase.performance_snapshot) return '';
  
  // Use all performances
  const allCurrentPerformances = currentProject.value?.performances || [];
  
  return getPerformanceMismatchMessage(allCurrentPerformances, designCase.performance_snapshot);
});


// Form data
const formData = ref<{
  name: string;
  description: string;
  color: string;
  performance_values: { [key: string]: number | string };
  network: NetworkStructure;
  weight_mode: WeightMode;
}>({
  name: '',
  description: '',
  color: '#3357FF',
  performance_values: {},
  network: { nodes: [], edges: [] },
  weight_mode: 'discrete_7'
});

// Get utility function information for each performance
const getUtilityFunctions = (performanceId: string): UtilityFunction[] => {
  if (!currentProject.value) return [];
  
  const relations = currentProject.value.need_performance_relations.filter(
    r => r.performance_id === performanceId && r.utility_function_json
  );
  
  return relations.map(r => JSON.parse(r.utility_function_json!));
};

// Check if performance is discrete value
const isDiscretePerformance = (performanceId: string): boolean => {
  const functions = getUtilityFunctions(performanceId);
  return functions.length > 0 && functions.some(f => f.type === 'discrete');
};

// Get discrete value options (merge from multiple needs)
const getDiscreteOptions = (performanceId: string): string[] => {
  const functions = getUtilityFunctions(performanceId);
  const labelsSet = new Set<string>();
  
  functions.forEach(f => {
    if (f.type === 'discrete' && f.discreteRows) {
      f.discreteRows.forEach(row => labelsSet.add(row.label));
    }
  });
  
  return Array.from(labelsSet);
};

// Initialization
onMounted(() => {
  initializeForm();
});

watch(() => props.designCase, () => {
  initializeForm();
}, { deep: true });

function initializeForm() {
  if (props.designCase) {
    // Edit mode
    const mappedPerformanceValues: { [key: string]: number | string } = {};
    
    // If we have a snapshot and it's editable, map old IDs to new IDs
    if (props.designCase.performance_snapshot && isEditable.value) {
      const allCurrentPerformances = currentProject.value?.performances || [];
      const idMapping = createPerformanceIdMapping(allCurrentPerformances, props.designCase.performance_snapshot);
      
      // Map old performance values to new IDs
      Object.entries(props.designCase.performance_values).forEach(([oldId, value]) => {
        const newId = idMapping.get(oldId);
        if (newId) {
          mappedPerformanceValues[newId] = value;
        } else {
          // Keep the old ID if no mapping found (backward compatibility)
          mappedPerformanceValues[oldId] = value;
        }
      });
    } else {
      // No snapshot or not editable - use values as is
      Object.assign(mappedPerformanceValues, props.designCase.performance_values);
    }
    
    // Remap network performance IDs if needed
    let mappedNetwork = props.designCase.network;
    if (props.designCase.performance_snapshot && isEditable.value) {
      const allCurrentPerformances = currentProject.value?.performances || [];
      const idMapping = createPerformanceIdMapping(allCurrentPerformances, props.designCase.performance_snapshot);
      mappedNetwork = remapNetworkPerformanceIds(props.designCase.network, idMapping);
    }

    // Migrate old 7-level edge weights if needed
    // 旧7段階モード {-3,-1,-1/3,0,1/3,1,3} → 新7段階モード {-5,-3,-1,0,1,3,5}
    const hasWeightMode = !!props.designCase.weight_mode;
    let weight_mode: WeightMode = (props.designCase.weight_mode as WeightMode) || 'discrete_7';
    if (!hasWeightMode && needsEdgeMigration(mappedNetwork.edges)) {
      mappedNetwork = {
        ...mappedNetwork,
        edges: migrateNetworkEdges(mappedNetwork.edges, false)
      };
      weight_mode = 'discrete_7'; // After migration, use new 7-level mode
    }

    formData.value = {
      name: props.designCase.name,
      description: props.designCase.description || '',
      color: props.designCase.color || '#3357FF',
      performance_values: mappedPerformanceValues,
      network: mappedNetwork,
      weight_mode: weight_mode
    };
  } else {
    // Create mode
    formData.value = {
      name: '',
      description: '',
      color: getRandomColor(),
      performance_values: {},
      network: { nodes: [], edges: [] },
      weight_mode: 'discrete_7'
    };
    
    // Initialize performance values (for current leaf performances)
    displayPerformances.value.forEach(perf => {
      if (isDiscretePerformance(perf.id)) {
        // Empty string for discrete values
        formData.value.performance_values[perf.id] = '';
      } else {
        // 0 for continuous values
        formData.value.performance_values[perf.id] = 0;
      }
    });
  }
}

// Number of filled performances
const filledCount = computed(() => {
  return Object.entries(formData.value.performance_values).filter(
    ([key, val]) => {
      // Discrete values: not empty string
      if (isDiscretePerformance(key)) {
        return val !== '' && val !== undefined && val !== null;
      }
      // Continuous values: value exists
      return val !== undefined && val !== null;
    }
  ).length;
});

// Check if all performances are filled
const isAllPerformancesFilled = computed(() => {
  return filledCount.value === displayPerformances.value.length && displayPerformances.value.length > 0;
});

// Validation
const isValid = computed(() => {
  // 編集モードで編集不可の場合は無効
  if (isEdit.value && !isEditable.value) return false;
  
  return (
    formData.value.name.trim() !== '' &&
    isAllPerformancesFilled.value
  );
});

// Common function to prepare save data with ID remapping
function prepareSaveData() {
  let performanceValues = formData.value.performance_values;
  let networkStructure = formData.value.network;
  
  // In edit mode with snapshot, map current IDs back to original IDs
  if (isEdit.value && props.designCase?.performance_snapshot && isEditable.value) {
    const allCurrentPerformances = currentProject.value?.performances || [];
    const idMapping = createPerformanceIdMapping(allCurrentPerformances, props.designCase.performance_snapshot);
    
    // Create reverse mapping (current ID -> snapshot ID)
    const reverseMapping = new Map<string, string>();
    idMapping.forEach((currentId, snapshotId) => {
      reverseMapping.set(currentId, snapshotId);
    });
    
    // Map current IDs back to original snapshot IDs
    const remappedValues: { [key: string]: number | string } = {};
    Object.entries(performanceValues).forEach(([currentId, value]) => {
      const originalId = reverseMapping.get(currentId);
      if (originalId) {
        remappedValues[originalId] = value;
      } else {
        // Keep the current ID if no mapping found
        remappedValues[currentId] = value;
      }
    });
    performanceValues = remappedValues;
    
    // Also remap network performance IDs back to original
    networkStructure = remapNetworkPerformanceIds(networkStructure, idMapping, true);
  }
  
  const data: any = {
    name: formData.value.name,
    description: formData.value.description || undefined,
    color: formData.value.color,
    performance_values: performanceValues,
    network: networkStructure,
    weight_mode: formData.value.weight_mode
  };
  
  // Add performance_snapshot only when creating new
  if (!isEdit.value) {
    // Sort all performances by tree structure order and save as snapshot
    const allPerfs = currentProject.value?.performances || [];
    data.performance_snapshot = sortPerformancesByTree(allPerfs);
  }
  
  return data;
}

function handleSave() {
  if (!isValid.value) {
    alert('Please enter name and all performance values');
    return;
  }

  const hasNetwork = formData.value.network.nodes.length > 0 || formData.value.network.edges.length > 0;
  if (!hasNetwork) {
    alert('Please configure the network structure');
    return;
  }

  const data = prepareSaveData();
  emit('save', data);
}

async function handleNetworkSave() {
  if (!isValid.value) {
    alert('Please enter name and all performance values');
    return;
  }

  // Check SCC before saving
  try {
    sccChecking.value = true;
    const network = formData.value.network;

    if (network && network.nodes.length > 0) {
      const response = await sccApi.analyzeDirect(network);
      sccResult.value = response.data;

      // Check if there are divergent loops (ρ >= 1)
      const hasDivergentLoop = response.data.components?.some(c => !c.converges) || false;

      if (hasDivergentLoop) {
        showSccWarning.value = true;
        sccChecking.value = false;
        return; // Don't save, wait for user decision
      }
    }
  } catch (error) {
    console.error('SCC check failed:', error);
    // Continue with save even if SCC check fails
  } finally {
    sccChecking.value = false;
  }

  // Proceed with save
  proceedWithNetworkSave();
}

function proceedWithNetworkSave() {
  const data = prepareSaveData();
  emit('save', data);
  showNetworkEditor.value = false;
  showSccWarning.value = false;
  sccResult.value = null;
}

function handleSccContinue() {
  // User chose to continue despite divergent loop warning
  proceedWithNetworkSave();
}

function handleSccDismiss() {
  showSccWarning.value = false;
}

function getRandomColor(): string {
  const colors = [
    '#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#F5FF33',
    '#33F5FF', '#FF8C33', '#8C33FF', '#33FF8C', '#FF338C'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}
</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

// カスタムスクロールバースタイル
@mixin custom-scrollbar {
  &::-webkit-scrollbar {
    width: 0.8vw;
    height: 0.8vw;
  }
  
  &::-webkit-scrollbar-track {
    background: color.adjust($gray, $lightness: 5%);
    border-radius: 0.4vw;
  }
  
  &::-webkit-scrollbar-thumb {
    background: color.adjust($main_1, $alpha: -0.5);
    border-radius: 0.4vw;
    transition: background 0.3s ease;
    
    &:hover {
      background: color.adjust($main_1, $alpha: -0.3);
    }
    
    &:active {
      background: $main_1;
    }
  }
  
  // Firefox
  scrollbar-width: thin;
  scrollbar-color: color.adjust($main_1, $alpha: -0.5) color.adjust($gray, $lightness: 5%);
}

.design-case-form {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: lighten($gray, 8%);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1rem, 2vw, 1.5rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  background: linear-gradient(145deg, lighten($gray, 10%), lighten($gray, 6%));
}

.form-header h2 {
  margin: 0;
  font-size: clamp(1.1rem, 1.8vw, 1.3rem);
  font-weight: 600;
  color: $white;
}

.back-btn {
  padding: 0 clamp(0.8rem, 1.5vw, 1rem);
  background: color.adjust($gray, $lightness: 20%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  transition: all 0.2s;
  height: clamp(1.8rem, 3vw, 2rem);
  color: $white;
}

.back-btn:hover {
  background: color.adjust($gray, $lightness: 25%);
  border-color: color.adjust($white, $alpha: -0.8);
  transform: translateY(-0.1vh);
}

.form-content {
  flex: 1;
  overflow-y: auto;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1rem, 2vw, 1.5rem);
  background: $gray;
  @include custom-scrollbar;
}

.form-section {
  margin-bottom: clamp(1.5rem, 3vh, 2rem);
  background: lighten($gray, 8%);
  padding: clamp(1rem, 2vh, 1.5rem);
  border-radius: 0.8vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.form-section h3 {
  margin: 0 0 clamp(0.8rem, 1.5vh, 1rem) 0;
  font-size: clamp(0.95rem, 1.3vw, 1.1rem);
  font-weight: 600;
  color: $white;
  display: flex;
  align-items: center;
  gap: 0.5vw;
}

.section-hint {
  margin: clamp(-0.4rem, -0.8vh, -0.5rem) 0 clamp(0.8rem, 1.5vh, 1rem) 0;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.5);
  padding: clamp(0.6rem, 1vh, 0.8rem) clamp(0.8rem, 1.2vw, 1rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  border-radius: 0.4vw;
}

.form-group {
  margin-bottom: clamp(0.8rem, 1.5vh, 1rem);
}

.form-group label {
  display: block;
  margin-bottom: clamp(0.3rem, 0.6vh, 0.4rem);
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  color: color.adjust($white, $alpha: -0.2);
}

.required {
  color: $sub_1;
}

.form-input {
  width: 100%;
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(0.6rem, 1vw, 0.8rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  transition: all 0.2s;
  background: $gray;
  color: $white;
}

.form-input:focus {
  outline: none;
  border-color: $main_1;
  box-shadow: 0 0 0 0.3vw color.adjust($main_1, $alpha: -0.8);
}

.form-input:disabled {
  background: color.adjust($gray, $lightness: -5%);
  color: color.adjust($white, $alpha: -0.5);
  cursor: not-allowed;
}

.form-textarea {
  width: 100%;
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(0.6rem, 1vw, 0.8rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
  background: $gray;
  color: $white;
  @include custom-scrollbar;
}

.form-textarea:focus {
  outline: none;
  border-color: $main_1;
  box-shadow: 0 0 0 0.3vw color.adjust($main_1, $alpha: -0.8);
}

.form-textarea:disabled {
  background: color.adjust($gray, $lightness: -5%);
  color: color.adjust($white, $alpha: -0.5);
  cursor: not-allowed;
}

.color-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 1vw;
}

.color-input {
  width: clamp(3rem, 5vw, 4rem);
  height: clamp(3rem, 5vh, 4rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  cursor: pointer;
}

.color-input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.color-value {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-family: monospace;
  color: color.adjust($white, $alpha: -0.4);
}

.performance-table {
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.8vw;
  overflow: hidden;
  background: $gray;
}

.table-header {
  display: flex;
  background: linear-gradient(145deg, lighten($gray, 12%), lighten($gray, 8%));
  padding: clamp(0.6rem, 1.2vh, 0.8rem) clamp(0.8rem, 1.2vw, 1rem);
  font-weight: 600;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.2);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
}

.table-row {
  display: flex;
  padding: clamp(0.6rem, 1.2vh, 0.8rem) clamp(0.8rem, 1.2vw, 1rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.97);
  transition: all 0.2s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: lighten($gray, 5%);
  box-shadow: inset 0 0 1vh color.adjust($main_1, $alpha: -0.95);
}

.col-performance {
  flex: 2;
  display: flex;
  align-items: center;
}

.col-unit {
  flex: 1;
  display: flex;
  align-items: center;
  color: color.adjust($white, $alpha: -0.5);
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  padding-left: 0.5vw;
}

.col-value {
  flex: 1;
  display: flex;
  align-items: center;
}

.perf-name {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: $white;
}

.unit-text {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
}

.value-input-wrapper {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5vw;
}

.value-input {
  flex: 1;
  padding: clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.5rem, 0.8vw, 0.6rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  transition: all 0.2s;
  background: lighten($gray, 3%);
  color: $white;
}

.value-input:focus {
  outline: none;
  border-color: $main_1;
}

.value-input:disabled {
  background: color.adjust($gray, $lightness: -5%);
  color: color.adjust($white, $alpha: -0.5);
  cursor: not-allowed;
}

.input-unit {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
  white-space: nowrap;
  min-width: fit-content;
}

.value-select {
  width: 100%;
  padding: clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.5rem, 0.8vw, 0.6rem);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  background: lighten($gray, 3%);
  color: $white;
  cursor: pointer;
  transition: all 0.2s;
}

.value-select:focus {
  outline: none;
  border-color: $main_1;
}

.value-select:disabled {
  background: color.adjust($gray, $lightness: -5%);
  color: color.adjust($white, $alpha: -0.5);
  cursor: not-allowed;
}

.empty-performances {
  padding: clamp(2rem, 4vh, 2.5rem) clamp(1rem, 2vw, 1.5rem);
  text-align: center;
  color: color.adjust($white, $alpha: -0.5);
}

.empty-performances p {
  margin: 0.8vh 0;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
}

.empty-hint {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.6);
}

.input-status {
  margin-top: clamp(0.8rem, 1.5vh, 1rem);
  padding: clamp(0.6rem, 1.2vh, 0.8rem) clamp(0.8rem, 1.2vw, 1rem);
  background: color.adjust($sub_2, $alpha: -0.85);
  border: 1px solid color.adjust($sub_2, $alpha: -0.5);
  border-radius: 0.5vw;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: $sub_2;
  display: flex;
  align-items: center;
  gap: 0.8vw;
}

.input-status.complete {
  background: color.adjust($sub_4, $alpha: -0.85);
  border-color: color.adjust($sub_4, $alpha: -0.5);
  color: $sub_4;
}

.status-icon {
  font-size: clamp(0.9rem, 1.2vw, 1rem);
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1vw;
  padding: clamp(0.8rem, 1.5vh, 1rem) clamp(1rem, 2vw, 1.5rem);
  border-top: 1px solid color.adjust($white, $alpha: -0.95);
  background: linear-gradient(145deg, lighten($gray, 10%), lighten($gray, 6%));
}

.btn-cancel {
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(1.2rem, 2vw, 1.5rem);
  background: color.adjust($gray, $lightness: 20%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  transition: all 0.2s;
  color: $white;
}

.btn-cancel:hover {
  background: color.adjust($gray, $lightness: 25%);
  transform: translateY(-0.1vh);
}

.btn-save {
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(1.2rem, 2vw, 1.5rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  transition: all 0.2s;
}

.btn-save:hover:not(:disabled) {
  background: linear-gradient(135deg, lighten($main_1, 10%) 0%, lighten($main_2, 10%) 100%);
  box-shadow: 0 0.3vh 1vh color.adjust($main_1, $alpha: -0.7);
  transform: translateY(-0.1vh);
}

.btn-save:disabled {
  background: color.adjust($gray, $lightness: 15%);
  cursor: not-allowed;
}

.network-section {
  margin-bottom: clamp(1.5rem, 3vh, 2rem);
}

.network-editor-wrapper {
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.8vw;
  overflow: hidden;
  margin-bottom: clamp(0.8rem, 1.5vh, 1rem);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.8vw;
}

.stat-label {
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
}

.stat-value {
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 600;
  color: $white;
}

.section-header-with-action {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: clamp(0.8rem, 1.5vh, 1rem);
}

.section-header-with-action h3 {
  margin: 0;
}

.edit-network-btn {
  padding: clamp(0.4rem, 0.8vh, 0.5rem) clamp(0.8rem, 1.5vw, 1rem);
  background: $sub_6;
  color: $white;
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  display: flex;
  align-items: center;
  gap: 0.5vw;
  transition: all 0.2s;
  flex-shrink: 0;
}

.edit-network-btn:hover:not(:disabled) {
  background: lighten($sub_6, 10%);
  transform: translateY(-0.1vh);
  box-shadow: 0 0.2vh 0.8vh color.adjust($sub_6, $alpha: -0.5);
}

.edit-network-btn:disabled {
  background: color.adjust($gray, $lightness: 15%);
  cursor: not-allowed;
  color: color.adjust($white, $alpha: -0.5);
}

.network-viewer-wrapper {
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.8vw;
  overflow: hidden;
  background: $gray;
}

/* Network edit modal */
.network-editor-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: color.adjust($black, $alpha: -0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  overflow: hidden;
  backdrop-filter: blur(0.5vw);
}

.network-editor-modal .modal-content {
  background: lighten($gray, 8%);
  width: 90vw;
  height: 85vh;
  max-height: 85vh;
  border-radius: 1.2vw;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1vh 4vh color.adjust($black, $alpha: -0.5);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  margin: 5vh auto; // 上下に余白を確保
}

.network-editor-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1.2rem, 2vw, 1.8rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  background: linear-gradient(145deg, lighten($gray, 10%), lighten($gray, 6%));
  border-radius: 1.2vw 1.2vw 0 0;
}

.network-editor-modal .modal-header h2 {
  margin: 0;
  font-size: clamp(1.1rem, 1.8vw, 1.3rem);
  color: $white;
}

.network-editor-modal .modal-header-actions {
  display: flex;
  align-items: center;
  gap: 1vw;
}

.network-editor-modal .save-network-btn {
  padding: clamp(0.5rem, 1vh, 0.75rem) clamp(1rem, 1.8vw, 1.2rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.8vw;
}

.network-editor-modal .save-network-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, lighten($main_1, 10%) 0%, lighten($main_2, 10%) 100%);
  box-shadow: 0 0.3vh 1vh color.adjust($main_1, $alpha: -0.7);
  transform: translateY(-0.1vh);
}

.network-editor-modal .save-network-btn:disabled {
  background: color.adjust($gray, $lightness: 15%);
  cursor: not-allowed;
}

/* SCC Checking Indicator */
.scc-checking {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(25, 118, 210, 0.1);
  border: 1px solid rgba(25, 118, 210, 0.3);
  border-radius: 6px;
  margin: 8px 16px;
  color: #1976d2;
  font-size: 13px;

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(25, 118, 210, 0.3);
    border-top-color: #1976d2;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
}

.network-editor-modal .modal-body {
  flex: 1;
  overflow: auto;
  padding: 0;
  background: $gray;
  @include custom-scrollbar;
  display: flex;
  flex-direction: column;
  min-height: 0; // flexboxで適切に縮小できるように
  border-radius: 0 0 1.2vw 1.2vw;
}

.network-editor-modal .close-btn {
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1vw, 0.8rem);
  background: color.adjust($gray, $lightness: 20%);
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(1rem, 1.5vw, 1.2rem);
  transition: all 0.2s;
  color: color.adjust($white, $alpha: -0.4);
}

.network-editor-modal .close-btn:hover {
  background: color.adjust($gray, $lightness: 25%);
  color: $white;
}

/* Performance mismatch warning */
.performance-mismatch-warning {
  display: flex;
  gap: 1vw;
  padding: clamp(0.8rem, 1.5vh, 1rem) clamp(1rem, 1.8vw, 1.2rem);
  background: color.adjust($sub_2, $alpha: -0.9);
  border: 2px solid $sub_2;
  border-radius: 0.8vw;
  margin-bottom: clamp(1.2rem, 2vh, 1.5rem);
}

.performance-mismatch-warning .warning-icon {
  font-size: clamp(1.2rem, 2vw, 1.5rem);
  flex-shrink: 0;
  color: $sub_2;
}

.performance-mismatch-warning .warning-content {
  flex: 1;
}

.performance-mismatch-warning .warning-title {
  font-weight: 600;
  color: $sub_2;
  margin-bottom: 0.5vh;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
}

.performance-mismatch-warning .warning-message {
  color: color.adjust($white, $alpha: -0.3);
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  line-height: 1.5;
  margin-bottom: 0.8vh;
}

</style>