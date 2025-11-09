<template>
  <div class="design-case-form">
    <div class="form-header">
      <h2>{{ isEdit ? '設計案を編集' : '新規設計案を作成' }}</h2>
      <button class="back-btn" @click="$emit('cancel')">← 戻る</button>
    </div>

    <div class="form-content">
      <div v-if="isEdit && isEditable" class="section-hint">
        この設計案は現在の性能ツリーと一致しています。編集可能です。
      </div>
      <!-- 性能不一致警告 -->
      <div v-if="isEdit && !isEditable" class="performance-mismatch-warning">
        <div class="warning-icon">⚠️</div>
        <div class="warning-content">
          <div class="warning-title">編集不可</div>
          <div class="warning-message">
            この設計案の作成後に性能ツリーが変更されているため、編集できません（閲覧のみ）。
          </div>
        </div>
      </div>

      <!-- 基本情報 -->
      <section class="form-section">
        <h3>基本情報</h3>
        
        <div class="form-group">
          <label>名前 <span class="required">*</span></label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="例: 設計案1"
            class="form-input"
            :disabled="isEdit && !isEditable"
          />
        </div>

        <div class="form-group">
          <label>説明</label>
          <textarea
            v-model="formData.description"
            placeholder="この設計案の説明を入力..."
            class="form-textarea"
            rows="3"
            :disabled="isEdit && !isEditable"
          ></textarea>
        </div>

        <div class="form-group">
          <label>表示色</label>
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

      <!-- 性能値入力 -->
      <section class="form-section">
        <h3>性能値を入力</h3>

        <div class="performance-table">
          <div class="table-header">
            <div class="col-performance">性能</div>
            <div class="col-unit">単位</div>
            <div class="col-value">値</div>
          </div>

          <div
            v-for="perf in performances"
            :key="perf.id"
            class="table-row"
          >
            <div class="col-performance">
              <span class="perf-name">{{ perf.name }}</span>
            </div>
            <div class="col-unit">
              <span class="unit-text">{{ perf.unit || '-' }}</span>
            </div>
            <div class="col-value">
              <!-- 離散値の場合: セレクトボックス -->
              <select
                v-if="isDiscretePerformance(perf.id)"
                v-model="formData.performance_values[perf.id]"
                class="value-select"
                :disabled="isEdit && !isEditable"
              >
                <option value="" disabled>選択してください</option>
                <option
                  v-for="option in getDiscreteOptions(perf.id)"
                  :key="option"
                  :value="option"
                >
                  {{ option }}
                </option>
              </select>
              
              <!-- 連続値の場合: 数値入力 + 単位 -->
              <div v-else class="value-input-wrapper">
                <input
                  v-model.number="formData.performance_values[perf.id]"
                  type="number"
                  step="any"
                  class="value-input"
                  :placeholder="'値を入力'"
                  :disabled="isEdit && !isEditable"
                />
                <span v-if="perf.unit" class="input-unit">{{ perf.unit }}</span>
              </div>
            </div>
          </div>

          <div v-if="performances.length === 0" class="empty-performances">
            <p>性能が定義されていません</p>
            <p class="empty-hint">先に「性能管理」タブで性能を作成してください</p>
          </div>
        </div>

        <!-- 入力状況 -->
        <div class="input-status" :class="{ complete: isAllPerformancesFilled }">
          <span v-if="isAllPerformancesFilled" class="status-icon">✓</span>
          <span v-else class="status-icon">⚠️</span>
          {{ filledCount }} / {{ performances.length }} 入力済み
        </div>
      </section>

      <!-- ★ ネットワーク表示セクション -->
      <section class="form-section network-section">
        <div class="section-header-with-action">
          <div>
            <h3><FontAwesomeIcon :icon="['fas', 'hexagon-nodes']" /> ネットワーク構造</h3>
          </div>
          <button 
            class="edit-network-btn" 
            @click="showNetworkEditor = true"
            :disabled="isEdit && !isEditable"
          >
            <FontAwesomeIcon :icon="['fas', 'pen-to-square']" /> 編集
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

    <!-- フッター -->
    <div class="form-footer">
      <button class="btn-cancel" @click="$emit('cancel')">キャンセル</button>
      <button 
        class="btn-save" 
        @click="handleSave"
        :disabled="!isValid"
      >
        {{ isEdit ? '更新' : '作成' }}
      </button>
    </div>

    <!-- ネットワーク編集モーダル -->
    <div v-if="showNetworkEditor" class="network-editor-modal" @click.self="showNetworkEditor = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>ネットワーク編集</h2>
          <div class="modal-header-actions">
            <button class="save-network-btn" @click="handleNetworkSave" :disabled="!isValid">
              <FontAwesomeIcon :icon="['fas', 'floppy-disk']" /> 保存して閉じる
            </button>
            <button class="close-btn" @click="showNetworkEditor = false">✕</button>
          </div>
        </div>
        <div class="modal-body">
          <NetworkEditor
            v-model="formData.network"
            :performances="performances"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, inject } from 'vue';
