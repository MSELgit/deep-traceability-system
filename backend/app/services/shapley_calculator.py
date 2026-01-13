# backend/app/services/shapley_calculator.py
"""
Shapley値によるトレードオフ寄与度分解

論文 design.tex 2849-2913行に基づく実装:
- 協力ゲーム理論に基づくShapley値の計算
- トレードオフ指標 C_ij を各属性の寄与に分解
- 計算量 O(2^l) の厳密計算とMonte Carlo近似
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
import numpy as np
import time
import random
import math


@dataclass
class ShapleyResult:
    """Shapley値計算の結果（レガシー: V のみがプレイヤー）"""
    perf_i_idx: int
    perf_j_idx: int
    C_ij: float
    cos_theta: float
    shapley_values: Dict[int, float]  # property_idx -> phi_k
    sum_check: float  # Σφ_k （= C_ij になるはず）
    computation_method: str  # 'exact' or 'monte_carlo'
    computation_time_ms: float
    n_properties: int


@dataclass
class NodeInfo:
    """ノード情報（V ∪ A のプレイヤー）"""
    node_id: str
    node_label: str
    node_type: str  # 'V' (Variable) or 'A' (Attribute)
    layer: int  # 2=Attribute, 3=Variable
    matrix_idx: int  # V or A の行列内インデックス


@dataclass
class NodeShapleyResult:
    """ノードShapley値計算の結果（V ∪ A がプレイヤー）"""
    perf_i_idx: int
    perf_j_idx: int
    C_ij: float
    cos_theta: float
    node_shapley_values: Dict[str, float]  # node_id -> phi
    sum_check: float
    computation_method: str
    computation_time_ms: float
    n_nodes: int  # |V| + |A|
    n_variables: int  # |V|
    n_attributes: int  # |A|


def compute_partial_tradeoff(
    T: np.ndarray,
    perf_i: int,
    perf_j: int,
    subset: Set[int]
) -> float:
    """
    部分集合のみを考慮したトレードオフ指標 C_ij(S) を計算

    Args:
        T: 総効果行列 (n_perf × n_vars)
        perf_i, perf_j: 性能のインデックス
        subset: 考慮する属性（変数）のインデックス集合

    Returns:
        C_ij(S) = Σ_{k∈S} T_ik × T_jk
    """
    if not subset:
        return 0.0

    T_i = T[perf_i, :]
    T_j = T[perf_j, :]

    # 部分集合のみで内積を計算
    subset_list = list(subset)
    partial_inner = np.sum(T_i[subset_list] * T_j[subset_list])

    return float(partial_inner)


def compute_shapley_values_exact(
    T: np.ndarray,
    perf_i: int,
    perf_j: int
) -> Dict[int, float]:
    r"""
    Shapley値の厳密計算

    φ_k = Σ_{S⊆Z\{k}} [|S|!(|Z|-|S|-1)!/|Z|!] × [C_ij(S∪{k}) - C_ij(S)]

    Args:
        T: 総効果行列 (n_perf × n_vars)
        perf_i, perf_j: 性能のインデックス

    Returns:
        {property_idx: shapley_value}
    """
    n_vars = T.shape[1]
    all_vars = set(range(n_vars))
    n = len(all_vars)

    if n == 0:
        return {}

    # 各変数のShapley値を計算
    shapley_values = {}

    # 係数の事前計算
    factorial_n = math.factorial(n)

    for k in all_vars:
        phi_k = 0.0
        others = all_vars - {k}

        # 全ての部分集合 S ⊆ Z \ {k} について
        for size in range(len(others) + 1):
            for S in combinations(others, size):
                S_set = set(S)
                S_with_k = S_set | {k}

                # 限界貢献: C_ij(S∪{k}) - C_ij(S)
                c_with_k = compute_partial_tradeoff(T, perf_i, perf_j, S_with_k)
                c_without_k = compute_partial_tradeoff(T, perf_i, perf_j, S_set)
                marginal = c_with_k - c_without_k

                # Shapley係数: |S|!(n-|S|-1)!/n!
                s = len(S_set)
                coeff = math.factorial(s) * math.factorial(n - s - 1) / factorial_n

                phi_k += coeff * marginal

        shapley_values[k] = phi_k

    return shapley_values


def compute_shapley_values_monte_carlo(
    T: np.ndarray,
    perf_i: int,
    perf_j: int,
    n_samples: int = 1000,
    seed: Optional[int] = None
) -> Dict[int, float]:
    """
    Shapley値のMonte Carlo近似

    ランダムな順列をサンプリングし、各変数の限界貢献を平均化

    Args:
        T: 総効果行列 (n_perf × n_vars)
        perf_i, perf_j: 性能のインデックス
        n_samples: サンプル数
        seed: 乱数シード

    Returns:
        {property_idx: shapley_value}
    """
    if seed is not None:
        random.seed(seed)

    n_vars = T.shape[1]
    if n_vars == 0:
        return {}

    # 各変数の限界貢献の累積
    marginal_sums = {k: 0.0 for k in range(n_vars)}
    counts = {k: 0 for k in range(n_vars)}

    all_vars = list(range(n_vars))

    for _ in range(n_samples):
        # ランダムな順列を生成
        perm = all_vars.copy()
        random.shuffle(perm)

        # 順列に沿って変数を追加していき、限界貢献を計算
        S = set()
        prev_value = 0.0

        for k in perm:
            S_with_k = S | {k}
            curr_value = compute_partial_tradeoff(T, perf_i, perf_j, S_with_k)
            marginal = curr_value - prev_value

            marginal_sums[k] += marginal
            counts[k] += 1

            S = S_with_k
            prev_value = curr_value

    # 平均を計算
    shapley_values = {}
    for k in range(n_vars):
        if counts[k] > 0:
            shapley_values[k] = marginal_sums[k] / counts[k]
        else:
            shapley_values[k] = 0.0

    return shapley_values


def estimate_computation_cost(n_properties: int) -> Dict[str, Any]:
    """
    計算量の見積もり

    Args:
        n_properties: 属性（変数）の数

    Returns:
        計算量情報
    """
    n_subsets = 2 ** n_properties
    # 大まかな時間見積もり（1サブセットあたり約0.01ms）
    estimated_time_ms = n_subsets * 0.01

    if n_properties <= 10:
        warning = "low"
        recommendation = "exact"
    elif n_properties <= 15:
        warning = "medium"
        recommendation = "exact_with_cache"
    else:
        warning = "high"
        recommendation = "monte_carlo"

    return {
        "n_properties": n_properties,
        "n_subsets": n_subsets,
        "estimated_time_ms": estimated_time_ms,
        "warning": warning,
        "recommendation": recommendation,
        "message": f"属性数 {n_properties} に対して {n_subsets:,} 個の部分集合を評価"
    }


def compute_shapley_for_performance_pair(
    T: np.ndarray,
    perf_i: int,
    perf_j: int,
    property_ids: Optional[List[str]] = None,
    method: str = "auto",
    n_monte_carlo_samples: int = 1000
) -> ShapleyResult:
    """
    性能ペアに対するShapley値を計算

    Args:
        T: 総効果行列 (n_perf × n_vars)
        perf_i, perf_j: 性能のインデックス
        property_ids: 属性IDのリスト（オプション）
        method: 'exact', 'monte_carlo', 'auto'
        n_monte_carlo_samples: Monte Carloのサンプル数

    Returns:
        ShapleyResult
    """
    start_time = time.time()

    n_vars = T.shape[1]

    # C_ij と cos θ の計算
    T_i = T[perf_i, :]
    T_j = T[perf_j, :]
    C_ij = float(np.dot(T_i, T_j))

    norm_i = np.linalg.norm(T_i)
    norm_j = np.linalg.norm(T_j)
    if norm_i > 1e-10 and norm_j > 1e-10:
        cos_theta = C_ij / (norm_i * norm_j)
    else:
        cos_theta = 0.0

    # 計算方法の選択
    if method == "auto":
        if n_vars <= 12:
            method = "exact"
        else:
            method = "monte_carlo"

    # Shapley値の計算
    if method == "exact":
        shapley_values = compute_shapley_values_exact(T, perf_i, perf_j)
        computation_method = "exact"
    else:
        shapley_values = compute_shapley_values_monte_carlo(
            T, perf_i, perf_j, n_monte_carlo_samples
        )
        computation_method = "monte_carlo"

    # 合計チェック（Σφ_k = C_ij になるはず）
    sum_check = sum(shapley_values.values())

    elapsed_ms = (time.time() - start_time) * 1000

    return ShapleyResult(
        perf_i_idx=perf_i,
        perf_j_idx=perf_j,
        C_ij=C_ij,
        cos_theta=cos_theta,
        shapley_values=shapley_values,
        sum_check=sum_check,
        computation_method=computation_method,
        computation_time_ms=elapsed_ms,
        n_properties=n_vars
    )


def shapley_result_to_dict(
    result: ShapleyResult,
    performance_names: Optional[List[str]] = None,
    property_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    ShapleyResultを辞書形式に変換（API用）

    Args:
        result: ShapleyResult
        performance_names: 性能名のリスト
        property_names: 属性名のリスト

    Returns:
        API用の辞書
    """
    # 性能情報
    perf_i_name = performance_names[result.perf_i_idx] if performance_names else f"P{result.perf_i_idx}"
    perf_j_name = performance_names[result.perf_j_idx] if performance_names else f"P{result.perf_j_idx}"

    # Shapley値のリスト（寄与度の絶対値でソート）
    shapley_list = []
    total_abs = sum(abs(v) for v in result.shapley_values.values())

    for idx, phi in sorted(result.shapley_values.items(), key=lambda x: -abs(x[1])):
        prop_name = property_names[idx] if property_names and idx < len(property_names) else f"A{idx}"
        percentage = abs(phi) / total_abs * 100 if total_abs > 0 else 0.0

        shapley_list.append({
            "property_idx": idx,
            "property_name": prop_name,
            "phi": phi,
            "abs_phi": abs(phi),
            "percentage": percentage,
            "sign": "positive" if phi > 0 else ("negative" if phi < 0 else "neutral")
        })

    return {
        "perf_i": {
            "idx": result.perf_i_idx,
            "name": perf_i_name
        },
        "perf_j": {
            "idx": result.perf_j_idx,
            "name": perf_j_name
        },
        "C_ij": result.C_ij,
        "cos_theta": result.cos_theta,
        "relationship": "tradeoff" if result.cos_theta < -0.1 else ("synergy" if result.cos_theta > 0.1 else "neutral"),
        "shapley_values": shapley_list,
        "sum_check": result.sum_check,
        "additivity_error": abs(result.sum_check - result.C_ij),
        "computation": {
            "method": result.computation_method,
            "n_properties": result.n_properties,
            "time_ms": result.computation_time_ms
        }
    }


