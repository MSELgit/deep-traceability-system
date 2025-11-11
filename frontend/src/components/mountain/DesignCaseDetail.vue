<template>
  <div class="design-case-detail">
    <div class="detail-header">
      <h2>{{ designCase.name }}の詳細</h2>
      <button class="close-btn" @click="$emit('close')">✕</button>
    </div>

    <div class="detail-content">
      <!-- 基本情報（常に表示） -->
      <section class="detail-section basic-info-section">
        <h3>基本情報</h3>
        
        <div class="section-content">
          <!-- 構造不一致警告 -->
          <div v-if="isStructureMismatch" class="structure-warning">
            <FontAwesomeIcon :icon="['fas', 'triangle-exclamation']" />
            <span>この設計案の性能ツリー構造は最新のものと異なります</span>
          </div>
          
          <div class="info-row">
            <span class="info-label">標高</span>
            <span class="info-value">{{ designCase.mountain_position ? designCase.mountain_position.H.toFixed(2) : '-' }}</span>
          </div>
          
          <div class="info-row">
            <span class="info-label">エネルギー</span>
            <span class="info-value">{{ energyData ? energyData.total_energy.toFixed(2) : '-' }}</span>
          </div> 

          <div class="info-row">
            <span class="info-label">色</span>
            <div class="color-display">
              <div 
                class="color-box" 
                :style="{ background: designCase.color }"
              ></div>
              <span class="color-text">{{ designCase.color }}</span>
            </div>
          </div>

          <div class="info-row">
            <span class="info-label">作成日時</span>
            <span class="info-value">{{ formatDateTime(designCase.created_at) }}</span>
          </div>

          <div class="info-row">
            <span class="info-label">更新日時</span>
            <span class="info-value">{{ formatDateTime(designCase.updated_at) }}</span>
          </div>

          <div v-if="designCase.description" class="info-row vertical">
            <span class="info-label">説明</span>
            <p class="description-text">{{ designCase.description }}</p>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- 性能値 -->
      <section class="detail-section">
        <h3 @click="toggleSection('performance')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.performance ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          性能値
        </h3>
        
        <div v-show="sectionStates.performance" class="section-content">
          <div class="performance-list">
          <div
            v-for="perf in performancesWithValues"
            :key="perf.id"
            class="performance-item"
          >
            <div class="perf-info">
              <span class="perf-name">{{ perf.name }}</span>
              <span class="perf-unit">{{ perf.unit || '' }}</span>
            </div>
            <div class="perf-value">{{ formatValue(designCase.performance_values[perf.id]) }}</div>
          </div>

            <div v-if="performancesWithValues.length === 0" class="empty-state">
              性能値がありません
            </div>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- 平均効用 -->
      <section class="detail-section">
        <h3 @click="toggleSection('utility')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.utility ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          効用レーダーチャート
        </h3>
        
        <div v-show="sectionStates.utility" class="section-content">
          <div v-if="!designCase.partial_heights || !designCase.performance_weights" class="empty-state">
          平均効用を計算するには、再計算ボタン（<FontAwesomeIcon :icon="['fas', 'rotate-right']" />）をクリックしてください
          </div>
          <div v-else class="radar-chart-container">
            <Radar :data="radarChartData" :options="radarChartOptions" />
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- 性能分析（残り標高＋エネルギー） -->
      <section v-if="remainingHeights.length > 0" class="detail-section">
        <h3 @click="toggleSection('remaining')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.remaining ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          性能分析
        </h3>
        
        <div v-show="sectionStates.remaining" class="section-content">
          <div class="remaining-heights-list">
          <div 
            v-for="item in remainingHeights" 
            :key="item.perfId"
            class="remaining-height-item"
            :class="{ expanded: expandedPerfId === item.perfId }"
          >
            <div 
              class="remaining-height-content"
              @click="togglePerfExpand(item.perfId)"
            >
              <div class="remaining-height-header">
                <div class="header-left">
                  <FontAwesomeIcon 
                    :icon="['fas', expandedPerfId === item.perfId ? 'chevron-down' : 'chevron-right']" 
                    class="expand-indicator"
                  />
                  <span class="remaining-height-name">{{ item.perfName }}</span>
                </div>
                <span class="performance-importance">重要度: {{ getPerformanceImportance(item.perfId).toFixed(1) }}</span>
              </div>
              <div class="remaining-height-values">
                <span class="remaining-value">残り: {{ item.remaining.toFixed(2) }}</span>
                <span class="detail-values">
                  (実際: {{ item.actual.toFixed(2) }} / 最大: {{ item.hMax.toFixed(2) }})
                </span>
                <span v-if="energyData" class="energy-value">
                  部分エネルギー: {{ (energyData.partial_energies[item.perfId] || 0).toFixed(3) }}
                </span>
              </div>
            </div>
            
            <!-- 展開部分：エネルギー詳細 -->
            <div v-if="expandedPerfId === item.perfId && energyData" class="energy-details">
              <!-- ネットワークビュー -->
              <div class="perf-network-view">
                <NetworkHighlightViewer 
                  v-if="designCase.network.nodes.length > 0"
                  :network="designCase.network"
                  :performances="performances"
                  :highlighted-perf-id="item.perfId"
                  :height="300"
                />
              </div>
              
              <h5>他性能との相性（Match値）</h5>
              <div class="match-details">
                <div 
                  v-for="(matchData, index) in getMatchDetailsForPerformance(item.perfId)"
                  :key="index"
                  class="match-item"
                >
                  <span class="match-perf-name">
                    {{ matchData.perfName }}
                    <span class="match-perf-importance">(重要度: {{ matchData.perfImportance.toFixed(1) }})</span>
                  </span>
                  <span class="match-value">Match: {{ matchData.match.toFixed(4) }}</span>
                  <span class="partial-partial-energy">エネルギー: {{ matchData.energy.toFixed(4) }}</span>
                </div>
                <div v-if="getMatchDetailsForPerformance(item.perfId).length === 0" class="no-matches">
                  他の性能との相性データがありません
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>
      </section>

      <div class="divider"></div>

      <!-- ネットワーク構造 -->
      <section class="detail-section">
        <h3 @click="toggleSection('network')" class="section-header">
          <FontAwesomeIcon :icon="['fas', sectionStates.network ? 'chevron-down' : 'chevron-right']" class="toggle-icon" />
          ネットワーク構造
        </h3>
        
        <div v-show="sectionStates.network" class="section-content">
          <div class="network-viewer-wrapper">

          <NetworkViewer 
            v-if="designCase.network.nodes.length > 0"
            :network="designCase.network"
            :performances="performances"
          />
            <div v-else class="empty-state">
              ネットワークが未定義です
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import type { DesignCase, Performance } from '../../types/project';
import NetworkViewer from '../network/NetworkViewer.vue';
import NetworkHighlightViewer from '../network/NetworkHighlightViewer.vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { calculationApi } from '../../utils/api';
import { useProjectStore } from '../../stores/projectStore';
import { Radar } from 'vue-chartjs';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js';

