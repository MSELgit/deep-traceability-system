<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-content import-preview-dialog">
      <div class="modal-header">
        <h2>Import Preview</h2>
        <button class="close-btn" @click="$emit('cancel')">&times;</button>
      </div>

      <div class="modal-body">
        <!-- Project Info -->
        <div class="section project-info">
          <h3>Project: {{ preview.project_name }}</h3>
          <div class="counts">
            <span class="count-item">
              <strong>{{ preview.counts.stakeholders }}</strong> Stakeholders
            </span>
            <span class="count-item">
              <strong>{{ preview.counts.needs }}</strong> Needs
            </span>
            <span class="count-item">
              <strong>{{ preview.counts.performances }}</strong> Performances
            </span>
            <span class="count-item">
              <strong>{{ preview.counts.design_cases }}</strong> Design Cases
            </span>
          </div>
        </div>

        <!-- Validation Errors -->
        <div v-if="preview.validation.errors.length > 0" class="section errors">
          <h3 class="error-title">Validation Errors</h3>
          <ul class="error-list">
            <li v-for="(error, i) in preview.validation.errors" :key="i">{{ error }}</li>
          </ul>
        </div>

        <!-- Version & Migration Info -->
        <div class="section version-info">
          <h3>Version Migration</h3>
          <div class="version-badge-container">
            <span class="version-badge source">{{ preview.migration_analysis.source_version }}</span>
            <span class="arrow">→</span>
            <span class="version-badge target">{{ preview.migration_analysis.target_version }}</span>
          </div>
        </div>

        <!-- User Choices Section -->
        <div v-if="hasUserChoices" class="section user-choices">
          <h3>
            <FontAwesomeIcon :icon="faQuestionCircle" />
            Configuration Required
          </h3>
          <div
            v-for="choice in preview.migration_analysis.user_choices"
            :key="choice.key"
            class="user-choice-item"
          >
            <label class="choice-label">{{ choice.label }}</label>
            <p class="choice-description">{{ choice.description }}</p>

            <!-- Single Select -->
            <div v-if="choice.type === 'single_select'" class="choice-options">
              <label
                v-for="option in choice.options"
                :key="option.value"
                class="radio-option"
                :class="{ selected: userChoices[choice.key] === option.value }"
              >
                <input
                  type="radio"
                  :name="choice.key"
                  :value="option.value"
                  v-model="userChoices[choice.key]"
                />
                <span class="radio-content">
                  <span class="radio-label">{{ option.label }}</span>
                  <span class="radio-description">{{ option.description }}</span>
                </span>
              </label>
            </div>

            <!-- Number Input -->
            <div v-else-if="choice.type === 'number_input'" class="choice-number">
              <input
                type="number"
                v-model.number="userChoices[choice.key]"
                :min="choice.min"
                :max="choice.max"
                :step="choice.step"
                class="number-input"
              />
            </div>

            <!-- Needs Priority Table -->
            <div v-else-if="choice.type === 'needs_priority_table'" class="choice-priority-table">
              <table class="priority-table">
                <thead>
                  <tr>
                    <th class="need-name-header">Need</th>
                    <th class="priority-header">Priority</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="need in choice.needs" :key="need.id">
                    <td class="need-name">{{ need.name }}</td>
                    <td class="need-priority">
                      <input
                        type="number"
                        class="priority-input"
                        min="0"
                        max="1"
                        step="0.01"
                        :value="userChoices[choice.key]?.[need.id] ?? 1.0"
                        @input="updateNeedPriority(choice.key, need.id, $event)"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Migrations -->
        <div v-if="preview.migration_analysis.needs_migration || hasAmbiguousMigrations" class="section migrations">
          <h3>Migrations to Apply</h3>

          <div
            v-for="(migration, i) in preview.migration_analysis.migrations"
            :key="i"
            class="migration-item"
          >
            <div class="migration-header">
              <span class="migration-type">
                <FontAwesomeIcon :icon="getMigrationIcon(migration.type)" />
              </span>
              <span class="migration-description">{{ migration.description }}</span>
              <span v-if="!migration.is_ambiguous" class="migration-count">{{ migration.affected_count }} items</span>
              <span v-else class="migration-count ambiguous">
                <FontAwesomeIcon :icon="faQuestionCircle" />
                Requires selection
              </span>
            </div>

            <!-- Weight Migration Summary (確定している場合) -->
            <div v-if="migration.type === 'edge_weights' && migration.summary && Object.keys(migration.summary).length > 0" class="migration-details weight-summary">
              <table class="weight-table">
                <thead>
                  <tr>
                    <th>Weight Change</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(count, change) in migration.summary" :key="change">
                    <td class="weight-change">{{ change }}</td>
                    <td class="weight-count">{{ count }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="migration.has_legacy_format" class="format-badge legacy">
                Legacy format detected (±0.33)
              </div>
            </div>

            <!-- Weight Migration Ambiguous Summary (曖昧な場合) -->
            <div v-else-if="migration.type === 'edge_weights' && migration.is_ambiguous && migration.ambiguous_summary" class="migration-details weight-summary">
              <p class="ambiguous-note">
                <FontAwesomeIcon :icon="faInfoCircle" />
                If you select "Legacy format", the following conversions will be applied:
              </p>
              <table class="weight-table">
                <thead>
                  <tr>
                    <th>Weight Change</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(count, change) in migration.ambiguous_summary" :key="change">
                    <td class="weight-change">{{ change }}</td>
                    <td class="weight-count">{{ count }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Other Migration Details -->
            <div v-else-if="migration.details && migration.details.length > 0" class="migration-details">
              <details>
                <summary>Show details ({{ Math.min(migration.details.length, 10) }} of {{ migration.affected_count }})</summary>
                <ul class="detail-list">
                  <li v-for="(detail, j) in migration.details.slice(0, 10)" :key="j">
                    <template v-if="migration.type === 'needs_priority'">
                      {{ detail.name }}: {{ detail.change }}
                    </template>
                    <template v-else-if="migration.type === 'design_case_fields'">
                      {{ detail.name }}: +{{ detail.missing_fields.join(', +') }}
                    </template>
                    <template v-else-if="migration.type === 'node_type'">
                      [{{ detail.case_name }}] {{ detail.node_label }}: {{ detail.change }}
                    </template>
                    <template v-else>
                      {{ JSON.stringify(detail) }}
                    </template>
                  </li>
                </ul>
              </details>
            </div>
          </div>
        </div>

        <!-- No Migration Needed -->
        <div v-else class="section no-migration">
          <p class="success-message">No migration needed. Data is already in the latest format.</p>
        </div>

        <!-- Warnings -->
        <div v-if="visibleWarnings.length > 0" class="section warnings">
          <details>
            <summary class="warning-title">
              Warnings ({{ preview.validation.warnings.length }})
            </summary>
            <ul class="warning-list">
              <li v-for="(warning, i) in visibleWarnings" :key="i">{{ warning }}</li>
            </ul>
            <p v-if="preview.validation.warnings.length > 20" class="more-warnings">
              ... and {{ preview.validation.warnings.length - 20 }} more warnings
            </p>
          </details>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
        <button
          class="btn btn-primary"
          @click="handleConfirm"
          :disabled="!canImport"
        >
          {{ importButtonLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import type { ImportPreviewResponse } from '@/utils/api';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import type { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import { faChartBar, faFolderOpen, faTag, faBalanceScale, faFileAlt, faQuestionCircle, faInfoCircle } from '@fortawesome/free-solid-svg-icons';

const props = defineProps<{
  visible: boolean;
  preview: ImportPreviewResponse;
}>();

const emit = defineEmits<{
  (e: 'confirm', userChoices: Record<string, any>): void;
  (e: 'cancel'): void;
}>();

// ユーザー選択の状態管理
const userChoices = reactive<Record<string, any>>({});

// previewが変わったらデフォルト値で初期化
watch(() => props.preview, (newPreview) => {
  if (newPreview?.migration_analysis?.user_choices) {
    for (const choice of newPreview.migration_analysis.user_choices) {
      if (!(choice.key in userChoices)) {
        userChoices[choice.key] = choice.default;
      }
    }
  }
}, { immediate: true });

const hasUserChoices = computed(() => {
  return props.preview.migration_analysis.user_choices &&
         props.preview.migration_analysis.user_choices.length > 0;
});

const hasAmbiguousMigrations = computed(() => {
  return props.preview.migration_analysis.migrations.some(m => m.is_ambiguous);
});

const visibleWarnings = computed(() => {
  return props.preview.validation.warnings.slice(0, 20);
});

const canImport = computed(() => {
  return props.preview.validation.valid;
});

const importButtonLabel = computed(() => {
  if (props.preview.migration_analysis.needs_migration || hasAmbiguousMigrations.value) {
    return 'Import with Migrations';
  }
  return 'Import';
});

function getMigrationIcon(type: string): IconDefinition {
  const icons: Record<string, IconDefinition> = {
    needs_priority: faChartBar,
    design_case_fields: faFolderOpen,
    node_type: faTag,
    edge_weights: faBalanceScale
  };
  return icons[type] || faFileAlt;
}

function updateNeedPriority(choiceKey: string, needId: string, event: Event) {
  const target = event.target as HTMLInputElement;
  let priority = parseFloat(target.value);

  // 範囲チェック
  if (isNaN(priority)) {
    priority = 1.0;
  } else if (priority < 0) {
    priority = 0;
  } else if (priority > 1) {
    priority = 1;
  }

  // userChoices[choiceKey]がオブジェクトでない場合は初期化
  if (!userChoices[choiceKey] || typeof userChoices[choiceKey] !== 'object') {
    userChoices[choiceKey] = {};
  }

  userChoices[choiceKey][needId] = priority;
}

function handleConfirm() {
  emit('confirm', { ...userChoices });
}
</script>

<style scoped lang="scss">
@import '@/style/_color.scss';

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
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
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

.section {
  margin-bottom: 20px;
}

.section h3 {
  margin: 0 0 12px 0;
  font-size: 1rem;
  color: $main_2;
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-info .counts {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.count-item {
  background: $gray;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 0.875rem;
  color: $white;
}

.count-item strong {
  color: $sub_6;
}

.version-badge-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version-badge {
  padding: 6px 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
}

.version-badge.source {
  background: rgba($sub_2, 0.2);
  color: $sub_2;
}

.version-badge.target {
  background: rgba($sub_4, 0.2);
  color: $sub_4;
}

.arrow {
  color: $main_3;
  font-size: 1.2rem;
}

/* User Choices Section */
.user-choices {
  background: rgba($sub_6, 0.1);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid rgba($sub_6, 0.3);
}

.user-choices h3 {
  color: $sub_6;
}

.user-choice-item {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba($black, 0.3);
  border-radius: 6px;
}

.user-choice-item:last-child {
  margin-bottom: 0;
}

.choice-label {
  font-weight: 600;
  color: $white;
  display: block;
  margin-bottom: 4px;
}

.choice-description {
  color: $main_3;
  font-size: 0.85rem;
  margin: 0 0 12px 0;
}

.choice-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: $gray;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
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
}

.radio-description {
  font-size: 0.8rem;
  color: $main_3;
}

.choice-number {
  display: flex;
  align-items: center;
  gap: 8px;
}

.number-input {
  width: 100px;
  padding: 8px 12px;
  border: 1px solid $main_1;
  border-radius: 4px;
  background: $gray;
  color: $white;
  font-size: 1rem;
}

.number-input:focus {
  outline: none;
  border-color: $sub_6;
}

/* Needs Priority Table */
.choice-priority-table {
  max-height: 300px;
  overflow-y: auto;
  border-radius: 6px;
  border: 1px solid $main_1;
}

.priority-table {
  width: 100%;
  border-collapse: collapse;
}

.priority-table th {
  position: sticky;
  top: 0;
  background: $gray;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: $main_2;
  border-bottom: 2px solid $main_1;
}

.priority-table .priority-header {
  width: 100px;
  text-align: center;
  background: #10b981;
  color: white;
}

.priority-table td {
  padding: 8px 12px;
  border-bottom: 1px solid $main_1;
}

.priority-table tr:last-child td {
  border-bottom: none;
}

.priority-table tr:hover {
  background: rgba($white, 0.03);
}

.need-name {
  color: $white;
}

.need-priority {
  text-align: center;
}

.priority-input {
  width: 80px;
  padding: 6px 8px;
  border: 1px solid $main_1;
  border-radius: 4px;
  background: $gray;
  color: $white;
  font-size: 0.9rem;
  text-align: center;
}

.priority-input:focus {
  outline: none;
  border-color: $sub_6;
}

/* Migration Items */
.migration-item {
  background: $gray;
  border: 1px solid $main_1;
  border-radius: 6px;
  margin-bottom: 12px;
  overflow: hidden;
}

.migration-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba($main_1, 0.3);
}

.migration-type {
  font-size: 1rem;
  color: $sub_6;
  width: 20px;
  text-align: center;
}

.migration-description {
  flex: 1;
  font-weight: 500;
  color: $white;
}

.migration-count {
  background: $sub_6;
  color: $white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
}

.migration-count.ambiguous {
  background: $sub_2;
  display: flex;
  align-items: center;
  gap: 4px;
}

.migration-details {
  padding: 12px;
  font-size: 0.875rem;
  color: $white;
}

.ambiguous-note {
  color: $sub_2;
  font-size: 0.85rem;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.weight-table {
  width: 100%;
  border-collapse: collapse;
}

.weight-table th,
.weight-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid $main_1;
}

.weight-table th {
  background: rgba($main_1, 0.3);
  font-weight: 500;
  color: $main_2;
}

.weight-change {
  font-family: monospace;
  color: $white;
}

.weight-count {
  text-align: right;
  color: $sub_6;
}

.format-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.format-badge.legacy {
  background: rgba($sub_2, 0.2);
  color: $sub_2;
}

.detail-list {
  margin: 8px 0;
  padding-left: 20px;
  color: $main_3;
}

.detail-list li {
  margin-bottom: 4px;
  font-family: monospace;
  font-size: 0.8rem;
}

.errors {
  background: rgba($sub_1, 0.2);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid $sub_1;
}

.error-title {
  color: $sub_1;
}

.error-list {
  margin: 0;
  padding-left: 20px;
  color: $sub_1;
}

.warnings {
  background: rgba($sub_2, 0.15);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid rgba($sub_2, 0.5);
}

.warning-title {
  color: $sub_2;
  cursor: pointer;
}

.warning-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
  color: $sub_2;
  font-size: 0.85rem;
}

.more-warnings {
  color: $main_3;
  font-style: italic;
  margin: 8px 0 0 0;
}

.no-migration {
  background: rgba($sub_4, 0.15);
  padding: 16px;
  border-radius: 6px;
  text-align: center;
  border: 1px solid rgba($sub_4, 0.5);
}

.success-message {
  color: $sub_4;
  margin: 0;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid $main_1;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
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

details summary {
  cursor: pointer;
  user-select: none;
  color: $main_3;
}

details summary:hover {
  color: $sub_6;
}
</style>
