<template>
  <div v-if="visible" class="modal-overlay" @click.self="handleCancel">
    <div class="modal-content json-import-dialog">
      <div class="modal-header">
        <h2>ネットワークJSONインポート</h2>
        <button class="close-btn" @click="handleCancel">&times;</button>
      </div>

      <div class="modal-body">
        <!-- 入力タブ -->
        <div class="input-section">
          <div class="tab-bar">
            <button
              class="tab-btn"
              :class="{ active: inputMode === 'paste' }"
              @click="inputMode = 'paste'"
            >
              <FontAwesomeIcon :icon="['fas', 'paste']" />
              ペースト
            </button>
            <button
              class="tab-btn"
              :class="{ active: inputMode === 'file' }"
              @click="inputMode = 'file'"
            >
              <FontAwesomeIcon :icon="['fas', 'file-upload']" />
              ファイル選択
            </button>
          </div>

          <!-- ペーストモード -->
          <div v-if="inputMode === 'paste'" class="paste-area">
            <textarea
              v-model="jsonText"
              class="json-textarea"
              placeholder='{ "nodes": [...], "edges": [...] }'
              spellcheck="false"
              rows="12"
            ></textarea>
          </div>

          <!-- ファイルモード -->
          <div v-else class="file-area">
            <div
              class="drop-zone"
              :class="{ dragover: isDragOver }"
              @dragover.prevent="isDragOver = true"
              @dragleave="isDragOver = false"
              @drop.prevent="handleFileDrop"
              @click="triggerFileInput"
            >
              <FontAwesomeIcon :icon="['fas', 'cloud-upload-alt']" class="drop-icon" />
              <p>ここにJSONファイルをドロップ<br>またはクリックして選択</p>
              <p v-if="fileName" class="file-name">{{ fileName }}</p>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept=".json"
              style="display: none"
              @change="handleFileSelect"
            />
          </div>

          <!-- インポートモード -->
          <div class="import-mode-section">
            <label class="mode-label">インポートモード:</label>
            <div class="mode-options">
              <label class="radio-option" :class="{ selected: importMode === 'replace' }">
                <input type="radio" v-model="importMode" value="replace" />
                <span class="radio-content">
                  <span class="radio-label">置換</span>
                  <span class="radio-description">既存のネットワーク（性能ノード以外）を削除して置換</span>
                </span>
              </label>
              <label class="radio-option" :class="{ selected: importMode === 'merge' }">
                <input type="radio" v-model="importMode" value="merge" />
                <span class="radio-content">
                  <span class="radio-label">マージ</span>
                  <span class="radio-description">既存ネットワークに追加（同名ノードは再利用）</span>
                </span>
              </label>
            </div>
          </div>

          <button class="btn btn-validate" @click="runValidation" :disabled="!jsonText.trim()">
            <FontAwesomeIcon :icon="['fas', 'check-circle']" />
            バリデーション &amp; プレビュー
          </button>
        </div>

        <!-- プレビューセクション -->
        <div v-if="preview" class="preview-section">
          <div class="section-divider"></div>

          <!-- 統計 -->
          <div class="section stats-section">
            <h3>統計</h3>
            <div class="stats-grid">
              <span class="stat-item" style="border-left-color: var(--layer-p-color)">
                <strong>{{ preview.stats.nodesByLayer.P }}</strong> P (性能)
              </span>
              <span class="stat-item" style="border-left-color: var(--layer-a-color)">
                <strong>{{ preview.stats.nodesByLayer.A }}</strong> A (属性)
              </span>
              <span class="stat-item" style="border-left-color: var(--layer-v-color)">
                <strong>{{ preview.stats.nodesByLayer.V }}</strong> V (変数)
              </span>
              <span class="stat-item" style="border-left-color: var(--layer-e-color)">
                <strong>{{ preview.stats.nodesByLayer.E }}</strong> E (モノ・環境)
              </span>
              <span class="stat-item stat-edges">
                <strong>{{ preview.stats.edgeCount }}</strong> エッジ
              </span>
            </div>
          </div>

          <!-- エラー -->
          <div v-if="preview.errors.length > 0" class="section errors-section">
            <h3 class="error-title">
              <FontAwesomeIcon :icon="['fas', 'times-circle']" />
              エラー（{{ preview.errors.length }}件 — インポート不可）
            </h3>
            <ul class="message-list error-list">
              <li v-for="(err, i) in preview.errors" :key="'e-' + i">
                <span v-if="err.edgeLabels" class="edge-label">{{ err.edgeLabels }}:</span>
                {{ err.message }}
              </li>
            </ul>
          </div>

          <!-- 性能マッチング -->
          <div v-if="preview.performanceMatches.length > 0" class="section perf-match-section">
            <h3>
              <FontAwesomeIcon :icon="['fas', 'link']" />
              性能マッチング
            </h3>
            <div
              v-for="(match, i) in preview.performanceMatches"
              :key="'pm-' + i"
              class="match-item"
              :class="matchStatusClass(match)"
            >
              <!-- 自動マッチ成功 -->
              <template v-if="match.matchedPerformance">
                <span class="match-icon success">
                  <FontAwesomeIcon :icon="['fas', 'check']" />
                </span>
                <span class="match-text">
                  "{{ match.inputLabel }}" → {{ match.matchedPerformance.name }}
                  <span class="match-type">({{ matchTypeLabel(match.matchType) }})</span>
                </span>
              </template>

              <!-- 候補あり: ユーザー選択 -->
              <template v-else-if="match.candidates.length > 0">
                <span class="match-icon ambiguous">
                  <FontAwesomeIcon :icon="['fas', 'question']" />
                </span>
                <div class="match-select">
                  <span class="match-label">"{{ match.inputLabel }}" → 候補を選択:</span>
                  <div class="candidate-options">
                    <label
                      v-for="cand in match.candidates"
                      :key="cand.id"
                      class="radio-option small"
                      :class="{ selected: perfSelections[match.inputLabel] === cand.id }"
                    >
                      <input
                        type="radio"
                        :name="'perf-' + i"
                        :value="cand.id"
                        v-model="perfSelections[match.inputLabel]"
                      />
                      <span class="radio-label">{{ cand.name }}</span>
                    </label>
                  </div>
                </div>
              </template>

              <!-- マッチなし -->
              <template v-else>
                <span class="match-icon error">
                  <FontAwesomeIcon :icon="['fas', 'times']" />
                </span>
                <span class="match-text error-text">
                  "{{ match.inputLabel }}" → 一致する性能が見つかりません
                </span>
              </template>
            </div>
          </div>

          <!-- 警告 -->
          <div v-if="preview.warnings.length > 0" class="section warnings-section">
            <details>
              <summary class="warning-title">
                <FontAwesomeIcon :icon="['fas', 'exclamation-triangle']" />
                警告（{{ preview.warnings.length }}件）
              </summary>
              <ul class="message-list warning-list">
                <li v-for="(warn, i) in preview.warnings.slice(0, 20)" :key="'w-' + i">
                  {{ warn.message }}
                </li>
              </ul>
              <p v-if="preview.warnings.length > 20" class="more-items">
                ... 他 {{ preview.warnings.length - 20 }}件
              </p>
            </details>
          </div>

          <!-- 情報 -->
          <div v-if="preview.infos.length > 0" class="section infos-section">
            <details>
              <summary class="info-title">
                <FontAwesomeIcon :icon="['fas', 'info-circle']" />
                情報（{{ preview.infos.length }}件）
              </summary>
              <ul class="message-list info-list">
                <li v-for="(info, i) in preview.infos.slice(0, 20)" :key="'i-' + i">
                  {{ info.message }}
                </li>
              </ul>
            </details>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="handleCancel">キャンセル</button>
        <button
          class="btn btn-primary"
          @click="handleImport"
          :disabled="!canImport"
        >
          <FontAwesomeIcon :icon="['fas', 'file-import']" />
          インポート実行
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import type { NetworkStructure, WeightMode, Performance } from '@/types/project';
import type { NetworkImportPreview, PerformanceMatchResult } from '@/utils/networkJsonImport';
import { parseAndValidateNetworkJson, buildFinalNetwork } from '@/utils/networkJsonImport';

