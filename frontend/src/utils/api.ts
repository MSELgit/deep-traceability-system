// frontend/src/utils/api.ts

import axios, { AxiosInstance, AxiosError } from 'axios';
import { API_BASE_URL } from '../config/environment';
import type {
  Project, ProjectCreate,
  Stakeholder, StakeholderCreate,
  Need, NeedCreate,
  Performance, PerformanceCreate,
  DesignCase, DesignCaseCreate,
  StakeholderNeedRelation,
  NeedPerformanceRelation,
  HHIResult,
  MountainPosition,
  NetworkNode,
  NetworkEdge
} from '../types/project';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// エラーハンドリング
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      console.error('API Error:', {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
        config: {
          method: error.config?.method,
          url: error.config?.url,
          data: error.config?.data ? JSON.parse(error.config.data) : null
        }
      });
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ========== プロジェクト ==========

// ========== ステークホルダー ==========

export const stakeholderApi = {
  list: (projectId: string) => apiClient.get<Stakeholder[]>(`/projects/${projectId}/stakeholders`),
  create: (projectId: string, data: StakeholderCreate) =>
    apiClient.post<Stakeholder>(`/projects/${projectId}/stakeholders`, data),
  update: (projectId: string, id: string, data: StakeholderCreate) =>
    apiClient.put<Stakeholder>(`/projects/${projectId}/stakeholders/${id}`, data),
  delete: (projectId: string, id: string) =>
    apiClient.delete(`/projects/${projectId}/stakeholders/${id}`),
};

// ========== ニーズ ==========

export const needApi = {
  list: (projectId: string) => apiClient.get<Need[]>(`/projects/${projectId}/needs`),
  create: (projectId: string, data: NeedCreate) =>
    apiClient.post<Need>(`/projects/${projectId}/needs`, data),
  update: (projectId: string, id: string, data: NeedCreate) =>
    apiClient.put<Need>(`/projects/${projectId}/needs/${id}`, data),
  delete: (projectId: string, id: string) =>
    apiClient.delete(`/projects/${projectId}/needs/${id}`),
};

// ========== ステークホルダー-ニーズ関係 ==========

export const stakeholderNeedRelationApi = {
  list: (projectId: string) =>
    apiClient.get<StakeholderNeedRelation[]>(`/projects/${projectId}/stakeholder-need-relations`),
  create: (projectId: string, data: StakeholderNeedRelation) =>
    apiClient.post(`/projects/${projectId}/stakeholder-need-relations`, data),
  update: (projectId: string, stakeholderId: string, needId: string, data: { relationship_weight: number }) =>
    apiClient.put(`/projects/${projectId}/stakeholder-need-relations/${stakeholderId}/${needId}`, data),
  delete: (projectId: string, stakeholderId: string, needId: string) =>
    apiClient.delete(`/projects/${projectId}/stakeholder-need-relations/${stakeholderId}/${needId}`),
};

// ========== 性能 ==========

export const performanceApi = {
  list: (projectId: string) => apiClient.get<Performance[]>(`/projects/${projectId}/performances`),
  create: (projectId: string, data: PerformanceCreate) =>
    apiClient.post<Performance>(`/projects/${projectId}/performances`, data),
  update: (projectId: string, id: string, data: PerformanceCreate) =>
    apiClient.put<Performance>(`/projects/${projectId}/performances/${id}`, data),
  delete: (projectId: string, id: string) =>
    apiClient.delete(`/projects/${projectId}/performances/${id}`),
};

// ========== ニーズ-性能関係 ==========

export const needPerformanceRelationApi = {
  list: (projectId: string) =>
    apiClient.get<NeedPerformanceRelation[]>(`/projects/${projectId}/need-performance-relations`),
  create: (projectId: string, data: NeedPerformanceRelation) =>
    apiClient.post(`/projects/${projectId}/need-performance-relations`, data),
  update: (projectId: string, needId: string, performanceId: string, data: NeedPerformanceRelation) =>
    apiClient.put(`/projects/${projectId}/need-performance-relations/${needId}/${performanceId}`, data),
  delete: (projectId: string, needId: string, performanceId: string) =>
    apiClient.delete(`/projects/${projectId}/need-performance-relations/${needId}/${performanceId}`),
};

// ========== 効用関数 ==========

export const utilityFunctionApi = {
  save: (projectId: string, needId: string, performanceId: string, data: any) =>
    apiClient.put(`/projects/${projectId}/utility-functions/${needId}/${performanceId}`, data),
  get: (projectId: string, needId: string, performanceId: string) =>
    apiClient.get<any>(`/projects/${projectId}/utility-functions/${needId}/${performanceId}`),
  list: (projectId: string) =>
    apiClient.get<any[]>(`/projects/${projectId}/utility-functions`),
};

