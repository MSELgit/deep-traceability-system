// frontend/src/stores/projectStore.ts

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type {
  Project, Stakeholder, Need, Performance, DesignCase,
  StakeholderNeedRelation, NeedPerformanceRelation, HHIResult, MountainPosition, DesignCaseCreate
} from '../types/project';
import {
  projectApi, stakeholderApi, needApi, performanceApi,
  designCaseApi, stakeholderNeedRelationApi, needPerformanceRelationApi,
  calculationApi, utilityFunctionApi
} from '../utils/api';

export const useProjectStore = defineStore('project', () => {
  // State
  const currentProject = ref<Project | null>(null);
  const projects = ref<Project[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  
  // HHI計算結果
  const hhiResults = ref<HHIResult[]>([]);
  
  // ソート関数
  function sortStakeholders(stakeholders: Stakeholder[]): Stakeholder[] {
    return stakeholders.sort((a, b) => {
      // カテゴリーでソート（nullは最後）
      if (a.category && !b.category) return -1;
      if (!a.category && b.category) return 1;
      if (a.category && b.category) {
        const categoryCompare = a.category.localeCompare(b.category);
        if (categoryCompare !== 0) return categoryCompare;
      }
      // 同じカテゴリー内では名前でソート
      return a.name.localeCompare(b.name);
    });
  }

  function sortNeeds(needs: Need[]): Need[] {
    return needs.sort((a, b) => {
      // カテゴリーでソート（nullは最後）
      if (a.category && !b.category) return -1;
      if (!a.category && b.category) return 1;
      if (a.category && b.category) {
        const categoryCompare = a.category.localeCompare(b.category);
        if (categoryCompare !== 0) return categoryCompare;
      }
      // 同じカテゴリー内では名前でソート
      return a.name.localeCompare(b.name);
    });
  }
  
  // Computed
  const stakeholders = computed(() => currentProject.value?.stakeholders || []);
  const needs = computed(() => currentProject.value?.needs || []);
  const performances = computed(() => currentProject.value?.performances || []);
  const designCases = computed(() => currentProject.value?.design_cases || []);
  const stakeholderNeedRelations = computed(
    () => currentProject.value?.stakeholder_need_relations || []
  );
  const needPerformanceRelations = computed(
    () => currentProject.value?.need_performance_relations || []
  );
  
  // 末端性能のみ取得
  const leafPerformances = computed(() =>
    performances.value.filter(p => p.is_leaf)
  );
  
  // 階層化された性能ツリー
  const performanceTree = computed(() => {
    const tree: Performance[] = [];
    const map = new Map<string, Performance & { children?: Performance[] }>();
    
    // 全性能をマップに格納
    performances.value.forEach(p => {
      map.set(p.id, { ...p, children: [] });
    });
    
    // 親子関係を構築（配列の順序を保持）
    performances.value.forEach(perf => {
      const node = map.get(perf.id)!;
      if (node.parent_id) {
        const parent = map.get(node.parent_id);
        if (parent) {
          parent.children!.push(node);
        }
      } else {
        tree.push(node);
      }
    });
    
    return tree;
  });
  
  // Actions
  async function loadProjects() {
    loading.value = true;
    error.value = null;
    try {
      const response = await projectApi.list();
      projects.value = response.data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }
  
  async function loadProject(id: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await projectApi.get(id);
      currentProject.value = response.data;
      // プロジェクトを読み込んだ後にソート
      if (currentProject.value) {
        currentProject.value.stakeholders = sortStakeholders(currentProject.value.stakeholders);
        currentProject.value.needs = sortNeeds(currentProject.value.needs);
      }
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }
  
  async function createProject(name: string, description?: string) {
    loading.value = true;
    try {
      const response = await projectApi.create({ name, description });
      projects.value.push(response.data);
      currentProject.value = response.data;
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }
  
  async function addStakeholder(data: { name: string; category?: string; votes?: number }) {
    if (!currentProject.value) return;
    
    const response = await stakeholderApi.create(currentProject.value.id, {
      name: data.name,
      category: data.category,
      votes: data.votes || 100
    });
    
    currentProject.value.stakeholders.push(response.data);
    // ソート処理を追加
    currentProject.value.stakeholders = sortStakeholders(currentProject.value.stakeholders);
    return response.data;
  }
  
  async function updateStakeholder(id: string, data: { name: string; category?: string; votes: number }) {
    if (!currentProject.value) return;
    
    const response = await stakeholderApi.update(currentProject.value.id, id, {
      name: data.name,
      category: data.category,
      votes: data.votes
    });
    
    const index = currentProject.value.stakeholders.findIndex(s => s.id === id);
    if (index !== -1) {
      currentProject.value.stakeholders[index] = response.data;
      // カテゴリーが変更される可能性があるのでソート
      currentProject.value.stakeholders = sortStakeholders(currentProject.value.stakeholders);
    }
  }
  
  async function deleteStakeholder(id: string) {
    if (!currentProject.value) return;
    
    try {
      await stakeholderApi.delete(currentProject.value.id, id);
      
      const index = currentProject.value.stakeholders.findIndex(s => s.id === id);
      if (index !== -1) {
        currentProject.value.stakeholders.splice(index, 1);
      }
    } catch (error) {
      console.error('Failed to delete stakeholder:', error);
      throw error;
    }
  }
  
  async function addNeed(data: { name: string; category?: string; description?: string }) {
    if (!currentProject.value) return;
    
    const response = await needApi.create(currentProject.value.id, data);
    currentProject.value.needs.push(response.data);
    // ソート処理を追加
    currentProject.value.needs = sortNeeds(currentProject.value.needs);
    return response.data;
  }
  
  async function updateNeed(id: string, data: { name: string; category?: string; description?: string; priority?: number }) {
    if (!currentProject.value) return;
    
    const response = await needApi.update(currentProject.value.id, id, data);
    
    const index = currentProject.value.needs.findIndex(n => n.id === id);
    if (index !== -1) {
      currentProject.value.needs[index] = response.data;
      // カテゴリーが変更される可能性があるのでソート
      currentProject.value.needs = sortNeeds(currentProject.value.needs);
    }
    return response.data;
  }
  
  async function deleteNeed(id: string) {
    if (!currentProject.value) return;
    
    try {
      await needApi.delete(currentProject.value.id, id);
      
      const index = currentProject.value.needs.findIndex(n => n.id === id);
      if (index !== -1) {
        currentProject.value.needs.splice(index, 1);
      }
    } catch (error) {
      console.error('Failed to delete need:', error);
      throw error;
    }
  }
  
  async function addPerformance(data: {
    name: string;
    parent_id?: string;
    level: number;
    is_leaf?: boolean;
    unit?: string;
  }) {
    if (!currentProject.value) return;
    
    const response = await performanceApi.create(currentProject.value.id, data);
    
    // 性能追加後、プロジェクト全体を再取得して親のis_leafを更新
    await loadProject(currentProject.value.id);
    
    return response.data;
  }

  async function updatePerformance(performanceId: string, data: {
    name: string;
    unit?: string;
    description?: string;
  }) {
    if (!currentProject.value) return;

    // 既存の性能データを取得
    const existingPerf = currentProject.value.performances.find(p => p.id === performanceId);
    if (!existingPerf) {
      throw new Error('Performance not found');
    }

    // 更新用に既存データとマージ
    const updateData = {
      name: data.name,
      parent_id: existingPerf.parent_id,
      level: existingPerf.level,
      is_leaf: existingPerf.is_leaf,
      unit: data.unit,
      description: data.description
    };

    const response = await performanceApi.update(currentProject.value.id, performanceId, updateData);

    // 性能更新後、プロジェクト全体を再取得
    await loadProject(currentProject.value.id);

    return response.data;
  }

  async function deletePerformance(performanceId: string) {
    if (!currentProject.value) return;

    await performanceApi.delete(currentProject.value.id, performanceId);

    // 性能削除後、プロジェクト全体を再取得して親のis_leafを更新
    await loadProject(currentProject.value.id);
  }
  
  async function addStakeholderNeedRelation(stakeholderId: string, needId: string, weight: number = 1.0) {
    if (!currentProject.value) return;
    
    // 既に存在する関係かチェック（ローカル確認のみ、APIは重複を許可しない）
    const exists = currentProject.value.stakeholder_need_relations.some(
      r => r.stakeholder_id === stakeholderId && r.need_id === needId
    );
    
    if (exists) {
      console.warn('Relation already exists locally:', { stakeholderId, needId });
      return;
    }
    
    try {
      await stakeholderNeedRelationApi.create(currentProject.value.id, {
        stakeholder_id: stakeholderId,
        need_id: needId,
        relationship_weight: weight
      });
      
      currentProject.value.stakeholder_need_relations.push({
        stakeholder_id: stakeholderId,
        need_id: needId,
        relationship_weight: weight
      });
    } catch (error: any) {
      // 400エラー（重複）は無視、その他はエラーを投げる
      if (error.response?.status !== 400) {
        throw error;
      }
      console.warn('Relation already exists in database, syncing local state');
      // ローカル状態がDBと同期していない場合、プロジェクトを再読み込み
      if (currentProject.value) {
        await loadProject(currentProject.value.id);
      }
    }
  }
  
  async function updateStakeholderNeedRelation(stakeholderId: string, needId: string, weight: number) {
    if (!currentProject.value) return;
    
    // ローカル配列で該当関係を見つけて更新（楽観的更新）
    const relation = currentProject.value.stakeholder_need_relations.find(
      r => r.stakeholder_id === stakeholderId && r.need_id === needId
    );
    
    if (!relation) {
      console.warn('Relation not found locally:', { stakeholderId, needId });
      return;
    }
    
    const originalWeight = relation.relationship_weight;
    relation.relationship_weight = weight;
    
    try {
      await stakeholderNeedRelationApi.update(
        currentProject.value.id,
        stakeholderId,
        needId,
        { relationship_weight: weight }
      );
    } catch (error: any) {
      // エラーが発生した場合は元に戻す
      console.error('Failed to update relation, rolling back:', error);
      relation.relationship_weight = originalWeight;
      throw error;
    }
  }
  
  async function removeStakeholderNeedRelation(stakeholderId: string, needId: string) {
    if (!currentProject.value) return;
    
    // ローカル配列から先に削除（楽観的更新）
    const index = currentProject.value.stakeholder_need_relations.findIndex(
      r => r.stakeholder_id === stakeholderId && r.need_id === needId
    );
    
    if (index === -1) {
      console.warn('Relation not found locally:', { stakeholderId, needId });
      return;
    }
    
    const removedRelation = currentProject.value.stakeholder_need_relations[index];
    currentProject.value.stakeholder_need_relations.splice(index, 1);
    
    try {
      await stakeholderNeedRelationApi.delete(
        currentProject.value.id,
        stakeholderId,
        needId
      );
    } catch (error: any) {
      // エラーが発生した場合は元に戻す
      console.error('Failed to delete relation, rolling back:', error);
      currentProject.value.stakeholder_need_relations.splice(index, 0, removedRelation);
      throw error;
    }
  }
  
  async function addNeedPerformanceRelation(
    needId: string,
    performanceId: string,
    direction: 'up' | 'down'
  ) {
    if (!currentProject.value) return;
    
    // 既に存在する関係かチェック（ローカル確認のみ）
    const exists = currentProject.value.need_performance_relations.some(
      r => r.need_id === needId && r.performance_id === performanceId
    );
    
    if (exists) {
      console.warn('Relation already exists locally:', { needId, performanceId });
      return;
    }
    
    try {
      await needPerformanceRelationApi.create(currentProject.value.id, {
        need_id: needId,
        performance_id: performanceId,
        direction
      });
      
      currentProject.value.need_performance_relations.push({
        need_id: needId,
        performance_id: performanceId,
        direction
      });
    } catch (error: any) {
      // 400エラー（重複）は無視、その他はエラーを投げる
      if (error.response?.status !== 400) {
        throw error;
      }
      console.warn('Relation already exists in database, syncing local state');
      if (currentProject.value) {
        await loadProject(currentProject.value.id);
      }
    }
  }
  
  async function updateNeedPerformanceRelation(
    needId: string,
    performanceId: string,
    direction: 'up' | 'down'
  ) {
    if (!currentProject.value) return;
    
    const index = currentProject.value.need_performance_relations.findIndex(
      r => r.need_id === needId && r.performance_id === performanceId
    );
    
    if (index === -1) {
      console.warn('Relation not found locally:', { needId, performanceId });
      return;
    }
    
    const oldDirection = currentProject.value.need_performance_relations[index].direction;
    currentProject.value.need_performance_relations[index].direction = direction;
    
    try {
      await needPerformanceRelationApi.update(
        currentProject.value.id,
        needId,
        performanceId,
        { need_id: needId, performance_id: performanceId, direction }
      );
    } catch (error) {
      // エラーが発生した場合は元に戻す
      console.error('Failed to update relation, rolling back:', error);
      currentProject.value.need_performance_relations[index].direction = oldDirection;
      throw error;
    }
  }
  
  async function removeNeedPerformanceRelation(needId: string, performanceId: string) {
    if (!currentProject.value) return;
    
    const index = currentProject.value.need_performance_relations.findIndex(
      r => r.need_id === needId && r.performance_id === performanceId
    );
    
    if (index === -1) {
      console.warn('Relation not found locally:', { needId, performanceId });
      return;
    }
    
    const removedRelation = currentProject.value.need_performance_relations[index];
    currentProject.value.need_performance_relations.splice(index, 1);
    
    try {
      await needPerformanceRelationApi.delete(
        currentProject.value.id,
        needId,
        performanceId
      );
    } catch (error) {
      // エラーが発生した場合は元に戻す
      console.error('Failed to delete relation, rolling back:', error);
      currentProject.value.need_performance_relations.splice(index, 0, removedRelation);
      throw error;
    }
  }
  
  // 効用関数を保存
  async function saveUtilityFunction(
    needId: string,
    performanceId: string,
    utilityData: any
  ) {
    if (!currentProject.value) return;
    
    try {
      await utilityFunctionApi.save(
        currentProject.value.id,
        needId,
        performanceId,
        utilityData
      );
      
      // ローカルの関係も更新
      const relation = currentProject.value.need_performance_relations.find(
        r => r.need_id === needId && r.performance_id === performanceId
      );
      if (relation) {
        relation.utility_function_json = JSON.stringify(utilityData);
      }
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }
  
  // 効用関数を取得
  async function getUtilityFunction(needId: string, performanceId: string) {
    if (!currentProject.value) return null;
    
    try {
      const response = await utilityFunctionApi.get(
        currentProject.value.id,
        needId,
        performanceId
      );
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      return null;
    }
  }
  
  // プロジェクトの全効用関数を読み込み
  async function loadUtilityFunctions() {
    if (!currentProject.value) return [];
    
    try {
      const response = await utilityFunctionApi.list(
        currentProject.value.id
      );
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      return [];
    }
  }
  
  async function calculateHHI() {
    if (!currentProject.value) return;
    
    loading.value = true;
    try {
      const response = await calculationApi.calculateHHI(currentProject.value.id);
      hhiResults.value = response.data;
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }
  
  async function calculateMountain() {
    if (!currentProject.value) return;
    
    loading.value = true;
    try {
      const response = await calculationApi.calculateMountain(currentProject.value.id);
      
      // 設計案の座標を更新
      response.data.forEach((pos: any) => {
        const designCase = currentProject.value!.design_cases.find(
          dc => dc.id === pos.case_id
        );
        if (designCase) {
          designCase.mountain_position = {
            x: pos.x,
            y: pos.y,
            z: pos.z,
            H: pos.H
          };
          designCase.utility_vector = pos.utility_vector;
        }
      });
      
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function loadDesignCases() {
    if (!currentProject.value) return [];
    
    try {
      const response = await designCaseApi.list(currentProject.value.id);
      if (currentProject.value) {
        currentProject.value.design_cases = response.data;
      }
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      return [];
    }
  }

  async function createDesignCase(data: DesignCaseCreate) {
    if (!currentProject.value) return;
    
    try {
      const response = await designCaseApi.create(currentProject.value.id, data);
      
      // プロジェクトを再読み込み（山の座標も含む）
      await loadProject(currentProject.value.id);
      
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  async function updateDesignCase(caseId: string, data: DesignCaseCreate) {
    if (!currentProject.value) return;
    
    try {
      const response = await designCaseApi.update(currentProject.value.id, caseId, data);
      
      // プロジェクトを再読み込み
      await loadProject(currentProject.value.id);
      
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  async function deleteDesignCase(caseId: string) {
    if (!currentProject.value) return;
    
    try {
      await designCaseApi.delete(currentProject.value.id, caseId);
      
      // プロジェクトを再読み込み
      await loadProject(currentProject.value.id);
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  async function copyDesignCase(caseId: string) {
    if (!currentProject.value) return;
    
    try {
      const response = await designCaseApi.copy(currentProject.value.id, caseId);
      
      // プロジェクトを再読み込み
      await loadProject(currentProject.value.id);
      
      return response.data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  async function updateDesignCaseColor(caseId: string, color: string) {
    if (!currentProject.value) return;
    
    try {
      await designCaseApi.updateColor(currentProject.value.id, caseId, color);
      
      // ローカルの状態も更新
      const designCase = currentProject.value.design_cases.find(dc => dc.id === caseId);
      if (designCase) {
        designCase.color = color;
      }
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  
  function reset() {
    currentProject.value = null;
    hhiResults.value = [];
    error.value = null;
  }
  
  return {
    // State
    currentProject,
    projects,
    loading,
    error,
    hhiResults,
    
    // Computed
    stakeholders,
    needs,
    performances,
    designCases,
    stakeholderNeedRelations,
    needPerformanceRelations,
    leafPerformances,
    performanceTree,
    
    // Actions
    loadProjects,
    loadProject,
    createProject,
    addStakeholder,
    updateStakeholder,
    deleteStakeholder,
    addNeed,
    updateNeed,
    deleteNeed,
    addPerformance,
    updatePerformance,
    deletePerformance,
    addStakeholderNeedRelation,
    updateStakeholderNeedRelation,
    removeStakeholderNeedRelation,
    addNeedPerformanceRelation,
    updateNeedPerformanceRelation,
    removeNeedPerformanceRelation,
    saveUtilityFunction,
    getUtilityFunction,
    loadUtilityFunctions,
    calculateHHI,
    calculateMountain,
    loadDesignCases,
    createDesignCase,
    updateDesignCase,
    deleteDesignCase,
    copyDesignCase,
    updateDesignCaseColor,
    reset
  };
});
