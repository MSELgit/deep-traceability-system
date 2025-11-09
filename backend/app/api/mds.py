from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize
import time
from typing import Any
import logging
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# ===== パフォーマンス計測 =====

class PerformanceTimer:
    """パフォーマンス計測用のコンテキストマネージャ"""
    def __init__(self, name: str, timing_dict: dict = None):
        self.name = name
        self.timing_dict = timing_dict
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.info(f"⏱️  [{self.name}] 開始")
        return self
    
    def __exit__(self, *args):
        elapsed = time.perf_counter() - self.start_time
        logger.info(f"✅ [{self.name}] 完了: {elapsed:.4f}秒")
        if self.timing_dict is not None:
            self.timing_dict[self.name] = round(elapsed, 4)

# ===== Pydanticモデル =====

class NetworkComparisonRequest(BaseModel):
    networks: List[dict]
    iterations: int = 1
    method: str = "circular_mds"
    n_init: int = 50
    compare_methods: bool = True
    n_workers: Optional[int] = None  # 追加：並列ワーカー数（Noneで自動）

class NetworkComparisonResponse(BaseModel):
    success: bool
    wl_iterations: int
    label_count: int
    kernel_matrix: List[List[float]]
    distance_matrix: List[List[float]]
    coordinates: List[List[float]]
    thetas: List[float]
    circular_coordinates: List[List[float]]
    stress: float
    circular_stress: float
    comparison: Optional[dict] = None
    timing: Optional[Dict[str, float]] = None

# ===== 並列化用のヘルパー関数（トップレベル関数として定義） =====

def _optimize_single_trial(args):
    """単一の最適化試行（並列実行用）
    
    Args:
        args: (D_normalized, n, seed) のタプル
    
    Returns:
        (stress, thetas) のタプル
    """
    D_normalized, n, seed = args
    
    # 各ワーカーで乱数シードを設定
    np.random.seed(seed)
    
    def circular_distance(theta_i: float, theta_j: float) -> float:
        diff = abs(theta_i - theta_j)
        return min(diff, 2*np.pi - diff)
    
    def stress_function(thetas):
        total = 0
        for i in range(n):
            for j in range(i+1, n):
                circ_dist = circular_distance(thetas[i], thetas[j])
                total += (D_normalized[i,j] - circ_dist)**2
        return total
    
    # ランダム初期化
    theta0 = np.random.uniform(0, 2*np.pi, n)
    
    # 最適化
    result = minimize(
        stress_function,
        theta0,
        method='L-BFGS-B',
        bounds=[(0, 2*np.pi)]*n,
        options={'maxiter': 1000}
    )
    
    return (result.fun, result.x)

# ===== 内部計算関数 =====

def classical_mds(distance_matrix: List[List[float]], n_components: int = 2) -> dict:
    """Classical MDS implementation"""
    D = np.array(distance_matrix)
    n = D.shape[0]
    
    if D.shape[0] != D.shape[1]:
        raise ValueError("Distance matrix must be square")
    
    # Double centering
    D_squared = D ** 2
    row_mean = D_squared.mean(axis=1)
    col_mean = D_squared.mean(axis=0)
    total_mean = D_squared.mean()
    
    B = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            B[i, j] = -0.5 * (D_squared[i, j] - row_mean[i] - col_mean[j] + total_mean)
    
    # Eigenvalue decomposition
    eigenvalues, eigenvectors = eigh(B)
    
    # Sort by eigenvalue (descending)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Compute coordinates
    coordinates = np.zeros((n, n_components))
    for i in range(n_components):
        if eigenvalues[i] > 0:
            coordinates[:, i] = eigenvectors[:, i] * np.sqrt(eigenvalues[i])
    
    # Normalize to [-1, 1] range
    max_coord = np.max(np.abs(coordinates))
    if max_coord > 0:
        coordinates = coordinates / max_coord
    
    # Calculate stress
    stress = 0
    dist_sum = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = coordinates[i, 0] - coordinates[j, 0]
            dy = coordinates[i, 1] - coordinates[j, 1]
            embedded_dist = np.sqrt(dx*dx + dy*dy)
            orig_dist = D[i, j]
            stress += (orig_dist - embedded_dist) ** 2
            dist_sum += orig_dist ** 2
    
    stress = np.sqrt(stress / dist_sum) if dist_sum > 0 else 0
    
    return {
        'coordinates': coordinates.tolist(),
        'eigenvalues': eigenvalues[:n_components].tolist(),
        'stress': float(stress)
    }

