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
  calculateEnergy: (projectId: string) =>
    apiClient.post<Array<{
      case_id: string;
      case_name: string;
      total_energy: number;
      partial_energies: { [key: string]: number };
      match_matrix: { [key: string]: number };
    }>>(`/calculations/energy/${projectId}`),
  calculateCaseEnergy: (projectId: string, caseId: string) =>
    apiClient.get<{
      total_energy: number;
      partial_energies: { [key: string]: number };
      partial_energies_by_node: { [key: string]: number };
      match_matrix: { [key: string]: number };
      importance: { [key: string]: number };
    }>(`/calculations/energy/${projectId}/${caseId}`),
  calculateTradeoff: (projectId: string) => {
    console.log(`[API] Calling POST /calculations/tradeoff/${projectId}`);
    console.log(`[API] Full URL: ${API_BASE_URL}/calculations/tradeoff/${projectId}`);
    return apiClient.post<{ [key: string]: { 
      ratio: number; 
      total_paths: number; 
      tradeoff_paths: number; 
      is_valid: boolean; 
    } }>(`/calculations/tradeoff/${projectId}`).then(response => {
      console.log('[API] Response received:', response.status);
      return response;
    }).catch(error => {
      console.error('[API] Error:', error);
      throw error;
    });
  },
};

// ========== エクスポート・インポート ==========

export const projectApi = {
  list: () => apiClient.get<Project[]>('/projects'),
  get: (id: string) => apiClient.get<Project>(`/projects/${id}`),
  create: (data: ProjectCreate) => apiClient.post<Project>('/projects', data),
  update: (id: string, data: ProjectCreate) => apiClient.put<Project>(`/projects/${id}`, data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
  export: (id: string) => apiClient.get(`/projects/${id}/export`),
  import: (data: any) => apiClient.post<Project>('/projects/import', data),
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

export default apiClient;
