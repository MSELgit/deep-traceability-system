<template>
  <div class="design-case-list">
    <div class="list-header">
      <h2>Design Case List</h2>
      <button class="close-btn" @click="$emit('toggle-panel')">✕</button>
    </div>

    <!-- Peak elevation display -->
    <div v-if="hMax !== null" class="h-max-display">
      <span class="label">Peak Elevation H<sub>max</sub></span>
      <span class="value">{{ hMax.toFixed(2) }}</span>
    </div>

    <div class="actions">
      <button class="create-btn" @click="$emit('create')">
        + New Design Case
      </button>
    </div>

    <div class="sort-control">
      <label>Sort by:</label>
      <select :value="sortBy" @change="$emit('sort-change', ($event.target as HTMLSelectElement).value)">
        <option value="height-desc">Elevation (High → Low)</option>
        <option value="height-asc">Elevation (Low → High)</option>
        <option value="date-desc">Created Date (New → Old)</option>
        <option value="date-asc">Created Date (Old → New)</option>
        <option value="name">Name (A → Z)</option>
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
            title="Highlight in mountain view"
          >
            <FontAwesomeIcon :icon="['fas', 'eye']" />
          </button>
          <button 
            class="action-btn edit-btn" 
            @click="$emit('edit', designCase)"
            title="Edit"
          >
            <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
          </button>
          <button 
            class="action-btn copy-btn" 
            @click="$emit('copy', designCase)"
            title="Copy"
          >
            <FontAwesomeIcon :icon="['fas', 'copy']" />
          </button>
          <button 
            class="action-btn delete-btn" 
            @click="$emit('delete', designCase)"
            title="Delete"
          >
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>

      <div v-if="designCases.length === 0" class="empty-state">
        <p>No design cases</p>
        <p class="empty-hint">Create one using "+ New Design Case"</p>
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

.design-case-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: lighten($gray, 8%);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1rem, 2vw, 1.5rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
}

.list-header h2 {
  margin: 0;
  font-size: clamp(1.1rem, 1.8vw, 1.3rem);
  font-weight: 600;
  color: $white;
}

.close-btn {
  width: clamp(1.8rem, 3vw, 2rem);
  height: clamp(1.8rem, 3vw, 2rem);
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: clamp(1.2rem, 2vw, 1.4rem);
  color: color.adjust($white, $alpha: -0.4);
  border-radius: 0.3vw;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: color.adjust($gray, $lightness: 15%);
  color: $white;
}

/* Peak elevation display */
.h-max-display {
  padding: clamp(0.75rem, 1.5vh, 1rem) clamp(1rem, 2vw, 1.5rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  border-bottom: 2px solid color.adjust($white, $alpha: -0.8);
}

.h-max-display .label {
  font-weight: 600;
  opacity: 0.9;
}

.h-max-display .value {
  font-size: clamp(1.1rem, 1.8vw, 1.3rem);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.actions {
  padding: clamp(0.8rem, 1.5vh, 1rem) clamp(1rem, 2vw, 1.5rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
}

.create-btn {
  width: 100%;
  padding: clamp(0.75rem, 1.5vh, 1rem);
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  color: $white;
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 0.3vh 1vh color.adjust($main_1, $alpha: -0.7);
}

.create-btn:hover {
  background: linear-gradient(135deg, lighten($main_1, 10%) 0%, lighten($main_2, 10%) 100%);
  box-shadow: 0 0.5vh 1.5vh color.adjust($main_1, $alpha: -0.5);
  transform: translateY(-0.1vh);
}

.sort-control {
  padding: clamp(0.6rem, 1.2vh, 0.8rem) clamp(1rem, 2vw, 1.5rem);
  display: flex;
  align-items: center;
  gap: 0.8vw;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  background: color.adjust($gray, $lightness: 5%);
}

.sort-control label {
  font-size: clamp(0.75rem, 1vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
  white-space: nowrap;
}

.sort-control select {
  flex: 1;
  padding: 0.6vh 0.8vw;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.3vw;
  font-size: clamp(0.75rem, 1vw, 0.85rem);
  background: $gray;
  color: $white;
  cursor: pointer;
}

.sort-control select:focus {
  outline: none;
  border-color: $main_1;
}

.case-list {
  flex: 1;
  overflow-y: auto;
  padding: clamp(0.6rem, 1.2vh, 0.8rem);
  @include custom-scrollbar;
}

.case-card {
  display: flex;
  align-items: center;
  gap: 1vw;
  padding: clamp(0.75rem, 1.5vh, 1rem);
  background: linear-gradient(145deg, lighten($gray, 12%), lighten($gray, 8%));
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.5vw;
  margin-bottom: 0.8vh;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.case-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 0;
  height: 100%;
  background: linear-gradient(90deg, transparent, color.adjust($main_1, $alpha: -0.9));
  transition: width 0.3s ease;
}

.case-card:hover {
  box-shadow: 0 0.5vh 1.5vh color.adjust($black, $alpha: -0.5);
  border-color: color.adjust($main_1, $alpha: -0.7);
  transform: translateY(-0.1vh);
}

.case-card:hover::before {
  width: 100%;
}

.case-color {
  width: 0.5vw;
  height: clamp(2.5rem, 4vh, 3rem);
  border-radius: 0.3vw;
  flex-shrink: 0;
  box-shadow: 0 0 0.5vh rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.case-info {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.case-name {
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  font-weight: 600;
  color: $white;
  margin-bottom: 0.5vh;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-meta {
  display: flex;
  gap: 1vw;
  font-size: clamp(0.7rem, 0.95vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.5);
}

.case-height {
  background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 600;
}

.case-actions {
  display: flex;
  gap: 0.5vw;
  position: relative;
  z-index: 1;
}

.action-btn {
  width: clamp(1.8rem, 3vw, 2rem);
  height: clamp(1.8rem, 3vw, 2rem);
  border: none;
  background: color.adjust($gray, $lightness: 20%);
  border-radius: 0.4vw;
  cursor: pointer;
  font-size: clamp(0.8rem, 1.1vw, 0.9rem);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: color.adjust($white, $alpha: -0.4);
}

.action-btn:hover {
  transform: translateY(-0.1vh);
}

.action-btn.focus-btn:hover {
  color: $white;
  background: $main_1;
  box-shadow: 0 0.2vh 0.8vh color.adjust($main_1, $alpha: -0.5);
}

.action-btn.edit-btn:hover {
  color: $white;
  background: $sub_1;
  box-shadow: 0 0.2vh 0.8vh color.adjust($sub_1, $alpha: -0.5);
}

.action-btn.copy-btn:hover {
  color: $white;
  background: $sub_3;
  box-shadow: 0 0.2vh 0.8vh color.adjust($sub_3, $alpha: -0.5);
}

.action-btn.delete-btn:hover {
  color: $white;
  background: $sub_1;
  box-shadow: 0 0.2vh 0.8vh color.adjust($sub_1, $alpha: -0.5);
}

.empty-state {
  text-align: center;
  padding: clamp(3rem, 6vh, 4rem) clamp(1rem, 2vw, 1.5rem);
  color: color.adjust($white, $alpha: -0.5);
}

.empty-state p {
  margin: 0.8vh 0;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
}

.empty-hint {
  font-size: clamp(0.75rem, 1vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.6);
  font-style: italic;
}
</style>