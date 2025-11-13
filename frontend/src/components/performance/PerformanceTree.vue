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
        </div>

        <div class="node-actions">
          <button 
            class="icon-btn"
            @click="$emit('add-child', performance)"
            title="Add child performance"
          >
            +
          </button>
          <button 
            class="icon-btn"
            @click="$emit('edit', performance)"
            title="Edit"
          >
            <FontAwesomeIcon :icon="['fas', 'pen-to-square']" />
          </button>
          <button 
            class="icon-btn danger"
            @click="$emit('delete', performance)"
            title="Delete"
          >
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>

      <!-- Display child performances recursively -->
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
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

defineProps<{
  performances: Performance[]
}>()

defineEmits<{
  'add-child': [performance: Performance]
  'edit': [performance: Performance]
  'delete': [performance: Performance]
}>()
</script>

<style scoped lang="scss">
@import '../../style/color';
.tree-node {
  margin-bottom: 1vh;
}

.node-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5vh 1.5vw;
  background: lighten($gray, 8%);
  border: 1px solid transparentize($white, 0.9);
  border-radius: 0.8vw;
  transition: all 0.3s ease;
}

.node-content:hover {
  border-color: transparentize($main_1, 0.5);
  box-shadow: 0 0.5vh 1.5vh transparentize($main_1, 0.8);
  background: lighten($gray, 10%);
}

.node-content.is-leaf {
  border-left: 4px solid $sub_4;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 0.8vw;
  flex: 1;
}

.node-icon {
  font-size: clamp(1rem, 1.3vw, 1.2rem);
  color: $main_1;
}

.node-name {
  font-weight: 600;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  color: $white;
}

.node-unit {
  color: transparentize($white, 0.4);
  font-size: clamp(0.8rem, 0.95vw, 0.9rem);
}

.node-actions {
  display: flex;
  gap: 0.5vw;
}

.icon-btn {
  padding: 0.6vh 0.8vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  background: transparentize($black, 0.5);
  border: 1px solid transparentize($white, 0.9);
  border-radius: 0.4vw;
  cursor: pointer;
  transition: all 0.2s ease;
  color: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
}

.icon-btn:hover {
  background: transparentize($black, 0.3);
  border-color: transparentize($white, 0.8);
  transform: scale(1.1);
}

.icon-btn.danger {
  color: $sub_1;
}

.icon-btn.danger:hover {
  background: transparentize($sub_1, 0.9);
  border-color: $sub_1;
}
.icon-btn.danger:hover {
  background: #fee;
  border-color: #e74c3c;
  color: #e74c3c;
}
</style>
