<template>
  <div class="discretization-confidence">
    <div class="confidence-header">
      <h4>Discretization Confidence</h4>
      <button class="refresh-btn" @click="fetchConfidence" :disabled="loading">
        <FontAwesomeIcon :icon="['fas', 'rotate-right']" :spin="loading" />
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading...</span>
    </div>

    <div v-else-if="error" class="error-state">
      <FontAwesomeIcon :icon="['fas', 'exclamation-triangle']" />
      <span>{{ error }}</span>
    </div>

    <div v-else-if="!data" class="empty-state">
      <span>Click refresh to calculate</span>
    </div>

    <div v-else-if="!data.is_discrete" class="continuous-mode-state">
      <FontAwesomeIcon :icon="['fas', 'check-circle']" />
      <div class="continuous-message">
        <div class="title">Continuous Mode</div>
        <div class="description">No discretization - 100% precision</div>
      </div>
    </div>

    <div v-else class="confidence-content">
      <!-- Mode Info -->
      <div class="mode-info">
        <span class="mode-label">{{ data.n_discrete_levels || '?' }}-level discretization</span>
        <span class="mode-name">({{ formatModeName(data.weight_mode) }})</span>
      </div>

      <!-- Sign Preservation -->
      <div class="confidence-card" :class="getConfidenceClass">
        <div class="card-icon">
          <FontAwesomeIcon :icon="['fas', 'percentage']" />
        </div>
        <div class="card-content">
          <div class="card-label">Sign Preservation (P_sign)</div>
          <div class="card-value">
            {{ formatPercentage(data.sign_preservation_probability) }}
          </div>
          <div class="card-detail">
            Probability that inner product signs are preserved
          </div>
        </div>
      </div>

      <!-- Order Preservation -->
      <div class="confidence-card order" :class="getOrderClass">
        <div class="card-icon">
          <FontAwesomeIcon :icon="['fas', 'sort-amount-down']" />
        </div>
        <div class="card-content">
          <div class="card-label">Order Preservation (P_order)</div>
          <div class="card-value">
            {{ formatPercentage(data.order_preservation_probability) }}
          </div>
          <div class="card-detail">
            Probability that pairwise ordering is preserved
          </div>
        </div>
      </div>

      <!-- Technical Details -->
      <div class="technical-details">
        <div class="detail-row">
          <span class="detail-label">σ_eff (Effective Error)</span>
          <span class="detail-value">{{ formatSigmaEff(data.sigma_eff) }}</span>
        </div>
        <div v-if="data.connection_density" class="detail-row">
          <span class="detail-label">Connection Density (d)</span>
          <span class="detail-value">{{ data.connection_density.toFixed(3) }}</span>
        </div>
        <div v-if="data.B_AA_frobenius_norm" class="detail-row">
          <span class="detail-label">||B_AA||_F (Loop Factor)</span>
          <span class="detail-value">{{ data.B_AA_frobenius_norm.toFixed(4) }}</span>
        </div>
      </div>

      <!-- Interpretation -->
      <div class="interpretation" :class="getConfidenceClass">
        <FontAwesomeIcon :icon="getConfidenceIcon" />
        <span>{{ data.interpretation }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { calculationApi } from '../../utils/api';

const props = defineProps<{
  projectId: string;
  caseId: string;
  autoLoad?: boolean;
}>();

interface ConfidenceData {
  case_id: string;
  case_name: string;
  weight_mode: string;
  is_discrete: boolean;
  n_discrete_levels: number | null;
  sign_preservation_probability: number | null;
  min_sign_preservation: number | null;
  order_preservation_probability: number | null;
  sigma_eff: number;
  connection_density: number | null;
  B_AA_frobenius_norm: number | null;
  interpretation: string;
}

const data = ref<ConfidenceData | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

async function fetchConfidence() {
  if (!props.projectId || !props.caseId) {
    error.value = 'Missing project or case ID';
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const response = await calculationApi.getDiscretizationConfidence(props.projectId, props.caseId);
    data.value = response.data;
  } catch (e) {
    error.value = 'Failed to load confidence data';
    console.error('Discretization confidence error:', e);
  } finally {
    loading.value = false;
  }
}

function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  return `${(value * 100).toFixed(1)}%`;
}

function formatSigmaEff(value: number | null | undefined): string {
  if (value === null || value === undefined || value === 0) return 'N/A';
  return value.toFixed(4);
}

function formatModeName(mode: string): string {
  const names: Record<string, string> = {
    'discrete_3': '3-level: ±1, 0',
    'discrete_5': '5-level: ±3, ±1, 0',
    'discrete_7': '7-level: ±5, ±3, ±1, 0',
    'continuous': 'Continuous',
  };
  return names[mode] || mode;
}