import type { DesignCase, Performance, DesignCaseCreate, NeedPerformanceRelation, UtilityFunction, NetworkStructure } from '../../types/project';
import { useProjectStore } from '../../stores/projectStore';
import { storeToRefs } from 'pinia';
import NetworkEditor from '../network/NetworkEditor.vue';
import NetworkViewer from '../network/NetworkViewer.vue';
import { isDesignCaseEditable, getPerformanceMismatchMessage } from '../../utils/performanceComparison';

const props = defineProps<{
  designCase: DesignCase | null;
  performances: Performance[];
}>();

const showNetworkEditor = ref(false);

// ネットワークエディタモーダルの表示/非表示を監視してスクロールを制御
watch(showNetworkEditor, (isOpen) => {
  if (isOpen) {
    // モーダルが開いたときにスクロールを無効化
    document.body.style.overflow = 'hidden';
  } else {
    // モーダルが閉じたときにスクロールを再有効化
    document.body.style.overflow = '';
  }
});

// コンポーネントがアンマウントされたときにスクロールを再有効化
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

// 性能ツリーの整合性チェック
const isEditable = computed(() => {
  // 新規作成モードは常に編集可能
  if (!isEdit.value) return true;
  
  // 編集モードの場合、performance_snapshotの整合性をチェック
  const designCase = props.designCase;
  
  if (!designCase || !designCase.performance_snapshot || designCase.performance_snapshot.length === 0) {
    // スナップショットがない場合は編集可能（後方互換性）
    return true;
  }
  
  // 全ての性能（葉と親の両方）を取得
  const allCurrentPerformances = currentProject.value?.performances || [];
  
  // 全ての性能ツリーと保存されたスナップショットを比較
  const result = isDesignCaseEditable(allCurrentPerformances, designCase.performance_snapshot);
  
  return result;
});

// 性能不一致の詳細メッセージ
const performanceMismatchWarning = computed(() => {
  if (!isEdit.value || isEditable.value) return '';
  
  const designCase = props.designCase;
  if (!designCase || !designCase.performance_snapshot) return '';
  
  // 全ての性能を使用
  const allCurrentPerformances = currentProject.value?.performances || [];
  
  return getPerformanceMismatchMessage(allCurrentPerformances, designCase.performance_snapshot);
});


// フォームデータ
const formData = ref<{
  name: string;
  description: string;
  color: string;
  performance_values: { [key: string]: number | string };
  network: NetworkStructure;
}>({
  name: '',
  description: '',
  color: '#3357FF',
  performance_values: {},
  network: { nodes: [], edges: [] } 
});

// 性能ごとの効用関数情報を取得
const getUtilityFunctions = (performanceId: string): UtilityFunction[] => {
  if (!currentProject.value) return [];
  
  const relations = currentProject.value.need_performance_relations.filter(
    r => r.performance_id === performanceId && r.utility_function_json
  );
  
  return relations.map(r => JSON.parse(r.utility_function_json!));
};

// 性能が離散値かどうか判定
const isDiscretePerformance = (performanceId: string): boolean => {
  const functions = getUtilityFunctions(performanceId);
  return functions.length > 0 && functions.some(f => f.type === 'discrete');
};

// 離散値の選択肢を取得（複数のニーズからマージ）
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

// 初期化
onMounted(() => {
  initializeForm();
});

watch(() => props.designCase, () => {
  initializeForm();
}, { deep: true });

function initializeForm() {
  if (props.designCase) {
    // 編集モード
    formData.value = {
      name: props.designCase.name,
      description: props.designCase.description || '',
      color: props.designCase.color || '#3357FF',
      performance_values: { ...props.designCase.performance_values },
      network: JSON.parse(JSON.stringify(props.designCase.network)) 
    };
  } else {
    // 新規作成モード
    formData.value = {
      name: '',
      description: '',
      color: getRandomColor(),
      performance_values: {},
      network: { nodes: [], edges: [] }
    };
    
    // 性能値を初期化
    props.performances.forEach(perf => {
      if (isDiscretePerformance(perf.id)) {
        // 離散値の場合は空文字列
        formData.value.performance_values[perf.id] = '';
      } else {
        // 連続値の場合は0
        formData.value.performance_values[perf.id] = 0;
      }
    });
  }
}

// 入力済みの性能数
const filledCount = computed(() => {
  return Object.entries(formData.value.performance_values).filter(
    ([key, val]) => {
      // 離散値の場合: 空文字列でないこと
      if (isDiscretePerformance(key)) {
        return val !== '' && val !== undefined && val !== null;
      }
      // 連続値の場合: 値が存在すること
      return val !== undefined && val !== null;
    }
  ).length;
});

// 全ての性能が入力されているか
const isAllPerformancesFilled = computed(() => {
  return filledCount.value === props.performances.length && props.performances.length > 0;
});

// バリデーション
const isValid = computed(() => {
  return (
    formData.value.name.trim() !== '' &&
    isAllPerformancesFilled.value
  );
});

