# Deep Traceability System 段階的拡張計画

**作成日**: 2026-01-09
**目的**: 論文(design.tex)の理論を既存システムに破壊なく導入する

---

## 現行システムデータフロー詳細

### データ構造（DB + JSON）

```
ProjectModel
├── stakeholders[] ─────────────────┐
│   └── id, name, votes             │
├── needs[] ────────────────────────┼─→ StakeholderNeedRelation
│   └── id, name, priority          │      └── relationship_weight (1.0/0.5)
├── performances[] ─────────────────┼─→ NeedPerformanceRelation
│   └── id, name, parent_id,        │      └── direction, utility_function_json
│       is_leaf, utility_function   │
├── design_cases[] ─────────────────┘
│   ├── performance_values_json      # {perf_id: 値}
│   ├── network_json                 # {nodes: [], edges: []}
│   ├── performance_snapshot_json    # 作成時の性能ツリー
│   ├── mountain_position_json       # {x, y, z, H, total_energy}
│   ├── utility_vector_json          # {perf_need: utility}
│   ├── partial_heights_json         # {perf_id: 部分標高}
│   └── performance_weights_json     # {perf_id: 票数}
└── two_axis_plots[]
```

### 処理フロー

```
[入力]                        [計算]                      [出力]
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Stakeholder票              ↓                                   │
│       ↓              distribute_votes_to_needs()                │
│  relationship_weight        ↓                                   │
│       ↓              distribute_votes_to_performances()         │
│  Need×Perf direction        ↓                                   │
│       ↓              calculate_utility_vector()                 │
│  効用関数                   ↓                                   │
│       ↓              calculate_elevation() → H                  │
│  performance_values         ↓                                   │
│                       calculate_mountain_positions()            │
│  network_json               ↓                                   │
│       ↓              WL Kernel → MDS → θ                       │
│       ↓                     ↓                                   │
│                       半球座標 (x, y, z)                        │
│                                                                 │
│  エッジweight               ↓                                   │
│       ↓              calculate_energy_for_case()                │
│                             ↓                                   │
│                       calculate_match() → Match_ij              │
│                             ↓                                   │
│                       total_energy, partial_energies            │
│                                                                 │
│  (現行トレードオフ)         ↓                                   │
│       ↓              TradeoffCalculator                         │
│  共通Property経由    find_paths_through_properties()            │
│       ↓                     ↓                                   │
│                       tradeoff_ratio (競合パス数/総パス数)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ネットワーク構造（network_json）

```json
{
  "nodes": [
    {"id": "node-xxx", "layer": 1, "type": "performance", "label": "P1", "x": 100, "y": 100, "performance_id": "perf-xxx"},
    {"id": "node-yyy", "layer": 2, "type": "property", "label": "Attr1", "x": 200, "y": 300},
    {"id": "node-zzz", "layer": 3, "type": "variable", "label": "Var1", "x": 300, "y": 500},
    {"id": "node-www", "layer": 4, "type": "object", "label": "Obj1", "x": 400, "y": 700}
  ],
  "edges": [
    {"id": "edge-xxx", "source_id": "node-xxx", "target_id": "node-yyy", "weight": 3, "type": "type1"}
  ]
}
```

**エッジweight**: 現行は離散値 `-3, -1, 0, +1, +3`（論文の5段階離散化と同等）

### エクスポートJSON形式

```json
{
  "project": {...},
  "stakeholders": [...],
  "needs": [...],
  "stakeholder_need_relations": [...],
  "performances": [...],
  "need_performance_relations": [...],
  "design_cases": [
    {
      "id": "...",
      "network_json": "...",  // ← 文字列化されたJSON
      "mountain_position_json": "...",
      ...
    }
  ]
}
```

---

## 拡張における互換性ルール

### 必須原則

1. **既存フィールドは削除しない** - 追加のみ
2. **計算結果は別フィールドに保存** - 既存の `tradeoff_ratio` を壊さない
3. **新機能は Optional** - 既存データでも動作
4. **フロントエンドは段階的に** - バックエンドAPIを先に整備

### JSON互換性

```python
# 良い例: 新フィールドを追加（Optionalで）
mountain_position_json = {
    "x": ..., "y": ..., "z": ..., "H": ...,
    "total_energy": ...,
    # 新規追加（既存JSONにはない→Noneとして扱う）
    "structural_tradeoff": {...}  # Optional[Dict]
}