def circular_mds_parallel(distance_matrix: np.ndarray, n_init: int = 50, n_workers: int = None) -> tuple:
    """距離行列から直接円環座標を計算（並列版Circular MDS）
    
    Args:
        distance_matrix: 距離行列
        n_init: 初期値試行回数
        n_workers: 並列ワーカー数（Noneで自動：CPU数）
    
    Returns:
        (thetas, normalized_stress) のタプル
    """
    D = np.array(distance_matrix)
    n = len(D)
    
    # 距離を[0, π]の範囲に正規化
    max_dist = np.max(D)
    if max_dist > 0:
        D_normalized = (D / max_dist) * np.pi
    else:
        D_normalized = D
    
    # ワーカー数の決定
    if n_workers is None:
        n_workers = min(multiprocessing.cpu_count(), n_init)
    
    logger.info(f"   並列Circular MDS: {n_init}回の試行を{n_workers}ワーカーで実行")
    
    # 並列実行の準備（各試行に異なるシードを割り当て）
    args_list = [(D_normalized, n, seed) for seed in range(n_init)]
    
    optimization_start = time.perf_counter()
    
    # 並列実行
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(_optimize_single_trial, args_list))
    
    optimization_time = time.perf_counter() - optimization_start
    
    # 最良の結果を選択
    best_stress, best_thetas = min(results, key=lambda x: x[0])
    
    # ストレスを正規化
    normalized_stress = np.sqrt(best_stress / (n * (n-1) / 2))
    
    logger.info(f"   並列最適化完了: {optimization_time:.4f}秒")
    logger.info(f"   実効速度: {n_init/optimization_time:.1f}試行/秒 (理論値: {n_workers}並列)")
    
    return best_thetas, normalized_stress

def circular_mds_sequential(distance_matrix: np.ndarray, n_init: int = 50) -> tuple:
    """距離行列から直接円環座標を計算（逐次版Circular MDS）"""
    
    def circular_distance(theta_i: float, theta_j: float) -> float:
        diff = abs(theta_i - theta_j)
        return min(diff, 2*np.pi - diff)
    
    D = np.array(distance_matrix)
    n = len(D)
    
    # 距離を[0, π]の範囲に正規化
    max_dist = np.max(D)
    if max_dist > 0:
        D_normalized = (D / max_dist) * np.pi
    else:
        D_normalized = D
    
    def stress_function(thetas):
        total = 0
        for i in range(n):
            for j in range(i+1, n):
                circ_dist = circular_distance(thetas[i], thetas[j])
                total += (D_normalized[i,j] - circ_dist)**2
        return total
    
    # 複数の初期値で最適化
    best_result = None
    best_stress = float('inf')
    
    logger.info(f"  🔄 逐次Circular MDS: {n_init}回の試行")
    
    for trial in range(n_init):
        theta0 = np.random.uniform(0, 2*np.pi, n)
        
        result = minimize(
            stress_function,
            theta0,
            method='L-BFGS-B',
            bounds=[(0, 2*np.pi)]*n,
            options={'maxiter': 1000}
        )
        
        if result.fun < best_stress:
            best_stress = result.fun
            best_result = result
    
    # ストレスを正規化
    normalized_stress = np.sqrt(best_stress / (n * (n-1) / 2))
    
    return best_result.x, normalized_stress

