# backend/app/services/weighted_wl_kernel.py
"""
Weighted Weisfeiler-Lehman カーネル

連続値エッジ重みに対応するWLカーネルの拡張版。
従来のWLカーネルはラベル文字列のハッシュで比較するが、
Weighted版は数値的な特徴ベクトルを保持し連続的に比較。

参考: Schulz et al. 2022 "Weisfeiler and Leman go Continuous"

既存の compute_wl_kernel (mds.py) との互換性を維持しつつ、
連続値エッジ重みに対応。
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# 統一重み正規化モジュールをインポート
from app.services.weight_normalization import (
    normalize_weight as _normalize_weight_impl,
    WeightModeType,
    WEIGHT_SCHEMES
)


class WeightedWLKernel:
    """
    Weighted Weisfeiler-Lehman カーネル

    従来のWL:
        - ラベル = 文字列
        - 近傍集約 = ソートして結合
        - 類似度 = ラベル一致のカウント

    Weighted WL:
        - ラベル = 数値ベクトル (layer, type_id, 集約特徴)
        - 近傍集約 = 重み付き平均/合計
        - 類似度 = RBFカーネル or ヒストグラム内積
    """

    def __init__(
        self,
        n_iterations: int = 3,
        weight_mode: str = 'continuous',
        aggregation: str = 'weighted_mean',
        sigma: float = 1.0
    ):
        """
        Args:
            n_iterations: WL反復回数
            weight_mode: 重みモード
                - 'continuous': 連続値 (-1~+1)
                - 'discrete': 5段階（後方互換、'discrete_5'と同等）
                - 'discrete_3': 3段階 {-1, 0, +1}
                - 'discrete_5': 5段階 {-3, -1, 0, +1, +3}
                - 'discrete_7': 7段階 {-5, -3, -1, 0, +1, +3, +5}
            aggregation: 近傍集約方法 ('weighted_mean', 'weighted_sum', 'attention')
            sigma: RBFカーネルの幅パラメータ
        """
        self.n_iterations = n_iterations
        # 後方互換性: 'discrete' → 'discrete_5'
        if weight_mode == 'discrete':
            weight_mode = 'discrete_5'
        self.weight_mode = weight_mode
        self.aggregation = aggregation
        self.sigma = sigma

        # レイヤー・タイプのエンコーディング
        self.layer_encoding = {1: 0, 2: 1, 3: 2, 4: 3}  # P, A, V, E
        self.type_encoding = {
            'performance': 0, 'property': 1, 'attribute': 1,
            'variable': 2, 'object': 3, 'environment': 3, 'entity': 3
        }

    def fit_transform(
        self,
        graphs: List[Dict],
        weight_modes: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        グラフリストからカーネル行列を計算

        Args:
            graphs: ネットワークのリスト [{'nodes': [...], 'edges': [...]}, ...]
            weight_modes: 各グラフのweight_modeリスト（オプション）
                          指定しない場合はインスタンスのweight_modeを使用

        Returns:
            K: (n_graphs × n_graphs) カーネル行列（正規化済み）
        """
        n = len(graphs)
        if n == 0:
            return np.array([])

        # weight_modesが指定されていない場合はインスタンスのweight_modeを使用
        if weight_modes is None:
            weight_modes = [self.weight_mode] * n
        elif len(weight_modes) != n:
            raise ValueError(f"weight_modes length ({len(weight_modes)}) must match graphs length ({n})")

        # 各グラフの特徴を抽出（個別のweight_modeを適用）
        all_features = []
        for graph, wm in zip(graphs, weight_modes):
            features = self._extract_features(graph, weight_mode=wm)
            all_features.append(features)

        # カーネル行列を計算
        K = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                k_ij = self._graph_kernel(all_features[i], all_features[j])
                K[i, j] = k_ij
                K[j, i] = k_ij

        # 正規化
        K_normalized = self._normalize_kernel(K)

        return K_normalized

    def _extract_features(self, graph: Dict, weight_mode: Optional[str] = None) -> Dict:
        """
        グラフから階層的特徴を抽出

        Args:
            graph: ネットワークデータ
            weight_mode: このグラフに適用するweight_mode（Noneの場合はインスタンスのweight_modeを使用）

        Returns:
            {
                'node_features': List[np.ndarray],  # 各ノードの特徴ベクトル
                'iteration_features': List[List[np.ndarray]],  # 各反復での特徴
                'histogram': np.ndarray,  # 全体のヒストグラム特徴
            }
        """
        # 使用するweight_modeを決定
        effective_weight_mode = weight_mode if weight_mode is not None else self.weight_mode

        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])

        if not nodes:
            return {
                'node_features': [],
                'iteration_features': [],
                'histogram': np.array([])
            }

        n_nodes = len(nodes)

        # ノードIDからインデックスへのマッピング
        node_id_to_idx = {node['id']: i for i, node in enumerate(nodes)}

        # 隣接リスト（重み付き）
        adjacency = defaultdict(list)  # node_idx -> [(neighbor_idx, weight), ...]
        for edge in edges:
            src_idx = node_id_to_idx.get(edge.get('source_id'))
            tgt_idx = node_id_to_idx.get(edge.get('target_id'))
            weight = edge.get('weight', 0)

            if weight is None:
                weight = 0

            # 指定されたweight_modeで連続値に正規化
            weight = self._normalize_weight(weight, weight_mode=effective_weight_mode)

            if src_idx is not None and tgt_idx is not None:
                adjacency[src_idx].append((tgt_idx, weight))
                adjacency[tgt_idx].append((src_idx, weight))  # 無向グラフとして扱う

        # 初期特徴の設定（layer, type, degree, in_weight_sum, out_weight_sum）
        initial_features = []
        for i, node in enumerate(nodes):
            layer = node.get('layer', 0)
            node_type = node.get('type', 'unknown')

            layer_code = self.layer_encoding.get(layer, 0)
            type_code = self.type_encoding.get(node_type.lower(), 0)

            # 次数と重みの統計
            neighbors = adjacency[i]
            degree = len(neighbors)
            weight_sum = sum(w for _, w in neighbors)
            weight_abs_sum = sum(abs(w) for _, w in neighbors)

            # 特徴ベクトル: [layer, type, degree, weight_sum, weight_abs_sum]
            feature = np.array([
                layer_code / 3.0,  # 正規化
                type_code / 3.0,
                min(degree / 10.0, 1.0),  # 次数を正規化
                weight_sum / max(1, degree),  # 平均重み
                weight_abs_sum / max(1, degree),  # 平均絶対重み
            ])
            initial_features.append(feature)

        # 反復特徴を保存
        iteration_features = [initial_features.copy()]
        current_features = initial_features.copy()

        # WL反復
        for iteration in range(self.n_iterations):
            new_features = []

            for i in range(n_nodes):
                # 自身の特徴
                self_feature = current_features[i]

                # 近傍の特徴を集約
                neighbors = adjacency[i]
                if neighbors:
                    neighbor_features = []
                    neighbor_weights = []

                    for neighbor_idx, edge_weight in neighbors:
                        neighbor_features.append(current_features[neighbor_idx])
                        neighbor_weights.append(edge_weight)

                    aggregated = self._aggregate_neighbors(
                        neighbor_features, neighbor_weights
                    )
                else:
                    aggregated = np.zeros_like(self_feature)

                # 新しい特徴 = [自身の特徴, 集約特徴]
                new_feature = np.concatenate([self_feature, aggregated])
                new_features.append(new_feature)

            iteration_features.append(new_features)
            current_features = new_features

        # グラフ全体のヒストグラム特徴を計算
        histogram = self._compute_histogram(iteration_features)

        return {
            'node_features': current_features,
            'iteration_features': iteration_features,
            'histogram': histogram,
        }

    def _normalize_weight(self, weight: float, weight_mode: Optional[str] = None) -> float:
        """
        重みを [-1, 1] の範囲に正規化

        統一重み正規化モジュールを使用。
        各離散化スキームに応じた均等分割:
        - 3段階: {-1, 0, +1} → {-2/3, 0, +2/3}
        - 5段階: {-3, -1, 0, +1, +3} → {-4/5, -2/5, 0, +2/5, +4/5}
        - 7段階: {-5, -3, -1, 0, +1, +3, +5} → {-6/7, -4/7, -2/7, 0, +2/7, +4/7, +6/7}
        - 連続: そのまま（-1~+1にクリップ）

        Args:
            weight: 正規化する重み値
            weight_mode: 使用するweight_mode（Noneの場合はインスタンスのweight_modeを使用）
        """
        effective_mode = weight_mode if weight_mode is not None else self.weight_mode
        return _normalize_weight_impl(weight, effective_mode)

    def _aggregate_neighbors(
        self,
        neighbor_features: List[np.ndarray],
        neighbor_weights: List[float]
    ) -> np.ndarray:
        """
        近傍ノードの特徴を集約

        Args:
            neighbor_features: 近傍ノードの特徴ベクトルのリスト
            neighbor_weights: 各近傍へのエッジ重み

        Returns:
            集約された特徴ベクトル
        """
        if not neighbor_features:
            return np.zeros(len(neighbor_features[0]) if neighbor_features else 5)

        features = np.array(neighbor_features)
        weights = np.array(neighbor_weights)

        if self.aggregation == 'weighted_mean':
            # 重み付き平均（絶対値で重み付け）
            abs_weights = np.abs(weights) + 1e-10
            weighted_sum = np.sum(features * abs_weights[:, np.newaxis], axis=0)
            return weighted_sum / np.sum(abs_weights)

        elif self.aggregation == 'weighted_sum':
            # 重み付き合計（符号付き）
            return np.sum(features * weights[:, np.newaxis], axis=0)

        elif self.aggregation == 'attention':
            # シンプルなアテンション（softmax重み）
            attention = np.exp(np.abs(weights))
            attention = attention / np.sum(attention)
            return np.sum(features * attention[:, np.newaxis], axis=0)

        else:
            # デフォルト: 平均
            return np.mean(features, axis=0)

    def _compute_histogram(
        self,
        iteration_features: List[List[np.ndarray]]
    ) -> np.ndarray:
        """
        全反復の特徴からグラフ全体のヒストグラム特徴を計算

        各反復で特徴ベクトルのサイズが異なるため、反復ごとに統計を計算して結合
        """
        if not iteration_features:
            return np.array([])

        histograms = []

        for iter_idx, iter_features in enumerate(iteration_features):
            if not iter_features:
                continue

            # 同じ反復内の特徴は同じサイズなのでスタック可能
            features = np.array(iter_features)

            # 統計量: mean, std, min, max
            iter_histogram = np.concatenate([
                np.mean(features, axis=0),
                np.std(features, axis=0),
                np.min(features, axis=0),
                np.max(features, axis=0),
            ])
            histograms.append(iter_histogram)

        if not histograms:
            return np.array([])

        # 全反復のヒストグラムを結合
        return np.concatenate(histograms)

    def _graph_kernel(self, features_i: Dict, features_j: Dict) -> float:
        """
        2つのグラフ間のカーネル値を計算

        ヒストグラム特徴のRBFカーネル + ノード特徴のマッチング
        """
        # ヒストグラム特徴のRBFカーネル
        hist_i = features_i['histogram']
        hist_j = features_j['histogram']

        if hist_i.size == 0 or hist_j.size == 0:
            return 0.0

        # サイズを合わせる
        max_size = max(len(hist_i), len(hist_j))
        hist_i = np.pad(hist_i, (0, max_size - len(hist_i)))
        hist_j = np.pad(hist_j, (0, max_size - len(hist_j)))

        # RBFカーネル
        diff = hist_i - hist_j
        k_histogram = np.exp(-np.sum(diff ** 2) / (2 * self.sigma ** 2))

        # ノード特徴の類似度（オプショナル）
        nodes_i = features_i['node_features']
        nodes_j = features_j['node_features']

        if nodes_i and nodes_j:
            # 最適マッチングの近似（平均類似度）
            k_nodes = 0.0
            count = 0
            for f_i in nodes_i:
                for f_j in nodes_j:
                    # サイズを合わせる
                    max_len = max(len(f_i), len(f_j))
                    f_i_padded = np.pad(f_i, (0, max_len - len(f_i)))
                    f_j_padded = np.pad(f_j, (0, max_len - len(f_j)))

                    diff = f_i_padded - f_j_padded
                    k_nodes += np.exp(-np.sum(diff ** 2) / (2 * self.sigma ** 2))
                    count += 1

            if count > 0:
                k_nodes /= count
        else:
            k_nodes = 0.0

        # 組み合わせ
        return 0.7 * k_histogram + 0.3 * k_nodes

    def _normalize_kernel(self, K: np.ndarray) -> np.ndarray:
        """
        カーネル行列を正規化

        K_normalized[i,j] = K[i,j] / sqrt(K[i,i] * K[j,j])
        """
        n = K.shape[0]
        K_normalized = np.zeros_like(K)

        diag = np.diag(K)
        for i in range(n):
            for j in range(n):
                if diag[i] > 0 and diag[j] > 0:
                    K_normalized[i, j] = K[i, j] / np.sqrt(diag[i] * diag[j])

        return K_normalized


