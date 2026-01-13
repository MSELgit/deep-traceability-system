# backend/app/services/weight_normalization.py
"""
離散値重み ↔ 連続値重みの変換モジュール

論文6章準拠: 各離散化スキームにおける均等分割

離散化スキーム:
- 3段階: {-1, 0, +1} → {-2/3, 0, +2/3}
- 5段階: {-3, -1, 0, +1, +3} → {-4/5, -2/5, 0, +2/5, +4/5}
- 7段階: {-3, -1, -1/3, 0, +1/3, +1, +3} → {-6/7, -4/7, -2/7, 0, +2/7, +4/7, +6/7}

一般形式:
- n段階 (n = 2k+1) の場合、連続値は ±2i/(n+1) for i = 0, 1, ..., k
- 最大値は 2k/(n+1) = (n-1)/(n+1)
"""

from typing import Dict, List, Literal, Optional, Tuple
import numpy as np

# =============================================================================
# 定数定義
# =============================================================================

WeightModeType = Literal['discrete_3', 'discrete_5', 'discrete_7', 'continuous']

# 各離散化スキームの定義
# discrete_values: UI入力値 / DB保存値
# continuous_values: 計算用に変換された値 [-1, 1] の均等分割

WEIGHT_SCHEMES: Dict[str, Dict] = {
    'discrete_3': {
        'n_levels': 3,
        'discrete_values': [-1, 0, 1],
        'continuous_values': [-2/3, 0, 2/3],  # ±2/(3+1) = ±0.5 ではなく ±2/3
        'labels': ['-1 (Negative)', '0 (No effect)', '+1 (Positive)'],
    },
    'discrete_5': {
        'n_levels': 5,
        'discrete_values': [-3, -1, 0, 1, 3],
        'continuous_values': [-4/5, -2/5, 0, 2/5, 4/5],
        'labels': ['-3 (Strong -)', '-1 (Weak -)', '0', '+1 (Weak +)', '+3 (Strong +)'],
    },
    'discrete_7': {
        'n_levels': 7,
        'discrete_values': [-5, -3, -1, 0, 1, 3, 5],
        'continuous_values': [-6/7, -4/7, -2/7, 0, 2/7, 4/7, 6/7],
        'labels': ['-5 (Strong -)', '-3', '-1', '0', '+1', '+3', '+5 (Strong +)'],
    },
    'continuous': {
        'n_levels': float('inf'),
        'discrete_values': None,  # 連続値モードでは離散値なし
        'continuous_values': None,
        'labels': None,
    },
}

# 旧7段階モードからのマイグレーションマップ
# 旧形式: {-3, -1, -1/3, 0, 1/3, 1, 3}
# 新形式: {-5, -3, -1, 0, 1, 3, 5}
LEGACY_7_LEVEL_VALUES = [-3, -1, -1/3, 0, 1/3, 1, 3]

# 旧形式の±1/3は浮動小数点で保存されていることがある
# -1/3 ≈ -0.3333... だが、-0.33 として保存されている場合あり
LEGACY_FRACTIONAL_VALUES = {
    -1/3: -1,  # 新形式の-1にマップ
    1/3: 1,    # 新形式の1にマップ
}
# 浮動小数点近似値も含める（-0.33, 0.33）
LEGACY_FRACTIONAL_TOLERANCE = 0.02  # ±0.02の許容誤差

LEGACY_7_LEVEL_MIGRATION_MAP: Dict[float, float] = {
    -3: -5,
    -1: -3,
    -1/3: -1,
    0: 0,
    1/3: 1,
    1: 3,
    3: 5,
}

# 各スキームの離散値→連続値マッピング辞書を構築
DISCRETE_TO_CONTINUOUS_MAPS: Dict[str, Dict[float, float]] = {}
CONTINUOUS_TO_DISCRETE_MAPS: Dict[str, Dict[float, float]] = {}

for mode, scheme in WEIGHT_SCHEMES.items():
    if scheme['discrete_values'] is not None:
        # 離散値 → 連続値
        d2c = {}
        c2d = {}
        for d, c in zip(scheme['discrete_values'], scheme['continuous_values']):
            d2c[d] = c
            c2d[c] = d
        DISCRETE_TO_CONTINUOUS_MAPS[mode] = d2c
        CONTINUOUS_TO_DISCRETE_MAPS[mode] = c2d