const props = defineProps<{
  visible: boolean;
  performances: Performance[];
  currentNetwork: NetworkStructure;
  currentWeightMode: WeightMode;
}>();

const emit = defineEmits<{
  (e: 'import', result: { network: NetworkStructure; weightMode?: WeightMode }): void;
  (e: 'cancel'): void;
}>();

// 状態
const inputMode = ref<'paste' | 'file'>('paste');
const jsonText = ref('');
const fileName = ref('');
const isDragOver = ref(false);
const importMode = ref<'replace' | 'merge'>('replace');
const fileInput = ref<HTMLInputElement | null>(null);
const preview = ref<NetworkImportPreview | null>(null);
const perfSelections = reactive<Record<string, string>>({});

// ダイアログが閉じたらリセット
watch(() => props.visible, (val) => {
  if (!val) {
    resetState();
  }
});

function resetState() {
  jsonText.value = '';
  fileName.value = '';
  preview.value = null;
  inputMode.value = 'paste';
  importMode.value = 'replace';
  Object.keys(perfSelections).forEach(k => delete perfSelections[k]);
}

// ファイル操作
function triggerFileInput() {
  fileInput.value?.click();
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) readFile(file);
}

function handleFileDrop(event: DragEvent) {
  isDragOver.value = false;
  const file = event.dataTransfer?.files[0];
  if (file) readFile(file);
}

