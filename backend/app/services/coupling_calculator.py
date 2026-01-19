"""
トレードオフ間カップリングと性能クラスタリング計算

論文 design.tex 3573-3786行に基づく実装:
- 正規化カップリング: NormCoupling(TO_ij, TO_kl) = Σ|φ_a(C_ij)|·|φ_a(C_kl)| / (||φ_ij|| · ||φ_kl||)
- 間接結合度: Connection(P_i, P_k) = max_{j,l} K_{(ij),(kl)}
- 階層的クラスタリング: 平均連結法 + Silhouette係数
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)


@dataclass
class TradeoffInfo:
    """トレードオフ情報"""
    perf_i_idx: int
    perf_j_idx: int
    perf_i_label: str
    perf_j_label: str
    cos_theta: float
    c_ij: float
    shapley_vector: np.ndarray  # 寄与ベクトル φ_ij


@dataclass
class CouplingResult:
    """カップリング計算結果"""
    # トレードオフ情報
    tradeoff_infos: List[TradeoffInfo]
    tradeoff_labels: List[str]  # "P1-P2" 形式

    # カップリング行列 (トレードオフ間)
    coupling_matrix: np.ndarray  # 正規化カップリング K

    # 性能間の間接結合度行列
    performance_connection_matrix: np.ndarray  # C^(P)
    performance_labels: List[str]

    # クラスタリング結果
    linkage_matrix: Optional[np.ndarray] = None
    clusters: Optional[List[int]] = None
    optimal_n_clusters: Optional[int] = None
    silhouette_score: Optional[float] = None
    dendrogram_data: Optional[Dict] = None


def compute_coupling_for_case(
    network: Dict,
    matrices: Dict,
    cos_theta_matrix: np.ndarray,
    inner_product_matrix: np.ndarray,
    perf_labels: List[str],
    node_shapley_func,  # callable to compute node shapley for a pair
    tradeoff_threshold: float = 0.0
) -> CouplingResult:
    """
    設計案のカップリングとクラスタリングを計算

    Args:
        network: ネットワーク構造
        matrices: 隣接行列情報
        cos_theta_matrix: cos θ 行列
        inner_product_matrix: 内積行列 C_ij
        perf_labels: 性能ラベル
        node_shapley_func: ノードShapley値計算関数
        tradeoff_threshold: トレードオフと見なす cos θ の閾値 (default: 0.0)

    Returns:
        CouplingResult
    """
    n_perfs = len(perf_labels)

    # 1. トレードオフペアを抽出し、各々のShapley寄与ベクトルを計算
    tradeoff_infos = []
    tradeoff_labels = []

    for i in range(n_perfs):
        for j in range(i + 1, n_perfs):
            cos_theta = cos_theta_matrix[i][j]
            if cos_theta < tradeoff_threshold:  # トレードオフ
                # ノードShapley値を取得
                shapley_result = node_shapley_func(i, j)
                if shapley_result is None:
                    continue

                # 寄与ベクトルを構築
                shapley_vector = shapley_result.get('shapley_vector', np.array([]))

                tradeoff_infos.append(TradeoffInfo(
                    perf_i_idx=i,
                    perf_j_idx=j,
                    perf_i_label=perf_labels[i],
                    perf_j_label=perf_labels[j],
                    cos_theta=cos_theta,
                    c_ij=inner_product_matrix[i][j],
                    shapley_vector=shapley_vector
                ))
                tradeoff_labels.append(f"{perf_labels[i]}-{perf_labels[j]}")

    n_tradeoffs = len(tradeoff_infos)

    if n_tradeoffs == 0:
        # トレードオフがない場合
        return CouplingResult(
            tradeoff_infos=[],
            tradeoff_labels=[],
            coupling_matrix=np.array([[]]),
            performance_connection_matrix=np.eye(n_perfs),
            performance_labels=perf_labels,
        )

    # 2. カップリング行列を計算
    coupling_matrix = np.zeros((n_tradeoffs, n_tradeoffs))

    for a, to_a in enumerate(tradeoff_infos):
        for b, to_b in enumerate(tradeoff_infos):
            if a == b:
                coupling_matrix[a][b] = 1.0
            else:
                coupling_matrix[a][b] = _compute_normalized_coupling(
                    to_a.shapley_vector,
                    to_b.shapley_vector
                )

    # 3. 性能間の間接結合度行列を計算
    performance_connection_matrix = _compute_performance_connection_matrix(
        tradeoff_infos, coupling_matrix, n_perfs
    )

    # 4. 階層的クラスタリング
    clustering_result = _perform_hierarchical_clustering(
        performance_connection_matrix, perf_labels
    )

    return CouplingResult(
        tradeoff_infos=tradeoff_infos,
        tradeoff_labels=tradeoff_labels,
        coupling_matrix=coupling_matrix,
        performance_connection_matrix=performance_connection_matrix,
        performance_labels=perf_labels,
        linkage_matrix=clustering_result.get('linkage_matrix'),
        clusters=clustering_result.get('clusters'),
        optimal_n_clusters=clustering_result.get('optimal_n_clusters'),
        silhouette_score=clustering_result.get('silhouette_score'),
        dendrogram_data=clustering_result.get('dendrogram_data'),
    )


def _compute_normalized_coupling(phi_a: np.ndarray, phi_b: np.ndarray) -> float:
    """
    正規化カップリングを計算

    NormCoupling = Σ|φ_a(k)|·|φ_b(k)| / (||φ_a|| · ||φ_b||)
    """
    if len(phi_a) == 0 or len(phi_b) == 0:
        return 0.0

    # 長さを揃える
    max_len = max(len(phi_a), len(phi_b))
    phi_a_padded = np.pad(phi_a, (0, max_len - len(phi_a)), mode='constant')
    phi_b_padded = np.pad(phi_b, (0, max_len - len(phi_b)), mode='constant')

    # 分子: 絶対値の内積
    numerator = np.sum(np.abs(phi_a_padded) * np.abs(phi_b_padded))

    # 分母: ノルムの積
    norm_a = np.linalg.norm(phi_a_padded)
    norm_b = np.linalg.norm(phi_b_padded)

    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0

    return numerator / (norm_a * norm_b)


def _compute_performance_connection_matrix(
    tradeoff_infos: List[TradeoffInfo],
    coupling_matrix: np.ndarray,
    n_perfs: int
) -> np.ndarray:
    """
    性能間の間接結合度行列を計算

    Connection(P_i, P_k) = max_{j: TO_ij ∈ TO, l: TO_kl ∈ TO} K_{(ij),(kl)}
    """
    # 性能がどのトレードオフに関与しているかをマッピング
    perf_to_tradeoffs: Dict[int, List[int]] = {i: [] for i in range(n_perfs)}

    for to_idx, to_info in enumerate(tradeoff_infos):
        perf_to_tradeoffs[to_info.perf_i_idx].append(to_idx)
        perf_to_tradeoffs[to_info.perf_j_idx].append(to_idx)

    # 間接結合度行列を計算
    connection_matrix = np.zeros((n_perfs, n_perfs))

    for i in range(n_perfs):
        for k in range(n_perfs):
            if i == k:
                connection_matrix[i][k] = 1.0
            else:
                # P_i と P_k が関与するトレードオフ間の最大カップリング
                max_coupling = 0.0
                for to_i in perf_to_tradeoffs[i]:
                    for to_k in perf_to_tradeoffs[k]:
                        if to_i != to_k:
                            max_coupling = max(max_coupling, coupling_matrix[to_i][to_k])
                connection_matrix[i][k] = max_coupling

    return connection_matrix


def _perform_hierarchical_clustering(
    connection_matrix: np.ndarray,
    perf_labels: List[str]
) -> Dict:
    """
    階層的クラスタリングを実行
    """
    n = len(connection_matrix)

    if n < 2:
        return {
            'linkage_matrix': None,
            'clusters': [0] if n == 1 else [],
            'optimal_n_clusters': 1 if n == 1 else 0,
            'silhouette_score': None,
            'dendrogram_data': None,
        }

    # 距離行列 D = 1 - C^(P) (対称化)
    symmetrized = (connection_matrix + connection_matrix.T) / 2
    distance_matrix = 1.0 - symmetrized

    # 対角成分を0に
    np.fill_diagonal(distance_matrix, 0)

    # 負の値を0にクリップ（数値誤差対策）
    distance_matrix = np.clip(distance_matrix, 0, None)

    # condensed形式に変換
    try:
        condensed_dist = squareform(distance_matrix, checks=False)
    except Exception as e:
        logger.warning(f"squareform failed: {e}")
        return {
            'linkage_matrix': None,
            'clusters': list(range(n)),
            'optimal_n_clusters': n,
            'silhouette_score': None,
            'dendrogram_data': None,
        }

    # 階層的クラスタリング（平均連結法）
    try:
        Z = linkage(condensed_dist, method='average')
    except Exception as e:
        logger.warning(f"linkage failed: {e}")
        return {
            'linkage_matrix': None,
            'clusters': list(range(n)),
            'optimal_n_clusters': n,
            'silhouette_score': None,
            'dendrogram_data': None,
        }

    # リンケージ行列から全てのマージ高さを取得
    merge_heights = sorted(set(Z[:, 2].tolist()))

    # 各高さでのSilhouetteスコアを計算
    silhouette_curve = []
    best_n_clusters = 2
    best_silhouette = -1.0
    best_clusters = None
    best_height = merge_heights[0] if merge_heights else 0

    for height in merge_heights:
        try:
            # この高さでカット
            clusters = fcluster(Z, height, criterion='distance')
            n_clusters = len(set(clusters))

            if n_clusters >= 2 and n_clusters < n:
                score = silhouette_score(distance_matrix, clusters, metric='precomputed')
                silhouette_curve.append({
                    'height': height,
                    'n_clusters': n_clusters,
                    'silhouette': score
                })

                if score > best_silhouette:
                    best_silhouette = score
                    best_n_clusters = n_clusters
                    best_clusters = clusters.tolist()
                    best_height = height
        except Exception:
            continue

    # 最小/最大高さも追加（UI用）
    if merge_heights:
        # 最小高さより少し下（全て別クラスタ）
        silhouette_curve.insert(0, {
            'height': 0,
            'n_clusters': n,
            'silhouette': None
        })
        # 最大高さより上（全て1クラスタ）
        max_height = max(merge_heights)
        silhouette_curve.append({
            'height': max_height + 0.01,
            'n_clusters': 1,
            'silhouette': None
        })

    if best_clusters is None:
        best_clusters = fcluster(Z, 2, criterion='maxclust').tolist()
        best_n_clusters = len(set(best_clusters))

    # デンドログラムデータを生成
    dendrogram_data = _generate_dendrogram_data(Z, perf_labels, silhouette_curve, best_height)

    return {
        'linkage_matrix': Z.tolist(),
        'clusters': best_clusters,
        'optimal_n_clusters': best_n_clusters,
        'silhouette_score': best_silhouette if best_silhouette > -1 else None,
        'dendrogram_data': dendrogram_data,
    }


def _generate_dendrogram_data(
    Z: np.ndarray,
    labels: List[str],
    silhouette_curve: List[Dict] = None,
    optimal_height: float = None
) -> Dict:
    """
    デンドログラム描画用のデータを生成
    """
    try:
        # matplotlib不要の軽量なデンドログラムデータ生成
        n = len(labels)

        # リンケージ行列から階層構造を構築
        nodes = []
        for i, label in enumerate(labels):
            nodes.append({
                'id': i,
                'label': label,
                'is_leaf': True,
                'height': 0,
                'children': []
            })

        # 内部ノードを追加
        for i, row in enumerate(Z):
            left_idx = int(row[0])
            right_idx = int(row[1])
            height = row[2]

            internal_node = {
                'id': n + i,
                'label': f'Cluster_{n + i}',
                'is_leaf': False,
                'height': height,
                'children': [left_idx, right_idx]
            }
            nodes.append(internal_node)

        # 最大高さを取得
        max_height = max(row[2] for row in Z) if len(Z) > 0 else 1.0

        return {
            'nodes': nodes,
            'n_leaves': n,
            'labels': labels,
            'max_height': max_height,
            'silhouette_curve': silhouette_curve or [],
            'optimal_height': optimal_height,
        }
    except Exception as e:
        logger.warning(f"Dendrogram data generation failed: {e}")
        return None


def coupling_result_to_dict(result: CouplingResult) -> Dict[str, Any]:
    """
    CouplingResultをAPIレスポンス用の辞書に変換
    """
    # トレードオフ情報
    tradeoff_list = []
    for i, to_info in enumerate(result.tradeoff_infos):
        tradeoff_list.append({
            'index': i,
            'label': result.tradeoff_labels[i],
            'perf_i_idx': to_info.perf_i_idx,
            'perf_j_idx': to_info.perf_j_idx,
            'perf_i_label': to_info.perf_i_label,
            'perf_j_label': to_info.perf_j_label,
            'cos_theta': to_info.cos_theta,
            'c_ij': to_info.c_ij,
        })

    # クラスタ情報を整理
    cluster_groups = {}
    if result.clusters:
        for perf_idx, cluster_id in enumerate(result.clusters):
            if cluster_id not in cluster_groups:
                cluster_groups[cluster_id] = []
            cluster_groups[cluster_id].append({
                'perf_idx': perf_idx,
                'perf_label': result.performance_labels[perf_idx]
            })

    return {
        'n_tradeoffs': len(result.tradeoff_infos),
        'tradeoffs': tradeoff_list,
        'coupling_matrix': result.coupling_matrix.tolist() if result.coupling_matrix.size > 0 else [],
        'tradeoff_labels': result.tradeoff_labels,
        'performance_connection_matrix': result.performance_connection_matrix.tolist(),
        'performance_labels': result.performance_labels,
        'clustering': {
            'clusters': result.clusters,
            'optimal_n_clusters': result.optimal_n_clusters,
            'silhouette_score': result.silhouette_score,
            'cluster_groups': cluster_groups,
        },
        'dendrogram': result.dendrogram_data,
    }