# =============================================================================
# 変換関数
# =============================================================================

def discrete_to_continuous(
    weight: float,
    mode: WeightModeType = 'discrete_5'
) -> float:
    """
    離散値重みを連続値に変換

    Args:
        weight: 離散値重み（例: -3, -1, 0, +1, +3）
        mode: 離散化モード

    Returns:
        連続値 [-1, 1] の範囲
    """
    # Handle None weight
    if weight is None:
        return 0.0

    # Validate mode - fallback to discrete_7 for invalid modes
    if mode not in WEIGHT_SCHEMES:
        mode = 'discrete_7'

    if mode == 'continuous':
        # 連続モードではそのまま（クリップ）
        return float(np.clip(weight, -1.0, 1.0))

    # 旧形式の±1/3（および近似値-0.33, 0.33）を検出してマイグレーション
    # これはdiscrete_7モードでのみ発生する
    if mode == 'discrete_7':
        for legacy_val, new_discrete in LEGACY_FRACTIONAL_VALUES.items():
            if abs(weight - legacy_val) < LEGACY_FRACTIONAL_TOLERANCE:
                # 旧形式を検出 → 新形式の離散値に変換してから連続値に
                mapping = DISCRETE_TO_CONTINUOUS_MAPS.get(mode, {})
                return mapping.get(new_discrete, 0.0)

    mapping = DISCRETE_TO_CONTINUOUS_MAPS.get(mode, {})

    # 完全一致の場合
    if weight in mapping:
        return mapping[weight]

    # 浮動小数点誤差を考慮した近似マッチ
    for d_val, c_val in mapping.items():
        if abs(weight - d_val) < 1e-6:
            return c_val

    # マッチしない場合: 最も近い離散値にマップしてから変換
    scheme = WEIGHT_SCHEMES.get(mode, {})
    discrete_values = scheme.get('discrete_values', [])

    if not discrete_values:
        return float(np.clip(weight, -1.0, 1.0))

    # 最も近い離散値を見つける
    closest_discrete = min(discrete_values, key=lambda x: abs(x - weight))
    return mapping.get(closest_discrete, 0.0)


def continuous_to_discrete(
    weight: float,
    mode: WeightModeType = 'discrete_5'
) -> float:
    """
    連続値重みを最も近い離散値に変換

    Args:
        weight: 連続値重み [-1, 1]
        mode: 離散化モード

    Returns:
        離散値（例: -3, -1, 0, +1, +3）
    """
    if mode == 'continuous':
        return weight

    scheme = WEIGHT_SCHEMES.get(mode, {})
    continuous_values = scheme.get('continuous_values', [])
    discrete_values = scheme.get('discrete_values', [])

    if not continuous_values or not discrete_values:
        return weight

    # 最も近い連続値を見つけ、対応する離散値を返す
    closest_idx = np.argmin([abs(c - weight) for c in continuous_values])
    return discrete_values[closest_idx]


def normalize_weight(
    weight: float,
    mode: WeightModeType = 'discrete_5'
) -> float:
    """
    重みを計算用に正規化

    離散モード: 離散値→連続値に変換
    連続モード: [-1, 1]にクリップ

    Args:
        weight: 入力重み
        mode: 重みモード

    Returns:
        正規化された重み [-1, 1]
    """
    return discrete_to_continuous(weight, mode)


def get_discretization_error(mode: WeightModeType) -> float:
    """
    離散化スキームの最大量子化誤差を計算

    連続値を離散値にマップしたときの最大誤差。
    均等分割の場合、隣接する値の間隔の半分が最大誤差。

    Args:
        mode: 離散化モード

    Returns:
        最大量子化誤差 (連続値スケール)
    """
    if mode == 'continuous':
        return 0.0

    scheme = WEIGHT_SCHEMES.get(mode, {})
    continuous_values = scheme.get('continuous_values', [])

    if not continuous_values or len(continuous_values) < 2:
        return 0.0

    # 隣接値の間隔の最大値の半分
    intervals = [continuous_values[i+1] - continuous_values[i]
                 for i in range(len(continuous_values) - 1)]
    return max(intervals) / 2