def kernel_to_distance(K: np.ndarray) -> np.ndarray:
    """
    カーネル行列から距離行列を計算

    D[i,j] = sqrt(K[i,i] + K[j,j] - 2*K[i,j])
    """
    n = K.shape[0]
    D = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            d_squared = K[i, i] + K[j, j] - 2 * K[i, j]
            D[i, j] = np.sqrt(max(0, d_squared))

    return D


# =============================================================================
# 離散化信頼度の計算（論文6章準拠）
# =============================================================================

def _spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """
    Spearman順位相関係数を計算

    ρ = 1 - (6 * Σd_i²) / (n * (n² - 1))

    where d_i = rank(x_i) - rank(y_i)
    """
    from scipy.stats import rankdata

    if len(x) != len(y) or len(x) < 2:
        return 1.0

    rank_x = rankdata(x)
    rank_y = rankdata(y)

    d = rank_x - rank_y
    n = len(x)

    rho = 1 - (6 * np.sum(d ** 2)) / (n * (n ** 2 - 1))
    return float(rho)


def _extract_upper_triangle(matrix: np.ndarray) -> np.ndarray:
    """上三角行列の要素を1次元配列として抽出（対角除く）"""
    n = matrix.shape[0]
    indices = np.triu_indices(n, k=1)
    return matrix[indices]