// ========== 設計案 ==========

export const designCaseApi = {
  list: (projectId: string) => 
    apiClient.get<DesignCase[]>(`/projects/${projectId}/design-cases`),
    
  get: (projectId: string, caseId: string) =>
    apiClient.get<DesignCase>(`/projects/${projectId}/design-cases/${caseId}`),
    
  create: (projectId: string, data: DesignCaseCreate) =>
    apiClient.post<DesignCase>(`/projects/${projectId}/design-cases`, data),
    
  update: (projectId: string, caseId: string, data: DesignCaseCreate) =>
    apiClient.put<DesignCase>(`/projects/${projectId}/design-cases/${caseId}`, data),
    
  delete: (projectId: string, caseId: string) =>
    apiClient.delete(`/projects/${projectId}/design-cases/${caseId}`),
    
  copy: (projectId: string, caseId: string) =>
    apiClient.post<DesignCase>(`/projects/${projectId}/design-cases/${caseId}/copy`),
    
  updateColor: (projectId: string, caseId: string, color: string) =>
    apiClient.patch(`/projects/${projectId}/design-cases/${caseId}/color`, { color }),
};

// ========== 計算 ==========

export const calculationApi = {
  calculateHHI: (projectId: string) =>
    apiClient.post<HHIResult[]>(`/calculations/hhi/${projectId}`),
  calculateMountain: (projectId: string) =>
    apiClient.post<Array<{
      case_id: string;
      x: number;
      y: number;
      z: number;
      H: number;
      utility_vector: { [key: string]: number };
    }>>(`/calculations/mountain/${projectId}`),
  calculateUtility: (projectId: string, caseId: string) =>
    apiClient.get<{ [key: string]: number }>(`/calculations/utility/${projectId}/${caseId}`),
  // 論文準拠エネルギー計算: E = Σ(i<j) W_i × W_j × L(C_ij) / (Σ W_i)²
  calculateEnergy: (projectId: string) =>
    apiClient.post<Array<{
      case_id: string;
      case_name: string;
      total_energy: number;
      partial_energies: { [key: string]: number };
      inner_product_matrix: number[][];
      cos_theta_matrix: number[][];
      energy_contributions: Array<{
        perf_i_id: string;
        perf_j_id: string;
        perf_i_label: string;
        perf_j_label: string;
        W_i: number;
        W_j: number;
        C_ij: number;
        cos_theta: number;
        L_ij: number;
        contribution: number;
      }>;
    }>>(`/calculations/energy/${projectId}`),
  calculateCaseEnergy: (projectId: string, caseId: string) =>
    apiClient.get<{
      total_energy: number;
      partial_energies: { [key: string]: number };
      inner_product_matrix: number[][];
      cos_theta_matrix: number[][];
      energy_contributions: Array<{
        perf_i_id: string;
        perf_j_id: string;
        perf_i_label: string;
        perf_j_label: string;
        W_i: number;
        W_j: number;
        C_ij: number;
        cos_theta: number;
        L_ij: number;
        contribution: number;
      }>;
      performance_ids: string[];
      performance_labels: string[];
      norms: number[];
      metadata: {
        n_performances: number;
        n_tradeoff_pairs: number;
        total_weight: number;
        spectral_radius: number;
        convergence: boolean;
      };
    }>(`/calculations/energy/${projectId}/${caseId}`),
  calculateTradeoff: (projectId: string) =>
    apiClient.post<{ [key: string]: {
      ratio: number;
      total_paths: number;
      tradeoff_paths: number;
      is_valid: boolean;
    } }>(`/calculations/tradeoff/${projectId}`),
  getDiscretizationConfidence: (projectId: string, caseId: string) =>
    apiClient.get<{
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
    }>(`/calculations/discretization-confidence/${projectId}/${caseId}`),
};

// ========== エクスポート・インポート ==========

export interface UserChoiceOption {
  value: string;
  label: string;
  description: string;
}

export interface NeedPriorityItem {
  index: number;
  id: string;
  name: string;
  change: string;
}

export interface UserChoice {
  key: string;
  type: 'single_select' | 'number_input' | 'needs_priority_table';
  label: string;
  description: string;
  options?: UserChoiceOption[];  // single_select用
  default: any;
  min?: number;  // number_input用
  max?: number;
  step?: number;
  needs?: NeedPriorityItem[];  // needs_priority_table用
}