def get_scheme_info(mode: WeightModeType) -> Dict:
    """
    離散化スキームの情報を取得

    Returns:
        {
            'n_levels': int,
            'discrete_values': List[float],
            'continuous_values': List[float],
            'max_continuous': float,  # 連続値の最大絶対値
            'quantization_error': float,  # 最大量子化誤差
            'step_size': float,  # 連続値の間隔
        }
    """
    scheme = WEIGHT_SCHEMES.get(mode, {})

    if mode == 'continuous':
        return {
            'n_levels': float('inf'),
            'discrete_values': None,
            'continuous_values': None,
            'max_continuous': 1.0,
            'quantization_error': 0.0,
            'step_size': 0.0,
        }

    continuous_values = scheme.get('continuous_values', [])
    n = len(continuous_values)

    return {
        'n_levels': scheme.get('n_levels', 0),
        'discrete_values': scheme.get('discrete_values', []),
        'continuous_values': continuous_values,
        'max_continuous': max(abs(c) for c in continuous_values) if continuous_values else 0,
        'quantization_error': get_discretization_error(mode),
        'step_size': (continuous_values[1] - continuous_values[0]) if n >= 2 else 0,
    }


# =============================================================================
# 符号保存確率の計算
# =============================================================================

def compute_sign_preservation_probability(mode: WeightModeType) -> float:
    """
    離散化による符号保存確率を計算（理論値）

    連続一様分布 U(-1, 1) から離散化したとき、
    符号が保存される確率を計算。

    Args:
        mode: 離散化モード

    Returns:
        符号保存確率 [0, 1]
    """
    if mode == 'continuous':
        return 1.0

    scheme = WEIGHT_SCHEMES.get(mode, {})
    continuous_values = scheme.get('continuous_values', [])

    if not continuous_values:
        return 1.0

    # 0を含む区間の幅を計算
    # 連続値が [-a, 0, a] の場合、0に離散化される範囲は [-a/2, a/2]
    # 符号が失われるのは:
    # - 正の値が0に丸められる確率
    # - 負の値が0に丸められる確率

    n = len(continuous_values)
    zero_idx = continuous_values.index(0.0) if 0.0 in continuous_values else n // 2

    # 0の前後の境界を計算
    if zero_idx > 0:
        lower_boundary = (continuous_values[zero_idx - 1] + continuous_values[zero_idx]) / 2
    else:
        lower_boundary = -1.0

    if zero_idx < n - 1:
        upper_boundary = (continuous_values[zero_idx] + continuous_values[zero_idx + 1]) / 2
    else:
        upper_boundary = 1.0

    # 正の値が0に丸められる確率: upper_boundary / 2 (正の領域 [0, 1] のうち)
    # 負の値が0に丸められる確率: |lower_boundary| / 2 (負の領域 [-1, 0] のうち)

    # 全体で符号が失われる確率
    prob_sign_loss = (upper_boundary + abs(lower_boundary)) / 4

    return 1.0 - prob_sign_loss


def compute_spectral_radius_bound(mode: WeightModeType) -> float:
    """
    離散化スキームのスペクトル半径上界を計算

    すべてのエッジが最大重みの場合のスペクトル半径。

    Args:
        mode: 離散化モード

    Returns:
        スペクトル半径の上界
    """
    info = get_scheme_info(mode)
    return info['max_continuous']


# =============================================================================
# 便利関数
# =============================================================================

def get_all_modes() -> List[str]:
    """利用可能な全モードを返す"""
    return list(WEIGHT_SCHEMES.keys())


def is_valid_discrete_value(weight: float, mode: WeightModeType) -> bool:
    """指定モードで有効な離散値かどうか"""
    if mode == 'continuous':
        return True

    scheme = WEIGHT_SCHEMES.get(mode, {})
    discrete_values = scheme.get('discrete_values', [])

    return any(abs(weight - d) < 1e-6 for d in discrete_values)


# レガシー互換: 旧変換関数（非推奨）
def _legacy_discrete_to_continuous(weight: float) -> float:
    """
    旧バージョンの変換関数（非推奨）
    5段階のみ対応、matrix_utils.py の旧実装との互換性用
    """
    LEGACY_MAP = {
        -3: -0.8,
        -1: -0.4,
        0: 0.0,
        1: 0.4,
        3: 0.8,
    }
    return LEGACY_MAP.get(weight, float(np.clip(weight, -1.0, 1.0)))


# =============================================================================
# マイグレーション関数
# =============================================================================

