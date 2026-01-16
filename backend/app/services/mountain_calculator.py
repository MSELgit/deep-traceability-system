# backend/app/services/mountain_calculator.py

"""
山の座標計算サービス

設計案をMDS+円錐マッピングで3D空間に配置
"""

import numpy as np
from sklearn.manifold import MDS
from scipy.spatial.distance import pdist, squareform
from typing import List, Dict
from sqlalchemy.orm import Session
import json
import time

from app.models.database import ProjectModel, DesignCaseModel, NeedPerformanceRelationModel
from app.api.mds import compute_wl_kernel, kernel_to_distance, circular_mds_parallel
from app.services.structural_energy import compute_structural_energy


# Timing utility
class Timer:
    """計算時間計測用ユーティリティ"""
    def __init__(self):
        self.timings = {}
        self._start_times = {}

    def start(self, name: str):
        self._start_times[name] = time.time()

    def stop(self, name: str):
        if name in self._start_times:
            elapsed = (time.time() - self._start_times[name]) * 1000  # ms
            self.timings[name] = elapsed
            del self._start_times[name]

    def get_report(self) -> Dict[str, float]:
        return self.timings.copy()

    def print_report(self, prefix: str = ""):
        print(f"\n{'='*60}")
        print(f"⏱️  {prefix}Timing Report")
        print(f"{'='*60}")
        total = 0
        for name, ms in self.timings.items():
            print(f"  {name}: {ms:.2f} ms")
            total += ms
        print(f"{'─'*60}")
        print(f"  TOTAL: {total:.2f} ms")
        print(f"{'='*60}\n")

def calculate_network_kernel(networks: List[Dict]) -> np.ndarray:
    """
    ネットワーク間のカーネル行列を計算
    
    Args:
        networks: 各設計案のネットワーク情報のリスト
                  [{'nodes': [...], 'edges': [...]}, ...]
    
    Returns:
        カーネル行列 K (n x n)
    """
    n = len(networks)
    K = np.zeros((n, n))
    
    
    for i in range(n):
        for j in range(i, n):
            # 簡単なネットワーク類似度: エッジの共通度
            edges_i = set((e['source_id'], e['target_id']) for e in networks[i]['edges'])
            edges_j = set((e['source_id'], e['target_id']) for e in networks[j]['edges'])
            
            # Jaccard係数
            intersection = len(edges_i & edges_j)
            union = len(edges_i | edges_j)
            similarity = intersection / union if union > 0 else 0.0
            
            K[i, j] = similarity
            K[j, i] = similarity
            
    return K


def circular_mds_one_iteration(K: np.ndarray, initial_theta: np.ndarray = None) -> np.ndarray:
    """
    円環MDS: 1回の反復でθを計算
    
    Args:
        K: カーネル行列 (n x n)
        initial_theta: 初期角度 (n,)。Noneの場合は等間隔に配置
    
    Returns:
        更新されたθ (n,)
    """
    n = K.shape[0]
    
    # 初期角度の設定
    if initial_theta is None:
        # 等間隔に配置
        theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    else:
        theta = initial_theta.copy()
    
    # 1反復: カーネル行列から理想的な内積を計算し、角度を更新
    # 簡易的な更新: K[i,j] ≈ cos(θ_i - θ_j) を満たすようにθを調整
    
    # 中心化カーネル
    H = np.eye(n) - np.ones((n, n)) / n
    K_centered = H @ K @ H
    
    # 固有値分解
    eigenvalues, eigenvectors = np.linalg.eigh(K_centered)
    
    # 最大固有値に対応する固有ベクトルを使用して角度を決定
    # 2次元埋め込みの場合、上位2つの固有ベクトルを使用
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    
    # 上位2つの固有ベクトルから2D座標を計算
    if n > 1:
        v1 = eigenvectors[:, 0] * np.sqrt(max(0, eigenvalues[0]))
        v2 = eigenvectors[:, 1] * np.sqrt(max(0, eigenvalues[1]))
        
        # 角度を計算
        theta_updated = np.arctan2(v2, v1)
        
        # [0, 2π)の範囲に正規化
        theta_updated = theta_updated % (2 * np.pi)
    else:
        theta_updated = np.array([0.0])
    
    
    return theta_updated