export interface ImportPreviewResponse {
  validation: {
    valid: boolean;
    errors: string[];
    warnings: string[];
    version: string;
  };
  migration_analysis: {
    needs_migration: boolean;
    source_version: string;
    target_version: string;
    migrations: Array<{
      type: string;
      description: string;
      affected_count: number;
      details?: any[];
      summary?: Record<string, number>;
      ambiguous_summary?: Record<string, number>;
      has_legacy_format?: boolean;
      has_new_format?: boolean;
      is_ambiguous?: boolean;
      requires_user_choice?: boolean;
    }>;
    user_choices: UserChoice[];
  };
  project_name: string;
  counts: {
    stakeholders: number;
    needs: number;
    performances: number;
    design_cases: number;
  };
}

export const projectApi = {
  list: () => apiClient.get<Project[]>('/projects'),
  get: (id: string) => apiClient.get<Project>(`/projects/${id}`),
  create: (data: ProjectCreate) => apiClient.post<Project>('/projects', data),
  update: (id: string, data: ProjectCreate) => apiClient.put<Project>(`/projects/${id}`, data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
  export: (id: string) => apiClient.get(`/projects/${id}/export`),
  importPreview: (data: any) => apiClient.post<ImportPreviewResponse>('/projects/import/preview', data),
  import: (data: any, userChoices?: Record<string, any>) =>
    apiClient.post<Project>('/projects/import', { data, user_choices: userChoices }),
  updateTwoAxisPlots: (id: string, plots: any[]) => apiClient.put(`/projects/${id}/two-axis-plots`, plots),
};

// ネットワーク個別操作API (3D編集用)
// ネットワーク個別操作API (3D編集用)
export const networkApi = {
  // ノード操作
  getNodes: (projectId: string, caseId: string) => 
    apiClient.get<NetworkNode[]>(`/projects/${projectId}/design-cases/${caseId}/nodes`),
  
  createNode: (projectId: string, caseId: string, data: Partial<NetworkNode>) => 
    apiClient.post<NetworkNode>(`/projects/${projectId}/design-cases/${caseId}/nodes`, data),
  
  updateNode: (projectId: string, caseId: string, nodeId: string, data: Partial<NetworkNode>) => 
    apiClient.put(`/projects/${projectId}/design-cases/${caseId}/nodes/${nodeId}`, data),
  
  updateNode3DPosition: (projectId: string, caseId: string, nodeId: string, x3d: number, y3d: number) => 
    apiClient.put(`/projects/${projectId}/design-cases/${caseId}/nodes/${nodeId}/position3d`, { x3d, y3d }),

  deleteNode: (projectId: string, caseId: string, nodeId: string) => 
    apiClient.delete(`/projects/${projectId}/design-cases/${caseId}/nodes/${nodeId}`),

  // エッジ操作
  getEdges: (projectId: string, caseId: string) => 
    apiClient.get<NetworkEdge[]>(`/projects/${projectId}/design-cases/${caseId}/edges`),
  
  createEdge: (projectId: string, caseId: string, data: Partial<NetworkEdge>) => 
    apiClient.post<NetworkEdge>(`/projects/${projectId}/design-cases/${caseId}/edges`, data),
  
  updateEdge: (projectId: string, caseId: string, edgeId: string, data: Partial<NetworkEdge>) => 
    apiClient.put(`/projects/${projectId}/design-cases/${caseId}/edges/${edgeId}`, data),

  deleteEdge: (projectId: string, caseId: string, edgeId: string) =>
    apiClient.delete(`/projects/${projectId}/design-cases/${caseId}/edges/${edgeId}`),
};

// ========== SCC分析（ループ検出） ==========

export interface SCCComponent {
  nodes: string[];
  edges: Array<{ source: string; target: string }>;
  spectral_radius: number;
  converges: boolean;
  suggestions: Array<{
    type: 'edge_removal' | 'node_merge' | 'constraint' | 'convergent';
    description: string;
    priority: number;
    action_required: boolean;
    edge?: string[];
    edge_labels?: string[];
    nodes?: string[];
    node_labels?: string[];
  }>;
}

export interface SCCAnalysisResult {
  has_loops: boolean;
  n_components_with_loops: number;
  components: SCCComponent[];
  all_attribute_nodes: string[];
  dag_after_condensation: Array<{ from_scc: number; to_scc: number }>;
  message?: string;
}

export interface SCCSummaryItem {
  case_id: string;
  case_name: string;
  has_loops: boolean;
  n_components: number;
  all_converge: boolean;
}

export const sccApi = {
  analyze: (projectId: string, caseId: string) =>
    apiClient.get<SCCAnalysisResult>(`/calculations/scc/${projectId}/${caseId}`),

  // Analyze network directly without saving (for preview/validation)
  analyzeDirect: (network: { nodes: any[]; edges: any[] }) =>
    apiClient.post<SCCAnalysisResult>(`/calculations/scc-analyze`, network),

  summary: (projectId: string) =>
    apiClient.get<{
      project_id: string;
      n_cases: number;
      cases_with_loops: number;
      total_loop_components: number;
      summary: SCCSummaryItem[];
    }>(`/calculations/scc-summary/${projectId}`),
};

// ========== Shapley値分析（寄与度分解） ==========

export interface ShapleyValue {
  property_idx: number;
  property_name: string;
  phi: number;
  abs_phi: number;
  percentage: number;
  sign: 'positive' | 'negative' | 'neutral';
}

export interface ShapleyResult {
  perf_i: { idx: number; name: string };
  perf_j: { idx: number; name: string };
  C_ij: number;
  cos_theta: number;
  relationship: 'tradeoff' | 'synergy' | 'neutral';
  shapley_values: ShapleyValue[];
  sum_check: number;
  additivity_error: number;
  computation: {
    method: 'exact' | 'monte_carlo';
    n_properties: number;
    time_ms: number;
  };
}

export interface ShapleyComputationCost {
  n_properties: number;
  n_subsets: number;
  estimated_time_ms: number;
  warning: 'low' | 'medium' | 'high';
  recommendation: 'exact' | 'exact_with_cache' | 'monte_carlo';
  message: string;
}

export const shapleyApi = {
  computeForPair: (
    projectId: string,
    caseId: string,
    perfIId: string,
    perfJId: string,
    method: 'auto' | 'exact' | 'monte_carlo' = 'auto'
  ) =>
    apiClient.get<ShapleyResult>(
      `/calculations/shapley/${projectId}/${caseId}/${perfIId}/${perfJId}?method=${method}`
    ),

  computeAll: (
    projectId: string,
    caseId: string,
    onlyTradeoffs: boolean = true
  ) =>
    apiClient.get<ShapleyResult[]>(
      `/calculations/shapley-all/${projectId}/${caseId}?only_tradeoffs=${onlyTradeoffs}`
    ),

  estimateCost: (nProperties: number) =>
    apiClient.get<ShapleyComputationCost>(`/calculations/shapley-cost/${nProperties}`),
};

// ========== エッジShapley値分析（エッジ寄与度分解） ==========

export interface EdgeShapleyValue {
  edge_id: string;
  source_id: string;
  target_id: string;
  source_label: string;
  target_label: string;
  edge_type: 'AV' | 'AA' | 'PA';
  edge_weight: number;
  phi: number;
  abs_phi: number;
  percentage: number;
  sign: 'positive' | 'negative' | 'neutral';
}

export interface EdgeShapleyResult {
  perf_i: { idx: number; name: string };
  perf_j: { idx: number; name: string };
  C_ij: number;
  cos_theta: number;
  relationship: 'tradeoff' | 'synergy' | 'neutral';
  edge_shapley_values: EdgeShapleyValue[];
  sum_check: number;
  additivity_error: number;
  computation: {
    method: 'exact' | 'monte_carlo';
    n_edges: number;
    time_ms: number;
  };
}

export const edgeShapleyApi = {
  computeForPair: (
    projectId: string,
    caseId: string,
    perfIId: string,
    perfJId: string,
    method: 'auto' | 'exact' | 'monte_carlo' = 'auto'
  ) =>
    apiClient.get<EdgeShapleyResult>(
      `/calculations/edge-shapley/${projectId}/${caseId}/${perfIId}/${perfJId}?method=${method}`
    ),
};

// ========== ノードShapley値分析（V ∪ A がプレイヤー） ==========

export interface NodeShapleyValue {
  node_id: string;
  node_label: string;
  node_type: 'V' | 'A';  // Variable or Attribute
  layer: number;  // 2=Attribute, 3=Variable
  phi: number;
  abs_phi: number;
  percentage: number;
  sign: 'positive' | 'negative' | 'neutral';
}

export interface NodeShapleyResult {
  perf_i: { idx: number; name: string };
  perf_j: { idx: number; name: string };
  C_ij: number;
  cos_theta: number;
  relationship: 'tradeoff' | 'synergy' | 'neutral';
  node_shapley_values: NodeShapleyValue[];
  sum_check: number;
  additivity_error: number;
  computation: {
    method: 'exact' | 'monte_carlo';
    n_nodes: number;
    n_variables: number;
    n_attributes: number;
    time_ms: number;
  };
}

export const nodeShapleyApi = {
  computeForPair: (
    projectId: string,
    caseId: string,
    perfIId: string,
    perfJId: string,
    method: 'auto' | 'exact' | 'monte_carlo' = 'auto'
  ) =>
    apiClient.get<NodeShapleyResult>(
      `/calculations/node-shapley/${projectId}/${caseId}/${perfIId}/${perfJId}?method=${method}`
    ),
};

// ========== 構造的トレードオフ分析 ==========

export interface StructuralTradeoffResult {
  cos_theta_matrix: number[][];
  inner_product_matrix?: number[][];
  energy_matrix?: number[][];  // E_ij = max(0, -C_ij)
  performance_ids: string[];
  performance_labels: string[];  // API returns performance_labels
  performance_id_map?: { [networkNodeId: string]: string };  // network_node_id -> db_performance_id
  variable_ids?: string[];
  variable_labels?: string[];
  attribute_ids?: string[];
  attribute_labels?: string[];
  tradeoff_pairs: Array<{
    i: number;
    j: number;
    cos_theta: number;
    perf_i_id: string;
    perf_j_id: string;
    perf_i_label: string;
    perf_j_label: string;
    perf_i_performance_id?: string;
    perf_j_performance_id?: string;
    inner_product?: number;
    interpretation?: string;
  }>;
  synergy_pairs?: Array<{
    i: number;
    j: number;
    cos_theta: number;
    perf_i_id: string;
    perf_j_id: string;
    perf_i_label: string;
    perf_j_label: string;
  }>;
  metadata: {
    spectral_radius: number;
    convergence: boolean;
    method: string;
    n_performances: number;
    n_attributes: number;
    n_variables: number;
  };
}

export interface PaperMetricsResult {
  height: {
    H: number;
    breakdown: Array<{
      performance_id: string;
      name: string;
      W_i: number;
      U_i: number;
      contribution: number;
    }>;
  };
  energy: {
    E: number;
    n_tradeoff_pairs: number;
    contributions: Array<{
      perf_i_id: string;
      perf_i_name: string;
      perf_j_id: string;
      perf_j_name: string;
      E_ij: number;
      C_ij: number;
      cos_theta: number;
    }>;
  };
  structural_tradeoff: StructuralTradeoffResult;
}

export const structuralTradeoffApi = {
  getForCase: (projectId: string, caseId: string) =>
    apiClient.get<StructuralTradeoffResult>(
      `/calculations/structural-tradeoff/${projectId}/${caseId}`
    ),

  getPaperMetrics: (projectId: string, caseId: string) =>
    apiClient.get<PaperMetricsResult>(
      `/calculations/paper-metrics/${projectId}/${caseId}`
    ),

  getSummary: (projectId: string) =>
    apiClient.get<{
      project_id: string;
      cases: Array<{
        case_id: string;
        case_name: string;
        n_tradeoff_pairs: number;
        avg_cos_theta: number;
        min_cos_theta: number;
      }>;
    }>(`/calculations/structural-tradeoff-summary/${projectId}`),
};

// カップリング＆クラスタリングAPI
export interface CouplingTradeoff {
  index: number;
  label: string;
  perf_i_idx: number;
  perf_j_idx: number;
  perf_i_label: string;
  perf_j_label: string;
  cos_theta: number;
  c_ij: number;
}

export interface ClusterGroup {
  [clusterId: number]: Array<{
    perf_idx: number;
    perf_label: string;
  }>;
}

export interface DendrogramNode {
  id: number;
  label: string;
  is_leaf: boolean;
  height: number;
  children: number[];
}

export interface CouplingResult {
  n_tradeoffs: number;
  tradeoffs: CouplingTradeoff[];
  coupling_matrix: number[][];
  tradeoff_labels: string[];
  performance_connection_matrix: number[][];
  performance_labels: string[];
  clustering: {
    clusters: number[] | null;
    optimal_n_clusters: number | null;
    silhouette_score: number | null;
    cluster_groups: ClusterGroup;
  };
  dendrogram: {
    nodes: DendrogramNode[];
    n_leaves: number;
    labels: string[];
    max_height: number;
    silhouette_curve: {
      height: number;
      n_clusters: number;
      silhouette: number | null;
    }[];
    optimal_height: number | null;
  } | null;
}

export const couplingApi = {
  getForCase: (projectId: string, caseId: string, tradeoffThreshold: number = 0.0) =>
    apiClient.get<CouplingResult>(
      `/calculations/coupling/${projectId}/${caseId}`,
      { params: { tradeoff_threshold: tradeoffThreshold } }
    ),
};

export default apiClient;