# 悪い例: 既存フィールドの意味を変更
# weight: 3 → weight: 0.8  ❌ 互換性破壊
```

---

## 段階的拡張計画（全25ステップ）

### Phase 0: 準備（Step 1-3）

#### Step 1: 行列計算ユーティリティの追加
**ファイル**: `backend/app/services/matrix_utils.py` (新規)

```python
# 目的: 行列演算の基盤を整備
# 既存への影響: なし（新規ファイル）

import numpy as np
from typing import List, Dict, Tuple

def build_adjacency_matrices(network: Dict) -> Dict[str, np.ndarray]:
    """
    ネットワークから隣接行列を構築

    Returns:
        {
            'B_PA': np.ndarray,  # Property → Performance
            'B_AA': np.ndarray,  # Property → Property
            'B_AV': np.ndarray,  # Variable → Property
            'node_ids': {
                'P': [...],  # Performance node IDs
                'A': [...],  # Property node IDs
                'V': [...],  # Variable node IDs
            }
        }
    """
    pass

def normalize_weight(weight: float) -> float:
    """
    離散値weight (-3,-1,0,+1,+3) を連続値 (-1~+1) に正規化
    論文: 5段階均等分割の代表値
    """
    mapping = {-3: -0.8, -1: -0.4, 0: 0.0, 1: 0.4, 3: 0.8}
    return mapping.get(weight, weight / 3.0)
```

**テスト**: `tests/test_matrix_utils.py`
- 既存ネットワークから正しく行列が構築されるか
- 空ネットワークでもエラーにならないか


#### Step 2: 総効果行列の計算関数
**ファイル**: `backend/app/services/matrix_utils.py` (追加)

```python
def compute_total_effect_matrix(
    B_PA: np.ndarray,
    B_AA: np.ndarray,
    B_AV: np.ndarray
) -> np.ndarray:
    """
    総効果行列 T = B_PA × (I - B_AA)^(-1) × B_AV を計算

    論文5.2節の式に対応
    """
    n = B_AA.shape[0]
    I = np.eye(n)

    # スペクトル半径チェック（収束条件）
    spectral_radius = np.max(np.abs(np.linalg.eigvals(B_AA)))
    if spectral_radius >= 1.0:
        # 収束しない場合は警告を出しつつ、Neumann級数で近似
        # (I - B_AA)^(-1) ≈ I + B_AA + B_AA^2 + ... + B_AA^k
        pass

    try:
        inv_term = np.linalg.inv(I - B_AA)
    except np.linalg.LinAlgError:
        # 特異行列の場合はMoore-Penrose疑似逆行列
        inv_term = np.linalg.pinv(I - B_AA)

    T = B_PA @ inv_term @ B_AV
    return T
```

**テスト**:
- 単純なネットワークで手計算と一致するか
- B_AAが零行列の場合、T = B_PA × B_AVになるか


#### Step 3: cos θ計算関数
**ファイル**: `backend/app/services/matrix_utils.py` (追加)

```python
def compute_structural_tradeoff(T: np.ndarray) -> np.ndarray:
    """
    総効果行列から構造的トレードオフ行列を計算

    cos θ_ij = (T_i· · T_j·) / (||T_i·|| × ||T_j·||)

    Returns:
        cos_theta_matrix: (n_perf × n_perf) の対称行列
        cos_theta[i,j] < 0 → トレードオフ
        cos_theta[i,j] > 0 → 協調
    """
    n_perf = T.shape[0]
    cos_theta = np.zeros((n_perf, n_perf))

    for i in range(n_perf):
        for j in range(n_perf):
            norm_i = np.linalg.norm(T[i, :])
            norm_j = np.linalg.norm(T[j, :])
            if norm_i > 1e-10 and norm_j > 1e-10:
                cos_theta[i, j] = np.dot(T[i, :], T[j, :]) / (norm_i * norm_j)
            else:
                cos_theta[i, j] = 0.0  # 効果なし→独立

    return cos_theta
