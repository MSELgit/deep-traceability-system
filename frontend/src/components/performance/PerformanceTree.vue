<template>
  <div class="performance-tree">
    <div 
      v-for="performance in performances" 
      :key="performance.id"
      class="tree-node"
      :style="{ marginLeft: `${performance.level * 30}px` }"
    >
      <div class="node-content" :class="{ 'is-leaf': performance.is_leaf }">
        <div class="node-header">
          <span class="node-icon">
            <FontAwesomeIcon :icon="performance.is_leaf ? ['fas', 'folder'] : ['fas', 'folder-open']" />
          </span>
          <span class="node-name">{{ performance.name }}</span>
          <span v-if="performance.unit" class="node-unit">({{ performance.unit }})</span>
          <span v-if="performance.is_leaf" class="leaf-badge">末端</span>
        </div>

        <div class="node-actions">
          <button 
            class="icon-btn"
            @click="$emit('add-child', performance)"
            title="子性能を追加"
          >
            +
          </button>
          <button 
            class="icon-btn"
            @click="$emit('edit', performance)"
            title="編集"
          >
            <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
          </button>
          <button 
            class="icon-btn danger"
            @click="$emit('delete', performance)"
            title="削除"
          >
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>

      <!-- 子性能を再帰的に表示 -->
      <PerformanceTree
        v-if="performance.children && performance.children.length > 0"
        :performances="performance.children"
        @add-child="$emit('add-child', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Performance } from '../../types/project'

defineProps<{
  performances: Performance[]
}>()

defineEmits<{
  'add-child': [performance: Performance]
  'edit': [performance: Performance]
  'delete': [performance: Performance]
}>()
</script>

<style scoped>
.tree-node {
  margin-bottom: 8px;
}

.node-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  transition: all 0.2s;
}

.node-content:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.node-content.is-leaf {
  border-left: 4px solid #28a745;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.node-icon {
  font-size: 20px;
  color: #666;
}

.node-name {
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.node-unit {
  color: #666;
  font-size: 14px;
}

.leaf-badge {
  background: #28a745;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.node-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  padding: 6px 10px;
  font-size: 16px;
  background: transparent;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: #f0f0f0;
  border-color: #999;
}

.icon-btn.danger {
  color: #e74c3c;
}
.icon-btn.danger:hover {
  background: #fee;
  border-color: #e74c3c;
  color: #e74c3c;
}
</style>