def compute_circular_stress(D: np.ndarray, thetas: np.ndarray) -> float:
    """円環距離でのストレス計算"""
    
    def circular_distance(theta_i: float, theta_j: float) -> float:
        diff = abs(theta_i - theta_j)
        return min(diff, 2*np.pi - diff)
    
    n = len(thetas)
    max_dist = np.max(D)
    if max_dist > 0:
        D_normalized = (D / max_dist) * np.pi
    else:
        D_normalized = D
    
    stress = 0
    for i in range(n):
        for j in range(i+1, n):
            circ_dist = circular_distance(thetas[i], thetas[j])
            stress += (D_normalized[i,j] - circ_dist)**2
    
    return np.sqrt(stress / (n * (n-1) / 2))

def compute_wl_kernel(networks: List[dict], iterations: int) -> np.ndarray:
    """Weisfeiler-Lehmanカーネル計算"""
    n = len(networks)
    kernel = np.zeros((n, n))
    
    # ラベル履歴を保存
    label_histories = []
    
    # 初期ラベルの設定
    for net in networks:
        initial_labels = []
        for node in net['nodes']:
            in_degree = sum(1 for e in net['edges'] if e['target_id'] == node['id'])
            out_degree = sum(1 for e in net['edges'] if e['source_id'] == node['id'])
            degree = in_degree + out_degree
            
            label = f"L{node['layer']}-{node['type'][0].upper()}-D{degree}"
            initial_labels.append(label)
        
        label_histories.append([initial_labels])
    
    # WL反復
    for iter_num in range(iterations + 1):
        if iter_num > 0:
            for net_idx, net in enumerate(networks):
                prev_labels = label_histories[net_idx][iter_num - 1]
                new_labels = []
                
                for node_idx, node in enumerate(net['nodes']):
                    neighbor_info = []
                    
                    for edge in net['edges']:
                        if edge['source_id'] == node['id']:
                            target_idx = next(i for i, n in enumerate(net['nodes']) if n['id'] == edge['target_id'])
                            # weightがNoneや未定義の場合は0をデフォルト値として使用
                            weight = edge.get('weight')
                            if weight is None:
                                weight = 0
                            neighbor_info.append({
                                'label': prev_labels[target_idx],
                                'weight': weight
                            })
                        elif edge['target_id'] == node['id']:
                            source_idx = next(i for i, n in enumerate(net['nodes']) if n['id'] == edge['source_id'])
                            # weightがNoneや未定義の場合は0をデフォルト値として使用
                            weight = edge.get('weight')
                            if weight is None:
                                weight = 0
                            neighbor_info.append({
                                'label': prev_labels[source_idx],
                                'weight': weight
                            })

                    sorted_neighbors = sorted([
                        f"{info['label']}@{round(info['weight'] * 100) / 100}"
                        for info in neighbor_info
                    ])
                    new_label = f"{prev_labels[node_idx]}|[{','.join(sorted_neighbors)}]"
                    new_labels.append(new_label)
                
                label_histories[net_idx].append(new_labels)
        
        # カーネル値の更新
        for i in range(n):
            for j in range(i, n):
                labels_i = label_histories[i][iter_num]
                labels_j = label_histories[j][iter_num]
                
                count_i = {}
                count_j = {}
                
                for label in labels_i:
                    count_i[label] = count_i.get(label, 0) + 1
                for label in labels_j:
                    count_j[label] = count_j.get(label, 0) + 1
                
                dot_product = sum(
                    count_i[label] * count_j.get(label, 0)
                    for label in count_i
                )
                
                kernel[i, j] += dot_product
                if i != j:
                    kernel[j, i] += dot_product
    
    # 正規化
    normalized_kernel = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if kernel[i, i] > 0 and kernel[j, j] > 0:
                normalized_kernel[i, j] = kernel[i, j] / np.sqrt(kernel[i, i] * kernel[j, j])
    
    return normalized_kernel

def kernel_to_distance(kernel: np.ndarray) -> np.ndarray:
    """カーネル行列から距離行列を計算"""
    n = len(kernel)
    distances = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            dist = np.sqrt(max(0, kernel[i, i] + kernel[j, j] - 2 * kernel[i, j]))
            distances[i, j] = dist
    
    return distances

# ===== APIエンドポイント =====

