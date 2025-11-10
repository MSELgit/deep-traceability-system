<template>
  <div class="design-case-list">
    <div class="list-header">
      <h2>設計案一覧</h2>
      <button class="close-btn" @click="$emit('toggle-panel')">✕</button>
    </div>

    <!-- 頂点標高表示 -->
    <div v-if="hMax !== null" class="h-max-display">
      <span class="label">頂点標高 H<sub>max</sub></span>
      <span class="value">{{ hMax.toFixed(2) }}</span>
    </div>

    <div class="actions">
      <button class="create-btn" @click="$emit('create')">
        + 新規設計案
      </button>
    </div>

    <div class="sort-control">
      <label>並び替え:</label>
      <select :value="sortBy" @change="$emit('sort-change', ($event.target as HTMLSelectElement).value)">
        <option value="height-desc">標高（高→低）</option>
        <option value="height-asc">標高（低→高）</option>
        <option value="date-desc">作成日時（新→旧）</option>
        <option value="date-asc">作成日時（旧→新）</option>
        <option value="name">名前（A→Z）</option>
      </select>
    </div>

    <div class="case-list">
      <div
        v-for="designCase in designCases"
        :key="designCase.id"
        class="case-card"
      >
        <div class="case-color" :style="{ background: designCase.color }"></div>
        
        <div class="case-info">
          <div class="case-name">{{ designCase.name }}</div>
          <div class="case-meta">
            <span v-if="designCase.mountain_position" class="case-height">
              H={{ designCase.mountain_position.H.toFixed(1) }}
            </span>
            <span class="case-date">
              {{ formatDate(designCase.created_at) }}
            </span>
          </div>
        </div>

        <div class="case-actions">
          <button 
            class="action-btn focus-btn" 
            @click="$emit('focus', designCase)"
            title="山で強調表示"
          >
            <FontAwesomeIcon :icon="['fas', 'eye']" />
          </button>
          <button 
            class="action-btn edit-btn" 
            @click="$emit('edit', designCase)"
            title="編集"
          >
            <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
          </button>
          <button 
            class="action-btn copy-btn" 
            @click="$emit('copy', designCase)"
            title="コピー"
          >
            <FontAwesomeIcon :icon="['fas', 'copy']" />
          </button>
          <button 
            class="action-btn delete-btn" 
            @click="$emit('delete', designCase)"
            title="削除"
          >
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>

      <div v-if="designCases.length === 0" class="empty-state">
        <p>設計案がありません</p>
        <p class="empty-hint">「+ 新規設計案」から作成してください</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DesignCase } from '../../types/project';

const props = defineProps<{
  designCases: DesignCase[];
  sortBy: string;
  hMax: number | null;
}>();


defineEmits<{
  'toggle-panel': [];
  'create': [];
  'edit': [designCase: DesignCase];
  'copy': [designCase: DesignCase];
  'delete': [designCase: DesignCase];
  'focus': [designCase: DesignCase];
  'sort-change': [sortBy: string];
}>();

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return `${date.getMonth() + 1}/${date.getDate()}`;
}
</script>

<style scoped>
.design-case-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.list-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 20px;
  color: #666;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

/* 頂点標高表示 */
.h-max-display {
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
}

.h-max-display .label {
  font-weight: 600;
}

.h-max-display .value {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.actions {
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.create-btn {
  width: 100%;
  padding: 12px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.create-btn:hover {
  background: #45a049;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.sort-control {
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.sort-control label {
  font-size: 13px;
  color: #666;
}

.sort-control select {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  background: white;
}

.case-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.case-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s;
}

.case-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #ccc;
}

.case-color {
  width: 8px;
  height: 40px;
  border-radius: 4px;
  flex-shrink: 0;
}

.case-info {
  flex: 1;
  min-width: 0;
}

.case-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

.case-height {
  color: #4CAF50;
  font-weight: 500;
}

.case-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: #e0e0e0;
  transform: translateY(-1px);
}

.delete-btn:hover {
  background: #ffebee;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state p {
  margin: 8px 0;
}

.empty-hint {
  font-size: 13px;
  color: #bbb;
}
</style>