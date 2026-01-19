# backend/app/services/energy_calculator.py

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.database import ProjectModel, DesignCaseModel

logger = logging.getLogger(__name__)


def calculate_energy_for_case(
    design_case: DesignCaseModel,
    performances: List[Dict],
    db: Session
) -> Dict:
    """
    設計案のエネルギーを計算
    
    Returns:
        {
            "total_energy": float,  # 総合エネルギー
            "partial_energies": Dict[str, float],  # 各性能の部分エネルギー
            "match_matrix": Dict[str, float]  # Match値の行列
        }
    """
    network = design_case.network
    if not network or 'nodes' not in network or 'edges' not in network:
        logger.warning("ネットワーク情報が不足しています")
        return {
            "total_energy": 0.0,
            "partial_energies": {},
            "match_matrix": {}
        }
    
    # 性能ノードと特性ノードを抽出
    performance_nodes = [n for n in network['nodes'] if n['layer'] == 1]
    property_nodes = [n for n in network['nodes'] if n['layer'] == 2]
    
    # 性能ノードIDのマッピング
    perf_id_to_node = {n['id']: n for n in performance_nodes}
    prop_id_to_node = {n['id']: n for n in property_nodes}
    
    # エッジの重みマッピング（source -> target -> weight）
    edge_weights = {}
    for edge in network['edges']:
        if edge['source_id'] not in edge_weights:
            edge_weights[edge['source_id']] = {}
        edge_weights[edge['source_id']][edge['target_id']] = edge.get('weight', 0)
    
    # 各性能ペアのMatch値を計算
    n = len(performance_nodes)
    match_matrix = {}
    
    for i in range(n):
        for j in range(i + 1, n):
            perf_i = performance_nodes[i]
            perf_j = performance_nodes[j]
            
            # 両方の性能に接続された特性を見つける
            connected_properties = find_common_properties(
                perf_i['id'], perf_j['id'], property_nodes, edge_weights
            )
            
            # Match_ijを計算
            match_value = calculate_match(
                perf_i['id'], perf_j['id'], connected_properties, edge_weights
            )
            
            key = f"{perf_i['id']}_{perf_j['id']}"
            match_matrix[key] = match_value
    
    # 性能の重要度を取得（performance_weightsから）
    importance = {}
    
    if hasattr(design_case, 'performance_weights') and design_case.performance_weights:
        for perf_node in performance_nodes:
            perf_id = perf_node.get('performance_id')
            if perf_id:
                weight = design_case.performance_weights.get(perf_id, 0.0)
                importance[perf_node['id']] = weight
            else:
                importance[perf_node['id']] = 0.0
    else:
        # デフォルトの重要度
        logger.debug("performance_weightsが設定されていません。デフォルト値(0.0)を使用します。")
        for perf_node in performance_nodes:
            importance[perf_node['id']] = 0.0
    
    # 部分エネルギーと総合エネルギーを計算
    partial_energies = {}
    total_energy = 0.0
    
    # 各性能から見た部分エネルギーを計算
    for i in range(n):
        perf_i = performance_nodes[i]
        partial_energy = 0.0
        
        
        for j in range(n):
            if i != j:
                perf_j = performance_nodes[j]
                
                # Match値を取得（対称性を考慮）
                if i < j:
                    key = f"{perf_i['id']}_{perf_j['id']}"
                    match_value = match_matrix.get(key, 0.0)
                else:
                    key = f"{perf_j['id']}_{perf_i['id']}"
                    match_value = match_matrix.get(key, 0.0)
                
                # 距離を計算
                r_ij = np.sqrt(2 * (1 - match_value))
                
                # エネルギー寄与を計算
                if r_ij > 1e-10:
                    q_i = importance[perf_i['id']]
                    q_j = importance[perf_j['id']]
                    energy_contribution = (q_i * q_j) / r_ij
                    partial_energy += energy_contribution
        
        # 部分エネルギーは他のすべての性能との相互作用の半分
        partial_energies[perf_i['id']] = partial_energy / 2.0
        total_energy += partial_energy / 2.0
    
    # performance_idでの部分エネルギーも作成
    partial_energies_by_perf_id = {}
    for perf_node in performance_nodes:
        if 'performance_id' in perf_node:
            partial_energies_by_perf_id[perf_node['performance_id']] = partial_energies[perf_node['id']]
    
    # performance_idベースのmatch_matrixも作成
    match_matrix_by_perf_id = {}
    node_id_to_perf_id = {n['id']: n.get('performance_id') for n in performance_nodes if n.get('performance_id')}
    
    for key, value in match_matrix.items():
        node_ids = key.split('_')
        if len(node_ids) == 2:
            perf_id1 = node_id_to_perf_id.get(node_ids[0])
            perf_id2 = node_id_to_perf_id.get(node_ids[1])
            if perf_id1 and perf_id2:
                new_key = f"{perf_id1}_{perf_id2}"
                match_matrix_by_perf_id[new_key] = value
    
    return {
        "total_energy": total_energy,
        "partial_energies": partial_energies_by_perf_id,
        "partial_energies_by_node": partial_energies,
        "match_matrix": match_matrix_by_perf_id,  # performance_idベースに変更
        "match_matrix_by_node": match_matrix,  # node_idベースも保持
        "importance": importance
    }