# HHI calculatorから移植した関数
def calculate_effective_votes(up_votes: float, down_votes: float) -> float:
    """
    有効投票数を計算（方向性を考慮）
    
    I(a, b) = (a + b) * [1 + H(x)]
    where H(x) = -x*log2(x) - (1-x)*log2(1-x) (Shannon entropy)
    """
    total = up_votes + down_votes
    if total == 0:
        return 0.0
    
    x = up_votes / total
    
    # Shannon entropy
    if x == 0 or x == 1:
        entropy = 0
    else:
        entropy = -x * np.log2(x) - (1 - x) * np.log2(1 - x)
    
    return total * (1 + entropy)


def distribute_votes_to_needs(project: ProjectModel) -> Dict[str, float]:
    """ステークホルダーの票をニーズに按分（重み付き）

    各ニーズのpriorityも適用される
    """
    need_votes = {}

    # ニーズIDからpriorityを取得するマップを作成
    need_priorities = {need.id: (need.priority if need.priority is not None else 1.0)
                       for need in project.needs}

    for stakeholder in project.stakeholders:
        # 重みを含む関係を取得
        related_needs = [(r.need_id, r.relationship_weight or 1.0) for r in project.stakeholder_need_relations
                        if r.stakeholder_id == stakeholder.id and (r.relationship_weight or 1.0) > 0]

        if len(related_needs) > 0:
            # 総重みを計算
            total_weight = sum(weight for _, weight in related_needs)

            # 重みに比例して票を配分
            for need_id, weight in related_needs:
                vote_portion = (weight / total_weight) * stakeholder.votes
                # priorityを適用
                priority = need_priorities.get(need_id, 1.0)
                need_votes[need_id] = need_votes.get(need_id, 0) + (vote_portion * priority)

    return need_votes


def distribute_votes_to_performances(project: ProjectModel, need_votes: Dict[str, float]) -> Dict[tuple, Dict[str, float]]:
    """
    ニーズの票を性能に按分し、↑↓票を集計
    
    Returns:
        {(performance_id, need_id): {'up': float, 'down': float}}
    """
    performance_need_votes = {}
    
    
    for need_id, votes in need_votes.items():
        related_perfs = [r for r in project.need_performance_relations 
                        if r.need_id == need_id]
        
        if len(related_perfs) > 0:
            votes_per_perf = votes / len(related_perfs)
            for rel in related_perfs:
                perf_id = rel.performance_id
                key = (perf_id, need_id)
                
                if key not in performance_need_votes:
                    performance_need_votes[key] = {'up': 0.0, 'down': 0.0}
                
                if rel.direction == 'up':
                    performance_need_votes[key]['up'] += votes_per_perf
                else:
                    performance_need_votes[key]['down'] += votes_per_perf
    
    return performance_need_votes


def interpolate_utility_function(points: List[Dict], value: float) -> float:
    """
    効用関数を補間して効用値を計算
    
    Args:
        points: [{"x": キャンバス座標, "y": キャンバス座標, "valueX": 性能値, "valueY": 効用値}, ...]
        value: 実際の性能値
    
    Returns:
        効用値（0~1）
    """
    if not points:
        return 0.5  # デフォルト値
    
    # valueXとvalueYを使用（実際の値）
    actual_points = []
    for p in points:
        if 'valueX' in p and 'valueY' in p:
            actual_points.append({'x': p['valueX'], 'y': p['valueY']})
        else:
            # 古いフォーマットの場合はx,yをそのまま使用
            actual_points.append({'x': p['x'], 'y': p['y']})
    
    if not actual_points:
        return 0.5
    
    # x値でソート
    sorted_points = sorted(actual_points, key=lambda p: p['x'])
    
    # 範囲外の処理：効用関数の定義範囲外は0を返す
    if value < sorted_points[0]['x']:
        return 0.0
    if value > sorted_points[-1]['x']:
        return 0.0
    
    # 線形補間
    for i in range(len(sorted_points) - 1):
        x1, y1 = sorted_points[i]['x'], sorted_points[i]['y']
        x2, y2 = sorted_points[i + 1]['x'], sorted_points[i + 1]['y']
        
        if x1 <= value <= x2:
            if x2 == x1:
                return y1
            ratio = (value - x1) / (x2 - x1)
            return y1 + ratio * (y2 - y1)
    
    return 0.5