```

---

### Phase 1: バックエンド計算機能（Step 4-9）

#### Step 4: StructuralTradeoffCalculatorクラスの作成
**ファイル**: `backend/app/services/structural_tradeoff.py` (新規)

```python
class StructuralTradeoffCalculator:
    """論文の構造的トレードオフ分析を実装"""

    def __init__(self, network: Dict, performances: List[Dict]):
        self.network = network
        self.performances = performances
        self._matrices = None
        self._total_effect = None
        self._cos_theta = None

    def analyze(self) -> Dict:
        """
        構造分析を実行

        Returns:
            {
                'total_effect_matrix': List[List[float]],
                'cos_theta_matrix': List[List[float]],
                'performance_ids': List[str],
                'variable_ids': List[str],
                'tradeoff_pairs': [
                    {'perf_i': str, 'perf_j': str, 'cos_theta': float, 'interpretation': str}
                ],
                'metadata': {
                    'spectral_radius': float,
                    'convergence_warning': bool
                }
            }
        """
        pass
```


#### Step 5: APIエンドポイントの追加（分析実行）
**ファイル**: `backend/app/api/calculations.py` (追加)

```python
@router.get("/{project_id}/design-cases/{case_id}/structural-tradeoff")
def get_structural_tradeoff(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    設計案の構造的トレードオフ分析を取得

    既存の calculate_tradeoff_ratio と共存
    新しい指標として並列提供
    """
    # 既存データを破壊しない
    # 計算結果はレスポンスのみ（DBには保存しない、Step 8で保存対応）
```


#### Step 6: 既存tradeoff_calculatorとの統合
**ファイル**: `backend/app/services/tradeoff_calculator.py` (修正)

```python
class TradeoffCalculator:
    # 既存メソッドはそのまま維持

    @staticmethod
    def calculate_single_case_tradeoff_ratio(...):
        # 既存コード変更なし
        pass

    # 新メソッドを追加
    @staticmethod
    def calculate_with_structural_analysis(
        network: Dict,
        performances: List[Dict]
    ) -> Dict:
        """
        既存のトレードオフ比率 + 新しい構造的分析を両方返す
        """
        # 既存計算
        classic_result = TradeoffCalculator.calculate_single_case_tradeoff_ratio(...)

        # 新計算
        from .structural_tradeoff import StructuralTradeoffCalculator
        structural = StructuralTradeoffCalculator(network, performances)
        structural_result = structural.analyze()

        return {
            'classic': classic_result,       # 互換性維持
            'structural': structural_result   # 新機能
        }
```


#### Step 7: プロジェクト単位の一括分析API
**ファイル**: `backend/app/api/calculations.py` (追加)

```python
@router.get("/{project_id}/structural-tradeoff-summary")
def get_project_structural_tradeoff(project_id: str, db: Session = Depends(get_db)):
    """
    プロジェクト全体の構造的トレードオフサマリー

    Returns:
        {
            'cases': [
                {
                    'case_id': str,
                    'case_name': str,
                    'tradeoff_pairs': [...],
                    'classic_ratio': float  # 既存指標も併記
                }
            ],
            'common_tradeoffs': [...]  # 全設計案で共通のトレードオフ
        }
    """
```


#### Step 8: 計算結果のDB保存（Optional）
**ファイル**: `backend/app/models/database.py` (修正)

```python
class DesignCaseModel(Base):
    # 既存フィールドは全て維持
    ...

    # 新フィールド追加（Optional、NULLable）
    structural_analysis_json = Column(Text, nullable=True)
    # ↑ 既存データは None のまま動作可能
```

**マイグレーション**: Alembicで安全に追加
```bash
alembic revision --autogenerate -m "add structural_analysis_json"
alembic upgrade head
```


#### Step 9: エクスポート/インポートの対応
**ファイル**: `backend/app/api/projects.py` (修正)

```python
# export_project 修正
export_data = {
    ...
    "design_cases": [
        {
            ...
            # 既存フィールド全て維持
            "structural_analysis_json": d.structural_analysis_json  # 新規（あれば）
        }
    ]
}

# import_project 修正
# structural_analysis_jsonがなくても動作（後方互換性）
structural_json = design_case.get("structural_analysis_json")  # None許容
```

---

### Phase 2: Shapley値分解（Step 10-14）

#### Step 10: Shapley値計算の基盤
**ファイル**: `backend/app/services/shapley_calculator.py` (新規)

```python
from itertools import combinations
from math import factorial

def compute_shapley_values(
    T: np.ndarray,
    perf_i: int,
    perf_j: int,
    property_ids: List[str]
) -> Dict[str, float]:
    """
    トレードオフ cos θ_ij への各Property（属性）の寄与をShapley値で分解

    論文5.3節: φ_k = Σ [|S|!(|Z|-|S|-1)!/|Z|!] × [C_ij(S∪{k}) - C_ij(S)]

    計算量: O(2^l) where l = 属性数
    l <= 10 なら実用的（2^10 = 1024）
    """
    n_properties = len(property_ids)
    shapley = {}

    for k in range(n_properties):
        phi_k = 0.0
        other_indices = [i for i in range(n_properties) if i != k]

        for size in range(n_properties):
            for S in combinations(other_indices, size):
                S_set = set(S)

                # C_ij(S) の計算
                c_without_k = _compute_partial_cos_theta(T, perf_i, perf_j, S_set)
                c_with_k = _compute_partial_cos_theta(T, perf_i, perf_j, S_set | {k})

                marginal = c_with_k - c_without_k
                weight = factorial(size) * factorial(n_properties - size - 1) / factorial(n_properties)
                phi_k += weight * marginal

        shapley[property_ids[k]] = phi_k

    return shapley
```


#### Step 11: Shapley値のAPI
**ファイル**: `backend/app/api/calculations.py` (追加)

```python
@router.get("/{project_id}/design-cases/{case_id}/shapley/{perf_i_id}/{perf_j_id}")
def get_shapley_contribution(
    project_id: str,
    case_id: str,
    perf_i_id: str,
    perf_j_id: str,
    db: Session = Depends(get_db)
):
    """
    特定の性能ペアのトレードオフに対するShapley値分解

    Returns:
        {
            'perf_i': {...},
            'perf_j': {...},
            'cos_theta': float,
            'contributions': [
                {'property_id': str, 'property_name': str, 'phi': float, 'percentage': float}
            ],
            'total': float  # Σφ = cos_theta を検証
        }
    """
```


#### Step 12: 計算量警告の実装
**ファイル**: `backend/app/services/shapley_calculator.py` (追加)

```python
def estimate_computation_time(n_properties: int) -> Dict:
    """
    Shapley値計算の計算量を推定

    Returns:
        {
            'n_properties': int,
            'combinations': int,  # 2^n
            'estimated_seconds': float,
            'warning': str or None
        }
    """
    combos = 2 ** n_properties

    # 実測ベースの推定（1000組み合わせ ≈ 0.1秒と仮定）
    estimated = combos / 10000

    warning = None
    if n_properties > 15:
        warning = "Property数が多すぎます。近似計算を推奨します。"
    elif n_properties > 10:
        warning = f"計算に約{estimated:.1f}秒かかります。"

    return {
        'n_properties': n_properties,
        'combinations': combos,
        'estimated_seconds': estimated,
        'warning': warning
    }
```


#### Step 13: 近似Shapley値（Monte Carlo）
**ファイル**: `backend/app/services/shapley_calculator.py` (追加)

```python
def compute_shapley_values_monte_carlo(
    T: np.ndarray,
    perf_i: int,
    perf_j: int,
    property_ids: List[str],
    n_samples: int = 1000
) -> Dict[str, float]:
    """
    Monte Carlo法によるShapley値の近似計算

    Property数が多い場合（> 10）に使用
    """
    import random
    n_properties = len(property_ids)
    shapley = {pid: 0.0 for pid in property_ids}

    for _ in range(n_samples):
        # ランダム順列を生成
        perm = list(range(n_properties))
        random.shuffle(perm)

        S = set()
        for k in perm:
            c_without = _compute_partial_cos_theta(T, perf_i, perf_j, S)
            c_with = _compute_partial_cos_theta(T, perf_i, perf_j, S | {k})
            shapley[property_ids[k]] += (c_with - c_without)
            S.add(k)

    # 平均化
    for pid in shapley:
        shapley[pid] /= n_samples

    return shapley
```


#### Step 14: Shapley結果のキャッシュ
**ファイル**: `backend/app/services/shapley_calculator.py` (追加)

```python
# 計算コストが高いため、結果をキャッシュ
# Redis or メモリキャッシュ（functools.lru_cache）

from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_shapley(case_id: str, perf_i_id: str, perf_j_id: str) -> Dict:
    """
    Shapley値のキャッシュ

    キャッシュキー: (case_id, perf_i_id, perf_j_id)
    ネットワーク変更時はキャッシュクリア
    """
    pass
```

---

### Phase 3: スキーマ拡張（Step 15-17）

#### Step 15: 新しいPydanticスキーマ
**ファイル**: `backend/app/schemas/analysis.py` (新規)

```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class TradeoffPair(BaseModel):
    perf_i_id: str
    perf_i_name: str
    perf_j_id: str
    perf_j_name: str
    cos_theta: float
    interpretation: str  # 'strong_tradeoff' | 'weak_tradeoff' | 'independent' | 'synergy'

class StructuralAnalysis(BaseModel):
    total_effect_matrix: List[List[float]]
    cos_theta_matrix: List[List[float]]
    performance_ids: List[str]
    variable_ids: List[str]
    tradeoff_pairs: List[TradeoffPair]
    metadata: Dict

class ShapleyContribution(BaseModel):
    property_id: str
    property_name: str
    phi: float
    percentage: float

class ShapleyResult(BaseModel):
    perf_i: Dict
    perf_j: Dict
    cos_theta: float
    contributions: List[ShapleyContribution]
    is_approximate: bool
    n_samples: Optional[int]  # Monte Carloの場合
```


#### Step 16: フロントエンド型定義
**ファイル**: `frontend/src/types/analysis.ts` (新規)

```typescript
export interface TradeoffPair {
  perf_i_id: string;
  perf_i_name: string;
  perf_j_id: string;
  perf_j_name: string;
  cos_theta: number;
  interpretation: 'strong_tradeoff' | 'weak_tradeoff' | 'independent' | 'synergy';
}

export interface StructuralAnalysis {
  total_effect_matrix: number[][];
  cos_theta_matrix: number[][];
  performance_ids: string[];
  variable_ids: string[];
  tradeoff_pairs: TradeoffPair[];
  metadata: {
    spectral_radius: number;
    convergence_warning: boolean;
  };
}

export interface ShapleyContribution {
  property_id: string;
  property_name: string;
  phi: number;
  percentage: number;
}

export interface ShapleyResult {
  perf_i: { id: string; name: string };
  perf_j: { id: string; name: string };
  cos_theta: number;
  contributions: ShapleyContribution[];
  is_approximate: boolean;
  n_samples?: number;
}
```


#### Step 17: API関数の追加
**ファイル**: `frontend/src/utils/api.ts` (追加)

```typescript
export const analysisApi = {
  // 構造的トレードオフ分析
  getStructuralTradeoff: (projectId: string, caseId: string) =>
    api.get<StructuralAnalysis>(`/projects/${projectId}/design-cases/${caseId}/structural-tradeoff`),

  // プロジェクト全体サマリー
  getProjectTradeoffSummary: (projectId: string) =>
    api.get(`/projects/${projectId}/structural-tradeoff-summary`),

  // Shapley値分解
  getShapleyContribution: (projectId: string, caseId: string, perfI: string, perfJ: string) =>
    api.get<ShapleyResult>(`/projects/${projectId}/design-cases/${caseId}/shapley/${perfI}/${perfJ}`),
};
```

---

### Phase 4: フロントエンドUI（Step 18-23）

#### Step 18: トレードオフマトリクス表示コンポーネント
**ファイル**: `frontend/src/components/analysis/TradeoffMatrix.vue` (新規)

```vue
<template>
  <div class="tradeoff-matrix">
    <h3>Structural Tradeoff Matrix (cos θ)</h3>

    <!-- ヒートマップ表示 -->
    <table class="matrix-table">
      <thead>
        <tr>
          <th></th>
          <th v-for="perf in performances" :key="perf.id">{{ perf.name }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in cosTheta" :key="i">
          <th>{{ performances[i].name }}</th>
          <td
            v-for="(val, j) in row"
            :key="j"
            :style="getCellStyle(val)"
            @click="showDetail(i, j)"
          >
            {{ val.toFixed(2) }}
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 凡例 -->
    <div class="legend">
      <span class="synergy">Synergy (> 0)</span>
      <span class="independent">Independent (≈ 0)</span>
      <span class="tradeoff">Tradeoff (< 0)</span>
    </div>
  </div>
</template>
```

**配置先**: 最初はMountainView内のサブパネルとして


#### Step 19: Shapley値表示コンポーネント
**ファイル**: `frontend/src/components/analysis/ShapleyBreakdown.vue` (新規)

```vue
<template>
  <div class="shapley-breakdown">
    <h4>Why {{ perfI.name }} vs {{ perfJ.name }} tradeoff?</h4>

    <!-- 棒グラフで寄与を表示 -->
    <div v-for="contrib in contributions" :key="contrib.property_id" class="contrib-bar">
      <span class="label">{{ contrib.property_name }}</span>
      <div class="bar" :style="{ width: Math.abs(contrib.percentage) + '%' }">
        {{ contrib.percentage.toFixed(1) }}%
      </div>
    </div>

    <!-- 近似計算の場合の警告 -->
    <div v-if="isApproximate" class="warning">
      ⚠ Monte Carlo近似（{{ nSamples }}サンプル）
    </div>
  </div>
</template>
```


#### Step 20: MountainViewへの統合（Panel追加）
**ファイル**: `frontend/src/components/mountain/MountainView.vue` (修正)

```vue
<!-- 既存の3D表示 -->
<div class="mountain-3d">...</div>

<!-- 新しいパネル（トグル表示） -->
<div v-if="showAnalysisPanel" class="analysis-panel">
  <div class="panel-tabs">
    <button @click="activeAnalysisTab = 'tradeoff'">Tradeoff</button>
    <button @click="activeAnalysisTab = 'detail'">Detail</button>
  </div>

  <TradeoffMatrix
    v-if="activeAnalysisTab === 'tradeoff'"
    :analysis="structuralAnalysis"
    @select-pair="onSelectPair"
  />

  <ShapleyBreakdown
    v-if="activeAnalysisTab === 'detail' && selectedPair"
    :perf-i="selectedPair.perfI"
    :perf-j="selectedPair.perfJ"
    :case-id="selectedCase.id"
  />
</div>

<!-- パネルのトグルボタン -->
<button class="toggle-analysis" @click="showAnalysisPanel = !showAnalysisPanel">
  📊 Analysis
</button>
```


#### Step 21: 2軸評価への統合（Optional）
**ファイル**: `frontend/src/components/twoaxis/TwoAxisEvaluation.vue` (修正)

```vue
<!-- 既存の散布図 -->
<div class="scatter-plot">...</div>

<!-- トレードオフ情報の表示（2軸で選択されている性能ペアの場合） -->
<div v-if="tradeoffInfo" class="tradeoff-indicator">
  <span :class="tradeoffInfo.interpretation">
    cos θ = {{ tradeoffInfo.cos_theta.toFixed(2) }}
  </span>
</div>
```


#### Step 22: ネットワーク編集画面への統合
**ファイル**: `frontend/src/components/network/NetworkEditor.vue` (修正)

```vue
<!-- 既存のネットワーク編集キャンバス -->
<canvas ref="networkCanvas">...</canvas>

<!-- トレードオフ構造の視覚化オプション -->
<div class="visualization-options">
  <label>
    <input type="checkbox" v-model="showTradeoffPaths" />
    Show tradeoff paths
  </label>
</div>

<!-- トレードオフパスの強調表示 -->
<!-- 赤線: 負のパス、緑線: 正のパス -->
```


#### Step 23: ローディング・エラー処理
**ファイル**: `frontend/src/components/analysis/AnalysisLoader.vue` (新規)

```vue
<template>
  <div class="analysis-loader">
    <!-- 計算中の表示 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Analyzing structure...</p>
      <p v-if="estimatedTime">Est. {{ estimatedTime }}s</p>
    </div>

    <!-- エラー表示 -->
    <div v-if="error" class="error">
      <p>{{ error.message }}</p>
      <button @click="retry">Retry</button>
    </div>

    <!-- 結果表示 -->
    <slot v-if="!loading && !error"></slot>
  </div>
</template>
```

---

### Phase 5: 連続値対応（Step 24-25）

#### Step 24: エッジweight入力の拡張
**ファイル**: `frontend/src/components/network/NetworkEditor.vue` (修正)

```vue
<!-- 既存の離散値セレクタ -->
<select v-if="weightMode === 'discrete'" v-model="edge.weight">
  <option :value="-3">-3 (Strong -)</option>
  <option :value="-1">-1 (Weak -)</option>
  <option :value="0">0 (None)</option>
  <option :value="1">+1 (Weak +)</option>
  <option :value="3">+3 (Strong +)</option>
</select>

<!-- 新しい連続値スライダー -->
<div v-else class="continuous-weight">
  <input
    type="range"
    v-model.number="edge.weight"
    min="-1"
    max="1"
    step="0.1"
  />
  <span>{{ edge.weight.toFixed(1) }}</span>
</div>

<!-- モード切り替え -->
<button @click="toggleWeightMode">
  {{ weightMode === 'discrete' ? '📊 Discrete' : '📈 Continuous' }}
</button>
```

**互換性**:
- 既存データは離散値のまま
- 連続値で保存しても、計算時に離散値と同様に扱える
- normalize_weight()が両方を処理


#### Step 25: 離散化誤差の表示
**ファイル**: `frontend/src/components/analysis/DiscretizationInfo.vue` (新規)

```vue
<template>
  <div class="discretization-info">
    <h4>Discretization Analysis</h4>

    <!-- 5段階離散化の説明 -->
    <p>Current mode: {{ mode }}</p>

    <!-- 理論的誤差範囲 -->
    <div v-if="mode === 'discrete'">
      <p>Max error: |ε| ≤ {{ (1/5).toFixed(2) }}</p>
      <p>Sign preservation: ✓ Guaranteed for cos θ > {{ threshold.toFixed(2) }}</p>
    </div>

    <!-- 信頼度インジケータ -->
    <div class="confidence">
      <span v-for="pair in tradeoffPairs" :key="pair.id">
        {{ pair.perfI }} vs {{ pair.perfJ }}:
        <span :class="getConfidenceClass(pair.cos_theta)">
          {{ getConfidenceLabel(pair.cos_theta) }}
        </span>
      </span>
    </div>
  </div>
</template>
```

---

## 実装順序サマリー

| Phase | Steps | 主な成果物 | 既存への影響 |
|-------|-------|----------|-------------|
| 0 | 1-3 | matrix_utils.py | なし |
| 1 | 4-9 | structural_tradeoff.py, API | 新カラム追加（Nullable） |
| 2 | 10-14 | shapley_calculator.py | なし |
| 3 | 15-17 | schemas, types | なし |
| 4 | 18-23 | Vue components | 既存UIに追加パネル |
| 5 | 24-25 | 連続値対応 | 既存データと互換 |

---

## テスト計画

### 単体テスト
- `tests/test_matrix_utils.py`
- `tests/test_structural_tradeoff.py`
- `tests/test_shapley_calculator.py`

### 結合テスト
- 既存エクスポートJSONのインポートが成功するか
- 新フィールドがないJSONでもエラーにならないか
- 新旧両方のtradeoff指標が計算できるか

### E2Eテスト
- 新UIパネルの表示・非表示
- Shapley値計算の待ち時間
- エラー時のリカバリー

---

## リスクと緩和策

| リスク | 緩和策 |
|-------|-------|
| Shapley計算が遅い | Monte Carlo近似、キャッシュ、Property数警告 |
| 既存JSONとの互換性 | 新フィールドはOptional、古いJSONでもNoneで動作 |
| 逆行列が計算できない | 疑似逆行列、Neumann級数近似 |
| UIが複雑化 | パネルを折りたたみ式に、段階的に公開 |

---

## 次のアクション

**Step 1から開始**: `backend/app/services/matrix_utils.py` の作成

```bash
# 作業開始
touch backend/app/services/matrix_utils.py
touch tests/test_matrix_utils.py
```

この計画に沿って進めますか？
