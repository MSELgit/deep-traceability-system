<template>
  <div v-if="showAnalysis" class="decomposition-analysis">
    <h3>Insufficient Decomposition Analysis</h3>
    <div v-if="analysis.rootLevel.length > 0" class="analysis-item">
      <strong>Root-level performances with insufficient decomposition for needs:</strong>
      <span class="performance-list">{{ analysis.rootLevel.join(', ') }}</span>
    </div>
    <div v-if="analysis.leafLevel.length > 0" class="analysis-item">
      <strong>Leaf-level performances with insufficient decomposition for needs:</strong>
      <span class="performance-list">{{ analysis.leafLevel.join(', ') }}</span>
    </div>
    <div class="analysis-action">
      <button class="decompose-button" @click="$emit('navigate-to-performance')">
        Decompose
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  analysis: {
    rootLevel: string[]
    leafLevel: string[]
  }
  needsCount: number
  hasStakeholdersOrPerformances: boolean
}>()

defineEmits<{
  'navigate-to-performance': []
}>()

const showAnalysis = computed(() => {
  return (props.analysis.rootLevel.length > 0 || props.analysis.leafLevel.length > 0) && 
         props.needsCount > 0 && 
         props.hasStakeholdersOrPerformances
})
</script>

<style scoped lang="scss">
@import '../../style/color';

.decomposition-analysis {
  margin-top: 3vh;
  padding: 2vh 2vw;
  background: lighten($gray, 8%);
  border-radius: 1vw;
  border: 1px solid transparentize($white, 0.9);
  border-left: 4px solid $main_1;
}

.decomposition-analysis h3 {
  font-size: clamp(1.1rem, 1.5vw, 1.3rem);
  margin-bottom: 2vh;
  color: $white;
  font-weight: 600;
}

.analysis-item {
  margin-bottom: 1.5vh;
  line-height: 1.8;
}

.analysis-item strong {
  color: transparentize($white, 0.2);
  font-weight: 600;
  display: block;
  margin-bottom: 0.5vh;
}

.performance-list {
  color: $sub_1;
  font-weight: 600;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
}

.analysis-action {
  margin-top: 2vh;
  text-align: center;
}

.decompose-button {
  padding: 1.5vh 3vw;
  font-size: clamp(0.9rem, 1.2vw, 1.1rem);
  font-weight: 600;
  color: $white;
  background: linear-gradient(135deg, $main_1, $main_2);
  border: none;
  border-radius: 0.8vw;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0.5vh 1vh transparentize($main_1, 0.6);
}

.decompose-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.8vh 2vh transparentize($main_1, 0.4);
}

.decompose-button:active {
  transform: translateY(0);
  box-shadow: 0 0.3vh 0.8vh transparentize($main_1, 0.6);
}
</style>