def calculate_utility_vector(
    design_case: DesignCaseModel,
    project: ProjectModel,
    performance_need_relations: List
) -> Dict[tuple, float]:
    """
    設計案の効用ベクトルを計算（性能×ニーズのペアごと）
    
    Args:
        design_case: 設計案モデル
        project: プロジェクトモデル
        performance_need_relations: 性能-ニーズ関係のリスト
    
    Returns:
        {(performance_id, need_id): utility_value}
        効用関数未設定または性能値未設定の場合は0.0
    """
    performance_values = json.loads(design_case.performance_values_json)
    utility_vector = {}
    
    relations_with_utility = 0
    
    for rel in performance_need_relations:
        key = (rel.performance_id, rel.need_id)
        
        # 性能値が設定されているか確認
        perf_value = performance_values.get(rel.performance_id)
        if perf_value is None:
            # 性能値未設定 → 部分標高0
            utility_vector[key] = 0.0
            continue
        
        # 効用関数が設定されているか確認
        if not rel.utility_function_json:
            # 効用関数未設定 → 部分標高0
            utility_vector[key] = 0.0
            continue
        
        relations_with_utility += 1
        
        # 効用関数で補間
        utility_func = json.loads(rel.utility_function_json)
        func_type = utility_func.get('type', 'continuous')
        
        if func_type == 'discrete':
            # 離散値の場合
            discrete_rows = utility_func.get('discreteRows', [])
            # labelが一致するものを探す
            utility = 0.0
            for row in discrete_rows:
                if str(row.get('label')) == str(perf_value):
                    utility = row.get('value', 0.0)
                    break
            utility_vector[key] = utility
        else:
            # 連続値の場合
            points = utility_func.get('points', [])
            utility = interpolate_utility_function(points, perf_value)
            utility_vector[key] = utility
    
    
    return utility_vector


def calculate_elevation(
    utility_vector: Dict[tuple, float],
    performance_need_weights: Dict[tuple, float],
    leaf_performance_ids: set = None,
    normalize_weights: bool = True
) -> float:
    """
    標高 H を計算
    
    H = Σ W'_(i,j) * U_j(f_i)  （末端性能のみ）
    ここで、W'_(i,j) = W_(i,j) / Σ W_(i,j) （正規化された重み）
    
    Args:
        utility_vector: {(performance_id, need_id): utility_value}
        performance_need_weights: {(performance_id, need_id): weight}
        leaf_performance_ids: 末端性能のIDセット（指定された場合のみフィルタ）
        normalize_weights: 重みを正規化するかどうか（デフォルトTrue）
    
    Returns:
        標高値（正規化時は0-1の範囲）
    """
    # 対象となる重みの合計を計算（正規化用）
    if normalize_weights:
        total_weight = 0.0
        for key in utility_vector.keys():
            perf_id, need_id = key
            if leaf_performance_ids is None or perf_id in leaf_performance_ids:
                total_weight += performance_need_weights.get(key, 0)
        
        if total_weight == 0:
            return 0.0
    else:
        total_weight = 1.0  # 正規化しない場合は1で除算（変更なし）
    
    H = 0.0
    for key, utility in utility_vector.items():
        perf_id, need_id = key
        # 末端性能のみを対象とする
        if leaf_performance_ids is None or perf_id in leaf_performance_ids:
            weight = performance_need_weights.get(key, 0)
            normalized_weight = weight / total_weight if total_weight > 0 else 0
            H += normalized_weight * utility
    
    return H