def find_common_properties(
    perf_i_id: str,
    perf_j_id: str,
    property_nodes: List[Dict],
    edge_weights: Dict[str, Dict[str, float]]
) -> List[str]:
    """両方の性能に接続された特性を見つける"""
    connected_to_i = set()
    connected_to_j = set()
    
    # 性能から特性へのエッジを探す
    if perf_i_id in edge_weights:
        connected_to_i.update(edge_weights[perf_i_id].keys())
    
    if perf_j_id in edge_weights:
        connected_to_j.update(edge_weights[perf_j_id].keys())
    
    # 特性から性能へのエッジも探す
    for prop_id in [n['id'] for n in property_nodes]:
        if prop_id in edge_weights:
            if perf_i_id in edge_weights[prop_id]:
                connected_to_i.add(prop_id)
            if perf_j_id in edge_weights[prop_id]:
                connected_to_j.add(prop_id)
    
    # 共通の特性を返す
    return list(connected_to_i.intersection(connected_to_j))


def calculate_match(
    perf_i_id: str,
    perf_j_id: str,
    common_properties: List[str],
    edge_weights: Dict[str, Dict[str, float]]
) -> float:
    """
    Match_αβ = -tanh{log(3/2) * Σ sgn(W_iα * W_iβ) * √|W_iα * W_iβ|}
    """
    if not common_properties:
        return 0.0
    
    sum_term = 0.0
    
    for prop_id in common_properties:
        # 重みを取得（エッジの方向を考慮）
        w_prop_to_i = 0.0
        w_prop_to_j = 0.0
        
        # 性能から特性への重み
        if perf_i_id in edge_weights and prop_id in edge_weights[perf_i_id]:
            # 性能から特性への場合は逆数を取る
            weight = edge_weights[perf_i_id][prop_id]
            w_prop_to_i = 1.0 / weight if weight != 0 else 0.0
        
        if perf_j_id in edge_weights and prop_id in edge_weights[perf_j_id]:
            # 性能から特性への場合は逆数を取る
            weight = edge_weights[perf_j_id][prop_id]
            w_prop_to_j = 1.0 / weight if weight != 0 else 0.0
        
        # 特性から性能への重み
        if prop_id in edge_weights:
            if perf_i_id in edge_weights[prop_id]:
                w_prop_to_i = edge_weights[prop_id][perf_i_id]
            if perf_j_id in edge_weights[prop_id]:
                w_prop_to_j = edge_weights[prop_id][perf_j_id]
        
        # sgn(W_iα * W_iβ) * √|W_iα * W_iβ|
        product = w_prop_to_i * w_prop_to_j
        if product != 0:
            sign = np.sign(product)
            sqrt_abs = np.sqrt(np.abs(product))
            contribution = sign * sqrt_abs
            sum_term += contribution
    
    # -tanh{log(3/2) * sum}
    log_factor = np.log(3.0 / 2.0)
    match_value = -np.tanh(log_factor * sum_term)
    
    return match_value


def calculate_energy_for_project(project: ProjectModel, db: Session) -> List[Dict]:
    """
    プロジェクトの全設計案についてエネルギーを計算
    """
    results = []
    
    for design_case in project.design_cases:
        # 設計案のスナップショットがある場合はそれを使用
        if design_case.performance_snapshot:
            from app.schemas.project import Performance
            case_performances = [Performance(**perf_data) for perf_data in design_case.performance_snapshot]
            energy_result = calculate_energy_for_case(design_case, case_performances, db)
        else:
            # スナップショットがない場合は現在の性能ツリーを使用
            energy_result = calculate_energy_for_case(design_case, project.performances, db)
        
        results.append({
            "case_id": design_case.id,
            "case_name": design_case.name,
            "total_energy": energy_result["total_energy"],
            "partial_energies": energy_result["partial_energies"],
            "match_matrix": energy_result["match_matrix"]
        })
    
    return results