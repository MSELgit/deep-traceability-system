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
}

/**
 * ニーズ作成用
 */
export interface NeedCreate {
  name: string;
  description?: string;
  category?: string;
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
}

/**
 * ネットワーク構造
 */
export interface NetworkStructure {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

/**
 * ネットワークノード
 */
export interface NetworkNode {
  id: string;
  layer: 1 | 2 | 3 | 4; // 性能/特性/変数/モノ・環境
  type: 'performance' | 'property' | 'variable' | 'object' | 'environment';
  label: string;
  x: number; // キャンバス上の座標
  y: number;
  performance_id?: string; // layer=1の場合のみ
  x3d?: number;
  y3d?: number;
}

/**
 * ネットワークエッジ
 */
export interface NetworkEdge {
  id: string;
  source_id: string;
  target_id: string;
  type: 'type1' | 'type2' | 'type3' | 'type4';
  weight?: 3 | 1 | 0.33 | 0 | -0.33 | -1 | -3; // 因果関係の重み
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