function handleSave() {
  if (!isValid.value) {
    alert('名前と全ての性能値を入力してください');
    return;
  }

  const data: any = {
    name: formData.value.name,
    description: formData.value.description || undefined,
    color: formData.value.color,
    performance_values: formData.value.performance_values,
    network: formData.value.network
  };
  const hasNetwork = formData.value.network.nodes.length > 0 || formData.value.network.edges.length > 0;
  if (!hasNetwork) {
    alert('ネットワーク構造を設定してください');
    return;
  }

  // 新規作成時のみperformance_snapshotを追加
  if (!isEdit.value) {
    data.performance_snapshot = currentProject.value?.performances || [];
  }

  emit('save', data);
}

function handleNetworkSave() {
  if (!isValid.value) {
    alert('名前と全ての性能値を入力してください');
    return;
  }

  const data: any = {
    name: formData.value.name,
    description: formData.value.description || undefined,
    color: formData.value.color,
    performance_values: formData.value.performance_values,
    network: formData.value.network
  };

  // 新規作成時のみperformance_snapshotを追加
  if (!isEdit.value) {
    data.performance_snapshot = currentProject.value?.performances || [];
    console.log(data.performance_snapshot);
  }

  emit('save', data);
  showNetworkEditor.value = false;
}

function getRandomColor(): string {
  const colors = [
    '#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#F5FF33',
    '#33F5FF', '#FF8C33', '#8C33FF', '#33FF8C', '#FF338C'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}
</script>

<style scoped>
.design-case-form {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.form-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.back-btn {
  padding: 0px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  height: 32px;
}

.back-btn:hover {
  background: #e0e0e0;
}

.form-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.form-section {
  margin-bottom: 32px;
}

.form-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.section-hint {
  margin: -8px 0 16px 0;
  font-size: 13px;
  color: #999;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #555;
}

.required {
  color: #f44336;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
}

.form-textarea:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.color-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-input {
  width: 60px;
  height: 40px;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
}

.color-value {
  font-size: 14px;
  font-family: monospace;
  color: #666;
}

.performance-table {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: flex;
  background: #f5f5f5;
  padding: 12px;
  font-weight: 600;
  font-size: 13px;
  color: #555;
  border-bottom: 1px solid #e0e0e0;
}

.table-row {
  display: flex;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: #fafafa;
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
  color: #999;
  font-size: 13px;
}

.col-value {
  flex: 1;
  display: flex;
  align-items: center;
}

.perf-name {
  font-size: 14px;
  color: #333;
}

.unit-text {
  font-size: 13px;
}

.value-input-wrapper {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
}

.value-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s;
}

.value-input:focus {
  outline: none;
  border-color: #4CAF50;
}

.input-unit {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
  min-width: fit-content;
}

.value-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.value-select:focus {
  outline: none;
  border-color: #4CAF50;
}

.empty-performances {
  padding: 40px 20px;
  text-align: center;
  color: #999;
}

.empty-performances p {
  margin: 8px 0;
}

.empty-hint {
  font-size: 13px;
  color: #bbb;
}

.input-status {
  margin-top: 16px;
  padding: 12px;
  background: #fff3e0;
  border: 1px solid #ffe0b2;
  border-radius: 6px;
  font-size: 14px;
  color: #f57c00;
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-status.complete {
  background: #e8f5e9;
  border-color: #c8e6c9;
  color: #2e7d32;
}

.status-icon {
  font-size: 16px;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.btn-cancel {
  padding: 10px 24px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #f5f5f5;
}

.btn-save {
  padding: 10px 24px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-save:hover:not(:disabled) {
  background: #45a049;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.btn-save:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.network-section {
  margin-bottom: 32px;
}

.network-editor-wrapper {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 13px;
  color: #666;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.section-header-with-action {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
}

.section-header-with-action h3 {
  margin: 0;
}

.edit-network-btn {
  padding: 8px 16px;
  background: #1976D2;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.edit-network-btn:hover {
  background: #1565C0;
}

.network-viewer-wrapper {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

/* ネットワーク編集モーダル */
.network-editor-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  overflow: hidden;
}

.network-editor-modal .modal-content {
  background: white;
  width: 95%;
  height: 95%;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.network-editor-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.network-editor-modal .modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.network-editor-modal .modal-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.network-editor-modal .save-network-btn {
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.network-editor-modal .save-network-btn:hover:not(:disabled) {
  background: #45a049;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.network-editor-modal .save-network-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.network-editor-modal .modal-body {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.network-editor-modal .close-btn {
  padding: 8px 12px;
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  transition: background 0.2s;
}

.network-editor-modal .close-btn:hover {
  background: #e0e0e0;
}

/* 性能不一致警告 */
.performance-mismatch-warning {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #FFF9E6;
  border: 2px solid #FFD54F;
  border-radius: 8px;
  margin-bottom: 24px;
}

.performance-mismatch-warning .warning-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.performance-mismatch-warning .warning-content {
  flex: 1;
}

.performance-mismatch-warning .warning-title {
  font-weight: 600;
  color: #F57C00;
  margin-bottom: 6px;
  font-size: 15px;
}

.performance-mismatch-warning .warning-message {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
}

</style>