def is_legacy_7_level_weight(weight: float) -> bool:
    """
    旧7段階モードの重みかどうかを判定

    旧形式: {-3, -1, -1/3, 0, 1/3, 1, 3}
    新形式: {-5, -3, -1, 0, 1, 3, 5}

    -1/3, 1/3 は旧形式にしか存在しない
    -5, 5 は新形式にしか存在しない

    Note: -1/3 ≈ -0.333... だが、-0.33として保存されている場合があるため
    LEGACY_FRACTIONAL_TOLERANCE を使用して判定
    """
    for legacy_val in LEGACY_7_LEVEL_VALUES:
        # ±1/3 は近似値で保存されている可能性があるので、より大きな許容誤差を使用
        if legacy_val in LEGACY_FRACTIONAL_VALUES:
            if abs(weight - legacy_val) < LEGACY_FRACTIONAL_TOLERANCE:
                return True
        else:
            if abs(weight - legacy_val) < 1e-6:
                return True
    return False


def migrate_legacy_7_level_weight(weight: float) -> float:
    """
    旧7段階モードの重みを新形式にマイグレーション

    旧形式: {-3, -1, -1/3, 0, 1/3, 1, 3}
    新形式: {-5, -3, -1, 0, 1, 3, 5}

    Note: -1/3 ≈ -0.333... だが、-0.33として保存されている場合があるため
    LEGACY_FRACTIONAL_TOLERANCE を使用してマッチング

    Args:
        weight: 旧形式の重み

    Returns:
        新形式の重み
    """
    # 完全一致
    if weight in LEGACY_7_LEVEL_MIGRATION_MAP:
        return LEGACY_7_LEVEL_MIGRATION_MAP[weight]

    # 浮動小数点誤差を考慮（±1/3は大きめの許容誤差で）
    for old_val, new_val in LEGACY_7_LEVEL_MIGRATION_MAP.items():
        # ±1/3 は近似値で保存されている可能性があるので、より大きな許容誤差を使用
        if old_val in LEGACY_FRACTIONAL_VALUES:
            if abs(weight - old_val) < LEGACY_FRACTIONAL_TOLERANCE:
                return new_val
        else:
            if abs(weight - old_val) < 1e-6:
                return new_val

    # マッチしない場合はそのまま返す
    return weight


def migrate_network_edges(
    edges: List[Dict],
    has_weight_mode: bool = False
) -> Tuple[List[Dict], bool]:
    """
    ネットワークエッジの重みをマイグレーション

    weight_modeが設定されていない古いデータを検出し、
    旧7段階モードの重みを新形式に変換する

    Args:
        edges: エッジリスト
        has_weight_mode: weight_modeが明示的に設定されているか

    Returns:
        (マイグレーション済みエッジリスト, マイグレーションが発生したか)
    """
    if has_weight_mode:
        # 明示的にweight_modeが設定されている場合はマイグレーション不要
        return edges, False

    migrated = False
    new_edges = []

    for edge in edges:
        new_edge = edge.copy()
        weight = edge.get('weight')

        if weight is not None:
            # 旧7段階モードの重みかチェック
            # -1/3, 1/3 が含まれていれば確実に旧形式
            if abs(weight - (1/3)) < 1e-6 or abs(weight - (-1/3)) < 1e-6:
                new_weight = migrate_legacy_7_level_weight(weight)
                new_edge['weight'] = new_weight
                migrated = True
            elif is_legacy_7_level_weight(weight):
                # -3, -1, 0, 1, 3 は新旧両方に存在するが、
                # weight_modeがない場合は旧形式として扱う
                new_weight = migrate_legacy_7_level_weight(weight)
                new_edge['weight'] = new_weight
                if new_weight != weight:
                    migrated = True

        new_edges.append(new_edge)

    return new_edges, migrated


def needs_7_level_migration(edges: List[Dict]) -> bool:
    """
    旧7段階モードからのマイグレーションが必要かどうかを判定

    -1/3 または 1/3 の重みが含まれていれば確実に旧形式
    Note: -0.33, 0.33 として保存されている場合も検出
    """
    for edge in edges:
        weight = edge.get('weight')
        if weight is not None:
            # LEGACY_FRACTIONAL_TOLERANCE を使用して -1/3, 1/3 を検出
            if abs(weight - (1/3)) < LEGACY_FRACTIONAL_TOLERANCE or abs(weight - (-1/3)) < LEGACY_FRACTIONAL_TOLERANCE:
                return True
    return False