// Chart.jsのコンポーネントを登録
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

// 基準線を描画するカスタムプラグイン（n角形）
const referenceLinePlugin = {
  id: 'customLines',
  afterDatasetsDraw(chart: any, _args: any, options: any) {
    const { ctx, scales } = chart;
    const { r } = scales;
    
    if (!options.lines) return;
    
    const pointLabels = r._pointLabels || [];
    const numPoints = pointLabels.length;
    
    if (numPoints === 0) return;
    
    options.lines.forEach((line: any) => {
      const radius = r.getDistanceFromCenterForValue(line.value);
      const centerX = r.xCenter;
      const centerY = r.yCenter;
      
      ctx.save();
      ctx.strokeStyle = line.color;
      ctx.lineWidth = line.width;
      ctx.setLineDash([5, 5]); // 破線
      ctx.beginPath();
      
      // n角形を描画
      for (let i = 0; i < numPoints; i++) {
        const angle = r.getIndexAngle(i) - Math.PI / 2; // -90度回転（上から開始）
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.closePath();
      ctx.stroke();
      ctx.restore();
    });
  }
};

ChartJS.register(referenceLinePlugin);

const props = defineProps<{
  designCase: DesignCase;
  performances: Performance[];
  performanceHMax: { [key: string]: number };
}>();

const emit = defineEmits<{
  close: [];
  edit: [designCase: DesignCase];
  copy: [designCase: DesignCase];
  delete: [designCase: DesignCase];
}>();

const projectStore = useProjectStore();

// 構造不一致チェック
const isStructureMismatch = computed(() => {
  if (!props.designCase.performance_snapshot) return false;
  
  const currentPerformances = projectStore.currentProject?.performances || [];
  
  // スナップショットと現在の性能数が違えば不一致
  if (props.designCase.performance_snapshot.length !== currentPerformances.length) return true;
  
  // 各性能の詳細を比較
  const snapshotMap = new Map(props.designCase.performance_snapshot.map(p => [p.id, p]));
  
  for (const currentPerf of currentPerformances) {
    const snapshotPerf = snapshotMap.get(currentPerf.id);
    if (!snapshotPerf) return true;  // IDが見つからない
    
    // 主要な属性を比較
    if (snapshotPerf.name !== currentPerf.name ||
        snapshotPerf.parent_id !== currentPerf.parent_id ||
        snapshotPerf.level !== currentPerf.level ||
        snapshotPerf.unit !== currentPerf.unit) {
      return true;
    }
  }
  
  return false;
});

// エネルギーデータ
const energyData = ref<{
  total_energy: number;
  partial_energies: { [key: string]: number };
  match_matrix?: { [key: string]: number }; // "perfId1_perfId2": value の形式
} | null>(null);

// 展開された性能ID
const expandedPerfId = ref<string | null>(null);


// セクションの開閉状態（基本情報は常に開いているので除外）
const sectionStates = ref({
  performance: true,
  utility: true,
  remaining: true,
  network: true
});

// セクションの開閉切り替え
function toggleSection(section: keyof typeof sectionStates.value) {
  sectionStates.value[section] = !sectionStates.value[section];
}

// 値を持つ性能のみ（スナップショットから取得）
const performancesWithValues = computed(() => {
  // スナップショットがある場合はそれを使用、なければ現在の性能ツリーを使用（後方互換性）
  const performances = props.designCase.performance_snapshot || props.performances;
  
  // 末端性能のみ抽出して、値を持つものだけフィルタ
  return performances
    .filter(perf => perf.is_leaf)
    .filter(perf => props.designCase.performance_values[perf.id] !== undefined);
});

// レーダーチャートのデータ
const radarChartData = computed(() => {
  if (!props.designCase.partial_heights || !props.designCase.performance_weights) {
    return { labels: [], datasets: [] };
  }

  const labels = performancesWithValues.value.map(perf => perf.name);
  const data = performancesWithValues.value.map(perf => getAverageUtilityForPerf(perf.id));

  return {
    labels,
    datasets: [
      {
        label: '平均効用',
        data,
        backgroundColor: 'rgba(51, 87, 255, 0.2)',
        borderColor: 'rgba(51, 87, 255, 1)',
        borderWidth: 2,
        pointBackgroundColor: data.map((value) => 
          value < 0.5 ? 'rgba(255, 68, 68, 1)' : 'rgba(51, 87, 255, 1)'
        ),
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: data.map((value) => 
          value < 0.5 ? 'rgba(255, 68, 68, 1)' : 'rgba(51, 87, 255, 1)'
        ),
        pointRadius: 5
      }
    ]
  };
});

// レーダーチャートのオプション
const radarChartOptions = computed(() => {
  const data = performancesWithValues.value.map(perf => getAverageUtilityForPerf(perf.id));
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 1,
        ticks: {
          stepSize: 0.2,
          font: {
            size: 12
          }
        },
        pointLabels: {
          font: {
            size: 14,
            weight: 'bold' as const
          },
          color: (context: any) => {
            // 0.5未満の性能名を赤く表示
            const index = context.index;
            return data[index] < 0.5 ? 'rgba(255, 68, 68, 1)' : '#666';
          }
        }
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `${context.label}: ${context.parsed.r.toFixed(3)}`;
          }
        }
      },
      // 基準線を描画するカスタムプラグイン
      customLines: {
        lines: [
          { value: 0.5, color: 'rgba(255, 68, 68, 0.5)', width: 2 },  // 赤線（0.5）
          { value: 0.8, color: 'rgba(255, 193, 7, 0.5)', width: 2 }   // 黄線（0.8）
        ]
      }
    }
  };
});

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