function readFile(file: File) {
  fileName.value = file.name;
  const reader = new FileReader();
  reader.onload = (e) => {
    jsonText.value = e.target?.result as string || '';
    preview.value = null;
  };
  reader.readAsText(file);
}

// バリデーション実行
function runValidation() {
  Object.keys(perfSelections).forEach(k => delete perfSelections[k]);
  preview.value = parseAndValidateNetworkJson(
    jsonText.value,
    props.performances,
    props.currentWeightMode
  );
}

// インポート可否
const hasUnresolvedSelections = computed(() => {
  if (!preview.value) return true;
  return preview.value.performanceMatches.some(
    m => !m.matchedPerformance && m.candidates.length > 0 && !perfSelections[m.inputLabel]
  );
});

const canImport = computed(() => {
  if (!preview.value) return false;
  if (preview.value.errors.length > 0) return false;
  if (hasUnresolvedSelections.value) return false;
  return true;
});

// インポート実行
function handleImport() {
  if (!preview.value || !canImport.value) return;

  let network = buildFinalNetwork(preview.value, perfSelections);

  if (importMode.value === 'merge') {
    network = mergeWithExisting(network);
  }

  emit('import', {
    network,
    weightMode: preview.value.weightMode || undefined,
  });
}

function mergeWithExisting(imported: NetworkStructure): NetworkStructure {
  const existing = props.currentNetwork;
  const mergedNodes = [...existing.nodes];
  const mergedEdges = [...existing.edges];

  // 既存ノードのラベル+レイヤーマップ
  const existingMap = new Map<string, string>();
  for (const node of existing.nodes) {
    existingMap.set(`${node.label}::${node.layer}`, node.id);
  }

  // インポートノードのID変換マップ
  const idRemap = new Map<string, string>();

  for (const node of imported.nodes) {
    const key = `${node.label}::${node.layer}`;
    const existingId = existingMap.get(key);
    if (existingId) {
      // 既存ノードを再利用
      idRemap.set(node.id, existingId);
    } else {
      mergedNodes.push(node);
    }
  }

  // エッジを追加（ID変換適用、重複回避）
  const existingEdgeKeys = new Set(
    existing.edges.map(e => `${e.source_id}->${e.target_id}`)
  );

  for (const edge of imported.edges) {
    const sourceId = idRemap.get(edge.source_id) || edge.source_id;
    const targetId = idRemap.get(edge.target_id) || edge.target_id;
    const edgeKey = `${sourceId}->${targetId}`;
    if (!existingEdgeKeys.has(edgeKey)) {
      mergedEdges.push({ ...edge, source_id: sourceId, target_id: targetId });
      existingEdgeKeys.add(edgeKey);
    }
  }

  return { nodes: mergedNodes, edges: mergedEdges, weight_mode: imported.weight_mode };
}

function handleCancel() {
  emit('cancel');
}

// ヘルパー
function matchStatusClass(match: PerformanceMatchResult): string {
  if (match.matchedPerformance) return 'status-ok';
  if (match.candidates.length > 0) return 'status-ambiguous';
  return 'status-error';
}

function matchTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    exact: '完全一致',
    prefix: 'プレフィックス一致',
    name: '名前一致',
    fuzzy: '類似一致',
  };
  return labels[type] || type;
}
</script>

<style scoped lang="scss">
@use '@/style/_color.scss' as *;
@use 'sass:color';

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: $black;
  border-radius: 8px;
  max-width: 750px;
  width: 90%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  color: $white;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid $main_1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: $white;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: $main_3;
}