# キャッシュ付きの計算（同じ設計案内で繰り返し呼ばれる場合用）
_shapley_cache: Dict[Tuple[int, int, int], ShapleyResult] = {}


def get_cached_shapley(
    T: np.ndarray,
    perf_i: int,
    perf_j: int,
    cache_key: Optional[int] = None,
    **kwargs
) -> ShapleyResult:
    """
    キャッシュ付きShapley値計算

    Args:
        T: 総効果行列
        perf_i, perf_j: 性能インデックス
        cache_key: キャッシュキー（例: hash of network）
        **kwargs: compute_shapley_for_performance_pair への引数

    Returns:
        ShapleyResult
    """
    if cache_key is not None:
        key = (cache_key, perf_i, perf_j)
        if key in _shapley_cache:
            return _shapley_cache[key]

        result = compute_shapley_for_performance_pair(T, perf_i, perf_j, **kwargs)
        _shapley_cache[key] = result
        return result

    return compute_shapley_for_performance_pair(T, perf_i, perf_j, **kwargs)


def clear_shapley_cache():
    """キャッシュをクリア"""
    global _shapley_cache
    _shapley_cache = {}


def compute_all_pairwise_shapley(
    T: np.ndarray,
    performance_names: Optional[List[str]] = None,
    property_names: Optional[List[str]] = None,
    method: str = "auto",
    only_tradeoffs: bool = True
) -> List[Dict[str, Any]]:
    """
    全ての性能ペアに対するShapley値を計算

    Args:
        T: 総効果行列 (n_perf × n_vars)
        performance_names: 性能名のリスト
        property_names: 属性名のリスト
        method: 計算方法
        only_tradeoffs: Trueの場合、トレードオフ関係（cos θ < 0）のみ

    Returns:
        各ペアのShapley分解結果のリスト
    """
    n_perf = T.shape[0]
    results = []

    for i in range(n_perf):
        for j in range(i + 1, n_perf):
            result = compute_shapley_for_performance_pair(T, i, j, method=method)

            # トレードオフのみの場合、cos θ < 0 のペアだけを含める
            if only_tradeoffs and result.cos_theta >= 0:
                continue

            result_dict = shapley_result_to_dict(result, performance_names, property_names)
            results.append(result_dict)

    # cos θ の絶対値でソート（強いトレードオフ/相乗効果を先に）
    results.sort(key=lambda x: -abs(x['cos_theta']))

    return results