def compute_discretization_confidence(
    networks: List[Dict],
    n_iterations: int = 3
) -> Dict:
    """
    離散化による情報損失を評価（論文6章準拠）

    連続値と離散値の両方でカーネル行列を計算し、
    符号保存と順序保存を評価する。

    Args:
        networks: ネットワークのリスト
        n_iterations: WLカーネルの反復回数

    Returns:
        {
            'sign_preservation': {
                'rate': float,  # 符号が保存されたペアの割合
                'n_preserved': int,
                'n_violated': int,
                'n_total': int,
                'violated_pairs': List,  # 符号が変わったペア（最大10件）
            },
            'order_preservation': {
                'spearman_rho': float,  # Spearman順位相関係数
            },
            'edge_weight_stats': Dict,
            'kernel_comparison': {
                'max_kernel_diff': float,
                'mean_kernel_diff': float,
                'max_distance_diff': float,
                'mean_distance_diff': float,
            }
        }
    """
    if len(networks) < 2:
        return {
            'sign_preservation': {
                'rate': None,
                'n_preserved': 0,
                'n_violated': 0,
                'n_total': 0,
                'violated_pairs': [],
            },
            'order_preservation': {
                'spearman_rho': None,
            },
            'edge_weight_stats': {},
            'kernel_comparison': {},
            'error': 'need >= 2 networks',
        }

    # エッジ重みの統計
    all_weights = []
    for network in networks:
        for edge in network.get('edges', []):
            weight = edge.get('weight', 0)
            if weight is not None:
                all_weights.append(weight)

    edge_stats = {}
    if all_weights:
        weights = np.array(all_weights)
        edge_stats = {
            'count': len(weights),
            'mean': float(np.mean(weights)),
            'std': float(np.std(weights)),
            'min': float(np.min(weights)),
            'max': float(np.max(weights)),
            'n_positive': int(np.sum(weights > 0)),
            'n_negative': int(np.sum(weights < 0)),
            'n_zero': int(np.sum(weights == 0)),
        }

    # 連続モードでカーネル計算
    kernel_continuous = WeightedWLKernel(
        n_iterations=n_iterations,
        weight_mode='continuous'
    )
    K_cont = kernel_continuous.fit_transform(networks)

    # 離散モードでカーネル計算
    kernel_discrete = WeightedWLKernel(
        n_iterations=n_iterations,
        weight_mode='discrete'
    )
    K_disc = kernel_discrete.fit_transform(networks)

    n = len(networks)

    # =================================================================
    # 1. 符号保存の評価
    # =================================================================
    # カーネル値の符号（類似度の正負）が保存されるか
    # 注: 正規化カーネルは通常 [0,1] だが、差分や特殊なケースで負になりうる

    sign_preserved = 0
    sign_violated = 0
    violated_pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            # カーネル値から0.5を引いて中心化（類似/非類似の境界）
            # または距離行列の符号で比較
            k_cont = K_cont[i, j]
            k_disc = K_disc[i, j]

            # 類似度の相対的な大小関係で符号を定義
            # (平均との比較: 平均より大きければ「類似」、小さければ「非類似」)
            mean_cont = np.mean(_extract_upper_triangle(K_cont))
            mean_disc = np.mean(_extract_upper_triangle(K_disc))

            sign_cont = 1 if k_cont >= mean_cont else -1
            sign_disc = 1 if k_disc >= mean_disc else -1

            if sign_cont == sign_disc:
                sign_preserved += 1
            else:
                sign_violated += 1
                violated_pairs.append({'i': i, 'j': j, 'k_cont': k_cont, 'k_disc': k_disc})

    n_pairs = n * (n - 1) // 2
    sign_rate = sign_preserved / n_pairs if n_pairs > 0 else 1.0

    sign_preservation = {
        'rate': float(sign_rate),
        'n_preserved': sign_preserved,
        'n_violated': sign_violated,
        'n_total': n_pairs,
        'violated_pairs': violated_pairs[:10],  # 最大10件まで
    }

    # =================================================================
    # 2. 順序保存の評価（Spearman ρ）
    # =================================================================
    # 距離行列を計算
    D_cont = kernel_to_distance(K_cont)
    D_disc = kernel_to_distance(K_disc)

    # 上三角要素を抽出してSpearman相関を計算
    d_cont_flat = _extract_upper_triangle(D_cont)
    d_disc_flat = _extract_upper_triangle(D_disc)

    spearman_rho = _spearman_rho(d_cont_flat, d_disc_flat)

    order_preservation = {
        'spearman_rho': float(spearman_rho),
    }

    # =================================================================
    # 3. カーネル/距離の差分統計
    # =================================================================
    K_diff = np.abs(K_cont - K_disc)
    D_diff = np.abs(D_cont - D_disc)

    kernel_comparison = {
        'max_kernel_diff': float(np.max(K_diff)),
        'mean_kernel_diff': float(np.mean(K_diff)),
        'max_distance_diff': float(np.max(D_diff)),
        'mean_distance_diff': float(np.mean(D_diff)),
    }

    return {
        'sign_preservation': sign_preservation,
        'order_preservation': order_preservation,
        'edge_weight_stats': edge_stats,
        'kernel_comparison': kernel_comparison,
    }


# =============================================================================
# 便利関数
# =============================================================================

def compute_weighted_wl_kernel(
    networks: List[Dict],
    iterations: int = 3,
    weight_mode: str = 'continuous',
    weight_modes: Optional[List[str]] = None
) -> np.ndarray:
    """
    Weighted WLカーネルを計算する便利関数

    既存の compute_wl_kernel (mds.py) と同じインターフェース

    Args:
        networks: ネットワークのリスト
        iterations: WL反復回数
        weight_mode: デフォルトのweight_mode（weight_modesが指定されていない場合に使用）
        weight_modes: 各ネットワークのweight_modeリスト（オプション）
                      指定された場合はweight_modeパラメータより優先

    Returns:
        正規化されたカーネル行列
    """
    kernel = WeightedWLKernel(
        n_iterations=iterations,
        weight_mode=weight_mode
    )
    return kernel.fit_transform(networks, weight_modes=weight_modes)
