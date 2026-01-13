# backend/app/services/discretization_confidence.py
"""
離散化信頼度計算モジュール

論文(design.tex) Chapter 6 の理論に基づく符号保存確率・順序保存確率の計算

主要な公式（Theorem 6.9, 6.10）:
- 符号保存確率: P_sign = Φ(|C̃_ij| / σ_δC)
- 順序保存確率: P_order = Φ(|Δ̃| / σ_δΔ)

ここで:
- σ_eff = (1/√(3n)) × √(2/3 × l × d²)
  - n: 離散化段階数 (3, 5, 7)
  - l: 属性(Property)の数
  - d: 属性ノードの平均次数
- C̃_ij = T̃_i · T̃_j (離散内積)
- σ_δC = σ_eff × √(||T̃_i||² + ||T̃_j||²)
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple
from app.services.matrix_utils import (
    build_adjacency_matrices,
    compute_total_effect_matrix,
    compute_inner_products,
)
from app.services.weight_normalization import WEIGHT_SCHEMES, WeightModeType


def compute_sigma_eff(
    n_discrete_levels: int,
    n_attributes: int,
    connection_density: float,
    B_AA_frobenius_norm: float = 0.0
) -> float:
    """
    有効誤差 σ_eff を計算

    論文 design.tex の式:
    - B_AA = 0 の場合: σ_eff = σ_ε × √(2/3 × l × d²)
    - B_AA ≠ 0 の場合: σ_eff = σ_ε × √(2/3 × l × d² × (1 + ||B_AA||_F²))

    ここで σ_ε = 1/(√3 × n) は離散化誤差の標準偏差

    Args:
        n_discrete_levels: 離散化段階数 n (3, 5, 7)
        n_attributes: 属性(Attribute)の数 l
        connection_density: 接続密度 d = 存在するエッジ数 / 可能なエッジ数 [0, 1]
        B_AA_frobenius_norm: B_AA行列のフロベニウスノルム ||B_AA||_F

    Returns:
        有効誤差 σ_eff
    """
    if n_discrete_levels <= 0 or n_attributes <= 0 or connection_density <= 0:
        return 0.0

    # σ_ε = 1/(√3 × n) - 離散化誤差の標準偏差
    sigma_epsilon = 1.0 / (np.sqrt(3) * n_discrete_levels)

    # 基本項: 2/3 × l × d²
    base_term = (2.0 / 3.0) * n_attributes * (connection_density ** 2)

    # ループ補正係数: (1 + ||B_AA||_F²)
    loop_factor = 1.0 + B_AA_frobenius_norm ** 2

    # σ_eff = σ_ε × √(base_term × loop_factor)
    return sigma_epsilon * np.sqrt(base_term * loop_factor)


def compute_connection_density(network: Dict) -> float:
    """
    接続密度（connection density）を計算

    d = 存在するエッジ数 / 可能なエッジ数

    可能なエッジ数（PAVEモデル）:
    - A → P: |A| × |P|
    - A → A: |A| × |A|
    - V → A: |V| × |A|

    Args:
        network: ネットワーク構造 {'nodes': [...], 'edges': [...]}

    Returns:
        接続密度 d [0, 1]
    """
    nodes = network.get('nodes', [])
    edges = network.get('edges', [])

    # ノードをレイヤー別にカウント・収集
    p_ids = {n['id'] for n in nodes if n.get('layer') == 1}
    a_ids = {n['id'] for n in nodes if n.get('layer') == 2}
    v_ids = {n['id'] for n in nodes if n.get('layer') == 3}

    n_p = len(p_ids)
    n_a = len(a_ids)
    n_v = len(v_ids)

    if n_a == 0:
        return 0.0

    # 可能なエッジ数
    possible_AP = n_a * n_p
    possible_AA = n_a * n_a
    possible_VA = n_v * n_a
    total_possible = possible_AP + possible_AA + possible_VA

    if total_possible == 0:
        return 0.0

    # 実際のエッジ数（weight != 0）
    actual_count = 0
    for edge in edges:
        weight = edge.get('weight', 0)
        if weight == 0:
            continue

        source_id = edge.get('source_id')
        target_id = edge.get('target_id')

        # PAVEモデルの有効エッジのみカウント
        if source_id in a_ids and target_id in p_ids:
            actual_count += 1
        elif source_id in a_ids and target_id in a_ids:
            actual_count += 1
        elif source_id in v_ids and target_id in a_ids:
            actual_count += 1

    return actual_count / total_possible


def compute_sign_preservation_for_pair(
    C_ij: float,
    norm_i: float,
    norm_j: float,
    sigma_eff: float
) -> float:
    """
    ペア(i, j)の符号保存確率を計算

    P_sign = Φ(|C̃_ij| / σ_δC)
    where σ_δC = σ_eff × √(||T̃_i||² + ||T̃_j||²)

    Args:
        C_ij: 離散内積 C̃_ij = T̃_i · T̃_j
        norm_i: ||T̃_i||
        norm_j: ||T̃_j||
        sigma_eff: 有効誤差 σ_eff

    Returns:
        符号保存確率 [0, 1]
    """
    if sigma_eff <= 0:
        return 1.0  # 誤差なし → 確実に保存

    norm_sum_sq = norm_i ** 2 + norm_j ** 2
    if norm_sum_sq <= 0:
        return 1.0  # 効果なし → 保存

    sigma_delta_C = sigma_eff * np.sqrt(norm_sum_sq)

    if sigma_delta_C <= 0:
        return 1.0

    # P_sign = Φ(|C̃_ij| / σ_δC)
    z = abs(C_ij) / sigma_delta_C
    return float(stats.norm.cdf(z))


def compute_order_preservation_for_pairs(
    C_p1: float,
    C_p2: float,
    norm_i1: float,
    norm_j1: float,
    norm_i2: float,
    norm_j2: float,
    sigma_eff: float
) -> float:
    """
    2つのペア間の順序保存確率を計算

    P_order = Φ(|Δ̃| / σ_δΔ)
    where Δ̃ = C̃_p1 - C̃_p2
    and σ_δΔ² ≈ σ_eff² × (||T̃_i1||² + ||T̃_j1||² + ||T̃_i2||² + ||T̃_j2||²)

    Args:
        C_p1: ペア1の内積
        C_p2: ペア2の内積
        norm_i1, norm_j1: ペア1のノルム
        norm_i2, norm_j2: ペア2のノルム
        sigma_eff: 有効誤差

    Returns:
        順序保存確率 [0, 1]
    """
    if sigma_eff <= 0:
        return 1.0

    delta = abs(C_p1 - C_p2)
    norm_sum_sq = norm_i1**2 + norm_j1**2 + norm_i2**2 + norm_j2**2

    if norm_sum_sq <= 0:
        return 1.0

    sigma_delta = sigma_eff * np.sqrt(norm_sum_sq)

    if sigma_delta <= 0:
        return 1.0

    z = delta / sigma_delta
    return float(stats.norm.cdf(z))


def analyze_discretization_confidence(
    network: Dict,
    weight_mode: WeightModeType = 'discrete_7'
) -> Dict:
    """
    ネットワークの離散化信頼度を分析

    Args:
        network: ネットワーク構造
        weight_mode: 重みモード

    Returns:
        {
            'is_discrete': bool,
            'n_discrete_levels': int | None,
            'sigma_eff': float,
            'n_attributes': int,
            'connection_density': float,
            'sign_preservation': {
                'average': float,  # 全ペアの平均符号保存確率
                'min': float,      # 最小値
                'max': float,      # 最大値
                'per_pair': List[Dict],  # 各ペアの詳細
            },
            'order_preservation': {
                'average': float,  # 全ペア組の平均順序保存確率
            },
            'total_effect_matrix': {...},
            'inner_products': {...},
        }
    """
    if weight_mode == 'continuous':
        return {
            'is_discrete': False,
            'n_discrete_levels': None,
            'sigma_eff': 0.0,
            'n_attributes': 0,
            'connection_density': 0.0,
            'sign_preservation': {
                'average': 1.0,
                'min': 1.0,
                'max': 1.0,
                'per_pair': [],
            },
            'order_preservation': {
                'average': 1.0,
            },
            'interpretation': 'Continuous mode - no discretization error',
        }

    # 離散化段階数を取得
    scheme = WEIGHT_SCHEMES.get(weight_mode, {})
    n_levels = scheme.get('n_levels', 7)

    # ネットワーク構造パラメータ
    nodes = network.get('nodes', [])
    n_attributes = sum(1 for n in nodes if n.get('layer') == 2)
    connection_density = compute_connection_density(network)

    # 総効果行列を計算（σ_eff に B_AA が必要なため先に計算）
    matrices = build_adjacency_matrices(network, weight_mode)
    if matrices['B_PA'].size == 0:
        sigma_eff = compute_sigma_eff(n_levels, n_attributes, connection_density, 0.0)
        return {
            'is_discrete': True,
            'n_discrete_levels': n_levels,
            'sigma_eff': sigma_eff,
            'n_attributes': n_attributes,
            'connection_density': connection_density,
            'sign_preservation': {
                'average': 1.0,
                'min': 1.0,
                'max': 1.0,
                'per_pair': [],
            },
            'order_preservation': {
                'average': 1.0,
            },
            'interpretation': 'No performance-attribute connections',
        }

    # B_AA のフロベニウスノルムを計算
    B_AA = matrices['B_AA']
    B_AA_frobenius_norm = float(np.linalg.norm(B_AA, 'fro'))

    # σ_eff を計算（ループ構造を考慮）
    sigma_eff = compute_sigma_eff(n_levels, n_attributes, connection_density, B_AA_frobenius_norm)

    total_effect = compute_total_effect_matrix(
        matrices['B_PA'],
        matrices['B_AA'],
        matrices['B_AV']
    )
    T = total_effect['T']

    # 内積・ノルムを計算
    inner_products = compute_inner_products(T)
    C = inner_products['C']
    norms = inner_products['norms']
    n_perf = len(norms)

    # 各ペアの符号保存確率を計算
    sign_probs = []
    per_pair_details = []

    for i in range(n_perf):
        for j in range(i + 1, n_perf):
            C_ij = C[i, j]
            prob = compute_sign_preservation_for_pair(
                C_ij, norms[i], norms[j], sigma_eff
            )
            sign_probs.append(prob)

            per_pair_details.append({
                'i': i,
                'j': j,
                'perf_i_id': matrices['node_ids']['P'][i],
                'perf_j_id': matrices['node_ids']['P'][j],
                'perf_i_label': matrices['node_labels']['P'][i],
                'perf_j_label': matrices['node_labels']['P'][j],
                'C_ij': float(C_ij),
                'norm_i': float(norms[i]),
                'norm_j': float(norms[j]),
                'sign_preservation_prob': prob,
            })

    # 順序保存確率（ペアの組み合わせ）
    order_probs = []
    n_pairs = len(per_pair_details)

    for p1_idx in range(n_pairs):
        for p2_idx in range(p1_idx + 1, n_pairs):
            p1 = per_pair_details[p1_idx]
            p2 = per_pair_details[p2_idx]

            prob = compute_order_preservation_for_pairs(
                p1['C_ij'], p2['C_ij'],
                p1['norm_i'], p1['norm_j'],
                p2['norm_i'], p2['norm_j'],
                sigma_eff
            )
            order_probs.append(prob)

    # 統計
    avg_sign = np.mean(sign_probs) if sign_probs else 1.0
    min_sign = min(sign_probs) if sign_probs else 1.0
    max_sign = max(sign_probs) if sign_probs else 1.0
    avg_order = np.mean(order_probs) if order_probs else 1.0

    # 解釈
    if avg_sign >= 0.95:
        interpretation = f'{n_levels}-level discretization has high reliability (P_sign ≥ 95%)'
    elif avg_sign >= 0.85:
        interpretation = f'{n_levels}-level discretization is generally reliable (P_sign ≥ 85%)'
    elif avg_sign >= 0.70:
        interpretation = 'Consider using more levels or continuous mode (P_sign < 85%)'
    else:
        interpretation = 'Low precision - recommend using continuous mode (P_sign < 70%)'

    return {
        'is_discrete': True,
        'n_discrete_levels': n_levels,
        'sigma_eff': float(sigma_eff),
        'n_attributes': n_attributes,
        'connection_density': float(connection_density),
        'B_AA_frobenius_norm': float(B_AA_frobenius_norm),
        'sign_preservation': {
            'average': float(avg_sign),
            'min': float(min_sign),
            'max': float(max_sign),
            'per_pair': per_pair_details,
        },
        'order_preservation': {
            'average': float(avg_order),
        },
        'interpretation': interpretation,
        'metadata': {
            'n_performances': n_perf,
            'n_pairs': len(per_pair_details),
            'n_pair_combinations': len(order_probs),
            'spectral_radius': total_effect['spectral_radius'],
            'convergence': total_effect['convergence'],
        }
    }


def compute_project_discretization_confidence(
    design_cases: List[Dict],
    default_weight_mode: WeightModeType = 'discrete_7'
) -> Dict:
    """
    プロジェクト全体の離散化信頼度を計算

    Args:
        design_cases: 設計案のリスト [{'network': {...}, 'weight_mode': str, ...}, ...]
        default_weight_mode: デフォルトの重みモード

    Returns:
        {
            'weight_modes': Dict[str, int],
            'primary_mode': str,
            'is_discrete': bool,
            'n_discrete_levels': int | None,
            'sign_preservation_probability': float,  # プロジェクト全体の平均
            'order_preservation_probability': float,
            'min_sign_preservation': float,
            'n_networks': int,
            'interpretation': str,
            'per_case': List[Dict],  # 各設計案の詳細
        }
    """
    if not design_cases:
        return {
            'weight_modes': {},
            'primary_mode': None,
            'is_discrete': False,
            'n_discrete_levels': None,
            'sign_preservation_probability': None,
            'order_preservation_probability': None,
            'min_sign_preservation': None,
            'n_networks': 0,
            'interpretation': 'No design cases',
            'per_case': [],
        }

    # 各設計案のweight_modeを集計
    weight_modes = {}
    per_case_results = []
    all_sign_probs = []
    all_order_probs = []

    for case in design_cases:
        mode = case.get('weight_mode') or default_weight_mode
        weight_modes[mode] = weight_modes.get(mode, 0) + 1

        network = case.get('network')
        if network:
            result = analyze_discretization_confidence(network, mode)
            result['case_id'] = case.get('id')
            result['case_name'] = case.get('name')
            per_case_results.append(result)

            if result['sign_preservation']['per_pair']:
                all_sign_probs.append(result['sign_preservation']['average'])
            if result['order_preservation']['average'] is not None:
                all_order_probs.append(result['order_preservation']['average'])

    # 最も多いモードを代表として使用
    primary_mode = max(weight_modes, key=weight_modes.get)
    is_discrete = primary_mode != 'continuous'

    if is_discrete:
        scheme = WEIGHT_SCHEMES.get(primary_mode, {})
        n_levels = scheme.get('n_levels')
    else:
        n_levels = None

    # 全体統計
    avg_sign = np.mean(all_sign_probs) if all_sign_probs else 1.0
    min_sign = min(all_sign_probs) if all_sign_probs else 1.0
    avg_order = np.mean(all_order_probs) if all_order_probs else 1.0

    # 解釈
    if not is_discrete:
        interpretation = 'Continuous mode - no discretization error'
    elif avg_sign >= 0.95:
        interpretation = f'{n_levels}-level discretization has high reliability'
    elif avg_sign >= 0.85:
        interpretation = f'{n_levels}-level discretization is generally reliable'
    elif avg_sign >= 0.70:
        interpretation = 'Consider using more levels or continuous mode'
    else:
        interpretation = 'Low precision - recommend using continuous mode'

    return {
        'weight_modes': weight_modes,
        'primary_mode': primary_mode,
        'is_discrete': is_discrete,
        'n_discrete_levels': n_levels,
        'sign_preservation_probability': float(avg_sign) if all_sign_probs else None,
        'order_preservation_probability': float(avg_order) if all_order_probs else None,
        'min_sign_preservation': float(min_sign) if all_sign_probs else None,
        'n_networks': len(design_cases),
        'interpretation': interpretation,
        'per_case': per_case_results,
    }