# =============================================================================
# ノードShapley分解（V ∪ A がプレイヤー）
# =============================================================================

def extract_node_info(
    network: Dict,
    matrices: Dict
) -> List[NodeInfo]:
    """
    ネットワークから V ∪ A のノード情報を抽出

    Args:
        network: ネットワーク構造
        matrices: build_adjacency_matrices()の結果

    Returns:
        NodeInfoのリスト（V と A の両方）
    """
    nodes = {n['id']: n for n in network.get('nodes', [])}

    v_ids = matrices['node_ids']['V']
    a_ids = matrices['node_ids']['A']
    v_labels = matrices['node_labels']['V']
    a_labels = matrices['node_labels']['A']

    node_infos = []

    # Variable nodes (layer 3)
    for idx, node_id in enumerate(v_ids):
        node = nodes.get(node_id, {})
        node_infos.append(NodeInfo(
            node_id=node_id,
            node_label=v_labels[idx] if idx < len(v_labels) else node_id,
            node_type='V',
            layer=3,
            matrix_idx=idx
        ))

    # Attribute nodes (layer 2)
    for idx, node_id in enumerate(a_ids):
        node = nodes.get(node_id, {})
        node_infos.append(NodeInfo(
            node_id=node_id,
            node_label=a_labels[idx] if idx < len(a_labels) else node_id,
            node_type='A',
            layer=2,
            matrix_idx=idx
        ))

    return node_infos