def calculate_mountain_positions(
    project: ProjectModel,
    db: Session,
    hemisphere_radius: float = 5.0,
    networks: List[Dict] = None  # ネットワーク情報を追加
) -> List[Dict]:
    """
    全設計案の半球座標を計算

    標高H_max（全効用関数が1.0の場合）が半球の頂点になるようにスケーリングする。
    各設計案は半球の表面上に配置される：x² + y² + z² = R²（y ≥ 0）

    Args:
        project: プロジェクトモデル
        db: データベースセッション
        hemisphere_radius: 半球の半径（デフォルト5.0）

    Returns:
        [{'case_id': str, 'x': float, 'y': float, 'z': float, 'H': float, 'utility_vector': dict}, ...]
    """
    timer = Timer()
    timer.start("total")

    design_cases = project.design_cases
    n_cases = len(design_cases)
    n_networks = len(networks) if networks else 0
    print(f"\n📊 Mountain calculation: {n_cases} design cases, {n_networks} networks")

    if len(design_cases) == 0:
        return {'positions': [], 'H_max': 1.0, 'timings': {}}

    # 1. 性能×ニーズペアごとの重みを計算
    timer.start("1_vote_distribution")
    need_votes = distribute_votes_to_needs(project)
    performance_need_votes = distribute_votes_to_performances(project, need_votes)
    timer.stop("1_vote_distribution")
    
    # 効用関数が設定されているペアを確認（標高計算用）
    relations_with_utility = set()
    for rel in project.need_performance_relations:
        if rel.utility_function_json:
            relations_with_utility.add((rel.performance_id, rel.need_id))
    
    # 全ペアの重みを計算（エネルギー計算用）
    performance_need_weights_all = {}
    for key, votes in performance_need_votes.items():
        weight = votes['up'] + votes['down']
        performance_need_weights_all[key] = weight
    
    
    # 効用関数が設定されているペアの重み（標高計算用）
    performance_need_weights = {}
    for key, weight in performance_need_weights_all.items():
        if key in relations_with_utility:
            performance_need_weights[key] = weight
    
    
    # 性能-ニーズ関係のリストを取得
    need_perf_relations = project.need_performance_relations
    
    # 現在の性能ツリーから末端性能を取得（H_max計算用）
    current_leaf_performance_ids = set()
    for perf in project.performances:
        # この性能を親として持つ子が存在するか確認
        has_children = any(p.parent_id == perf.id for p in project.performances)
        if not has_children:
            current_leaf_performance_ids.add(perf.id)
    
    # 正規化された重みを使用するため、H_maxは常に1.0
    # （全ての重みの合計が1.0に正規化され、全効用が1.0の場合）
    H_max = 1.0

    # 2. 各設計案の効用ベクトルと標高を計算
    timer.start("2_utility_vectors")
    utility_vectors = []
    elevations = []

    for case in design_cases:
        # 設計案のスナップショットから末端性能を取得
        if case.performance_snapshot:
            # スナップショットが存在する場合（すでにリスト形式）
            case_performances = case.performance_snapshot
            case_leaf_performance_ids = set()

            # スナップショット内で末端性能を判定
            for perf in case_performances:
                # この性能を親として持つ子が存在するか確認
                has_children = any(p.get('parent_id') == perf['id'] for p in case_performances)
                if not has_children:
                    case_leaf_performance_ids.add(perf['id'])
        else:
            # スナップショットがない場合は現在の性能ツリーを使用（後方互換性）
            case_leaf_performance_ids = current_leaf_performance_ids

        utility_vec = calculate_utility_vector(case, project, need_perf_relations)
        H = calculate_elevation(utility_vec, performance_need_weights, case_leaf_performance_ids)

        utility_vectors.append(utility_vec)
        elevations.append(H)
    timer.stop("2_utility_vectors")

    # 3. 効用ベクトルからMDSで2D座標を計算
    # ↓ ネットワーク情報がある場合は円環MDSを使用（テスト段階）
    if networks is not None and len(networks) > 0:

        # WLカーネル計算（反復1回）
        timer.start("3a_wl_kernel")
        K = compute_wl_kernel(networks, iterations=int(1))
        timer.stop("3a_wl_kernel")

        # カーネル→距離行列変換
        timer.start("3b_kernel_to_distance")
        distance_matrix = kernel_to_distance(K)
        timer.stop("3b_kernel_to_distance")

        # 円環MDS（並列版、n_init=500）
        timer.start("3c_circular_mds")
        circular_mds_angles, circular_stress = circular_mds_parallel(
            distance_matrix,
            n_init=500,
            n_workers=None  # 自動でCPU数に応じて設定
        )
        timer.stop("3c_circular_mds")
        print(f"   Circular MDS stress: {circular_stress:.6f}")

        mds_angles = circular_mds_angles
    else:
        # 既存のMDS処理（効用ベクトルベース）
        if len(design_cases) == 1:
            # 1案のみの場合は原点に配置
            mds_coords = np.array([[0, 0]])
            mds_angles = np.array([0])
        else:
            # 効用ベクトルを行列に変換
            # (performance_id, need_id)のキーを統一
            all_keys = sorted(utility_vectors[0].keys())
            U_matrix = np.array([
                [uv.get(key, 0.0) for key in all_keys]
                for uv in utility_vectors
            ])
            
            # ユークリッド距離行列を計算
            distances = squareform(pdist(U_matrix, metric='euclidean'))
            
            # MDSで2次元に削減
            mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
            mds_coords = mds.fit_transform(distances)
            
            # 4. MDS座標を極座標に変換（第1案を基準に回転）
            # 第1案を角度0に固定
            mds_angles = np.arctan2(mds_coords[:, 1], mds_coords[:, 0])
            mds_angles = mds_angles - mds_angles[0]  # 第1案を0度に
    
    # 5. 最高標高の案を正面（角度0）に配置するため回転
    max_H_index = np.argmax(elevations)
    rotation_offset = -mds_angles[max_H_index]
    mds_angles = mds_angles + rotation_offset

    # 6. 円錐座標に変換（半球の制約に従う）
    timer.start("4_position_calculation")
    # 半球の半径を設定（H_maxが頂点になるように）
    hemisphere_radius = 10.0  # 半球の半径

    positions = []
    
    for i, case in enumerate(design_cases):
        H = elevations[i]
        theta = mds_angles[i]
        
        # 標高をスケーリング（H_max → hemisphere_radius）
        y = (H / H_max) * hemisphere_radius
        
        # 半球の制約：x² + z² = R² - y²
        # 標高に応じた半径を計算
        r_squared = hemisphere_radius ** 2 - y ** 2
        r = np.sqrt(max(0, r_squared))  # 負にならないように
        
        x = r * np.cos(theta)
        z = r * np.sin(theta)
        
        # 設計案のスナップショットから末端性能を取得（部分標高計算用）
        if case.performance_snapshot:
            # スナップショットが存在する場合（すでにリスト形式）
            case_performances = case.performance_snapshot
            case_leaf_performance_ids = set()
            
            # スナップショット内で末端性能を判定
            for perf in case_performances:
                # この性能を親として持つ子が存在するか確認
                has_children = any(p.get('parent_id') == perf['id'] for p in case_performances)
                if not has_children:
                    case_leaf_performance_ids.add(perf['id'])
        else:
            # スナップショットがない場合は現在の性能ツリーを使用（後方互換性）
            case_leaf_performance_ids = current_leaf_performance_ids
        
        # 部分標高を計算（末端性能ごとに集計）
        partial_heights = {}
        performance_total_weights = {}  # 性能ごとの合計票数（全ペアから集計）
        
        # まず全性能の合計票数を計算（効用関数の有無に関わらず）
        for key, weight in performance_need_weights_all.items():
            perf_id, _ = key
            # 設計案のスナップショットの末端性能のみを対象
            if perf_id in case_leaf_performance_ids:
                if perf_id not in performance_total_weights:
                    performance_total_weights[perf_id] = 0.0
                performance_total_weights[perf_id] += weight
        
        # 部分標高を計算（効用関数があるペアのみ）
        for key, utility in utility_vectors[i].items():
            perf_id, _ = key
            # 設計案のスナップショットの末端性能のみを対象
            if perf_id in case_leaf_performance_ids:
                weight = performance_need_weights.get(key, 0)  # 効用関数があるペアのみ
                partial_h = weight * utility
                
                if perf_id not in partial_heights:
                    partial_heights[perf_id] = 0.0
                partial_heights[perf_id] += partial_h
        
        
        positions.append({
            'case_id': case.id,
            'x': float(x),
            'y': float(y),
            'z': float(z),
            'H': float(H),
            'utility_vector': utility_vectors[i],
            'partial_heights': partial_heights,  # 性能ごとの部分標高
            'performance_weights': performance_total_weights  # 性能ごとの合計票数
        })
    timer.stop("4_position_calculation")

    # 7. データベースに座標を保存（オプション）
    timer.start("5_energy_and_db")
    for i, case in enumerate(design_cases):
        # 論文準拠エネルギーを計算
        # E = Σ(i<j) W_i × W_j × L(C_ij) / (Σ W_i)²
        network = case.network
        perf_weights = case.performance_weights or {}
        weight_mode = getattr(case, 'weight_mode', 'discrete_7') or 'discrete_7'

        if network and 'nodes' in network and 'edges' in network:
            energy_result = compute_structural_energy(
                network=network,
                performance_weights=perf_weights,
                weight_mode=weight_mode
            )
            total_energy = energy_result['E']

            # 性能ごとの部分エネルギーを集計（論文準拠: E_ij から E_i を導出）
            partial_energies = {}
            for contrib in energy_result.get('energy_contributions', []):
                perf_i_id = contrib['perf_i_id']
                perf_j_id = contrib['perf_j_id']
                contribution = contrib['contribution']
                # 各性能に半分ずつ配分
                partial_energies[perf_i_id] = partial_energies.get(perf_i_id, 0) + contribution / 2
                partial_energies[perf_j_id] = partial_energies.get(perf_j_id, 0) + contribution / 2
        else:
            total_energy = 0.0
            partial_energies = {}

        positions[i]['energy'] = {
            'total_energy': total_energy,
            'partial_energies': partial_energies
        }

        # 座標とエネルギーを保存（partial_energiesも含む）
        case.mountain_position_json = json.dumps({
            'x': positions[i]['x'],
            'y': positions[i]['y'],
            'z': positions[i]['z'],
            'H': positions[i]['H'],
            'total_energy': total_energy,
            'partial_energies': partial_energies
        })
        # utility_vectorはタプルキーをJSON化できないので文字列キーに変換
        utility_vec_str_keys = {
            f"{k[0]}_{k[1]}": v for k, v in positions[i]['utility_vector'].items()
        }
        case.utility_vector_json = json.dumps(utility_vec_str_keys)
        # 返却値も文字列キーに変換（APIレスポンス用）
        positions[i]['utility_vector'] = utility_vec_str_keys

        # 部分標高も保存
        case.partial_heights_json = json.dumps(positions[i]['partial_heights'])

        # 性能ごとの合計票数も保存
        case.performance_weights_json = json.dumps(positions[i]['performance_weights'])

    db.commit()
    timer.stop("5_energy_and_db")

    timer.stop("total")
    timer.print_report("Mountain Calculator ")

    return {
        'positions': positions,
        'H_max': float(H_max),
        'timings': timer.get_report()
    }