@router.post("/compute_network_comparison", response_model=NetworkComparisonResponse)
async def compute_network_comparison(request: NetworkComparisonRequest):
    """ネットワーク構造比較の全計算を一括実行"""
    timing = {}
    total_start = time.perf_counter()
    
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 ネットワーク比較計算開始")
        logger.info(f"  ネットワーク数: {len(request.networks)}")
        logger.info(f"  WL反復回数: {request.iterations}")
        logger.info(f"  MDS手法: {request.method}")
        logger.info(f"  n_init: {request.n_init}")
        logger.info(f"  並列ワーカー数: {request.n_workers or 'auto'}")
        logger.info(f"  比較モード: {request.compare_methods}")
        logger.info(f"{'='*60}\n")
        
        # WLカーネル計算
        with PerformanceTimer("WLカーネル計算", timing):
            kernel_matrix = compute_wl_kernel(request.networks, request.iterations)
        
        # 距離行列計算
        with PerformanceTimer("距離行列計算", timing):
            distance_matrix = kernel_to_distance(kernel_matrix)
        
        # ユニークラベル数
        with PerformanceTimer("ラベル数集計", timing):
            label_count = len(set(
                f"L{node['layer']}-{node['type'][0]}"
                for net in request.networks
                for node in net['nodes']
            ))
        
        # MDS計算（比較）
        comparison_results = {}
        selected_result = None
        
        methods = ['mds_polar', 'circular_mds'] if request.compare_methods else [request.method]
        
        for method in methods:
            method_start = time.perf_counter()
            logger.info(f"\n📊 MDS計算開始: {method}")
            
            if method == 'mds_polar':
                with PerformanceTimer(f"MDS計算 ({method})", timing):
                    mds_result = classical_mds(distance_matrix.tolist(), 2)
                    coords = np.array(mds_result['coordinates'])
                    thetas = np.arctan2(coords[:, 1], coords[:, 0])
                    thetas = (thetas + 2*np.pi) % (2*np.pi)
                
                with PerformanceTimer(f"円環ストレス計算 ({method})", timing):
                    circular_stress = compute_circular_stress(distance_matrix, thetas)
                
                stress = mds_result['stress']
            else:  # circular_mds
                with PerformanceTimer(f"Circular MDS計算 ({method})", timing):
                    # 並列版を使用
                    thetas, circular_stress = circular_mds_parallel(
                        distance_matrix,
                        request.n_init,
                        request.n_workers
                    )
                    stress = circular_stress
                    coords = np.column_stack([np.cos(thetas), np.sin(thetas)])
            
            method_time = time.perf_counter() - method_start
            logger.info(f"✅ {method} 完了: {method_time:.4f}秒")
            
            result = {
                'stress': float(stress),
                'circular_stress': float(circular_stress),
                'thetas': thetas.tolist(),
                'coordinates': coords.tolist()
            }
            
            comparison_results[method] = result
            
            if method == request.method:
                selected_result = result
        
        # 円環座標（可視化用）
        with PerformanceTimer("円環座標変換", timing):
            radius = 250
            circular_coords = [
                [radius * np.cos(theta), radius * np.sin(theta)]
                for theta in selected_result['thetas']
            ]
        
        total_time = time.perf_counter() - total_start
        timing['total'] = round(total_time, 4)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 全計算完了: {total_time:.4f}秒")
        logger.info(f"{'='*60}\n")
        
        logger.info("⏱️  処理時間サマリー:")
        for key, value in sorted(timing.items(), key=lambda x: -x[1]):
            percentage = (value / total_time * 100) if total_time > 0 else 0
            logger.info(f"  {key:.<40} {value:.4f}秒 ({percentage:>5.1f}%)")
        logger.info("")
        
        return NetworkComparisonResponse(
            success=True,
            wl_iterations=request.iterations,
            label_count=label_count,
            kernel_matrix=kernel_matrix.tolist(),
            distance_matrix=distance_matrix.tolist(),
            coordinates=selected_result['coordinates'],
            thetas=selected_result['thetas'],
            circular_coordinates=circular_coords,
            stress=selected_result['stress'],
            circular_stress=selected_result['circular_stress'],
            comparison=comparison_results if request.compare_methods else None,
            timing=timing
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))