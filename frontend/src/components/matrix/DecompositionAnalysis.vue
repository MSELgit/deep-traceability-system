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
  padding: 2.5vh 2.5vw;
  background: $gray;
  border-radius: 0.8vw;
  border: 1px solid transparentize($white, 0.85);
  box-shadow: 0 0.3vh 1vh transparentize($black, 0.7);
  position: relative;
  overflow: hidden;
}

.decomposition-analysis::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 0.5vh;
  background: linear-gradient(90deg, $sub_1, $sub_2, $sub_3);
}

.decomposition-analysis h3 {
  font-size: clamp(1.2rem, 1.6vw, 1.4rem);
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
  margin-bottom: 2vh;
  padding: 1.5vh 1.5vw;
  background: transparentize($black, 0.5);
  border-radius: 0.5vw;
  border: 1px solid transparentize($white, 0.95);
  line-height: 1.8;
}

.analysis-item strong {
  color: transparentize($white, 0.1);
  font-weight: 500;
  display: block;
  margin-bottom: 1vh;
  font-size: clamp(0.8rem, 0.95vw, 0.9rem);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.7;
}

.performance-list {
  color: $white;
  font-weight: 500;
  font-size: clamp(0.95rem, 1.1vw, 1.05rem);
  display: block;
  padding-left: 1.5vw;
  position: relative;
}

.performance-list::before {
  content: '→';
  position: absolute;
  left: 0;
  color: $main_2;
  font-weight: 700;
}

.analysis-action {
  margin-top: 2.5vh;
  display: flex;
  justify-content: center;
}

.decompose-button {
  padding: 1.2vh 2.5vw;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  font-weight: 600;
  color: $white;
  background: linear-gradient(135deg, $main_1, $main_2);
  border: none;
  border-radius: 0.5vw;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0.3vh 0.8vh transparentize($black, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  position: relative;
  overflow: hidden;
}

.decompose-button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: transparentize($white, 0.8);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.decompose-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 1.2vh transparentize($black, 0.4);
}

.decompose-button:hover::before {
  width: 300%;
  height: 300%;
}

.decompose-button:active {
  transform: translateY(0);
  box-shadow: 0 0.3vh 0.8vh transparentize($main_1, 0.6);
}
</style>