def compute_tradeoff_with_node_subset(
    B_PA_full: np.ndarray,
    B_AA_full: np.ndarray,
    B_AV_full: np.ndarray,
    node_infos: List[NodeInfo],
    subset_node_ids: Set[str],
    perf_i: int,
    perf_j: int
) -> float:
    """
    ノードの部分集合のみを有効にしたトレードオフ指標 C_ij(S) を計算

    ノードkが「不存在」とは:
    - k ∈ V: B_AV の k 列を0にする
    - k ∈ A: B_AV の k 行、B_AA の k 行/列、B_PA の k 列を0にする

    Args:
        B_PA_full, B_AA_full, B_AV_full: 元の行列
        node_infos: 全ノード情報
        subset_node_ids: 有効にするノードIDの集合
        perf_i, perf_j: 性能インデックス

    Returns:
        C_ij(S)
    """
    from app.services.matrix_utils import compute_total_effect_matrix

    # 行列をコピー
    B_PA = B_PA_full.copy()
    B_AA = B_AA_full.copy()
    B_AV = B_AV_full.copy()

    # 不存在のノードに対応する行列要素を0にする
    for node in node_infos:
        if node.node_id not in subset_node_ids:
            idx = node.matrix_idx
            if node.node_type == 'V':
                # Variable: B_AV の列を0に
                if idx < B_AV.shape[1]:
                    B_AV[:, idx] = 0
            elif node.node_type == 'A':
                # Attribute: B_AV の行、B_AA の行/列、B_PA の列を0に
                if idx < B_AV.shape[0]:
                    B_AV[idx, :] = 0
                if idx < B_AA.shape[0]:
                    B_AA[idx, :] = 0
                if idx < B_AA.shape[1]:
                    B_AA[:, idx] = 0
                if idx < B_PA.shape[1]:
                    B_PA[:, idx] = 0

    # 総効果行列を計算
    result = compute_total_effect_matrix(B_PA, B_AA, B_AV)
    T = result['T']

    if T.size == 0:
        return 0.0

    # C_ij を計算
    if perf_i < T.shape[0] and perf_j < T.shape[0]:
        T_i = T[perf_i, :]
        T_j = T[perf_j, :]
        return float(np.dot(T_i, T_j))

    return 0.0


def compute_node_shapley_values_exact(
    B_PA: np.ndarray,
    B_AA: np.ndarray,
    B_AV: np.ndarray,
    node_infos: List[NodeInfo],
    perf_i: int,
    perf_j: int
) -> Dict[str, float]:
    """
    ノードShapley値の厳密計算（V ∪ A がプレイヤー）

    φ_k = Σ_{S⊆N\{k}} [|S|!(|N|-|S|-1)!/|N|!] × [C_ij(S∪{k}) - C_ij(S)]

    Args:
        B_PA, B_AA, B_AV: 行列
        node_infos: 全ノード情報
        perf_i, perf_j: 性能インデックス

    Returns:
        {node_id: shapley_value}
    """
    all_node_ids = set(n.node_id for n in node_infos)
    n = len(all_node_ids)

    if n == 0:
        return {}

    factorial_n = math.factorial(n)
    shapley_values = {}

    for node in node_infos:
        node_id = node.node_id
        phi = 0.0
        others = all_node_ids - {node_id}

        for size in range(len(others) + 1):
            for S in combinations(others, size):
                S_set = set(S)
                S_with_node = S_set | {node_id}

                # 限界貢献
                c_with = compute_tradeoff_with_node_subset(
                    B_PA, B_AA, B_AV, node_infos, S_with_node, perf_i, perf_j
                )
                c_without = compute_tradeoff_with_node_subset(
                    B_PA, B_AA, B_AV, node_infos, S_set, perf_i, perf_j
                )
                marginal = c_with - c_without

                # Shapley係数
                s = len(S_set)
                coeff = math.factorial(s) * math.factorial(n - s - 1) / factorial_n

                phi += coeff * marginal

        shapley_values[node_id] = phi

    return shapley_values