.close-btn:hover {
  color: $white;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid $main_1;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* タブ */
.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid $main_1;
  border-radius: 4px 4px 0 0;
  background: $gray;
  color: $main_3;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.tab-btn.active {
  background: $main_1;
  color: $white;
  border-bottom-color: $main_1;
}

.tab-btn:hover:not(.active) {
  color: $white;
}

/* JSONテキストエリア */
.json-textarea {
  width: 100%;
  min-height: 200px;
  padding: 12px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  background: $gray;
  color: $white;
  border: 1px solid $main_1;
  border-radius: 0 4px 4px 4px;
  resize: vertical;
  tab-size: 2;
}

.json-textarea:focus {
  outline: none;
  border-color: $sub_6;
}

.json-textarea::placeholder {
  color: $main_3;
}

/* ファイルドロップゾーン */
.drop-zone {
  border: 2px dashed $main_1;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  color: $main_3;
}

.drop-zone:hover,
.drop-zone.dragover {
  border-color: $sub_6;
  background: rgba($sub_6, 0.05);
  color: $white;
}

.drop-icon {
  font-size: 2rem;
  margin-bottom: 12px;
  color: $sub_6;
}

.file-name {
  margin-top: 12px;
  color: $sub_6;
  font-weight: 500;
}

/* インポートモード */
.import-mode-section {
  margin-top: 16px;
}

.mode-label {
  font-weight: 500;
  color: $main_2;
  display: block;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.mode-options {
  display: flex;
  gap: 8px;
}

.radio-option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: $gray;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
}

.radio-option:hover {
  border-color: $main_2;
}

.radio-option.selected {
  border-color: $sub_6;
  background: rgba($sub_6, 0.1);
}

.radio-option input[type="radio"] {
  margin-top: 2px;
  accent-color: $sub_6;
}

.radio-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.radio-label {
  font-weight: 500;
  color: $white;
  font-size: 0.9rem;
}

.radio-description {
  font-size: 0.75rem;
  color: $main_3;
}

.radio-option.small {
  padding: 6px 10px;
  flex: unset;
}

.radio-option.small .radio-label {
  font-size: 0.85rem;
}

/* バリデーションボタン */
.btn-validate {
  margin-top: 16px;
  width: 100%;
  padding: 10px;
  background: $sub_6;
  color: $white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-validate:hover:not(:disabled) {
  background: color.adjust($sub_6, $lightness: 10%);
}

.btn-validate:disabled {
  background: $main_1;
  color: $main_3;
  cursor: not-allowed;
}

/* セクション共通 */
.section-divider {
  border-top: 1px solid $main_1;
  margin: 20px 0;
}

.preview-section .section {
  margin-bottom: 16px;
}

.preview-section h3 {
  margin: 0 0 10px 0;
  font-size: 0.95rem;
  color: $main_2;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 統計 */
.stats-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-item {
  background: $gray;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: $white;
  border-left: 3px solid $main_1;
}

.stat-item strong {
  color: $sub_6;
  margin-right: 4px;
}

.stat-edges {
  border-left-color: $main_3 !important;
}

/* CSS変数（レイヤー色） */
.json-import-dialog {
  --layer-p-color: #e74c3c;
  --layer-a-color: #3498db;
  --layer-v-color: #2ecc71;
  --layer-e-color: #f39c12;
}

/* エラーセクション */
.errors-section {
  background: rgba($sub_1, 0.15);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid rgba($sub_1, 0.5);
}

.error-title {
  color: $sub_1 !important;
}

.message-list {
  margin: 0;
  padding-left: 20px;
  font-size: 0.85rem;
}

.message-list li {
  margin-bottom: 4px;
}

.error-list {
  color: $sub_1;
}

.edge-label {
  font-family: monospace;
  font-weight: 600;
  margin-right: 4px;
}

/* 性能マッチング */
.match-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 4px;
  margin-bottom: 6px;
  font-size: 0.85rem;
}

.match-item.status-ok {
  background: rgba($sub_4, 0.1);
}

.match-item.status-ambiguous {
  background: rgba($sub_2, 0.1);
  border: 1px solid rgba($sub_2, 0.3);
}

.match-item.status-error {
  background: rgba($sub_1, 0.1);
}

.match-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
  margin-top: 2px;
}

.match-icon.success {
  background: $sub_4;
  color: $white;
}

.match-icon.ambiguous {
  background: $sub_2;
  color: $white;
}

.match-icon.error {
  background: $sub_1;
  color: $white;
}

.match-text {
  color: $white;
}

.match-type {
  color: $main_3;
  font-size: 0.75rem;
}

.error-text {
  color: $sub_1;
}

.match-select {
  flex: 1;
}

.match-label {
  color: $sub_2;
  font-weight: 500;
  display: block;
  margin-bottom: 6px;
}

.candidate-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 警告セクション */
.warnings-section {
  background: rgba($sub_2, 0.1);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid rgba($sub_2, 0.3);
}

.warning-title {
  color: $sub_2 !important;
  cursor: pointer;
  user-select: none;
}

.warning-list {
  color: $sub_2;
}

/* 情報セクション */
.infos-section {
  background: rgba($sub_6, 0.1);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid rgba($sub_6, 0.3);
}

.info-title {
  color: $sub_6 !important;
  cursor: pointer;
  user-select: none;
}

.info-list {
  color: $sub_6;
}

.more-items {
  color: $main_3;
  font-style: italic;
  font-size: 0.8rem;
  margin: 8px 0 0 0;
}

/* ボタン */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary {
  background: $main_1;
  color: $white;
}

.btn-secondary:hover {
  background: color.adjust($main_1, $lightness: 10%);
}

.btn-primary {
  background: $sub_6;
  color: $white;
}

.btn-primary:hover:not(:disabled) {
  background: color.adjust($sub_6, $lightness: 10%);
}

.btn-primary:disabled {
  background: $main_1;
  color: $main_3;
  cursor: not-allowed;
}
</style>
