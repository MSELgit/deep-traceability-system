// frontend/src/types/project.ts

/**
 * プロジェクト全体のデータ構造
 */
export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  
  stakeholders: Stakeholder[];
  needs: Need[];
  performances: Performance[];
  design_cases: DesignCase[];
  
  // マトリクス関係
  stakeholder_need_relations: StakeholderNeedRelation[];
  need_performance_relations: NeedPerformanceRelation[];
  
  // 2軸プロット設定
  two_axis_plots: TwoAxisPlot[];
}

/**
 * プロジェクト作成用
 */
export interface ProjectCreate {
  name: string;
  description?: string;
}

/**
 * ステークホルダー（関係者）
 */
export interface Stakeholder {
  id: string;
  name: string;
  category?: string;
  votes: number; // デフォルト100
  description?: string;
}

/**
 * ステークホルダー作成用
 */
export interface StakeholderCreate {
  name: string;
  category?: string;
  votes?: number;
  description?: string;
}

/**
 * ニーズ（要求）
 */
export interface Need {
  id: string;
  name: string;
  description?: string;
  category?: string;
  priority?: number; // 優先度（0~1、デフォルト1.0）
}

/**
 * ニーズ作成用
 */
export interface NeedCreate {
  name: string;
  description?: string;
  category?: string;
  priority?: number;
}

/**
 * ステークホルダーとニーズの関係
 */
export interface StakeholderNeedRelation {
  stakeholder_id: string;
  need_id: string;
  relationship_weight: number; // 1.0=○, 0.5=△
}

/**
 * 性能
 */
export interface Performance {
  id: string;
  name: string;
  parent_id?: string; // 階層構造の親
  level: number; // 階層の深さ（0が最上位）
  is_leaf: boolean; // 末端（評価対象）かどうか
  unit?: string; // 単位（km/h, kg, etc.）
  description?: string;
  utility_function?: UtilityFunction;
  children?: Performance[] // 階層化のための子性能配列
}

/**
 * 性能作成用
 */
export interface PerformanceCreate {
  name: string;
  parent_id?: string;
  level: number;
  is_leaf?: boolean;
  unit?: string;
  description?: string;
}

/**
 * ニーズと性能の関係
 */
export interface NeedPerformanceRelation {
  need_id: string;
  performance_id: string;
  direction: 'up' | 'down'; // ↑（高い方が良い） or ↓（低い方が良い）
  utility_function_json?: string; // 効用関数データ（JSON文字列）
}

/**
 * 効用関数
 */
export interface UtilityFunction {
  type: 'continuous' | 'discrete';
  points?: UtilityPoint[]; // グラフの制御点（continuous用）
  discreteRows?: DiscreteRow[]; // 離散値の選択肢（discrete用）
  axisMin?: number;
  axisMax?: number;
}

/**
 * 効用関数の制御点
 */
export interface UtilityPoint {
  x: number; // 性能値
  y: number; // 効用値（0~1）
}

/**
 * 離散値の行
 */
export interface DiscreteRow {
  label: string; // 選択肢のラベル（例: "低", "中", "高"）
  value: number; // 効用値（0~1）
}

/**
 * 設計案
 */
export interface DesignCase {
  id: string;
  name: string;
  description?: string;
  color: string;  // ★ 追加
  created_at: string;
  updated_at: string;
  performance_values: { [performanceId: string]: number | string }; // 離散値の場合は文字列
  network: NetworkStructure;
  performance_snapshot: Performance[];  // 作成時の性能ツリー
  mountain_position?: MountainPosition;
  utility_vector?: { [performanceId: string]: number };
  partial_heights?: { [performanceId: string]: number };  // 性能ごとの部分標高
  performance_weights?: { [performanceId: string]: number };  // 性能ごとの合計票数
  energy?: {
    total_energy: number;
    partial_energies: { [performanceId: string]: number };
  }; // エネルギー計算結果
  // Phase 4: 新規フィールド
  weight_mode?: WeightMode;  // エッジ重みモード
  kernel_type?: 'classic_wl' | 'weighted_wl';  // WLカーネルタイプ
  structural_analysis?: Record<string, unknown>;  // 構造的トレードオフ分析結果
  paper_metrics?: Record<string, unknown>;  // 論文準拠指標
  scc_analysis?: Record<string, unknown>;  // SCC分解結果
}

/**
 * 設計案作成用
 */
export interface DesignCaseCreate {
  name: string;
  description?: string;
  color?: string;
  performance_values: { [performanceId: string]: number | string }; // 離散値の場合は文字列
  network: NetworkStructure;
  performance_snapshot: Performance[];  // 作成時のみ必須
  weight_mode?: WeightMode;  // エッジ重みモード
}

/**
 * 設計案更新用
 */
export interface DesignCaseUpdate {
  name: string;
  description?: string;
  color?: string;
  performance_values: { [performanceId: string]: number | string };
  network: NetworkStructure;
  weight_mode?: WeightMode;  // エッジ重みモード
  // performance_snapshotは含めない（更新時は変更しない）
}

/**
 * 山の座標情報
 */
export interface MountainPosition {
  x: number;
  y: number;
  z: number;
  H: number; // 標高
  total_energy?: number; // エネルギー（プロットサイズ用）
}

