# backend/app/services/matrix_utils.py
"""
行列計算ユーティリティ

論文(design.tex)の理論に基づく構造的トレードオフ分析の基盤
- PAVE構造（Performance-Attribute-Variable-Entity）の行列表現
- 総効果行列の計算
- 構造的トレードオフ指標（cos θ）の計算
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# 統一重み正規化モジュールをインポート
from app.services.weight_normalization import (
    normalize_weight as _normalize_weight_impl,
    discrete_to_continuous,
    WEIGHT_SCHEMES,
    WeightModeType
)


# =============================================================================
# 定数・マッピング
# =============================================================================

# レイヤー番号 → PAVEカテゴリ
LAYER_TO_PAVE = {
    1: 'P',  # Performance（性能）
    2: 'A',  # Attribute（属性）= Property
    3: 'V',  # Variable（変数）
    4: 'E',  # Entity（実体）= Object/Environment
}

# 後方互換性のため、旧定数も維持（非推奨）
# 新コードでは weight_normalization.py を直接使用すること
DISCRETE_TO_CONTINUOUS = WEIGHT_SCHEMES['discrete_5']['discrete_values'] and {
    d: c for d, c in zip(
        WEIGHT_SCHEMES['discrete_5']['discrete_values'],
        WEIGHT_SCHEMES['discrete_5']['continuous_values']
    )
} or {}


# =============================================================================
# Step 1: 隣接行列の構築
# =============================================================================

def normalize_weight(weight: float, mode: WeightModeType = 'discrete_7') -> float:
    """
    離散値weightを連続値 (-1~+1) に正規化

    論文6章: 各離散化スキームの均等分割
    - 3段階: {-1, 0, +1} → {-2/3, 0, +2/3}
    - 5段階: {-3, -1, 0, +1, +3} → {-4/5, -2/5, 0, +2/5, +4/5}
    - 7段階: {-5, -3, -1, 0, +1, +3, +5} → {-6/7, -4/7, -2/7, 0, +2/7, +4/7, +6/7}

    Args:
        weight: エッジの重み（離散値または連続値）
        mode: 離散化モード ('discrete_3', 'discrete_5', 'discrete_7', 'continuous')

    Returns:
        正規化された重み（-1.0 ~ +1.0）
    """
    return _normalize_weight_impl(weight, mode)


def build_adjacency_matrices(network: Dict, weight_mode: WeightModeType = 'discrete_7') -> Dict:
    """
    ネットワークから隣接行列を構築

    論文5.2節のPAVE構造に対応:
    - B_PA: Attribute → Performance への直接効果行列
    - B_AA: Attribute → Attribute への相互作用行列
    - B_AV: Variable → Attribute への直接効果行列

    Args:
        network: ネットワーク構造 {'nodes': [...], 'edges': [...]}

    Returns:
        {
            'B_PA': np.ndarray,  # (n_perf × n_attr)
            'B_AA': np.ndarray,  # (n_attr × n_attr)
            'B_AV': np.ndarray,  # (n_attr × n_var)
            'node_ids': {
                'P': List[str],  # Performance node IDs
                'A': List[str],  # Attribute (Property) node IDs
                'V': List[str],  # Variable node IDs
            },
            'node_labels': {
                'P': List[str],
                'A': List[str],
                'V': List[str],
            },
            'performance_id_map': Dict[str, str],  # node_id → performance_id
        }
    """
    nodes = network.get('nodes', [])
    edges = network.get('edges', [])

    # ノードをレイヤーごとに分類
    p_nodes = []  # Performance (layer 1)
    a_nodes = []  # Attribute/Property (layer 2)
    v_nodes = []  # Variable (layer 3)

    for node in nodes:
        layer = node.get('layer', 0)
        if layer == 1:
            p_nodes.append(node)
        elif layer == 2:
            a_nodes.append(node)
        elif layer == 3:
            v_nodes.append(node)
        # layer 4 (Entity) は総効果行列の計算には直接使わない

    # ノード数
    n_perf = len(p_nodes)
    n_attr = len(a_nodes)
    n_var = len(v_nodes)

    # ノードIDのリスト
    p_ids = [n['id'] for n in p_nodes]
    a_ids = [n['id'] for n in a_nodes]
    v_ids = [n['id'] for n in v_nodes]

    # ノードラベルのリスト
    p_labels = [n.get('label', n['id']) for n in p_nodes]
    a_labels = [n.get('label', n['id']) for n in a_nodes]
    v_labels = [n.get('label', n['id']) for n in v_nodes]

    # performance_id マッピング（node_id → performance_id）
    perf_id_map = {}
    for node in p_nodes:
        perf_id_map[node['id']] = node.get('performance_id', node['id'])

    # IDからインデックスへのマッピング
    p_idx = {node_id: i for i, node_id in enumerate(p_ids)}
    a_idx = {node_id: i for i, node_id in enumerate(a_ids)}
    v_idx = {node_id: i for i, node_id in enumerate(v_ids)}

    # 行列の初期化
    B_PA = np.zeros((n_perf, n_attr)) if n_perf > 0 and n_attr > 0 else np.array([])
    B_AA = np.zeros((n_attr, n_attr)) if n_attr > 0 else np.array([])
    B_AV = np.zeros((n_attr, n_var)) if n_attr > 0 and n_var > 0 else np.array([])

    # エッジから行列を構築
    for edge in edges:
        source_id = edge.get('source_id')
        target_id = edge.get('target_id')
        weight = edge.get('weight', 0)

        if weight == 0:
            continue

        # 重みを正規化（設計案のweight_modeを使用）
        normalized_weight = normalize_weight(weight, weight_mode)

        # エッジの方向を判定して適切な行列に格納
        # PAVEモデルに準拠した有効なエッジのみ処理
        # 無効なエッジ (P→X, V→V, A→V, V→P, E→A, E→P) は無視される
        #
        # Attribute → Performance (A→P)
        if source_id in a_idx and target_id in p_idx:
            B_PA[p_idx[target_id], a_idx[source_id]] = normalized_weight

        # Attribute → Attribute (A→A, ループ構造)
        elif source_id in a_idx and target_id in a_idx:
            B_AA[a_idx[target_id], a_idx[source_id]] = normalized_weight

        # Variable → Attribute (V→A)
        elif source_id in v_idx and target_id in a_idx:
            B_AV[a_idx[target_id], v_idx[source_id]] = normalized_weight

        # その他のエッジは無視（V→V, A→V, P→X, E→X 等）
        # バリデーションは NetworkEditor.vue と data_migration.py で実施

    return {
        'B_PA': B_PA,
        'B_AA': B_AA,
        'B_AV': B_AV,
        'node_ids': {
            'P': p_ids,
            'A': a_ids,
            'V': v_ids,
        },
        'node_labels': {
            'P': p_labels,
            'A': a_labels,
            'V': v_labels,
        },
        'performance_id_map': perf_id_map,
        'dimensions': {
            'n_perf': n_perf,
            'n_attr': n_attr,
            'n_var': n_var,
        }
    }


# =============================================================================
# Step 2: 総効果行列の計算
# =============================================================================

def compute_total_effect_matrix(
    B_PA: np.ndarray,
    B_AA: np.ndarray,
    B_AV: np.ndarray,
    max_iterations: int = 100
) -> Dict:
    """
    総効果行列 T = B_PA × (I - B_AA)^(-1) × B_AV を計算

    論文5.2節の式に対応:
    - (I - B_AA)^(-1) は Neumann級数展開 I + B_AA + B_AA² + ... で計算可能
    - スペクトル半径 ρ(B_AA) < 1 で収束

    Args:
        B_PA: Attribute → Performance への直接効果行列 (n_perf × n_attr)
        B_AA: Attribute → Attribute への相互作用行列 (n_attr × n_attr)
        B_AV: Variable → Attribute への直接効果行列 (n_attr × n_var)
        max_iterations: Neumann級数の最大反復回数

    Returns:
        {
            'T': np.ndarray,  # 総効果行列 (n_perf × n_var)
            'spectral_radius': float,  # B_AAのスペクトル半径
            'convergence': bool,  # 収束したか
            'method': str,  # 計算方法 ('inverse' or 'neumann')
            'iterations': int,  # 使用した反復回数（Neumannの場合）
        }
    """
    # 空行列のチェック
    if B_PA.size == 0 or B_AV.size == 0:
        n_perf = B_PA.shape[0] if B_PA.size > 0 else 0
        n_var = B_AV.shape[1] if B_AV.size > 0 else 0
        return {
            'T': np.zeros((n_perf, n_var)),
            'spectral_radius': 0.0,
            'convergence': True,
            'method': 'empty',
            'iterations': 0,
        }

    n_attr = B_AA.shape[0] if B_AA.size > 0 else 0

    # B_AAが空または零行列の場合
    if n_attr == 0 or np.allclose(B_AA, 0):
        # (I - B_AA)^(-1) = I なので T = B_PA × B_AV
        T = B_PA @ B_AV
        return {
            'T': T,
            'spectral_radius': 0.0,
            'convergence': True,
            'method': 'direct',
            'iterations': 0,
        }

    I = np.eye(n_attr)

    # スペクトル半径の計算
    try:
        eigenvalues = np.linalg.eigvals(B_AA)
        spectral_radius = np.max(np.abs(eigenvalues))
    except np.linalg.LinAlgError:
        spectral_radius = float('inf')

    # 収束条件: ρ(B_AA) < 1
    convergence = spectral_radius < 1.0

    if convergence:
        # 直接逆行列を計算
        try:
            inv_term = np.linalg.inv(I - B_AA)
            T = B_PA @ inv_term @ B_AV
            return {
                'T': T,
                'spectral_radius': float(spectral_radius),
                'convergence': True,
                'method': 'inverse',
                'iterations': 0,
            }
        except np.linalg.LinAlgError:
            pass  # 特異行列の場合はNeumann級数にフォールバック

    # Neumann級数による近似: (I - B_AA)^(-1) ≈ I + B_AA + B_AA² + ...
    sum_matrix = I.copy()
    power_matrix = B_AA.copy()

    for iteration in range(1, max_iterations + 1):
        sum_matrix += power_matrix
        power_matrix = power_matrix @ B_AA

        # 収束判定
        if np.max(np.abs(power_matrix)) < 1e-10:
            break

    T = B_PA @ sum_matrix @ B_AV

    return {
        'T': T,
        'spectral_radius': float(spectral_radius),
        'convergence': convergence,
        'method': 'neumann',
        'iterations': iteration,
    }


# =============================================================================
# Step 3: 内積行列・構造的トレードオフ指標の計算
# =============================================================================

def compute_inner_products(T: np.ndarray) -> Dict:
    """
    総効果行列から内積行列を計算（論文Chapter 7のエネルギー計算用）

    論文5788行の重要な指摘:
    > 些細なトレードオフ（cos θ ≈ -1 だがノルムが小さい）と
    > 重大なトレードオフ（ノルムも大きい）を区別するため、
    > エネルギーの計算には内積 C_ij を用いる

    C_ij = ⟨T_i·, T_j·⟩ = ||T_i·|| × ||T_j·|| × cos θ_ij

    Args:
        T: 総効果行列 (n_perf × n_var)

    Returns:
        {
            'C': np.ndarray,  # 内積行列 C_ij = T_i· · T_j· (n_perf × n_perf)
            'norms': np.ndarray,  # 各行のノルム ||T_i·|| (n_perf,)
            'cos_theta': np.ndarray,  # 正規化された cos θ (n_perf × n_perf)
        }
    """
    if T.size == 0:
        return {
            'C': np.array([]),
            'norms': np.array([]),
            'cos_theta': np.array([]),
        }

    n_perf = T.shape[0]

    # 各行のノルムを計算
    norms = np.linalg.norm(T, axis=1)

    # 内積行列 C_ij = T_i · T_j (正規化なし)
    # 効率的に計算: C = T @ T.T
    C = T @ T.T

    # cos θ 行列（正規化版）
    cos_theta = np.zeros((n_perf, n_perf))
    for i in range(n_perf):
        for j in range(n_perf):
            if norms[i] > 1e-10 and norms[j] > 1e-10:
                cos_theta[i, j] = C[i, j] / (norms[i] * norms[j])
            elif i == j:
                cos_theta[i, j] = 1.0  # 自分自身
            else:
                cos_theta[i, j] = 0.0  # 効果なし→独立

    return {
        'C': C,
        'norms': norms,
        'cos_theta': cos_theta,
    }


def compute_structural_tradeoff(T: np.ndarray) -> Dict:
    """
    総効果行列から構造的トレードオフ行列を計算

    論文5.2節の定理5.1:
    cos θ_ij = (T_i· · T_j·) / (||T_i·|| × ||T_j·||)

    - cos θ < 0: トレードオフ関係
    - cos θ ≈ 0: 独立関係
    - cos θ > 0: 協調関係（シナジー）

    Args:
        T: 総効果行列 (n_perf × n_var)

    Returns:
        {
            'cos_theta': np.ndarray,  # (n_perf × n_perf) の対称行列
            'interpretations': List[List[str]],  # 解釈ラベルの行列
            'tradeoff_pairs': List[Dict],  # トレードオフペアのリスト
        }
    """
    if T.size == 0:
        return {
            'cos_theta': np.array([]),
            'interpretations': [],
            'tradeoff_pairs': [],
        }

    n_perf = T.shape[0]
    cos_theta = np.zeros((n_perf, n_perf))
    interpretations = [['' for _ in range(n_perf)] for _ in range(n_perf)]

    # ノルムを事前計算
    norms = np.linalg.norm(T, axis=1)

    for i in range(n_perf):
        for j in range(n_perf):
            if i == j:
                cos_theta[i, j] = 1.0
                interpretations[i][j] = 'self'
            elif norms[i] > 1e-10 and norms[j] > 1e-10:
                cos_theta[i, j] = np.dot(T[i, :], T[j, :]) / (norms[i] * norms[j])
                interpretations[i][j] = _interpret_cos_theta(cos_theta[i, j])
            else:
                cos_theta[i, j] = 0.0
                interpretations[i][j] = 'undefined'

    # トレードオフペアを抽出
    tradeoff_pairs = []
    for i in range(n_perf):
        for j in range(i + 1, n_perf):
            if cos_theta[i, j] < 0:
                tradeoff_pairs.append({
                    'i': i,
                    'j': j,
                    'cos_theta': float(cos_theta[i, j]),
                    'interpretation': interpretations[i][j],
                })

    # トレードオフの強い順にソート
    tradeoff_pairs.sort(key=lambda x: x['cos_theta'])

    return {
        'cos_theta': cos_theta,
        'interpretations': interpretations,
        'tradeoff_pairs': tradeoff_pairs,
    }


def _interpret_cos_theta(value: float) -> str:
    """
    cos θ の値を解釈ラベルに変換

    Args:
        value: cos θ の値 (-1 ~ +1)

    Returns:
        解釈ラベル
    """
    if value < -0.7:
        return 'strong_tradeoff'
    elif value < -0.3:
        return 'moderate_tradeoff'
    elif value < 0:
        return 'weak_tradeoff'
    elif value < 0.3:
        return 'independent'
    elif value < 0.7:
        return 'weak_synergy'
    else:
        return 'strong_synergy'


# =============================================================================
# 統合関数
# =============================================================================

def analyze_network_structure(network: Dict, weight_mode: WeightModeType = 'discrete_7') -> Dict:
    """
    ネットワークの構造的トレードオフ分析を実行

    Step 1-3 を統合した便利関数

    Args:
        network: ネットワーク構造 {'nodes': [...], 'edges': [...]}
        weight_mode: 重みモード ('discrete_3', 'discrete_5', 'discrete_7', 'continuous')

    Returns:
        {
            'matrices': {...},  # build_adjacency_matrices の結果
            'total_effect': {...},  # compute_total_effect_matrix の結果
            'inner_products': {...},  # compute_inner_products の結果（内積 C_ij）
            'tradeoff': {...},  # compute_structural_tradeoff の結果
            'summary': {
                'n_performances': int,
                'n_tradeoff_pairs': int,
                'strongest_tradeoff': Dict or None,
            }
        }
    """
    # Step 1: 隣接行列の構築
    matrices = build_adjacency_matrices(network, weight_mode)

    # Step 2: 総効果行列の計算
    total_effect = compute_total_effect_matrix(
        matrices['B_PA'],
        matrices['B_AA'],
        matrices['B_AV']
    )

    # Step 3a: 内積行列の計算（論文Chapter 7のエネルギー計算用）
    inner_products = compute_inner_products(total_effect['T'])

    # Step 3b: 構造的トレードオフの計算（cos θ）
    tradeoff = compute_structural_tradeoff(total_effect['T'])

    # サマリー
    n_perf = matrices['dimensions']['n_perf']
    tradeoff_pairs = tradeoff['tradeoff_pairs']

    summary = {
        'n_performances': n_perf,
        'n_tradeoff_pairs': len(tradeoff_pairs),
        'strongest_tradeoff': tradeoff_pairs[0] if tradeoff_pairs else None,
    }

    # ノード情報をトレードオフペアに追加
    for pair in tradeoff_pairs:
        pair['perf_i_id'] = matrices['node_ids']['P'][pair['i']]
        pair['perf_j_id'] = matrices['node_ids']['P'][pair['j']]
        pair['perf_i_label'] = matrices['node_labels']['P'][pair['i']]
        pair['perf_j_label'] = matrices['node_labels']['P'][pair['j']]
        # performance_id も追加
        pair['perf_i_performance_id'] = matrices['performance_id_map'].get(pair['perf_i_id'])
        pair['perf_j_performance_id'] = matrices['performance_id_map'].get(pair['perf_j_id'])
        # 内積 C_ij も追加（エネルギー計算用）
        i, j = pair['i'], pair['j']
        if inner_products['C'].size > 0:
            pair['inner_product'] = float(inner_products['C'][i, j])
            pair['norm_i'] = float(inner_products['norms'][i])
            pair['norm_j'] = float(inner_products['norms'][j])

    return {
        'matrices': matrices,
        'total_effect': total_effect,
        'inner_products': inner_products,
        'tradeoff': tradeoff,
        'summary': summary,
    }
