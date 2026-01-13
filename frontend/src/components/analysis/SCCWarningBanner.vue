<template>
  <div v-if="sccResult && (sccResult.has_loops || showInfo)" class="scc-banner-container">
    <!-- 発散ループ警告（ρ >= 1） -->
    <div
      v-if="hasDivergentLoop"
      class="scc-banner scc-warning"
    >
      <div class="banner-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </div>
      <div class="banner-content">
        <div class="banner-title">Divergent Loop Detected</div>
        <div class="banner-message">
          <span v-for="(comp, idx) in divergentComponents" :key="idx">
            [{{ comp.nodes.join(' ↔ ') }}] ρ={{ comp.spectral_radius.toFixed(3) }}
            <span v-if="idx < divergentComponents.length - 1">, </span>
          </span>
        </div>
        <div v-if="topSuggestion" class="banner-suggestion">
          Suggestion: {{ topSuggestion.description }}
        </div>
      </div>
      <div class="banner-actions">
        <button class="btn-details" @click="showDetails = !showDetails">
          {{ showDetails ? 'Hide Details' : 'Show Details' }}
        </button>
        <button class="btn-continue" @click="$emit('continue')">
          Continue Anyway
        </button>
      </div>
    </div>

    <!-- 収束ループ情報（ρ < 1） -->
    <div
      v-else-if="hasConvergentLoop && showInfo"
      class="scc-banner scc-info"
    >
      <div class="banner-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
      </div>
      <div class="banner-content">
        <div class="banner-title">Convergent Loop Detected</div>
        <div class="banner-message">
          <span v-for="(comp, idx) in convergentComponents" :key="idx">
            [{{ comp.nodes.join(' ↔ ') }}] ρ={{ comp.spectral_radius.toFixed(3) }}
            <span v-if="idx < convergentComponents.length - 1">, </span>
          </span>
          - Calculations are possible (Neumann series converges)
        </div>
      </div>
      <button class="btn-dismiss" @click="$emit('dismiss')">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- 詳細パネル -->
    <div v-if="showDetails && hasDivergentLoop" class="scc-details">
      <div v-for="(comp, idx) in sccResult.components" :key="idx" class="detail-component">
        <div class="detail-header">
          <span class="component-label">Component {{ idx + 1 }}</span>
          <span :class="['convergence-badge', comp.converges ? 'converges' : 'diverges']">
            {{ comp.converges ? 'Converges' : 'Diverges' }}
          </span>
        </div>
        <div class="detail-nodes">
          <strong>Nodes:</strong> {{ comp.nodes.join(', ') }}
        </div>
        <div class="detail-spectral">
          <strong>Spectral Radius:</strong> ρ = {{ comp.spectral_radius.toFixed(4) }}
          <span v-if="!comp.converges" class="spectral-warning">(≥ 1, divergent)</span>
        </div>
        <div v-if="comp.suggestions && comp.suggestions.length > 0" class="detail-suggestions">
          <strong>Resolution Suggestions:</strong>
          <ul>
            <li v-for="(sug, sIdx) in comp.suggestions" :key="sIdx" :class="['suggestion-item', sug.type]">
              <span class="suggestion-type">{{ formatSuggestionType(sug.type) }}</span>
              {{ sug.description }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { SCCAnalysisResult, SCCComponent } from '@/utils/api';

interface Props {
  sccResult: SCCAnalysisResult | null;
  showInfo?: boolean; // 収束ループの情報も表示するか
}

const props = withDefaults(defineProps<Props>(), {
  showInfo: true,
});

defineEmits<{
  (e: 'continue'): void;
  (e: 'dismiss'): void;
}>();

const showDetails = ref(false);

const divergentComponents = computed<SCCComponent[]>(() => {
  if (!props.sccResult) return [];
  return props.sccResult.components.filter(c => !c.converges);
});

const convergentComponents = computed<SCCComponent[]>(() => {
  if (!props.sccResult) return [];
  return props.sccResult.components.filter(c => c.converges);
});

const hasDivergentLoop = computed(() => divergentComponents.value.length > 0);
const hasConvergentLoop = computed(() => convergentComponents.value.length > 0);

const topSuggestion = computed(() => {
  if (!props.sccResult) return null;
  for (const comp of divergentComponents.value) {
    if (comp.suggestions && comp.suggestions.length > 0) {
      return comp.suggestions[0];
    }
  }
  return null;
});

function formatSuggestionType(type: string): string {
  const typeMap: Record<string, string> = {
    edge_removal: 'Edge Removal',
    node_merge: 'Node Merge',
    constraint: 'Constraint',
    convergent: 'Convergent',
  };
  return typeMap[type] || type;
}
</script>

<style scoped>
.scc-banner-container {
  margin: 8px 0;
}

.scc-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
}

.scc-warning {
  background: #fef3cd;
  border: 1px solid #ffc107;
  color: #856404;
}

.scc-info {
  background: #d1ecf1;
  border: 1px solid #17a2b8;
  color: #0c5460;
}

.banner-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.banner-content {
  flex: 1;
  min-width: 0;
}

.banner-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.banner-message {
  font-size: 12px;
  opacity: 0.9;
}

.banner-suggestion {
  margin-top: 6px;
  font-size: 12px;
  font-style: italic;
}

.banner-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-details,
.btn-continue {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: none;
}

.btn-details {
  background: transparent;
  border: 1px solid currentColor;
  color: inherit;
}

.btn-continue {
  background: #856404;
  color: white;
}

.btn-dismiss {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  opacity: 0.7;
  color: inherit;
}

.btn-dismiss:hover {
  opacity: 1;
}

.scc-details {
  background: #fff8e1;
  border: 1px solid #ffe082;
  border-radius: 0 0 8px 8px;
  margin-top: -1px;
  padding: 12px 16px;
}

.detail-component {
  padding: 8px 0;
  border-bottom: 1px solid #ffe082;
}

.detail-component:last-child {
  border-bottom: none;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.component-label {
  font-weight: 600;
  color: #333;
}

.convergence-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}

.convergence-badge.converges {
  background: #d4edda;
  color: #155724;
}

.convergence-badge.diverges {
  background: #f8d7da;
  color: #721c24;
}

.detail-nodes,
.detail-spectral {
  font-size: 12px;
  color: #555;
  margin: 4px 0;
}

.spectral-warning {
  color: #dc3545;
  font-weight: 500;
}

.detail-suggestions {
  margin-top: 8px;
  font-size: 12px;
}

.detail-suggestions ul {
  margin: 4px 0 0 16px;
  padding: 0;
}

.suggestion-item {
  margin: 4px 0;
  color: #555;
}

.suggestion-type {
  font-weight: 500;
  color: #333;
}
</style>