function formatValue(value: number | string): string {
  if (value === undefined || value === null) return '-';
  if (typeof value === 'string') return value;
  return Number(value).toFixed(2);
}


// 平均効用を計算（部分標高 / 合計票数）
function getAverageUtilityForPerf(perfId: string): number {
  if (!props.designCase.partial_heights || !props.designCase.performance_weights) return 0;
  
  const partialHeight = props.designCase.partial_heights[perfId] || 0;
  const totalWeight = props.designCase.performance_weights[perfId] || 0;
  
  if (totalWeight === 0) return 0;
  return partialHeight / totalWeight;
}

// 性能ごとの残り標高を計算（最大値 - 実際の部分標高）
const remainingHeights = computed(() => {
  if (!props.designCase.partial_heights || !props.performanceHMax) return [];
  
  const results: Array<{ perfId: string; perfName: string; remaining: number; hMax: number; actual: number }> = [];
  
  performancesWithValues.value.forEach(perf => {
    const hMax = props.performanceHMax[perf.id] || 0;
    const actual = props.designCase.partial_heights![perf.id] || 0;
    const remaining = hMax - actual;
    
    results.push({
      perfId: perf.id,
      perfName: perf.name,
      remaining,
      hMax,
      actual
    });
  });
  
  // 残り標高が大きい順にソート
  return results.sort((a, b) => b.remaining - a.remaining);
});

