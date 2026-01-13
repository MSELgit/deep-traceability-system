# backend/app/schemas/analysis.py
"""
構造的トレードオフ分析、SCC分解、Shapley値などの分析結果スキーマ

Phase 4: DB・スキーマ拡張で追加
"""

from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field


# ========== SCC分解（ループ検出） ==========

class SCCComponent(BaseModel):
    """強連結成分（ループ構造）"""
    nodes: List[str]  # ノードIDリスト
    edges: List[Dict[str, str]] = []  # {"source": str, "target": str}
    spectral_radius: float  # スペクトル半径
    converges: bool  # 収束するか（ρ < 1）
    suggestions: List[Dict] = []  # ループ解消の提案


class SCCResult(BaseModel):
    """SCC分解結果"""
    has_loops: bool  # ループが存在するか
    n_components_with_loops: int = 0  # ループを含むSCCの数
    components: List[SCCComponent] = []  # 各強連結成分


# ========== 構造的トレードオフ分析 ==========

class TradeoffPair(BaseModel):
    """トレードオフペアの情報"""
    i: int  # 性能iのインデックス
    j: int  # 性能jのインデックス
    perf_i_id: str
    perf_j_id: str
    perf_i_label: str
    perf_j_label: str
    cos_theta: float
    inner_product: Optional[float] = None  # C_ij
    interpretation: Optional[str] = None


class StructuralTradeoffResult(BaseModel):
    """構造的トレードオフ分析結果"""
    cos_theta_matrix: List[List[float]]  # cosθ行列
    inner_product_matrix: Optional[List[List[float]]] = None  # 内積行列 C_ij
    energy_matrix: Optional[List[List[float]]] = None  # エネルギー行列 E_ij
    performance_ids: List[str]
    performance_labels: List[str]
    performance_id_map: Optional[Dict[str, str]] = None  # network_node_id -> db_id
    tradeoff_pairs: List[TradeoffPair] = []
    synergy_pairs: List[TradeoffPair] = []
    metadata: Optional[Dict] = None


# ========== 論文準拠指標 ==========

class HeightBreakdown(BaseModel):
    """標高の内訳"""
    performance_id: str
    name: str
    W_i: float  # 重み
    U_i: float  # 効用値
    contribution: float  # H_i = W_i * U_i / ΣW


class HeightMetrics(BaseModel):
    """標高（Height）メトリクス"""
    H: float  # 全体標高
    breakdown: List[HeightBreakdown] = []


class EnergyContribution(BaseModel):
    """エネルギーの内訳（ペアごと）"""
    perf_i_id: str
    perf_j_id: str
    perf_i_name: str
    perf_j_name: str
    E_ij: float  # 部分エネルギー
    C_ij: float  # 内積
    cos_theta: float


class EnergyMetrics(BaseModel):
    """エネルギー（Energy）メトリクス"""
    E: float  # 全体エネルギー
    n_tradeoff_pairs: int = 0
    contributions: List[EnergyContribution] = []


class PaperMetrics(BaseModel):
    """論文準拠の統合指標"""
    height: HeightMetrics
    energy: EnergyMetrics
    structural_tradeoff: Optional[StructuralTradeoffResult] = None
    scc_analysis: Optional[SCCResult] = None


# ========== Shapley値（寄与度分解） ==========

class ShapleyValue(BaseModel):
    """単一属性のShapley寄与度"""
    property_idx: int
    property_name: str
    phi: float  # Shapley値
    abs_phi: float  # 絶対値
    percentage: float  # 寄与率（%）
    sign: Literal['positive', 'negative', 'neutral']


class ShapleyResult(BaseModel):
    """Shapley値計算結果"""
    perf_i: Dict[str, any]  # {"idx": int, "name": str}
    perf_j: Dict[str, any]
    C_ij: float
    cos_theta: float
    relationship: Literal['tradeoff', 'synergy', 'neutral']
    shapley_values: List[ShapleyValue]
    sum_check: float  # Σφ_k（C_ijと一致するはず）
    additivity_error: Optional[float] = None  # |sum_check - C_ij|
    computation: Dict  # {"method": str, "n_properties": int, "time_ms": float}


class ShapleyComputationCost(BaseModel):
    """Shapley計算コスト見積もり"""
    n_properties: int
    n_subsets: int
    estimated_time_ms: float
    warning: Literal['low', 'medium', 'high']
    recommendation: Literal['exact', 'exact_with_cache', 'monte_carlo']
    message: str


# ========== ネットワーク設定 ==========

class NetworkSettings(BaseModel):
    """ネットワークの設定"""
    kernel_type: Literal['classic_wl', 'weighted_wl'] = 'classic_wl'
    weight_mode: Literal['discrete', 'continuous'] = 'discrete'
