<template>
  <div class="twoaxis-eval-wrapper">
    <div class="view-header">
      <div class="axis-selectors">
        <label>
          X-axis:
          <select v-model="selectedX">
            <option v-for="perf in performances" :key="perf.id" :value="perf.id">
              {{ perf.name }}
            </option>
            <option value="__height">Height</option>
            <option value="__energy">Energy</option>
          </select>
        </label>
        <label>
          Y-axis:
          <select v-model="selectedY">
            <option v-for="perf in performances" :key="perf.id" :value="perf.id">
              {{ perf.name }}
            </option>
            <option value="__height">Height</option>
            <option value="__energy">Energy</option>
          </select>
        </label>
      </div>
      <div class="header-actions">
        <button class="camera-btn" @click="downloadPlotImage" title="Download 2-Axis Plot">
          <FontAwesomeIcon :icon="['fas', 'camera']" />
        </button>
        <button class="close-btn" @click="onRemove(viewId)" title="Close View">×</button>
      </div>
    </div>
    <div class="plot-area">
      <svg ref="plotSvg" :width="svgWidth" :height="svgHeight" :viewBox="`0 0 ${svgWidth} ${svgHeight}`">
        <!-- Axis lines -->
        <line :x1="margin" :y1="svgHeight/2" :x2="svgWidth - margin" :y2="svgHeight/2" stroke="#888" stroke-width="2" />
        <line :x1="svgWidth/2" :y1="margin" :x2="svgWidth/2" :y2="svgHeight - margin" stroke="#888" stroke-width="2" />
        <!-- Axis labels -->
        <text :x="svgWidth-48" :y="svgHeight/2 + 25" text-anchor="middle" font-size="14" fill="#333">{{ getPerfName(selectedX) }}</text>
        <text :x="svgWidth/2 - 8" :y="24" text-anchor="end" font-size="14" fill="#333" :transform="`rotate(-90,${svgWidth/2 - 8},24)`">{{ getPerfName(selectedY) }}</text>
        <!-- Design case plots -->
        <g v-for="dc in designCases" :key="dc.id">
          <circle
            :cx="scaleX(getValue(dc, selectedX))"
            :cy="scaleY(getValue(dc, selectedY))"
            r="8"
            :fill="dc.color || '#3357FF'"
            stroke="#333"
            stroke-width="2"
          />
          <title>{{ dc.name }}\nX: {{ getValue(dc, selectedX) }}\nY: {{ getValue(dc, selectedY) }}</title>
          <text
            :x="labelX(getValue(dc, selectedX))"
            :y="labelY(getValue(dc, selectedY))"
            :text-anchor="labelAnchor(getValue(dc, selectedX))"
            font-size="13"
            fill="#333"
          >{{ dc.name }}</text>
        </g>
      </svg>
    </div>
    <!-- Debug: X/Y values for each design case -->
    <div class="debug-values">
      <table>
        <thead>
          <tr>
            <th>Design Case</th>
            <th>{{ getPerfName(selectedX) }} (X)</th>
            <th>{{ getPerfName(selectedY) }} (Y)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dc in designCases" :key="dc.id">
            <td>{{ dc.name }}</td>
            <td>
              <template v-if="typeof getValue(dc, selectedX) === 'number'">
                {{ (getValue(dc, selectedX) as number).toFixed(3) }}
              </template>
              <template v-else>
                {{ getValue(dc, selectedX) }}
              </template>
            </td>
            <td>
              <template v-if="typeof getValue(dc, selectedY) === 'number'">
                {{ (getValue(dc, selectedY) as number).toFixed(3) }}
              </template>
              <template v-else>
                {{ getValue(dc, selectedY) }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import type { DesignCase, Performance } from '../../types/project';
import { calculationApi } from '../../utils/api';
import { useRoute } from 'vue-router';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

const props = defineProps<{
  viewId: number|string;
  designCases: DesignCase[];
  performances: Performance[];
  initialX?: string;
  initialY?: string;
  onRemove: (id: number|string) => void;
}>();

const emit = defineEmits<{
  'axis-change': [viewId: string, axis: 'x' | 'y', value: string];
}>();

const route = useRoute();

const svgWidth = ref(300);
const svgHeight = ref(280);
const margin = ref(38);
const plotSvg = ref<SVGSVGElement>();


const selectedX = ref(props.initialX || props.performances[0]?.id || '');
const selectedY = ref(props.initialY || props.performances[1]?.id || props.performances[0]?.id || '');

// エネルギーが全部0かチェック
const allEnergyZero = computed(() => {
  if (!props.designCases || props.designCases.length === 0) return false;
  return props.designCases.every(dc => !dc.energy || dc.energy.total_energy === 0);
});

// エネルギーを再計算する関数
async function recalculateEnergy() {
  const projectId = route.params.id as string;
  if (!projectId) return;
  
  try {
    const energyResults = await calculationApi.calculateEnergy(projectId);
    // 親コンポーネントのdesignCasesを更新するため、計算結果を反映
    for (const energy of energyResults.data) {
      const dc = props.designCases.find(d => d.id === energy.case_id);
      if (dc) {
        dc.energy = {
          total_energy: energy.total_energy,
          partial_energies: energy.partial_energies
        };
      }
    }
  } catch (error) {
    console.error('Failed to recalculate energy:', error);
  }
}

// エネルギー軸が選択されているかチェック
const isEnergyAxisSelected = computed(() => {
  return selectedX.value === "__energy" || selectedY.value === "__energy";
});

// designCasesを監視して、エネルギー軸が選択されていてエネルギーが全部0なら再計算
watch([() => props.designCases, selectedX, selectedY], async ([newDesignCases]) => {
  if (newDesignCases && newDesignCases.length > 0 && isEnergyAxisSelected.value && allEnergyZero.value) {
    await recalculateEnergy();
  }
}, { immediate: true });

watch(() => props.performances, (newVal) => {
  if (newVal.length > 0) {
    if (!selectedX.value) selectedX.value = newVal[0].id;
    if (!selectedY.value) selectedY.value = newVal[1]?.id || newVal[0].id;
  }
});

// 軸選択が変更されたときにemit
watch(selectedX, (newVal) => {
  emit('axis-change', String(props.viewId), 'x', newVal);
});

watch(selectedY, (newVal) => {
  emit('axis-change', String(props.viewId), 'y', newVal);
});

function getPerfName(id: string) {
  if (id === "__height") return "Height";
  if (id === "__energy") return "Energy";
  return props.performances.find(p => p.id === id)?.name || '';
}
function getValue(dc: DesignCase, perfId: string): number | string {
  if (perfId === "__height") {
    return dc.mountain_position?.H ?? 0;
  }
  if (perfId === "__energy") {
    if (dc.energy && typeof dc.energy.total_energy === 'number') {
      return dc.energy.total_energy;
    }
    return 0;
  }
  const val = dc.performance_values[perfId];
  if (typeof val === 'number') return val;
  if (typeof val === 'string') {
    // 離散値の場合は数値変換できれば数値、できなければ文字列
    const num = parseFloat(val);
    return isNaN(num) ? val : num;
  }
  return 0;
}

function getScaleInfo(axis: 'x' | 'y') {
  const key = axis === 'x' ? selectedX.value : selectedY.value;
  const vals = props.designCases.map(dc => getValue(dc, key));
  // 離散値（文字列）が混じる場合はユニーク値ごとに均等配置
  const isDiscrete = vals.some(v => typeof v === 'string');
  if (isDiscrete) {
    const unique = Array.from(new Set(vals.map(v => String(v))));
    return { isDiscrete: true, unique };
  } else {
    const numVals = vals.map(v => typeof v === 'number' ? v : parseFloat(String(v)) || 0);
    const min = Math.min(...numVals);
    const max = Math.max(...numVals);
    return { isDiscrete: false, min, max };
  }
}

function scaleX(val: number | string) {
  const info = getScaleInfo('x');
  if (info.isDiscrete && info.unique && info.unique.length > 0) {
    const idx = info.unique.indexOf(String(val));
    const n = info.unique.length;
    if (n <= 1 || idx < 0) return svgWidth.value / 2;
    return margin.value + (idx / (n - 1)) * (svgWidth.value - margin.value * 2);
  } else if (typeof info.min === 'number' && typeof info.max === 'number') {
    const min = info.min;
    const max = info.max;
    if (max === min) return svgWidth.value / 2;
    return margin.value + ((Number(val) - min) / (max - min)) * (svgWidth.value - margin.value * 2);
  } else {
    return svgWidth.value / 2;
  }
}
function scaleY(val: number | string) {
  const info = getScaleInfo('y');
  if (info.isDiscrete && info.unique && info.unique.length > 0) {
    const idx = info.unique.indexOf(String(val));
    const n = info.unique.length;
    if (n <= 1 || idx < 0) return svgHeight.value / 2;
    return svgHeight.value - margin.value - (idx / (n - 1)) * (svgHeight.value - margin.value * 2);
  } else if (typeof info.min === 'number' && typeof info.max === 'number') {
    const min = info.min;
    const max = info.max;
    if (max === min) return svgHeight.value / 2;
    return svgHeight.value - margin.value - ((Number(val) - min) / (max - min)) * (svgHeight.value - margin.value * 2);
  } else {
    return svgHeight.value / 2;
  }
}

// ノードラベルの位置・アンカーを自動調整
function labelX(val: number | string) {
  const x = scaleX(val);
  if (x > svgWidth.value - margin.value - 40) return x - 14;
  if (x < margin.value + 40) return x + 14;
  return x + 14;
}
function labelY(val: number | string) {
  return scaleY(val) + 4;
}
function labelAnchor(val: number | string) {
  const x = scaleX(val);
  if (x > svgWidth.value - margin.value - 40) return 'end';
  if (x < margin.value + 40) return 'start';
  return 'start';
}

// Download 2-axis plot as image
function downloadPlotImage() {
  if (!plotSvg.value) {
    console.error('SVG not available');
    return;
  }

  try {
    // Clone SVG to avoid modifying the original
    const svgClone = plotSvg.value.cloneNode(true) as SVGSVGElement;
    
    // Set viewBox and dimensions for proper scaling
    svgClone.setAttribute('viewBox', `0 0 ${svgWidth.value} ${svgHeight.value}`);
    svgClone.setAttribute('width', String(svgWidth.value));
    svgClone.setAttribute('height', String(svgHeight.value));
    
    // Convert SVG to data URL
    const svgData = new XMLSerializer().serializeToString(svgClone);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    
    // Create Image object and load SVG
    const img = new Image();
    img.onload = () => {
      // Create canvas
      const canvas = document.createElement('canvas');
      canvas.width = svgWidth.value;
      canvas.height = svgHeight.value;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      // Fill background
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw SVG
      ctx.drawImage(img, 0, 0);
      
      // Download
      const link = document.createElement('a');
      const xAxisName = getPerfName(selectedX.value);
      const yAxisName = getPerfName(selectedY.value);
      link.download = `2axis-plot-${xAxisName}-${yAxisName}-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      
      // Cleanup
      URL.revokeObjectURL(svgUrl);
    };
    
    img.onerror = () => {
      console.error('Failed to convert SVG');
      alert('Failed to download plot');
      URL.revokeObjectURL(svgUrl);
    };
    
    img.src = svgUrl;
  } catch (error) {
    console.error('Failed to generate plot image:', error);
    alert('Failed to download plot');
  }
}
</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

.twoaxis-eval-wrapper {
  position: relative;
  width: 100%;
  min-width: 0;
  max-width: none;
  margin: 0 0 clamp(1.5rem, 2vh, 2rem) 0;
  display: flex;
  flex-direction: column;
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.8vw;
  box-shadow: 0 0.3vh 0.8vh color.adjust($black, $alpha: -0.5);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: clamp(0.6rem, 1.2vh, 1rem) clamp(1rem, 2vw, 1.25rem) 0 clamp(1rem, 2vw, 1.25rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
}

.axis-selectors {
  display: flex;
  gap: clamp(1rem, 2vw, 1.5rem);
  flex-wrap: wrap;
}

.axis-selectors label {
  display: flex;
  align-items: center;
  gap: clamp(0.4rem, 0.8vw, 0.6rem);
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 500;
  color: $white;
}

.axis-selectors select {
  padding: clamp(0.3rem, 0.6vh, 0.5rem) clamp(0.5rem, 1vw, 0.75rem);
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  color: $white;
  font-size: clamp(0.75rem, 0.95vw, 0.85rem);
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: color.adjust($gray, $lightness: 20%);
    border-color: color.adjust($main_1, $alpha: -0.5);
  }

  &:focus {
    outline: none;
    background: color.adjust($gray, $lightness: 20%);
    border-color: $main_1;
    box-shadow: 0 0 0 0.15vw color.adjust($main_1, $alpha: -0.7);
  }

  option {
    background: color.adjust($gray, $lightness: 15%);
    color: $white;
  }
}

.header-actions {
  display: flex;
  gap: clamp(0.5rem, 1vw, 0.75rem);
  align-items: center;
}

.camera-btn {
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.4vw;
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.6rem, 1vw, 0.8rem);
  cursor: pointer;
  font-size: clamp(0.85rem, 1.1vw, 0.95rem);
  color: $white;
  transition: all 0.3s ease;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.8);

  &:hover {
    background: linear-gradient(135deg, $main_1 0%, $main_2 100%);
    border-color: color.adjust($main_1, $alpha: -0.3);
    transform: translateY(-0.05vh);
    box-shadow: 0 0.3vh 0.8vh color.adjust($main_1, $alpha: -0.5);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 0.2vh 0.5vh color.adjust($main_1, $alpha: -0.6);
  }
}

.close-btn {
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 50%;
  width: clamp(2rem, 3vw, 2.5rem);
  height: clamp(2rem, 3vw, 2.5rem);
  font-size: clamp(1.2rem, 1.6vw, 1.4rem);
  color: color.adjust($white, $alpha: -0.3);
  cursor: pointer;
  margin-left: clamp(0.75rem, 1.5vw, 1rem);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.8);
  transition: all 0.3s ease;

  &:hover {
    background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
    border-color: #d32f2f;
    color: $white;
    transform: scale(1.05);
    box-shadow: 0 0.3vh 0.8vh rgba(211, 47, 47, 0.4);
  }

  &:active {
    transform: scale(0.98);
  }
}

.plot-area {
  padding: clamp(0.5rem, 1vh, 0.75rem);
  display: flex;
  justify-content: center;
  align-items: center;
  background: white;
  margin: clamp(0.5rem, 1vh, 0.75rem);
  border-radius: 0.6vw;
  box-shadow: inset 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.9);

  svg {
    max-width: 100%;
    height: auto;
  }
}

.debug-values {
  margin: clamp(0.5rem, 1vh, 0.75rem) 0 0 0;
  padding: 0 clamp(1rem, 2vw, 1.25rem) clamp(0.75rem, 1.5vh, 1rem) clamp(1rem, 2vw, 1.25rem);
}

.debug-values table {
  width: 100%;
  border-collapse: collapse;
  font-size: clamp(0.75rem, 0.9vw, 0.8rem);
  background: color.adjust($gray, $lightness: 15%);
  border-radius: 0.6vw;
  overflow: hidden;
  box-shadow: inset 0 0.1vh 0.3vh color.adjust($black, $alpha: -0.9);
}

.debug-values th, 
.debug-values td {
  border: 1px solid color.adjust($white, $alpha: -0.95);
  padding: clamp(0.3rem, 0.6vh, 0.5rem) clamp(0.5rem, 1vw, 0.75rem);
  text-align: left;
}

.debug-values th {
  background: linear-gradient(135deg, $main_1 0%, color.adjust($main_1, $lightness: 10%) 100%);
  font-weight: 600;
  color: $white;
  font-size: clamp(0.7rem, 0.85vw, 0.75rem);
}

.debug-values td {
  color: $white;
}

.debug-values tr:nth-child(even) td {
  background: color.adjust($gray, $lightness: 10%);
}

.debug-values tr:hover td {
  background: color.adjust($main_1, $alpha: -0.8, $lightness: 25%);
}
</style>
