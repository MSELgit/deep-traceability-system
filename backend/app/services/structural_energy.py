# backend/app/services/structural_energy.py
"""
論文準拠エネルギー計算サービス

論文(design.tex) Chapter 7 式5820に基づくエネルギー計算:
E = Σ(i<j) W_i × W_j × L(C_ij) / (Σ W_i)²

where:
- C_ij = ⟨T_i·, T_j·⟩ (総効果行列の行ベクトル内積)
- L(x) = |x| if x < 0, else 0 (損失関数)
- W_i = 性能の重み（票数配分から算出）

既存の energy_calculator.py (Match値+クーロン力モデル) とは別の指標として提供
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

from .matrix_utils import (
    build_adjacency_matrices,
    compute_total_effect_matrix,
    compute_inner_products,
)


def loss_function(x: float) -> float:
    """
    損失関数 L(x) — 廃止（後方互換のため残置）

    旧式 L(x) = |x| if x < 0, else 0
    新式では4象限分解エネルギー E_ij = (W_i W_j |C_ij| - δ_i δ_j C_ij) / 2 に置き換え
    """
    if x < 0:
        return abs(x)
    return 0.0


def compute_structural_energy(
    network: Dict,
    performance_weights: Dict[str, float],
    weight_mode: str = 'discrete_7',
    performance_deltas: Dict[str, float] = None,
) -> Dict:
    """
    4象限分解エネルギー計算

    E = Σ(i<j) (W_i W_j |C_ij| - δ_i δ_j C_ij) / (2 (Σ W_k)²)

    δ_i = n_i↑ - n_i↓ (正味方向票)
    全票同方向の場合 δ_i = W_i となり旧式と一致（後方互換）

    Args:
        network: ネットワーク構造 {'nodes': [...], 'edges': [...]}
        performance_weights: 性能の重み {performance_id: W_i}
        weight_mode: 重みモード ('discrete_3', 'discrete_5', 'discrete_7', 'continuous')
        performance_deltas: 性能の正味方向票 {performance_id: δ_i}（Noneの場合W_iにフォールバック）

    Returns:
        {
            'E': float,  # 総エネルギー
            'total_energy_unnormalized': float,  # 正規化前の総エネルギー
            'normalization_factor': float,  # 2 * (Σ W_i)²
            'energy_contributions': [  # 各ペアの寄与
                {
                    'perf_i_id': str,
                    'perf_j_id': str,
                    'perf_i_label': str,
                    'perf_j_label': str,
                    'W_i': float,
                    'W_j': float,
                    'delta_i': float,
                    'delta_j': float,
                    'C_ij': float,  # 内積
                    'contribution': float,  # (W_i W_j |C_ij| - δ_i δ_j C_ij) / 2
                }
            ],
            'inner_product_matrix': List[List[float]],  # C_ij 行列
            'cos_theta_matrix': List[List[float]],  # cos θ 行列（参考）
            'norms': List[float],  # 各性能のノルム ||T_i·||
            'metadata': {
                'n_performances': int,
                'n_tradeoff_pairs': int,  # エネルギー正のペア数
                'total_weight': float,  # Σ W_i
            }
        }
    """
    # Step 1: 隣接行列を構築
    matrices = build_adjacency_matrices(network, weight_mode)

    n_perf = matrices['dimensions']['n_perf']
    perf_ids = matrices['node_ids']['P']
    perf_labels = matrices['node_labels']['P']
    perf_id_map = matrices['performance_id_map']

    if n_perf == 0:
        return _empty_result()

    # Step 2: 総効果行列を計算
    total_effect = compute_total_effect_matrix(
        matrices['B_PA'],
        matrices['B_AA'],
        matrices['B_AV']
    )
    T = total_effect['T']

    if T.size == 0:
        return _empty_result()

    # Step 3: 内積行列を計算
    inner_products = compute_inner_products(T)
    C = inner_products['C']
    cos_theta = inner_products['cos_theta']
    norms = inner_products['norms']

    # Step 4: 重みベクトルW_iとδベクトルを構築（node_id → performance_id → 値）
    _deltas = performance_deltas or {}
    W = []
    D = []
    for node_id in perf_ids:
        perf_id = perf_id_map.get(node_id, node_id)
        w_i = performance_weights.get(perf_id, 0.0)
        W.append(w_i)
        # δ_iが未指定の場合はW_iにフォールバック（後方互換: 全票同方向と仮定）
        D.append(_deltas.get(perf_id, w_i))
    W = np.array(W)
    D = np.array(D)

    # Step 5: 4象限分解エネルギー計算
    # E = Σ(i<j) (W_i W_j |C_ij| - δ_i δ_j C_ij) / (2 (Σ W_k)²)
    total_weight = np.sum(W)
    normalization_factor = 2.0 * total_weight ** 2 if total_weight > 0 else 1.0

    energy_contributions = []
    total_energy_unnormalized = 0.0
    n_tradeoff_pairs = 0

    for i in range(n_perf):
        for j in range(i + 1, n_perf):
            C_ij = float(C[i, j])
            W_i = float(W[i])
            W_j = float(W[j])
            delta_i = float(D[i])
            delta_j = float(D[j])

            # 非正規化寄与: E_ij = contribution / normalization_factor
            contribution = W_i * W_j * abs(C_ij) - delta_i * delta_j * C_ij

            if contribution > 0:
                n_tradeoff_pairs += 1
                total_energy_unnormalized += contribution

            # 方向合意度
            consensus_i = delta_i / W_i if W_i > 1e-10 else 0.0
            consensus_j = delta_j / W_j if W_j > 1e-10 else 0.0

            # λ_ij = E_ij / C_ij（エネルギー強度）
            if abs(C_ij) > 1e-12:
                lambda_ij = contribution / C_ij
            else:
                lambda_ij = 0.0

            # 相殺率: 全票同方向時のE_ij_maxに対する減少率
            E_max = W_i * W_j * abs(C_ij)
            offset_rate = 1.0 - contribution / E_max if E_max > 1e-12 else 0.0

            # エネルギー正のペアを記録
            if contribution > 0:
                energy_contributions.append({
                    'perf_i_id': perf_id_map.get(perf_ids[i], perf_ids[i]),
                    'perf_j_id': perf_id_map.get(perf_ids[j], perf_ids[j]),
                    'perf_i_label': perf_labels[i],
                    'perf_j_label': perf_labels[j],
                    'W_i': W_i,
                    'W_j': W_j,
                    'delta_i': delta_i,
                    'delta_j': delta_j,
                    'C_ij': C_ij,
                    'cos_theta': float(cos_theta[i, j]),
                    'contribution': contribution,
                    'consensus_i': consensus_i,
                    'consensus_j': consensus_j,
                    'lambda_ij': lambda_ij,
                    'offset_rate': offset_rate,
                })

    # 寄与の大きい順にソート
    energy_contributions.sort(key=lambda x: -x['contribution'])

    # 正規化されたエネルギー
    E = total_energy_unnormalized / normalization_factor if normalization_factor > 0 else 0.0

    return {
        'E': E,
        'total_energy_unnormalized': total_energy_unnormalized,
        'normalization_factor': normalization_factor,
        'energy_contributions': energy_contributions,
        'inner_product_matrix': C.tolist(),
        'cos_theta_matrix': cos_theta.tolist(),
        'norms': norms.tolist(),
        'performance_ids': [perf_id_map.get(pid, pid) for pid in perf_ids],
        'performance_labels': perf_labels,
        'metadata': {
            'n_performances': n_perf,
            'n_tradeoff_pairs': n_tradeoff_pairs,
            'total_weight': float(total_weight),
            'spectral_radius': total_effect.get('spectral_radius', 0.0),
            'convergence': total_effect.get('convergence', True),
        }
    }


def compute_structural_energy_for_case(
    network: Dict,
    performance_weights: Dict[str, float],
    classic_energy: Optional[float] = None,
    performance_deltas: Dict[str, float] = None
) -> Dict:
    """
    設計案のエネルギーを計算（従来エネルギーとの比較用）

    Args:
        network: ネットワーク構造
        performance_weights: 性能の重み
        classic_energy: 従来のエネルギー値（比較用、オプション）
        performance_deltas: 性能の正味方向票 {performance_id: δ_i}

    Returns:
        compute_structural_energy の結果 + classic_energy との比較
    """
    result = compute_structural_energy(
        network, performance_weights,
        performance_deltas=performance_deltas
    )

    if classic_energy is not None:
        result['comparison'] = {
            'paper_energy': result['E'],
            'classic_energy': classic_energy,
            'difference': result['E'] - classic_energy,
        }

    return result


def _empty_result() -> Dict:
    """空の結果を返す（性能がない場合など）"""
    return {
        'E': 0.0,
        'total_energy_unnormalized': 0.0,
        'normalization_factor': 1.0,
        'energy_contributions': [],
        'inner_product_matrix': [],
        'cos_theta_matrix': [],
        'norms': [],
        'performance_ids': [],
        'performance_labels': [],
        'metadata': {
            'n_performances': 0,
            'n_tradeoff_pairs': 0,
            'total_weight': 0.0,
            'spectral_radius': 0.0,
            'convergence': True,
        }
    }


# =============================================================================
# 標高計算（論文Chapter 7 式5759）
# =============================================================================

def compute_structural_height(
    utility_vector: Dict[str, float],
    performance_weights: Dict[str, float]
) -> Dict:
    """
    論文Chapter 7の定義に従う標高計算

    H = Σ(W_i × U_i) / Σ(W_i)

    Args:
        utility_vector: 効用ベクトル {performance_id: U_i}
        performance_weights: 性能の重み {performance_id: W_i}

    Returns:
        {
            'H': float,  # 標高 (0-1)
            'total_weighted_utility': float,  # Σ(W_i × U_i)
            'total_weight': float,  # Σ W_i
            'partial_heights': Dict[str, float],  # 各性能の寄与
            'breakdown': [
                {
                    'performance_id': str,
                    'U_i': float,
                    'W_i': float,
                    'contribution': float,  # W_i × U_i
                    'percentage': float,  # 全体に占める割合
                }
            ]
        }
    """
    breakdown = []
    total_weighted_utility = 0.0
    total_weight = 0.0
    partial_heights = {}

    for perf_id, U_i in utility_vector.items():
        W_i = performance_weights.get(perf_id, 0.0)
        contribution = W_i * U_i

        total_weighted_utility += contribution
        total_weight += W_i

        breakdown.append({
            'performance_id': perf_id,
            'U_i': U_i,
            'W_i': W_i,
            'contribution': contribution,
        })

    # 標高 H
    H = total_weighted_utility / total_weight if total_weight > 0 else 0.0

    # 各性能の寄与率
    for item in breakdown:
        if total_weighted_utility > 0:
            item['percentage'] = (item['contribution'] / total_weighted_utility) * 100
        else:
            item['percentage'] = 0.0
        partial_heights[item['performance_id']] = item['contribution']

    # 寄与の大きい順にソート
    breakdown.sort(key=lambda x: -x['contribution'])

    return {
        'H': H,
        'total_weighted_utility': total_weighted_utility,
        'total_weight': total_weight,
        'partial_heights': partial_heights,
        'breakdown': breakdown,
    }
