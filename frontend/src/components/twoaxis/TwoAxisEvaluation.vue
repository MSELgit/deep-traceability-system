<template>
  <div class="twoaxis-eval-wrapper">
    <div class="view-header">
      <div class="axis-selectors">
        <label>
          X軸:
          <select v-model="selectedX">
            <option v-for="perf in performances" :key="perf.id" :value="perf.id">
              {{ perf.name }}
            </option>
            <option value="__height">標高</option>
            <option value="__energy">エネルギー</option>
          </select>
        </label>
        <label>
          Y軸:
          <select v-model="selectedY">
            <option v-for="perf in performances" :key="perf.id" :value="perf.id">
              {{ perf.name }}
            </option>
            <option value="__height">標高</option>
            <option value="__energy">エネルギー</option>
          </select>
        </label>
      </div>
      <button class="close-btn" @click="onRemove(viewId)" title="ビューを閉じる">×</button>
    </div>
    <div class="plot-area">
      <svg :width="svgWidth" :height="svgHeight">
        <!-- 十字クロス軸 -->
        <line :x1="margin" :y1="svgHeight/2" :x2="svgWidth - margin" :y2="svgHeight/2" stroke="#888" stroke-width="2" />
        <line :x1="svgWidth/2" :y1="margin" :x2="svgWidth/2" :y2="svgHeight - margin" stroke="#888" stroke-width="2" />
        <!-- 軸ラベル -->
        <text :x="svgWidth/2" :y="svgHeight - 8" text-anchor="middle" font-size="14" fill="#333">{{ getPerfName(selectedX) }}</text>
        <text :x="svgWidth/2 - 8" :y="24" text-anchor="end" font-size="14" fill="#333" :transform="`rotate(-90,${svgWidth/2 - 8},24)`">{{ getPerfName(selectedY) }}</text>
        <!-- 設計案プロット -->
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
    <!-- デバッグ: 各案のX/Y値表示 -->
    <div class="debug-values">
      <table>
        <thead>
          <tr>
            <th>設計案</th>
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

const svgWidth = ref(340);
const svgHeight = ref(320);
const margin = ref(38);


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
    console.error('エネルギー再計算に失敗:', error);
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
  if (id === "__height") return "標高";
  if (id === "__energy") return "エネルギー";
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
</script>

<style scoped>
.twoaxis-eval-wrapper {
  position: relative;
  width: 340px;
  min-width: 280px;
  max-width: 100%;
  margin: 0 8px 24px 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px 0 16px;
}
.axis-selectors {
  display: flex;
  gap: 18px;
}
.close-btn {
  background: #eee;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  font-size: 20px;
  color: #888;
  cursor: pointer;
  margin-left: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  transition: background 0.2s, color 0.2s;
}
.close-btn:hover {
  background: #f44336;
  color: #fff;
}
.plot-area {
  padding: 8px 8px 16px 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}
  .debug-values {
    margin: 8px 0 0 0;
    padding: 0 16px 12px 16px;
  }
  .debug-values table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    background: #f8f9fa;
    border-radius: 6px;
    overflow: hidden;
  }
  .debug-values th, .debug-values td {
    border: 1px solid #e0e0e0;
    padding: 4px 8px;
    text-align: left;
  }
  .debug-values th {
    background: #e3eafc;
    font-weight: 600;
    color: #3357FF;
  }
  .debug-values tr:nth-child(even) {
    background: #f4f8ff;
  }
</style>
