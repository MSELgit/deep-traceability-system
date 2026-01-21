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
@use 'sass:color';
@import '../../style/color';

.decomposition-analysis {
  margin-top: 3vh;
  padding: 2.5vh 2.5vw;
  background: linear-gradient(145deg, color.adjust($gray, $lightness: 8%), color.adjust($gray, $lightness: 3%));
  border-radius: 1vw;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  box-shadow: 0 0.5vh 2vh color.adjust($black, $alpha: -0.5);
  position: relative;
  overflow: hidden;
}

.decomposition-analysis::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 0.3vh;
  background: linear-gradient(90deg, $main_1, $main_2);
}

.decomposition-analysis h3 {
  font-size: clamp(1.2rem, 1.5vw, 1.4rem);
  margin-bottom: 2.5vh;
  margin-top: 0.5vh;
  color: $white;
  font-weight: 600;
  letter-spacing: -0.02em;
  display: flex;
  align-items: center;
  gap: 1vw;
}

.analysis-item {
  margin-bottom: 1.8vh;
  padding: 1.5vh 1.5vw;
  background: color.adjust($black, $alpha: -0.6);
  border-radius: 0.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.92);
  position: relative;
  transition: all 0.3s ease;
}

.analysis-item:hover {
  transform: translateX(0.3vw);
  border-color: color.adjust($main_1, $alpha: -0.7);
  background: color.adjust($black, $alpha: -0.5);
}

.analysis-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 0.3vw;
  background: linear-gradient(180deg, $sub_1, $sub_3);
  border-radius: 0.5vw 0 0 0.5vw;
}

.analysis-item strong {
  color: color.adjust($white, $alpha: -0.3);
  font-weight: 500;
  display: block;
  margin-bottom: 0.8vh;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.performance-list {
  color: $white;
  font-weight: 500;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  line-height: 1.6;
  padding-left: 1vw;
}

.analysis-action {
  margin-top: 2vh;
  display: flex;
  justify-content: center;
}

.decompose-button {
  padding: 1.5vh 2.5vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 600;
  color: $white;
  background: linear-gradient(135deg, $main_1, $main_2);
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.decompose-button:hover {
  box-shadow: 0 0.5vh 2vh color.adjust($main_2, $alpha: -0.6);
}
</style>