def compute_node_shapley_values_monte_carlo(
    B_PA: np.ndarray,
    B_AA: np.ndarray,
    B_AV: np.ndarray,
    node_infos: List[NodeInfo],
    perf_i: int,
    perf_j: int,
    n_samples: int = 500,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    ノードShapley値のMonte Carlo近似（V ∪ A がプレイヤー）

    Args:
        B_PA, B_AA, B_AV: 行列
        node_infos: 全ノード情報
        perf_i, perf_j: 性能インデックス
        n_samples: サンプル数
        seed: 乱数シード

    Returns:
        {node_id: shapley_value}
    """
    if seed is not None:
        random.seed(seed)

    all_node_ids = [n.node_id for n in node_infos]
    n = len(all_node_ids)

    if n == 0:
        return {}

    marginal_sums = {nid: 0.0 for nid in all_node_ids}
    counts = {nid: 0 for nid in all_node_ids}

    for _ in range(n_samples):
        perm = all_node_ids.copy()
        random.shuffle(perm)

        S = set()
        prev_value = 0.0

        for node_id in perm:
            S_with_node = S | {node_id}
            curr_value = compute_tradeoff_with_node_subset(
                B_PA, B_AA, B_AV, node_infos, S_with_node, perf_i, perf_j
            )
            marginal = curr_value - prev_value

            marginal_sums[node_id] += marginal
            counts[node_id] += 1

            S = S_with_node
            prev_value = curr_value

    shapley_values = {}
    for node_id in all_node_ids:
        if counts[node_id] > 0:
            shapley_values[node_id] = marginal_sums[node_id] / counts[node_id]
        else:
            shapley_values[node_id] = 0.0

    return shapley_values


def compute_node_shapley_for_performance_pair(
    network: Dict,
    matrices: Dict,
    perf_i: int,
    perf_j: int,
    method: str = "auto",
    n_monte_carlo_samples: int = 500
) -> NodeShapleyResult:
    """
    性能ペアに対するノードShapley値を計算（V ∪ A がプレイヤー）

    Args:
        network: ネットワーク構造
        matrices: build_adjacency_matrices()の結果
        perf_i, perf_j: 性能インデックス
        method: 'exact', 'monte_carlo', 'auto'
        n_monte_carlo_samples: Monte Carloサンプル数

    Returns:
        NodeShapleyResult
    """
    from app.services.matrix_utils import compute_total_effect_matrix

    start_time = time.time()

    B_PA = matrices['B_PA']
    B_AA = matrices['B_AA']
    B_AV = matrices['B_AV']

    # ノード情報を抽出
    node_infos = extract_node_info(network, matrices)
    n_nodes = len(node_infos)
    n_variables = sum(1 for n in node_infos if n.node_type == 'V')
    n_attributes = sum(1 for n in node_infos if n.node_type == 'A')

    # 元のC_ijとcos θを計算
    total_effect = compute_total_effect_matrix(B_PA, B_AA, B_AV)
    T = total_effect['T']

    if T.size == 0 or perf_i >= T.shape[0] or perf_j >= T.shape[0]:
        return NodeShapleyResult(
            perf_i_idx=perf_i,
            perf_j_idx=perf_j,
            C_ij=0.0,
            cos_theta=0.0,
            node_shapley_values={},
            sum_check=0.0,
            computation_method="empty",
            computation_time_ms=0.0,
            n_nodes=0,
            n_variables=0,
            n_attributes=0
        )

    T_i = T[perf_i, :]
    T_j = T[perf_j, :]
    C_ij = float(np.dot(T_i, T_j))

    norm_i = np.linalg.norm(T_i)
    norm_j = np.linalg.norm(T_j)
    if norm_i > 1e-10 and norm_j > 1e-10:
        cos_theta = C_ij / (norm_i * norm_j)
    else:
        cos_theta = 0.0

    # 計算方法の選択
    if method == "auto":
        if n_nodes <= 8:
            method = "exact"
        else:
            method = "monte_carlo"

    # ノードShapley値の計算
    if method == "exact":
        node_shapley_values = compute_node_shapley_values_exact(
            B_PA, B_AA, B_AV, node_infos, perf_i, perf_j
        )
        computation_method = "exact"
    else:
        node_shapley_values = compute_node_shapley_values_monte_carlo(
            B_PA, B_AA, B_AV, node_infos, perf_i, perf_j, n_monte_carlo_samples
        )
        computation_method = "monte_carlo"

    sum_check = sum(node_shapley_values.values())
    elapsed_ms = (time.time() - start_time) * 1000

    return NodeShapleyResult(
        perf_i_idx=perf_i,
        perf_j_idx=perf_j,
        C_ij=C_ij,
        cos_theta=cos_theta,
        node_shapley_values=node_shapley_values,
        sum_check=sum_check,
        computation_method=computation_method,
        computation_time_ms=elapsed_ms,
        n_nodes=n_nodes,
        n_variables=n_variables,
        n_attributes=n_attributes
    )


def node_shapley_result_to_dict(
    result: NodeShapleyResult,
    node_infos: List[NodeInfo],
    performance_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    NodeShapleyResultを辞書形式に変換（API用）

    Args:
        result: NodeShapleyResult
        node_infos: ノード情報リスト
        performance_names: 性能名のリスト

    Returns:
        API用の辞書
    """
    perf_i_name = performance_names[result.perf_i_idx] if performance_names else f"P{result.perf_i_idx}"
    perf_j_name = performance_names[result.perf_j_idx] if performance_names else f"P{result.perf_j_idx}"

    # ノード情報のマップ
    node_map = {n.node_id: n for n in node_infos}

    # Shapley値のリスト（寄与度の絶対値でソート）
    shapley_list = []
    total_abs = sum(abs(v) for v in result.node_shapley_values.values())

    for node_id, phi in sorted(result.node_shapley_values.items(), key=lambda x: -abs(x[1])):
        node = node_map.get(node_id)
        percentage = abs(phi) / total_abs * 100 if total_abs > 0 else 0.0

        shapley_list.append({
            "node_id": node_id,
            "node_label": node.node_label if node else node_id,
            "node_type": node.node_type if node else "?",
            "layer": node.layer if node else 0,
            "phi": phi,
            "abs_phi": abs(phi),
            "percentage": percentage,
            "sign": "positive" if phi > 0 else ("negative" if phi < 0 else "neutral")
        })

    return {
        "perf_i": {
            "idx": result.perf_i_idx,
            "name": perf_i_name
        },
        "perf_j": {
            "idx": result.perf_j_idx,
            "name": perf_j_name
        },
        "C_ij": result.C_ij,
        "cos_theta": result.cos_theta,
        "relationship": "tradeoff" if result.cos_theta < -0.1 else ("synergy" if result.cos_theta > 0.1 else "neutral"),
        "node_shapley_values": shapley_list,
        "sum_check": result.sum_check,
        "additivity_error": abs(result.sum_check - result.C_ij),
        "computation": {
            "method": result.computation_method,
            "n_nodes": result.n_nodes,
            "n_variables": result.n_variables,
            "n_attributes": result.n_attributes,
            "time_ms": result.computation_time_ms
        }
    }


# =============================================================================
# エッジShapley分解
# =============================================================================

@dataclass
class EdgeInfo:
    """エッジ情報"""
    edge_id: str  # ネットワークのエッジID
    source_id: str  # ソースノードID
    target_id: str  # ターゲットノードID
    source_label: str  # ソースノードラベル
    target_label: str  # ターゲットノードラベル
    weight: float  # 正規化された重み
    edge_type: str  # 'AV', 'AA', 'PA'
    matrix_pos: Tuple[int, int]  # 行列内の位置 (row, col)


@dataclass
class EdgeShapleyResult:
    """エッジShapley値計算の結果"""
    perf_i_idx: int
    perf_j_idx: int
    C_ij: float
    cos_theta: float
    edge_shapley_values: Dict[str, float]  # edge_id -> phi_e
    sum_check: float
    computation_method: str
    computation_time_ms: float
    n_edges: int


def extract_edge_info(
    network: Dict,
    matrices: Dict,
    weight_mode: str = 'discrete_7'
) -> List[EdgeInfo]:
    """
    ネットワークからエッジ情報を抽出

    Args:
        network: ネットワーク構造
        matrices: build_adjacency_matrices()の結果
        weight_mode: 重みモード

    Returns:
        EdgeInfoのリスト
    """
    from app.services.matrix_utils import normalize_weight

    edges = network.get('edges', [])
    nodes = {n['id']: n for n in network.get('nodes', [])}

    p_ids = matrices['node_ids']['P']
    a_ids = matrices['node_ids']['A']
    v_ids = matrices['node_ids']['V']

    p_idx = {nid: i for i, nid in enumerate(p_ids)}
    a_idx = {nid: i for i, nid in enumerate(a_ids)}
    v_idx = {nid: i for i, nid in enumerate(v_ids)}

    edge_infos = []

    for edge in edges:
        edge_id = edge.get('id', f"{edge['source_id']}->{edge['target_id']}")
        source_id = edge.get('source_id')
        target_id = edge.get('target_id')
        weight = edge.get('weight', 0)

        if weight == 0:
            continue

        normalized_weight = normalize_weight(weight, weight_mode)

        source_node = nodes.get(source_id, {})
        target_node = nodes.get(target_id, {})
        source_label = source_node.get('label', source_id)
        target_label = target_node.get('label', target_id)

        # エッジタイプと行列位置を特定
        edge_type = None
        matrix_pos = None

        if source_id in a_idx and target_id in p_idx:
            # A → P
            edge_type = 'PA'
            matrix_pos = (p_idx[target_id], a_idx[source_id])
        elif source_id in a_idx and target_id in a_idx:
            # A → A
            edge_type = 'AA'
            matrix_pos = (a_idx[target_id], a_idx[source_id])
        elif source_id in v_idx and target_id in a_idx:
            # V → A
            edge_type = 'AV'
            matrix_pos = (a_idx[target_id], v_idx[source_id])

        if edge_type is not None:
            edge_infos.append(EdgeInfo(
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                source_label=source_label,
                target_label=target_label,
                weight=normalized_weight,
                edge_type=edge_type,
                matrix_pos=matrix_pos
            ))

    return edge_infos


def compute_tradeoff_with_edge_subset(
    B_PA_full: np.ndarray,
    B_AA_full: np.ndarray,
    B_AV_full: np.ndarray,
    edge_infos: List[EdgeInfo],
    subset_edge_ids: Set[str],
    perf_i: int,
    perf_j: int
) -> float:
    """
    エッジの部分集合のみを有効にしたトレードオフ指標 C_ij(S) を計算

    Args:
        B_PA_full, B_AA_full, B_AV_full: 元の行列（全エッジ有効）
        edge_infos: 全エッジ情報
        subset_edge_ids: 有効にするエッジIDの集合
        perf_i, perf_j: 性能インデックス

    Returns:
        C_ij(S)
    """
    from app.services.matrix_utils import compute_total_effect_matrix

    # 部分集合用の行列を作成（すべて0で初期化）
    B_PA = np.zeros_like(B_PA_full)
    B_AA = np.zeros_like(B_AA_full)
    B_AV = np.zeros_like(B_AV_full)

    # 部分集合のエッジのみ値を設定
    for edge in edge_infos:
        if edge.edge_id in subset_edge_ids:
            row, col = edge.matrix_pos
            if edge.edge_type == 'PA':
                B_PA[row, col] = edge.weight
            elif edge.edge_type == 'AA':
                B_AA[row, col] = edge.weight
            elif edge.edge_type == 'AV':
                B_AV[row, col] = edge.weight

    # 総効果行列を計算
    result = compute_total_effect_matrix(B_PA, B_AA, B_AV)
    T = result['T']

    if T.size == 0:
        return 0.0

    # 内積 C_ij を計算
    if perf_i < T.shape[0] and perf_j < T.shape[0]:
        T_i = T[perf_i, :]
        T_j = T[perf_j, :]
        return float(np.dot(T_i, T_j))

    return 0.0


def compute_edge_shapley_values_exact(
    B_PA: np.ndarray,
    B_AA: np.ndarray,
    B_AV: np.ndarray,
    edge_infos: List[EdgeInfo],
    perf_i: int,
    perf_j: int
) -> Dict[str, float]:
    """
    エッジShapley値の厳密計算

    φ_e = Σ_{S⊆E\{e}} [|S|!(|E|-|S|-1)!/|E|!] × [C_ij(S∪{e}) - C_ij(S)]

    Args:
        B_PA, B_AA, B_AV: 元の行列
        edge_infos: 全エッジ情報
        perf_i, perf_j: 性能インデックス

    Returns:
        {edge_id: shapley_value}
    """
    all_edge_ids = set(e.edge_id for e in edge_infos)
    n = len(all_edge_ids)

    if n == 0:
        return {}

    factorial_n = math.factorial(n)
    shapley_values = {}

    for edge in edge_infos:
        edge_id = edge.edge_id
        phi_e = 0.0
        others = all_edge_ids - {edge_id}

        for size in range(len(others) + 1):
            for S in combinations(others, size):
                S_set = set(S)
                S_with_e = S_set | {edge_id}

                # 限界貢献
                c_with_e = compute_tradeoff_with_edge_subset(
                    B_PA, B_AA, B_AV, edge_infos, S_with_e, perf_i, perf_j
                )
                c_without_e = compute_tradeoff_with_edge_subset(
                    B_PA, B_AA, B_AV, edge_infos, S_set, perf_i, perf_j
                )
                marginal = c_with_e - c_without_e

                # Shapley係数
                s = len(S_set)
                coeff = math.factorial(s) * math.factorial(n - s - 1) / factorial_n

                phi_e += coeff * marginal

        shapley_values[edge_id] = phi_e

    return shapley_values


def compute_edge_shapley_values_monte_carlo(
    B_PA: np.ndarray,
    B_AA: np.ndarray,
    B_AV: np.ndarray,
    edge_infos: List[EdgeInfo],
    perf_i: int,
    perf_j: int,
    n_samples: int = 500,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    エッジShapley値のMonte Carlo近似

    Args:
        B_PA, B_AA, B_AV: 元の行列
        edge_infos: 全エッジ情報
        perf_i, perf_j: 性能インデックス
        n_samples: サンプル数
        seed: 乱数シード

    Returns:
        {edge_id: shapley_value}
    """
    if seed is not None:
        random.seed(seed)

    all_edge_ids = [e.edge_id for e in edge_infos]
    n = len(all_edge_ids)

    if n == 0:
        return {}

    marginal_sums = {eid: 0.0 for eid in all_edge_ids}
    counts = {eid: 0 for eid in all_edge_ids}

    for _ in range(n_samples):
        perm = all_edge_ids.copy()
        random.shuffle(perm)

        S = set()
        prev_value = 0.0

        for edge_id in perm:
            S_with_e = S | {edge_id}
            curr_value = compute_tradeoff_with_edge_subset(
                B_PA, B_AA, B_AV, edge_infos, S_with_e, perf_i, perf_j
            )
            marginal = curr_value - prev_value

            marginal_sums[edge_id] += marginal
            counts[edge_id] += 1

            S = S_with_e
            prev_value = curr_value

    shapley_values = {}
    for edge_id in all_edge_ids:
        if counts[edge_id] > 0:
            shapley_values[edge_id] = marginal_sums[edge_id] / counts[edge_id]
        else:
            shapley_values[edge_id] = 0.0

    return shapley_values


def compute_edge_shapley_for_performance_pair(
    network: Dict,
    matrices: Dict,
    perf_i: int,
    perf_j: int,
    weight_mode: str = 'discrete_7',
    method: str = "auto",
    n_monte_carlo_samples: int = 500
) -> EdgeShapleyResult:
    """
    性能ペアに対するエッジShapley値を計算

    Args:
        network: ネットワーク構造
        matrices: build_adjacency_matrices()の結果
        perf_i, perf_j: 性能インデックス
        weight_mode: 重みモード
        method: 'exact', 'monte_carlo', 'auto'
        n_monte_carlo_samples: Monte Carloサンプル数

    Returns:
        EdgeShapleyResult
    """
    from app.services.matrix_utils import compute_total_effect_matrix

    start_time = time.time()

    B_PA = matrices['B_PA']
    B_AA = matrices['B_AA']
    B_AV = matrices['B_AV']

    # エッジ情報を抽出
    edge_infos = extract_edge_info(network, matrices, weight_mode)
    n_edges = len(edge_infos)

    # 元のC_ijとcos θを計算
    total_effect = compute_total_effect_matrix(B_PA, B_AA, B_AV)
    T = total_effect['T']

    if T.size == 0 or perf_i >= T.shape[0] or perf_j >= T.shape[0]:
        return EdgeShapleyResult(
            perf_i_idx=perf_i,
            perf_j_idx=perf_j,
            C_ij=0.0,
            cos_theta=0.0,
            edge_shapley_values={},
            sum_check=0.0,
            computation_method="empty",
            computation_time_ms=0.0,
            n_edges=0
        )

    T_i = T[perf_i, :]
    T_j = T[perf_j, :]
    C_ij = float(np.dot(T_i, T_j))

    norm_i = np.linalg.norm(T_i)
    norm_j = np.linalg.norm(T_j)
    if norm_i > 1e-10 and norm_j > 1e-10:
        cos_theta = C_ij / (norm_i * norm_j)
    else:
        cos_theta = 0.0

    # 計算方法の選択
    if method == "auto":
        if n_edges <= 10:
            method = "exact"
        else:
            method = "monte_carlo"

    # エッジShapley値の計算
    if method == "exact":
        edge_shapley_values = compute_edge_shapley_values_exact(
            B_PA, B_AA, B_AV, edge_infos, perf_i, perf_j
        )
        computation_method = "exact"
    else:
        edge_shapley_values = compute_edge_shapley_values_monte_carlo(
            B_PA, B_AA, B_AV, edge_infos, perf_i, perf_j, n_monte_carlo_samples
        )
        computation_method = "monte_carlo"

    sum_check = sum(edge_shapley_values.values())
    elapsed_ms = (time.time() - start_time) * 1000

    return EdgeShapleyResult(
        perf_i_idx=perf_i,
        perf_j_idx=perf_j,
        C_ij=C_ij,
        cos_theta=cos_theta,
        edge_shapley_values=edge_shapley_values,
        sum_check=sum_check,
        computation_method=computation_method,
        computation_time_ms=elapsed_ms,
        n_edges=n_edges
    )


def edge_shapley_result_to_dict(
    result: EdgeShapleyResult,
    edge_infos: List[EdgeInfo],
    performance_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    EdgeShapleyResultを辞書形式に変換（API用）

    Args:
        result: EdgeShapleyResult
        edge_infos: エッジ情報リスト
        performance_names: 性能名のリスト

    Returns:
        API用の辞書
    """
    perf_i_name = performance_names[result.perf_i_idx] if performance_names else f"P{result.perf_i_idx}"
    perf_j_name = performance_names[result.perf_j_idx] if performance_names else f"P{result.perf_j_idx}"

    # エッジ情報のマップ
    edge_map = {e.edge_id: e for e in edge_infos}

    # Shapley値のリスト（寄与度の絶対値でソート）
    shapley_list = []
    total_abs = sum(abs(v) for v in result.edge_shapley_values.values())

    for edge_id, phi in sorted(result.edge_shapley_values.items(), key=lambda x: -abs(x[1])):
        edge = edge_map.get(edge_id)
        percentage = abs(phi) / total_abs * 100 if total_abs > 0 else 0.0

        shapley_list.append({
            "edge_id": edge_id,
            "source_id": edge.source_id if edge else None,
            "target_id": edge.target_id if edge else None,
            "source_label": edge.source_label if edge else None,
            "target_label": edge.target_label if edge else None,
            "edge_type": edge.edge_type if edge else None,
            "edge_weight": edge.weight if edge else None,
            "phi": phi,
            "abs_phi": abs(phi),
            "percentage": percentage,
            "sign": "positive" if phi > 0 else ("negative" if phi < 0 else "neutral")
        })

    return {
        "perf_i": {
            "idx": result.perf_i_idx,
            "name": perf_i_name
        },
        "perf_j": {
            "idx": result.perf_j_idx,
            "name": perf_j_name
        },
        "C_ij": result.C_ij,
        "cos_theta": result.cos_theta,
        "relationship": "tradeoff" if result.cos_theta < -0.1 else ("synergy" if result.cos_theta > 0.1 else "neutral"),
        "edge_shapley_values": shapley_list,
        "sum_check": result.sum_check,
        "additivity_error": abs(result.sum_check - result.C_ij),
        "computation": {
            "method": result.computation_method,
            "n_edges": result.n_edges,
            "time_ms": result.computation_time_ms
        }
    }