/**
 * ネットワーク構造
 */
export interface NetworkStructure {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  weight_mode?: WeightMode;  // エッジ重みモード
}

/**
 * エッジ重みモード
 */
export type WeightMode = 'discrete_3' | 'discrete_5' | 'discrete_7' | 'continuous';

/**
 * 重みモードごとの選択肢
 */
export const WEIGHT_MODE_OPTIONS: Record<WeightMode, { values: number[]; labels: string[] }> = {
  discrete_3: {
    values: [1, 0, -1],
    labels: ['+1 (Positive)', '0 (No effect)', '-1 (Negative)']
  },
  discrete_5: {
    values: [3, 1, 0, -1, -3],
    labels: ['+3 (Strong positive)', '+1 (Positive)', '0 (No effect)', '-1 (Negative)', '-3 (Strong negative)']
  },
  discrete_7: {
    values: [5, 3, 1, 0, -1, -3, -5],
    labels: ['+5 (Strong positive)', '+3', '+1', '0 (No effect)', '-1', '-3', '-5 (Strong negative)']
  },
  continuous: {
    values: [],  // 連続値モードでは選択肢なし
    labels: []
  }
};

/**
 * 旧7段階モード→新形式へのマイグレーションマップ
 * 旧: {-3, -1, -1/3, 0, 1/3, 1, 3}
 * 新: {-5, -3, -1, 0, 1, 3, 5}
 */
export const LEGACY_7_LEVEL_MIGRATION: Record<number, number> = {
  [-3]: -5,
  [-1]: -3,
  [-1/3]: -1,
  [0]: 0,
  [1/3]: 1,
  [1]: 3,
  [3]: 5
};

/**
 * 旧7段階モードの重みかどうかを判定
 */
export function isLegacy7LevelWeight(weight: number): boolean {
  const legacyValues = [-3, -1, -1/3, 0, 1/3, 1, 3];
  return legacyValues.some(v => Math.abs(weight - v) < 1e-6);
}

/**
 * 旧7段階モードの重みを新形式にマイグレーション
 */
export function migrateLegacy7LevelWeight(weight: number): number {
  for (const [oldVal, newVal] of Object.entries(LEGACY_7_LEVEL_MIGRATION)) {
    if (Math.abs(weight - parseFloat(oldVal)) < 1e-6) {
      return newVal;
    }
  }
  return weight;
}

/**
 * ネットワークエッジのマイグレーションが必要かどうかを判定
 * -1/3 または 1/3 が含まれていれば旧形式
 */
export function needsEdgeMigration(edges: NetworkEdge[]): boolean {
  return edges.some(edge => {
    if (edge.weight === undefined || edge.weight === null) return false;
    return Math.abs(edge.weight - 1/3) < 1e-6 || Math.abs(edge.weight - (-1/3)) < 1e-6;
  });
}

/**
 * ネットワークエッジを新形式にマイグレーション
 */
export function migrateNetworkEdges(edges: NetworkEdge[], hasWeightMode: boolean): NetworkEdge[] {
  if (hasWeightMode) {
    // weight_modeが設定されている場合はマイグレーション不要
    return edges;
  }

  return edges.map(edge => {
    if (edge.weight === undefined || edge.weight === null) {
      return edge;
    }

    // 旧7段階モードの重みかチェック
    if (isLegacy7LevelWeight(edge.weight)) {
      return {
        ...edge,
        weight: migrateLegacy7LevelWeight(edge.weight)
      };
    }

    return edge;
  });
}

/**
 * ネットワークノード
 */
export interface NetworkNode {
  id: string;
  layer: 1 | 2 | 3 | 4; // 性能/属性/変数/モノ・環境
  type: 'performance' | 'attribute' | 'property' | 'variable' | 'object' | 'environment';  // 'property' is deprecated, use 'attribute'
  label: string;
  x: number; // キャンバス上の座標
  y: number;
  performance_id?: string; // layer=1の場合のみ
  x3d?: number;
  y3d?: number;
}

/**
 * 'property' → 'attribute' マイグレーション用ヘルパー
 */
export function migrateNodeType(type: NetworkNode['type']): NetworkNode['type'] {
  return type === 'property' ? 'attribute' : type;
}

/**
 * ネットワークエッジ
 */
export interface NetworkEdge {
  id: string;
  source_id: string;
  target_id: string;
  type: 'type1' | 'type2' | 'type3' | 'type4';
  weight?: number; // 因果関係の重み（離散: ±3, ±1, ±1/3, 0 / 連続: -1~+1）
}

/**
 * 2軸プロット設定
 */
export interface TwoAxisPlot {
  id: string;
  x_axis: string; // performance_id or "__height" or "__energy"
  y_axis: string; // performance_id or "__height" or "__energy"
}

/**
 * HHI計算結果
 */
export interface HHIResult {
  performance_id: string;
  hhi: number;
  p_squared: number;
  weight: number;
  children_count: number;
}

/**
 * 票数計算の中間データ
 */
export interface VoteDistribution {
  need_id: string;
  effective_votes: number; // 有効投票数
  up_votes: number;
  down_votes: number;
}