// エネルギーデータを取得
async function fetchEnergyData() {
  if (!projectStore.currentProject || !props.designCase) return;
  
  try {
    const response = await calculationApi.calculateCaseEnergy(
      projectStore.currentProject.id,
      props.designCase.id
    );
    energyData.value = {
      total_energy: response.data.total_energy,
      partial_energies: response.data.partial_energies,
      match_matrix: response.data.match_matrix
    };
  } catch (error) {
    console.error('エネルギー計算エラー:', error);
  }
}

// 性能名を取得（スナップショットから優先的に取得）
function getPerformanceName(perfId: string | number): string {
  const perfIdStr = String(perfId);
  
  // まずスナップショットから探す
  if (props.designCase.performance_snapshot) {
    const snapPerf = props.designCase.performance_snapshot.find(p => p.id === perfIdStr);
    if (snapPerf) return snapPerf.name;
  }
  
  // スナップショットにない場合は現在の性能ツリーから（後方互換性）
  const perf = props.performances.find(p => p.id === perfIdStr);
  return perf ? perf.name : perfIdStr;
}

// 性能の重要度を取得
function getPerformanceImportance(perfId: string | number): number {
  const perfIdStr = String(perfId);
  // performance_weightsは性能ごとの合計票数
  if (props.designCase.performance_weights && props.designCase.performance_weights[perfIdStr] !== undefined) {
    return props.designCase.performance_weights[perfIdStr];
  }
  return 0.0; // デフォルト値
}

// 性能カードの展開/折りたたみ
function togglePerfExpand(perfId: string) {
  if (expandedPerfId.value === perfId) {
    expandedPerfId.value = null;
  } else {
    expandedPerfId.value = perfId;
  }
}

// 特定性能のMatch詳細を取得
function getMatchDetailsForPerformance(perfId: string): Array<{perfName: string, perfImportance: number, match: number, energy: number}> {
  if (!energyData.value?.match_matrix || !props.designCase.performance_values) {
    return [];
  }
  
  const matrix = energyData.value.match_matrix;
  const details: Array<{perfName: string, perfImportance: number, match: number, energy: number}> = [];
  
  // 他の性能とのMatch値を取得
  const perfIds = Object.keys(props.designCase.performance_values);
  
  // match_matrixからnode_idを取得するための変換が必要
  // バックエンドはnode_idで保存しているが、フロントエンドはperformance_idを使用
  // ここでは簡易的にperformance_idのペアを検索
  
  for (const otherPerfId of perfIds) {
    if (otherPerfId === perfId) continue; // 自分自身は除外
    
    // Match値を取得（キーは "perfId1_perfId2" の形式）
    let matchValue = 0;
    
    // 両方の順番を試す（対称行列なので）
    const key1 = `${perfId}_${otherPerfId}`;
    const key2 = `${otherPerfId}_${perfId}`;
    
    if (matrix[key1] !== undefined) {
      matchValue = matrix[key1];
    } else if (matrix[key2] !== undefined) {
      matchValue = matrix[key2];
    }
    
    // 重要度を取得
    const qi = getPerformanceImportance(perfId);
    const qj = getPerformanceImportance(otherPerfId);
    
    // r = √2(1-Match)
    const r = Math.sqrt(2 * (1 - matchValue));
    
    // 部分部分エネルギー = qi * qj / r / 2 （両方向で計算されるので半分）
    const partialEnergy = r > 0 ? (qi * qj) / r / 2 : 0;
    
    details.push({
      perfName: getPerformanceName(otherPerfId),
      perfImportance: qj,
      match: matchValue,
      energy: partialEnergy
    });
  }
  
  // エネルギーの大きい順にソート
  return details.sort((a, b) => b.energy - a.energy);
}


// 設計案が変更されたらエネルギーを再計算
watch(() => props.designCase.id, () => {
  fetchEnergyData();
});

// 初回ロード時にエネルギーを取得
onMounted(() => {
  fetchEnergyData();
});

</script>

<style scoped>
.design-case-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.detail-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 20px;
  color: #666;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

/* セクションヘッダー */
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
  margin: 0 0 16px 0 !important;
}

.section-header:hover {
  color: #667eea;
}

.toggle-icon {
  font-size: 12px;
  color: #999;
  transition: transform 0.2s;
}