const getConfidenceClass = computed(() => {
  const prob = data.value?.sign_preservation_probability;
  if (prob === null || prob === undefined) return '';
  if (prob >= 0.95) return 'excellent';
  if (prob >= 0.85) return 'good';
  if (prob >= 0.70) return 'moderate';
  return 'poor';
});

const getOrderClass = computed(() => {
  const prob = data.value?.order_preservation_probability;
  if (prob === null || prob === undefined) return '';
  if (prob >= 0.95) return 'excellent';
  if (prob >= 0.85) return 'good';
  if (prob >= 0.70) return 'moderate';
  return 'poor';
});

const getConfidenceIcon = computed(() => {
  const cls = getConfidenceClass.value;
  if (cls === 'excellent') return ['fas', 'check-circle'];
  if (cls === 'good') return ['fas', 'thumbs-up'];
  if (cls === 'moderate') return ['fas', 'info-circle'];
  return ['fas', 'exclamation-triangle'];
});

// Watch for case changes and reload
watch(() => props.caseId, () => {
  if (props.autoLoad && props.caseId) {
    fetchConfidence();
  }
});

onMounted(() => {
  if (props.autoLoad && props.caseId) {
    fetchConfidence();
  }
});
</script>

<style scoped lang="scss">
@use '../../style/color' as *;
@use 'sass:color';

.discretization-confidence {
  background: color.adjust($gray, $lightness: 5%);
  border-radius: 8px;
  padding: 1rem;
}

.confidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;

  h4 {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: $white;
  }

  .refresh-btn {
    padding: 0.3rem 0.6rem;
    background: color.adjust($gray, $lightness: 15%);
    border: 1px solid color.adjust($white, $alpha: -0.8);
    border-radius: 4px;
    color: $white;
    cursor: pointer;
    transition: all 0.2s;

    &:hover:not(:disabled) {
      background: color.adjust($gray, $lightness: 20%);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  color: color.adjust($white, $alpha: -0.4);
  font-size: 0.85rem;
}

.error-state {
  color: $sub_1;
}

.continuous-mode-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: color.adjust(#4CAF50, $alpha: -0.9);
  border-radius: 6px;
  color: #4CAF50;

  .continuous-message {
    .title {
      font-weight: 600;
      font-size: 0.9rem;
    }
    .description {
      font-size: 0.75rem;
      opacity: 0.8;
    }
  }
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid color.adjust($white, $alpha: -0.8);
  border-top-color: $main_1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.mode-info {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: color.adjust($gray, $lightness: 10%);
  border-radius: 4px;
  font-size: 0.8rem;
  text-align: center;

  .mode-label {
    color: $white;
    font-weight: 500;
  }

  .mode-name {
    color: color.adjust($white, $alpha: -0.4);
    margin-left: 0.5rem;
  }
}

.confidence-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background: color.adjust($gray, $lightness: 10%);
  border-radius: 6px;
  border-left: 3px solid color.adjust($white, $alpha: -0.7);

  &.excellent { border-left-color: #4CAF50; }
  &.good { border-left-color: #8BC34A; }
  &.moderate { border-left-color: #FFC107; }
  &.poor { border-left-color: $sub_1; }

  .card-icon {
    font-size: 1.2rem;
    color: color.adjust($white, $alpha: -0.4);
  }

  .card-content {
    flex: 1;
  }

  .card-label {
    font-size: 0.7rem;
    color: color.adjust($white, $alpha: -0.4);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .card-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: $white;
  }

  .card-detail {
    font-size: 0.7rem;
    color: color.adjust($white, $alpha: -0.5);
  }

  .card-min {
    font-size: 0.7rem;
    color: color.adjust($white, $alpha: -0.4);
    margin-top: 0.2rem;
  }

  &.order {
    border-left-color: $main_2;

    &.excellent { border-left-color: #4CAF50; }
    &.good { border-left-color: #8BC34A; }
    &.moderate { border-left-color: #FFC107; }
    &.poor { border-left-color: $sub_1; }
  }
}

.technical-details {
  margin: 0.5rem 0;
  padding: 0.5rem 0.75rem;
  background: color.adjust($gray, $lightness: 8%);
  border-radius: 4px;
  font-size: 0.75rem;

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.25rem 0;

    &:not(:last-child) {
      border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
    }
  }

  .detail-label {
    color: color.adjust($white, $alpha: -0.4);
  }

  .detail-value {
    font-family: 'Roboto Mono', monospace;
    color: $main_2;
    font-weight: 500;
  }
}

.interpretation {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  font-size: 0.8rem;

  &.excellent {
    background: color.adjust(#4CAF50, $alpha: -0.85);
    color: #4CAF50;
  }

  &.good {
    background: color.adjust(#8BC34A, $alpha: -0.85);
    color: #8BC34A;
  }

  &.moderate {
    background: color.adjust(#FFC107, $alpha: -0.85);
    color: #FFC107;
  }

  &.poor {
    background: color.adjust($sub_1, $alpha: -0.85);
    color: $sub_1;
  }
}
</style>