.section-content {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.divider {
  height: 1px;
  background: #e0e0e0;
  margin: 24px 0;
}

/* 山の座標情報 */
.mountain-info {
  margin-bottom: 0;
}

.mountain-stats {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}

.stat-card {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  text-align: center;
}

.stat-card.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  grid-column: 1 / -1;
}

.stat-label {
  font-size: 12px;
  color: inherit;
  opacity: 0.8;
  margin-bottom: 8px;
}

.stat-card.primary .stat-label {
  color: white;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;

}

/* 基本情報 */
.basic-info-section h3 {
  margin-bottom: 16px !important;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row.highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  margin: -16px -16px 16px -16px;
  border-radius: 8px;
  border-bottom: none;
}

.info-row.highlight .info-label {
  color: white;
  opacity: 0.9;
}

.info-value-large {
  font-size: 28px;
  font-weight: 700;
  color: white;
}

.info-row.vertical {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  color: #999;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #333;
}

.description-text {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

/* 色表示 */
.color-display {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.color-box {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid #e0e0e0;
}

.color-text {
  font-size: 13px;
  font-family: monospace;
  color: #666;
}


/* 性能値 */
.performance-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.performance-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.perf-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.perf-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.perf-unit {
  font-size: 12px;
  color: #999;
}

.perf-value {
  font-size: 16px;
  font-weight: 600;
  color: #4CAF50;
}

/* 効用ベクトル */
.utility-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* レーダーチャート */
.radar-chart-container {
  width: 100%;
  height: 400px;
  margin: 20px auto;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 残り標高リスト */
.remaining-heights-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.remaining-height-item {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
  transition: all 0.3s ease;
  margin-bottom: 12px;
}

.remaining-height-item.expanded {
  background: #f0f4ff;
}

.remaining-height-content {
  padding: 12px;
  cursor: pointer;
  user-select: none;
}

.remaining-height-content:hover {
  background: rgba(102, 126, 234, 0.05);
}

.remaining-height-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-indicator {
  font-size: 12px;
  color: #667eea;
  transition: transform 0.3s ease;
}

.remaining-height-name {
  font-weight: 600;
  color: #333;
  font-size: 15px;
}

.performance-importance {
  color: #666;
  font-size: 12px;
}

.remaining-height-values {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
}

/* ホバー時の追加効果 */
.remaining-height-content:hover .expand-indicator {
  transform: scale(1.2);
  color: #5566dd;
}

.remaining-height-item:not(.expanded) .remaining-height-content:hover::after {
  opacity: 1;
}

.remaining-height-item {
  position: relative;
}

.remaining-value {
  color: #667eea;
  font-weight: 700;
  font-size: 14px;
}

.detail-values {
  color: #666;
  font-size: 14px;
}

.energy-value {
  color: #667eea;
  font-weight: 700;
  font-size: 14px;
  margin-left: auto;
}

.utility-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.utility-label {
  font-size: 13px;
  font-weight: 500;
  color: #555;
}

.utility-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.utility-bar {
  flex: 1;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.utility-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
  transition: width 0.3s ease;
}

.utility-value {
  font-size: 13px;
  font-weight: 600;
  color: #4CAF50;
  min-width: 40px;
  text-align: right;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 13px;
  color: #666;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

/* 空状態 */
.empty-state {
  padding: 80px 24px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

/* フッター */
.detail-footer {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.action-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.action-btn.edit {
  background: #2196F3;
  color: white;
}

.action-btn.edit:hover {
  background: #1976D2;
}

.action-btn.copy {
  background: #FF9800;
  color: white;
}

.action-btn.copy:hover {
  background: #F57C00;
}

.action-btn.delete {
  background: #f44336;
  color: white;
}

.action-btn.delete:hover {
  background: #d32f2f;
}

.network-viewer-wrapper {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.partial-energies-list h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.partial-energy-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

/* 構造不一致警告 */
.structure-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  margin: -4px -4px 16px -4px;
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  font-size: 14px;
}

.structure-warning svg {
  flex-shrink: 0;
  color: #f39c12;
}

/* エネルギー詳細展開部分 */
.energy-details {
  padding: 16px;
  background: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(102, 126, 234, 0.2);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.energy-details h5 {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 600;
  color: #555;
}

.match-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid #e0e0e0;
}

.match-perf-name {
  flex: 1;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.match-perf-importance {
  font-size: 11px;
  color: #666;
  font-weight: 400;
}

.match-value {
  color: #666;
  font-family: 'Courier New', monospace;
}

.partial-partial-energy {
  color: #ff6b6b;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.no-matches {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding: 16px;
  font-style: italic;
}

/* 性能ネットワークビュー */
.perf-network-view {
  margin-bottom: 20px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  overflow: hidden;
}
</style>