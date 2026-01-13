# Deep Traceability System 拡張計画書

**作成日**: 2026-01-09
**最終更新**: 2026-01-14 (Phase 9 完了: Import/Export機能、Need Priority個別設定、Network View連続値対応)
**目的**: 論文(design.tex)の理論を既存システムに破壊なく導入し、完全な設計トレーサビリティ分析基盤を構築する

---

## 目次

1. [システム概要](#1-システム概要)
2. [理論的基盤（design.texより）](#2-理論的基盤designtexより)
3. [機能要件](#3-機能要件)
4. [現在の実装状況](#4-現在の実装状況)
5. [段階的拡張計画](#5-段階的拡張計画)
6. [データ互換性・移行戦略](#6-データ互換性移行戦略)
7. [UI設計](#7-ui設計)
8. [API仕様](#8-api仕様)
9. [ファイル構成](#9-ファイル構成)

---

## 1. システム概要

### 1.1 目的

設計案に対して以下を実現する統合分析システム:

1. **PAVE構造でのネットワーク登録** - 4層構造の因果ネットワーク
2. **構造的トレードオフ分析** - cosθ行列による性能間関係の定量化
3. **Shapley値による寄与度分解** - トレードオフ原因の特定
4. **設計案の比較可視化** - WLカーネル + MDS による設計空間マッピング

### 1.2 アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                        │
├─────────────────────────────────────────────────────────────┤
│  NetworkEditor │ MountainView │ OPM3DView │ AnalysisPanels  │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────┐
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  calculations.py │ mds.py │ projects.py                     │
├─────────────────────────────────────────────────────────────┤
│  matrix_utils │ structural_energy │ weighted_wl_kernel      │
│  mountain_calculator │ energy_calculator │ shapley (予定)    │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    SQLite Database                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 理論的基盤（design.texより）

### 2.1 PAVE構造（設計ネットワーク）

**出典**: design.tex 1964-1980行

設計ネットワークは4層のPAVE構造で表現される:

```
Layer 1: Performance (P) - 性能指標
    ↑
Layer 2: Attribute (A)   - 特性・属性
    ↑
Layer 3: Variable (V)    - 設計変数
    ↑
Layer 4: Entity (E)      - 実体（モノ・環境）
```

**定義 (design.tex 6190-6203行)**:
> PAVEネットワークはラベル付きグラフ G = (V, E, ℓ_V, ℓ_E) として定義:
> - V: ノード集合（各層に所属）
> - E: エッジ集合（因果関係）
> - ℓ_V: ノードラベル（所属レイヤー）
> - ℓ_E: エッジラベル（因果関係タイプ・重み）

### 2.2 線形パスモデルと総効果行列

**出典**: design.tex 2056-2212行

#### 2.2.1 隣接行列の構築

ネットワークから3つの隣接行列を構築:

| 行列 | サイズ | 意味 |
|------|--------|------|
| **B_PA** | (性能数 × 属性数) | 属性→性能への直接効果 |
| **B_AA** | (属性数 × 属性数) | 属性間の相互作用 |
| **B_AV** | (属性数 × 変数数) | 変数→属性への直接効果 |

#### 2.2.2 総効果行列の計算

**定理 (design.tex 2173-2180行)**:

```
T = B_PA × (I - B_AA)^(-1) × B_AV
```

ここで:
- **I**: 単位行列
- **(I - B_AA)^(-1)**: Neumann級数展開で計算可能

```
(I - B_AA)^(-1) = I + B_AA + B_AA² + B_AA³ + ...
```

#### 2.2.3 収束条件（スペクトル半径）

**定理 (design.tex 2169-2212行)**:

> 行列 B_AA のスペクトル半径が ρ(B_AA) < 1 を満たすとき、
> (I - B_AA) は正則であり、Neumann級数が収束する。

```python
ρ(B_AA) = max(|λ_i|)  # 固有値の絶対値の最大値
```

- **ρ < 1**: 収束 → 逆行列計算可能
- **ρ ≥ 1**: 発散 → ループ処理が必要

### 2.3 ループ構造への対処（SCC分解）

**出典**: design.tex 2398-2469行

#### 2.3.1 強連結成分（SCC）分解

**定義 (design.tex 2417-2426行)**:

> 有向グラフにおいて、任意の2ノード間で双方向に到達可能な
> ノードの極大集合を強連結成分と呼ぶ。
> |C_k| ≥ 2 を満たす強連結成分が存在する場合、ループ構造が含まれる。

**アルゴリズム**: Tarjanアルゴリズム（計算量 O(|V| + |E|)）

#### 2.3.2 ループの解消方法

| 方法 | 説明 | 適用条件 |
|------|------|---------|
| **因果方向の再検討** | エッジを削除 | 設計者が方向性を判断可能 |
| **代表属性への縮約** | 複数ノードを1つに | 概念的にひとまとまり |
| **拘束条件として分離** | ネットワーク外で扱う | 物理的保存則 |
| **収束するループ** | Neumann級数で処理 | ρ(B_AA^(C_k)) < 1 |

### 2.4 構造的トレードオフ指標（cos θ）

**出典**: design.tex 2534-2620行

#### 2.4.1 定義

**定義 (design.tex 2536-2541行)**:

```
cos θ_ij = ⟨T_i·, T_j·⟩ / (||T_i·|| × ||T_j·||)
```

- **T_i·**: 総効果行列Tの第i行ベクトル（性能iへの全変数からの効果）
- **⟨·,·⟩**: 内積
- **||·||**: ノルム

#### 2.4.2 解釈

| cos θ の範囲 | θ の範囲 | 解釈 |
|-------------|---------|------|
| cos θ > 0 | 0° ≤ θ < 90° | **協調関係**（相乗効果） |
| cos θ ≈ 0 | θ ≈ 90° | **独立関係** |
| cos θ < 0 | 90° < θ ≤ 180° | **トレードオフ関係** |
| cos θ ≈ -1 | θ ≈ 180° | **強いトレードオフ（背反）** |

#### 2.4.3 定理: トレードオフの存在条件

**定理3 (design.tex 2573-2606行)**:

> cos θ_ij < 0 であることと、
> 「ある設計介入 ΔV が存在して ΔP_i > 0 かつ ΔP_j < 0 となる」
> ことは同値である。

### 2.5 内積行列 C_ij

**出典**: design.tex 5788行、6089-6093行

#### 2.5.1 定義

```
C_ij = ⟨T_i·, T_j·⟩ = ||T_i·|| × ||T_j·|| × cos θ_ij
```

#### 2.5.2 cos θ と C_ij の違い

| 指標 | 意味 | 用途 |
|------|------|------|
| **cos θ_ij** | 方向のみ（-1～+1） | トレードオフの有無判定 |
| **C_ij** | 方向 + 大きさ | エネルギー計算、重大さの評価 |

**論文5788行の重要な指摘**:
> 些細なトレードオフ（cos θ ≈ -1 だがノルムが小さい）と
> 重大なトレードオフ（ノルムも大きい）を区別するため、
> エネルギーの計算には内積 C_ij を用いる

### 2.6 Shapley値による寄与配分

**出典**: design.tex 2849-2913行

#### 2.6.1 背景

感度マスキングによる単純な寄与分解は加法性を満たさない（design.tex 2849行）。
この問題を解決するためShapley値を導入。

#### 2.6.2 定義

**定義7 (design.tex 2873-2883行)**:

```
φ_k = Σ_{S⊆Z\{k}} [|S|!(|Z|-|S|-1)!/|Z|!] × [C_ij(S∪{k}) - C_ij(S)]
```

- **Z**: 中間特性（属性）の集合
- **S**: Zの部分集合
- **C_ij(S)**: 部分集合Sのみを考慮したときのトレードオフ指標

#### 2.6.3 定理: Shapley値の加法性

**定理5 (design.tex 2889-2899行)**:

```
Σ_k φ_k = C_ij
```

> Shapley値による寄与配分は、トレードオフ指標を厳密に分解する。

#### 2.6.4 計算量

- **厳密計算**: O(2^l)（l = 属性数）
- **実用的範囲**: l ≤ 10 程度
- **大規模時**: Monte Carlo近似を使用

### 2.7 標高 H（価値）

**出典**: design.tex 5727-5760行

#### 2.7.1 定義

**定義 (design.tex 5755-5760行)**:

```
H = Σ(W_i × U_i) / Σ(W_i)
```

- **W_i**: 性能iの重み（ステークホルダー票数配分から算出）
- **U_i**: 効用値（効用関数による0-1スケール）
- **正規化**: H ∈ [0, 1]

#### 2.7.2 部分標高

```
H_i = W_i × U_i / Σ(W_k)
```

全体標高は部分標高の和: H = Σ H_i

### 2.8 エネルギー E（難易度）

**出典**: design.tex 6083-6169行

#### 2.8.1 損失関数

**定義 (design.tex 6093-6113行)**:

```
L(x) = |x|  if x < 0
     = 0   otherwise
```

> 相乗効果（C_ij > 0）はエネルギーに寄与せず、
> トレードオフ（C_ij < 0）のみがペナルティとして計上される。

#### 2.8.2 エネルギーの定義

**定義9 (design.tex 6121-6133行)**:

```
E = Σ_{i<j} W_i × W_j × L(C_ij) / (Σ W_i)²
```

**性質**:
- E ≥ 0（非負）
- トレードオフがなければ E = 0
- 重要な性能間のトレードオフほど E に大きく寄与

#### 2.8.3 部分エネルギー

**定義10 (design.tex 6148-6163行)**:

```
E_ij = W_i × W_j × L(C_ij) / (Σ W_k)²
```

全体エネルギーは部分エネルギーの和: E = Σ_{i<j} E_ij

#### 2.8.4 レガシー式（電荷モデル）との比較

**警告**: 現在の実装には2つのエネルギー計算方式が混在している。

##### 電荷モデル（レガシー）

**ファイル**: `backend/app/services/energy_calculator.py`

クーロン力モデルに基づく経験的な計算式:

```
Step 1: Match値の計算
  Match_ij = -tanh{log(3/2) × Σ_α sgn(W_iα × W_jα) × √|W_iα × W_jα|}

Step 2: 距離の計算（電荷間距離のアナロジー）
  r_ij = √(2 × (1 - Match_ij))

Step 3: 部分エネルギーの計算（クーロン力）
  E_i = Σ_{j≠i} (q_i × q_j) / r_ij / 2

Step 4: 総エネルギー
  E_total = Σ_i E_i

ここで:
- W_iα = 性能iと属性αを結ぶエッジの重み
- q_i, q_j = 性能の重要度（票数配分）
```

**問題点**:
- 理論的根拠が薄い（論文式との乖離）
- Match値は特性への**直接接続**のみを考慮（総効果行列Tを使わない）
- 総効果行列T経由の間接効果を無視

##### 論文準拠式（新）

**ファイル**: `backend/app/services/structural_energy.py`

総効果行列に基づく理論的計算式:

```
Step 1: 総効果行列の計算
  T = B_PA × (I - B_AA)^(-1) × B_AV

Step 2: 内積行列の計算
  C_ij = T_i· · T_j· = Σ_k T_ik × T_jk

Step 3: 損失関数の適用
  L(C_ij) = |C_ij| if C_ij < 0, else 0

Step 4: 部分エネルギーの計算
  E_ij = W_i × W_j × L(C_ij) / (Σ W_k)²

Step 5: 総エネルギー
  E = Σ_{i<j} E_ij

ここで:
- T_i· = 総効果行列の行ベクトル（性能iへの全変数からの総効果）
- W_i = 性能iの重み（票数配分から算出）
```

**利点**:
- 論文(design.tex)に完全準拠
- ループ構造（B_AA ≠ 0）の間接効果を考慮
- cos θ行列と整合的（C_ij / (||T_i|| × ||T_j||) = cos θ）

##### 現在の使用状況

| ファイル | 使用式 | 備考 |
|---------|--------|------|
| `mountain_calculator.py` | **論文準拠** | ✅ 移行完了 |
| `DesignCaseDetail.vue` | **論文準拠** | ✅ 移行完了 |
| `structural_energy.py` | 論文準拠 | ✅ 正しい |
| `/paper-metrics` API | 論文準拠（+比較用レガシー） | ✅ 正しい |
| `/energy` API | **論文準拠** | ✅ 移行完了 |
| `energy_calculator.py` | 電荷モデル（レガシー） | 比較用に保持 |

##### 移行完了 (2026-01-11)

1. ✅ `mountain_calculator.py`: `compute_structural_energy`を使用
2. ✅ `DesignCaseDetail.vue`: 新APIレスポンス形式に対応（cos θ, C_ij表示）
3. ✅ `/calculations/energy/{project_id}` API: 論文準拠式で再実装
4. ✅ `api.ts`: 型定義を新形式に更新

#### 2.8.5 実装ファイル

**論文準拠（推奨）**: `backend/app/services/structural_energy.py`

```python
def loss_function(x: float) -> float:
    """L(x) = |x| if x < 0, else 0"""
    return abs(x) if x < 0 else 0.0

def compute_structural_energy(
    network: Dict,
    performance_weights: Dict[str, float],
    weight_mode: str = 'discrete_7'
) -> Dict:
    """
    E = Σ(i<j) W_i × W_j × L(C_ij) / (Σ W_i)²

    Returns:
        {
            'E': float,  # 正規化総エネルギー [0, 1]
            'energy_contributions': [...],  # 各ペアの寄与 E_ij
            'inner_product_matrix': C_ij,
            'cos_theta_matrix': cos θ,
        }
    """
```

### 2.9 WLカーネル（Weisfeiler-Lehman）

**出典**: design.tex 6206-6269行

#### 2.9.1 概要

グラフ間の類似度を計算するグラフカーネル。
設計案のPAVEネットワーク構造を比較するために使用。

#### 2.9.2 WLラベル更新

**定義 (design.tex 6238-6250行)**:

```
ℓ^(i+1)(v) = hash(ℓ^(i)(v), {{ℓ^(i)(u) | u ∈ N(v)}})
```

- 各ノードのラベルを近傍構造に基づいて反復的に更新
- h回の反復でh-hop近傍の構造を捉える

#### 2.9.3 WLカーネル

**定義 (design.tex 6259-6269行)**:

```
k_WL^(h)(G_1, G_2) = Σ_{i=0}^{h} ⟨φ_i(G_1), φ_i(G_2)⟩
```

- **φ_i(G)**: 反復iにおける特徴ベクトル（ラベルのヒストグラム）

### 2.10 MDS（多次元尺度構成法）

**出典**: design.tex 6298-6373行

#### 2.10.1 カーネル→距離変換

**命題 (design.tex 6277-6286行)**:

```
d_ij = √(K_ii + K_jj - 2K_ij)
```

#### 2.10.2 古典的MDS

**命題 (design.tex 6308-6319行)**:

距離行列Dから、距離関係を保存する低次元座標Yを求める:

```
Y = V_k × Λ_k^(1/2)
```

- **B**: 二重中心化された行列
- **V_k, Λ_k**: Bの上位k個の固有ベクトル・固有値

#### 2.10.3 ストレス関数

**式 (design.tex 6319-6324行)**:

```
Stress = √(Σ(D_ij - d_ij)² / Σ D_ij²)
```

- Stress < 0.1: 良好な埋め込み

### 2.11 離散化信頼度（Discretization Confidence）

**出典**: design.tex Chapter 6 (Theorem 6.9, 6.10)

離散化されたエッジ重み（3/5/7段階）を使用する場合、連続値との誤差が分析結果に影響を与える可能性がある。
以下の確率指標により、離散化による結果の信頼性を評価する。

#### 2.11.1 有効誤差 σ_eff

**定義 (design.tex 式5990-6010)**:

```
B_AA = 0 の場合（ループなし）:
  σ_eff = σ_ε × √(2/3 × l × d²)

B_AA ≠ 0 の場合（ループあり）:
  σ_eff = σ_ε × √(2/3 × l × d² × (1 + ||B_AA||_F²))

ここで:
  σ_ε = 1/(√3 × n)  ← 離散化誤差の標準偏差
  ||B_AA||_F = フロベニウスノルム = √(Σ b_ij²)
```

**パラメータの意味**:
| パラメータ | 意味 | 取得方法 |
|-----------|------|---------|
| **n** | 離散化レベル数 | discrete_3→3, discrete_5→5, discrete_7→7 |
| **l** | 属性(Attribute)ノード数 | `sum(1 for n in nodes if n['layer'] == 2)` |
| **d** | **接続密度** | 存在するエッジ数 / 可能なエッジ数 [0, 1] |
| **||B_AA||_F** | 属性間行列のフロベニウスノルム | `np.linalg.norm(B_AA, 'fro')` |

**注意: d は「平均次数」ではなく「接続密度（connection density）」**

```
可能なエッジ数（PAVEモデル）:
  |A|×|P| + |A|×|A| + |V|×|A|
  （A→P）   （A→A）   （V→A）

d = 実際の非ゼロエッジ数 / 可能なエッジ数
```

**ループ構造の影響**:
- B_AA ≠ 0（ループあり）の場合、誤差が循環・増幅される
- ||B_AA||_F が大きいほど σ_eff が増加
- 例: ||B_AA||_F = 1.155 の場合、ループ補正係数 = 1 + 1.155² = 2.333

**数値例（loop設計案, discrete_3）**:
```
パラメータ:
  n = 3, l = 3, d = 0.333, ||B_AA||_F = 1.155

計算:
  σ_ε = 1/(√3 × 3) = 0.1925
  基本項 = 2/3 × 3 × 0.333² = 0.222
  ループ補正 = 1 + 1.155² = 2.333
  σ_eff = 0.1925 × √(0.222 × 2.333) = 0.1386
```

#### 2.11.2 符号保存確率 P_sign

**定理 (design.tex Theorem 6.9)**:

離散化された内積 C̃_ij の符号が真の内積と一致する確率:

```
P_sign = Φ(|C_ij| / σ_δC)
```

ここで:
- **Φ**: 標準正規分布の累積分布関数
- **C_ij = T_i · T_j**: 総効果ベクトルの内積（**cos θ ではない！**）
- **σ_δC = σ_eff × √(||T_i||² + ||T_j||²)**: 内積の誤差の標準偏差

**重要**: P_sign の計算には cos θ ではなく内積 C_ij を使用する

**解釈**:
| P_sign | 信頼性 |
|--------|--------|
| ≥ 0.95 | 高信頼（離散化が問題なし） |
| ≥ 0.85 | 概ね信頼可能 |
| ≥ 0.70 | 注意が必要（より多い段階数を推奨） |
| < 0.70 | 低信頼（連続値モードを推奨） |

#### 2.11.3 順序保存確率 P_order

**定理 (design.tex Theorem 6.10)**:

2つのペア間の順序（どちらがより強いトレードオフか）が保存される確率:

```
P_order = Φ(|Δ| / σ_δΔ)
```

ここで:
- **Δ = |C_p1 - C_p2|**: 2つのペアの内積の差
- **σ_δΔ = σ_eff × √(||T_i1||² + ||T_j1||² + ||T_i2||² + ||T_j2||²)**: 差の誤差の標準偏差

**用途**:
- トレードオフペアのランキングの信頼性評価
- 「性能AとBのトレードオフ」と「性能CとDのトレードオフ」のどちらが深刻かの判定

#### 2.11.4 実装ファイル

**ファイル**: `backend/app/services/discretization_confidence.py`

```python
def compute_sigma_eff(
    n_discrete_levels: int,
    n_attributes: int,
    connection_density: float,
    B_AA_frobenius_norm: float = 0.0
) -> float:
    """
    σ_eff を計算（design.tex 準拠）
    - B_AA = 0: σ_eff = σ_ε × √(2/3 × l × d²)
    - B_AA ≠ 0: σ_eff = σ_ε × √(2/3 × l × d² × (1 + ||B_AA||_F²))
    """

def compute_connection_density(network: Dict) -> float:
    """接続密度 d = 存在するエッジ数 / 可能なエッジ数"""

def compute_sign_preservation_for_pair(C_ij: float, norm_i: float, norm_j: float, sigma_eff: float) -> float:
    """P_sign = Φ(|C_ij| / (σ_eff × √(||T_i||² + ||T_j||²)))"""

def compute_order_preservation_for_pairs(C_p1, C_p2, norm_i1, norm_j1, norm_i2, norm_j2, sigma_eff) -> float:
    """P_order = Φ(|Δ| / σ_δΔ)"""

def analyze_discretization_confidence(network: Dict, weight_mode: str) -> Dict:
    """単一ネットワークの離散化信頼度を分析（B_AAフロベニウスノルム含む）"""
```

**APIエンドポイント**:
- `GET /calculations/discretization-confidence/{project_id}/{case_id}` - **設計案単位**で計算

**レスポンス例**:
```json
{
  "case_id": "xxx",
  "case_name": "loop",
  "weight_mode": "discrete_3",
  "is_discrete": true,
  "n_discrete_levels": 3,
  "sign_preservation_probability": 0.998,
  "order_preservation_probability": 0.868,
  "sigma_eff": 0.1386,
  "connection_density": 0.333,
  "B_AA_frobenius_norm": 1.1547,
  "interpretation": "3-level discretization has high reliability (P_sign ≥ 95%)"
}
```

---

## 3. 機能要件

### 3.1 ネットワーク登録

| 要件 | 詳細 |
|------|------|
| PAVE構造登録 | 4層構造でノード・エッジを登録 |
| エッジの向き | Layer 4→3→2→1 の方向 |
| E-V間接続 | 向きなし（接続関係のみ） |

### 3.2 エッジ重みの登録

| モード | 値 | 説明 |
|--------|-----|------|
| **3段階** | -1, 0, 1 | シンプル |
| **5段階** | -3, -1, 0, 1, 3 | 標準 |
| **7段階** | -5, -3, -1, 0, 1, 3, 5 | 詳細 |
| **連続値** | -1.0 ～ +1.0 | 精密（表示は小数3桁） |

**マトリクス入力対応**:
- ネットワーク登録後にエクセルテンプレートをダウンロード
- ユーザーが入力してインポート

### 3.3 収束性チェック

| チェック項目 | 条件 | 対処 |
|-------------|------|------|
| スペクトル半径 | ρ(B_AA) < 1 | 収束OK |
| ループ検出 | SCC分解で |C_k| ≥ 2 | SCC表示 |

### 3.4 計算機能

| 機能 | 連続値時 | 離散値時 |
|------|---------|---------|
| **cosθマトリクス** | ✅ | ✅ |
| **符号保存確率** | - | ✅ |
| **順位保存確率** | - | ✅ |
| **Shapley寄与度** | ✅ | ✅ |
| **エネルギーマトリクス** | ✅ | ✅ |

### 3.5 可視化機能

| 機能 | 説明 |
|------|------|
| レーダーチャート | 効用値の全性能表示 |
| 標高表示 | H値の3D山表示 |
| WLカーネル→MDS | 設計空間の2D/3Dマップ |
| エネルギーセルクリック | 寄与度ハイライトネットワーク |

---

## 4. 現在の実装状況

### 4.1 実装済み機能 ✅

| 機能 | ファイル | 行数 |
|------|---------|------|
| **PAVE構造登録** | NetworkEditor.vue, schemas/project.py | - |
| **7種類エッジ重み** | NetworkEditor.vue:152-164 | 13 |
| **スペクトル半径チェック** | matrix_utils.py:255-302 | 48 |
| **cosθ計算** | matrix_utils.py:364-430 | 67 |
| **内積行列計算** | matrix_utils.py:309-361 | 53 |
| **構造的エネルギー** | structural_energy.py | 200+ |
| **標高計算** | mountain_calculator.py | 100+ |
| **Classic WLカーネル** | mds.py | 150+ |
| **Weighted WLカーネル** | weighted_wl_kernel.py | 500+ |
| **MDS（Classical+Circular）** | mds.py | 300+ |
| **符号保存確率** | weighted_wl_kernel.py:605-650 | 46 |
| **SCC分解（ループ検出）** | scc_analyzer.py | 250+ |
| **Shapley値計算** | shapley_calculator.py | 350+ |

### 4.2 未実装機能 ❌

| 機能 | 計画Phase | 優先度 |
|------|----------|--------|
| **3/5段階重みモード切替** | Phase 6 | 中 |
| **cosθマトリクス表示UI** | Phase 5 | 中 |
| **エネルギーマトリクス表示UI** | Phase 5 | 中 |
| **Shapley寄与度表示UI** | Phase 5 | 中 |
| **SCCビューアUI** | Phase 5 | 中 |
| **レーダーチャート独立化** | Phase 5 | 低 |
| **マトリクス入力/エクスポート** | Phase 6 | 低 |

### 4.3 実装進捗

```
Phase 0-2: ✅ 完了 (13/13ステップ)
├─ Step 1-3:  行列計算ユーティリティ
├─ Step 4-5:  構造的トレードオフ分析
├─ Step 6-9:  論文準拠エネルギー計算
└─ Step 10-13: Weighted WLカーネル

Phase 3: ✅ 完了 (6/6ステップ)
├─ Step 14: ✅ SCC分解の実装 (scc_analyzer.py)
├─ Step 15: ✅ Shapley値計算基盤 (shapley_calculator.py)
├─ Step 16: ✅ Shapley値API
├─ Step 17: ✅ 計算量警告
├─ Step 18: ✅ Monte Carlo近似
└─ Step 19: ✅ キャッシュ

Phase 4: ✅ 完了 (3/3ステップ)
├─ Step 19: ✅ DBモデル拡張 (database.py: 新フィールド追加)
├─ Step 20: ✅ Pydanticスキーマ (analysis.py 新規作成、project.py 更新)
└─ Step 21: ✅ エクスポート/インポート対応 (data_migration.py 新規作成)

Phase 5: ✅ 完了 (5/5ステップ + UI改善)
├─ Step 22: ✅ api.ts拡張（sccApi, shapleyApi, structuralTradeoffApi）
├─ Step 23: ✅ 分析コンポーネント作成
│   ├─ SCCWarningBanner.vue（ループ警告バナー）
│   ├─ MatrixHeatmap.vue（cosθ/Energyヒートマップ）
│   ├─ ShapleyBreakdown.vue（Shapley寄与度分解）
│   ├─ TradeoffMatrixMini.vue（50%幅用ミニマトリクス）
│   └─ TradeoffAnalysisPanel.vue（70%幅用詳細パネル）
├─ Step 24: ✅ NetworkEditorにSCC警告追加（DesignCaseForm経由）
├─ Step 25: ✅ DesignCaseDetailにTradeoff Analysisセクション追加
├─ Step 26: ✅ MountainViewに幅切替機能追加（50%↔70%）
└─ UI改善: ✅
    ├─ structural_tradeoff APIに inner_product_matrix, energy_matrix, performance_id_map 追加
    ├─ ShapleyBreakdown: 性能名に重要度(w=X.X)表示、cos θ と E_ij 表示
    └─ MatrixHeatmap: セルクリック時の対称セル自動選択を解除

Phase 6: ✅ 完了 (2/2ステップ)
├─ Step 27: ✅ エッジweight入力の拡張 (3/5/7段階・連続値モード切替)
└─ Step 28: ✅ 離散化信頼度表示 (DiscretizationConfidence.vue)
```

---

## 5. 段階的拡張計画

### Phase 0-2: 基盤構築 ✅ 完了

#### ✅ Step 1-3: 行列計算ユーティリティ

**ファイル**: `backend/app/services/matrix_utils.py`

```python
def build_adjacency_matrices(network: Dict) -> Tuple[np.ndarray, ...]:
    """B_PA, B_AA, B_AV の構築"""

def compute_total_effect_matrix(B_PA, B_AA, B_AV) -> Dict:
    """T = B_PA × (I - B_AA)^(-1) × B_AV"""
    # スペクトル半径チェック含む

def compute_structural_tradeoff(T: np.ndarray) -> Dict:
    """cos θ_ij の計算"""

def compute_inner_products(T: np.ndarray) -> Dict:
    """内積行列 C_ij の計算"""
```

#### ✅ Step 4-5: StructuralTradeoffCalculator + API

**ファイル**: `backend/app/services/structural_tradeoff.py`

**APIエンドポイント**:
- `GET /calculations/structural-tradeoff/{project_id}/{case_id}`
- `GET /calculations/structural-tradeoff-summary/{project_id}`
- `GET /calculations/tradeoff-comparison/{project_id}/{case_id}`

#### ✅ Step 6-9: 論文準拠エネルギー計算

**ファイル**: `backend/app/services/structural_energy.py`

```python
def loss_function(x: float) -> float:
    """L(x) = |x| if x < 0, else 0"""

def compute_structural_energy(network, performance_weights) -> Dict:
    """E = Σ W_i×W_j×L(C_ij) / (ΣW_i)²"""

def compute_structural_height(utility_vector, performance_weights) -> Dict:
    """H = Σ(W_i × U_i) / Σ(W_i)"""
```

**APIエンドポイント**:
- `GET /calculations/paper-metrics/{project_id}/{case_id}`

#### ✅ Step 10-13: Weighted WLカーネル

**ファイル**: `backend/app/services/weighted_wl_kernel.py`

```python
class WeightedWLKernel:
    """連続値エッジ重みに対応するWLカーネル"""

    def __init__(self, n_iterations=3, aggregation='weighted_mean'):
        pass

    def compute_kernel_matrix(self, graphs: List[nx.DiGraph]) -> np.ndarray:
        """RBFカーネルによる類似度計算"""

def compute_discretization_confidence(networks) -> Dict:
    """離散化信頼度の計算"""
```

**APIエンドポイント**:
- `POST /mds/compute_network_comparison` (kernel_type, weight_mode追加)
- `GET /calculations/discretization-confidence/{project_id}`

---

### Phase 3: Shapley値分解 + SCC分解（未実装）

#### Step 14: SCC分解の実装（追加）

**ファイル**: `backend/app/services/scc_analyzer.py` (新規)

```python
def find_strongly_connected_components(network: Dict) -> List[List[str]]:
    """TarjanアルゴリズムでSCCを検出"""

def check_loop_convergence(network: Dict, scc: List[str]) -> Dict:
    """ループ内の収束条件をチェック"""
    # ρ(B_AA^(C_k)) < 1 かどうか

def suggest_loop_resolution(network: Dict, scc: List[str]) -> List[Dict]:
    """ループ解消の提案を生成"""
```

**APIエンドポイント**:
- `GET /calculations/scc/{project_id}/{case_id}`

#### Step 15: Shapley値計算の基盤

**ファイル**: `backend/app/services/shapley_calculator.py` (新規)

```python
def compute_partial_tradeoff(T: np.ndarray, perf_i: int, perf_j: int,
                             subset: Set[int]) -> float:
    """部分集合のみを考慮したC_ij(S)"""

def compute_shapley_values(T: np.ndarray, perf_i: int, perf_j: int,
                           property_ids: List[str]) -> Dict[str, float]:
    """
    φ_k = Σ [|S|!(|Z|-|S|-1)!/|Z|!] × [C_ij(S∪{k}) - C_ij(S)]

    Returns:
        {property_id: shapley_value, ...}
    """
```

#### Step 16: Shapley値のAPI

**APIエンドポイント**:
- `GET /calculations/shapley/{project_id}/{case_id}/{perf_i_id}/{perf_j_id}`

```json
// レスポンス例
{
  "perf_i": {"id": "...", "name": "燃費"},
  "perf_j": {"id": "...", "name": "重量"},
  "C_ij": -0.45,
  "cos_theta": -0.625,
  "shapley_values": [
    {"property_id": "...", "name": "エンジン効率", "phi": -0.30},
    {"property_id": "...", "name": "車体素材", "phi": -0.15}
  ],
  "sum_check": -0.45,  // Σφ_k = C_ij の検証
  "computation_time_ms": 125
}
```

#### Step 17: 計算量警告の実装

```python
def estimate_computation_cost(n_properties: int) -> Dict:
    """
    計算量 O(2^l) の見積もり
    """
    return {
        "n_properties": n_properties,
        "n_subsets": 2 ** n_properties,
        "estimated_time_seconds": ...,
        "warning": "high" if n_properties > 10 else "low",
        "recommendation": "monte_carlo" if n_properties > 12 else "exact"
    }
```

#### Step 18: Monte Carlo近似

```python
def compute_shapley_monte_carlo(T: np.ndarray, perf_i: int, perf_j: int,
                                property_ids: List[str],
                                n_samples: int = 1000) -> Dict[str, float]:
    """サンプリングによる近似計算"""
```

#### Step 19: Shapley結果のキャッシュ

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_shapley_values(case_id: str, perf_pair: Tuple[str, str]) -> Dict:
    """計算結果のキャッシュ"""
```

---

### Phase 4: DB・スキーマ拡張（未実装）

#### Step 20: DBモデル拡張

**ファイル**: `backend/app/models/database.py` (修正)

```python
class DesignCaseModel(Base):
    # 既存フィールド（全て維持）
    ...

    # 新フィールド追加（Optional、NULLable）
    structural_analysis_json = Column(Text, nullable=True)
    paper_metrics_json = Column(Text, nullable=True)
    scc_analysis_json = Column(Text, nullable=True)  # 追加
    kernel_type = Column(String(50), nullable=True, default='classic_wl')
    weight_mode = Column(String(20), nullable=True, default='discrete')
```

#### Step 21: Pydanticスキーマ

**ファイル**: `backend/app/schemas/analysis.py` (新規)

```python
class SCCResult(BaseModel):
    components: List[List[str]]
    has_loops: bool
    loop_details: List[Dict]

class ShapleyResult(BaseModel):
    perf_i_id: str
    perf_j_id: str
    C_ij: float
    cos_theta: float
    contributions: List[Dict[str, float]]

class PaperMetrics(BaseModel):
    height: HeightMetrics
    energy: EnergyMetrics
    structural_tradeoff: TradeoffMetrics
    scc_analysis: Optional[SCCResult]
```

#### Step 22: エクスポート/インポート対応

後方互換性を維持したバージョン管理（詳細は第6章）

---

### Phase 5: フロントエンドUI（未実装）

#### Step 23: 論文指標表示コンポーネント

**ファイル**: `frontend/src/components/analysis/PaperMetrics.vue` (新規)

```vue
<template>
  <div class="paper-metrics">
    <div class="metric-card">
      <h3>標高 H</h3>
      <div class="value">{{ height.toFixed(3) }}</div>
      <div class="breakdown">...</div>
    </div>
    <div class="metric-card">
      <h3>エネルギー E</h3>
      <div class="value">{{ energy.toFixed(3) }}</div>
      <div class="tradeoff-count">{{ nTradeoffPairs }} pairs</div>
    </div>
  </div>
</template>
```

#### Step 24: トレードオフマトリクス表示

**ファイル**: `frontend/src/components/analysis/TradeoffMatrix.vue` (新規)

- ヒートマップ形式でcos θ行列を表示
- セルクリックでShapley分解へ遷移
- 離散値時は確率表示オプション

#### Step 25: SCCビューア

**ファイル**: `frontend/src/components/analysis/SCCViewer.vue` (新規)

- 検出されたループ構造を可視化
- 各ループの収束条件表示
- 解消方法の提案表示

#### Step 26: Shapley値表示コンポーネント

**ファイル**: `frontend/src/components/analysis/ShapleyBreakdown.vue` (新規)

- 棒グラフで各Propertyの寄与を表示
- 正の寄与（協調）と負の寄与（トレードオフ）を色分け
- ネットワーク上でハイライト表示と連動

#### Step 27: エネルギーマトリクス表示

**ファイル**: `frontend/src/components/analysis/EnergyMatrix.vue` (新規)

- 部分エネルギーE_ijのヒートマップ
- セルクリック → Shapley分解 + ネットワークハイライト

#### Step 28: MountainViewへの統合

既存の3D表示に分析パネルを追加

---

### Phase 6: 連続値入力対応（未実装）

#### Step 29: エッジweight入力の拡張

**ファイル**: `frontend/src/components/network/NetworkEditor.vue` (修正)

```vue
<template>
  <div class="weight-mode-selector">
    <select v-model="weightMode">
      <option value="discrete_3">3段階 (-1, 0, 1)</option>
      <option value="discrete_5">5段階 (-3, -1, 0, 1, 3)</option>
      <option value="discrete_7">7段階 (-5, -3, -1, 0, 1, 3, 5)</option>
      <option value="continuous">連続値 (-1.0 ~ 1.0)</option>
    </select>
  </div>

  <!-- 連続値モード時 -->
  <input v-if="weightMode === 'continuous'"
         type="number" step="0.001" min="-1" max="1"
         v-model.number="edgeWeight" />
</template>
```

#### Step 30: マトリクス入力機能

**ファイル**: `frontend/src/components/network/MatrixImporter.vue` (新規)

- エクセルテンプレートのダウンロード
- CSVインポート
- 行列形式での一括重み設定

#### Step 31: 離散化信頼度表示

**ファイル**: `frontend/src/components/analysis/DiscretizationConfidence.vue` (新規)

---

## 6. データ互換性・移行戦略

### 6.1 バージョン管理の導入

**エクスポートデータにバージョンを追加**:

```json
{
  "version": "2.0.0",
  "exported_at": "2026-01-10T12:00:00Z",
  "project": {...},
  "stakeholders": [...],
  ...
}
```

### 6.2 バージョン履歴

| バージョン | 追加フィールド |
|-----------|---------------|
| **1.0.0** | 初期構造 |
| **1.1.0** | need.priority |
| **2.0.0** | network.weight_mode, scc_analysis, paper_metrics |

### 6.3 マイグレーション関数

**ファイル**: `backend/app/services/data_migration.py` (新規)

```python
def migrate_import_data(data: dict) -> dict:
    """インポートデータのバージョンマイグレーション"""
    version = data.get("version", "1.0.0")

    if version < "1.1.0":
        # priority フィールド追加
        for need in data.get("needs", []):
            need.setdefault("priority", 1.0)
        version = "1.1.0"

    if version < "2.0.0":
        # weight_mode 追加
        for case in data.get("design_cases", []):
            network = json.loads(case.get("network_json", "{}"))
            network.setdefault("weight_mode", "discrete_7")
            case["network_json"] = json.dumps(network)
        version = "2.0.0"

    data["version"] = version
    return data
```

#### 6.3.1 旧7段階重みのマイグレーション

**背景**: 旧システムの7段階モードは `{-3, -1, -1/3, 0, 1/3, 1, 3}` を使用していたが、
新システムでは `{-5, -3, -1, 0, 1, 3, 5}` に変更された。

**問題**: 旧形式の `-1/3` と `1/3` は浮動小数点で `-0.33` / `0.33` として保存されていることがある。

**対応ファイル**:
- `backend/app/services/weight_normalization.py` - `LEGACY_FRACTIONAL_TOLERANCE` で近似値検出
- `backend/scripts/migrate_legacy_weights.py` - 一括マイグレーションスクリプト

**マイグレーションマッピング**:
| 旧形式 | 新形式 |
|--------|--------|
| -3     | -5     |
| -1     | -3     |
| -1/3 (-0.33) | -1 |
| 0      | 0      |
| 1/3 (0.33) | 1  |
| 1      | 3      |
| 3      | 5      |

**使用方法**:
```bash
# プレビュー
python scripts/migrate_legacy_weights.py --dry-run

# 実行
python scripts/migrate_legacy_weights.py
```

### 6.4 後方互換性ルール（厳守）

| ルール | 説明 |
|--------|------|
| **既存フィールド削除禁止** | 追加のみ許可 |
| **既存計算維持** | 新指標は別名で追加 |
| **新フィールドはOptional** | デフォルト値で動作保証 |
| **正規化方式の明示** | メタデータに記録 |

```python
# 良い例: 従来と新規を併存
mountain_position_json = {
    "x": ..., "y": ..., "z": ..., "H": ...,
    "total_energy": ...,  # 従来（維持）
    "paper_metrics": {    # 新規追加
        "E": ...,
        "normalization": "sum_weights_squared"
    }
}
```

---

## 7. UI設計

### 7.1 新規コンポーネント構成

```
frontend/src/components/
├── analysis/
│   ├── PaperMetrics.vue        # H, E の表示
│   ├── TradeoffMatrix.vue      # cosθヒートマップ
│   ├── EnergyMatrix.vue        # E_ijヒートマップ
│   ├── ShapleyBreakdown.vue    # Shapley寄与度
│   ├── SCCViewer.vue           # ループ構造表示
│   └── DiscretizationConfidence.vue
├── network/
│   ├── WeightModeSelector.vue  # 重みモード選択
│   └── MatrixImporter.vue      # マトリクス入力
└── chart/
    └── RadarChart.vue          # レーダーチャート
```

### 7.2 UI変更一覧

| 画面 | 変更内容 |
|------|---------|
| **NetworkEditor** | 重みモード切替、連続値入力、マトリクスインポート |
| **MountainView** | 論文指標パネル追加、レーダーチャート独立化 |
| **OPM3DView** | エネルギーマトリクス連動 |
| **新規: AnalysisPanel** | cosθ/エネルギー/Shapley統合表示 |

### 7.3 ワイヤーフレーム

```
┌─────────────────────────────────────────────────────────────┐
│                    Analysis Panel                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│   cos θ Matrix  │  Energy Matrix  │   Shapley Breakdown     │
│   ┌───────────┐ │  ┌───────────┐  │   ┌─────────────────┐   │
│   │ Heatmap   │ │  │ Heatmap   │  │   │ ████████ A1     │   │
│   │           │ │  │           │  │   │ ██████ A2       │   │
│   │   Click   │→│  │   Click   │→→│   │ ███ A3          │   │
│   └───────────┘ │  └───────────┘  │   └─────────────────┘   │
│                 │                 │   [Network Highlight]    │
└─────────────────┴─────────────────┴─────────────────────────┘
```

---

## 8. API仕様

### 8.1 既存エンドポイント（実装済み）

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/calculations/mountain/{project_id}` | 標高計算 |
| POST | `/calculations/energy/{project_id}` | エネルギー計算（従来型） |
| GET | `/calculations/structural-tradeoff/{project_id}/{case_id}` | cosθ計算 |
| GET | `/calculations/paper-metrics/{project_id}/{case_id}` | 論文準拠指標 |
| GET | `/calculations/discretization-confidence/{project_id}` | 離散化信頼度 |
| POST | `/mds/compute_network_comparison` | WLカーネル+MDS |
| GET | `/calculations/scc/{project_id}/{case_id}` | SCC分解（ループ検出） |
| GET | `/calculations/scc-summary/{project_id}` | SCC分解サマリー |
| GET | `/calculations/shapley/{project_id}/{case_id}/{i}/{j}` | Shapley値（ペア） |
| GET | `/calculations/shapley-all/{project_id}/{case_id}` | Shapley値（全ペア） |
| GET | `/calculations/shapley-cost/{n_properties}` | Shapley計算コスト見積もり |

### 8.2 新規エンドポイント（計画）

| メソッド | パス | 説明 | Phase |
|---------|------|------|-------|
| POST | `/network/import-matrix/{project_id}/{case_id}` | マトリクス入力 | 6 |
| GET | `/network/export-template/{project_id}/{case_id}` | テンプレートDL | 6 |

### 8.3 レスポンス形式

#### paper-metrics（実装済み）

```json
{
  "height": {
    "H": 0.73,
    "breakdown": [
      {"performance_id": "...", "name": "燃費", "W_i": 0.3, "U_i": 0.8, "contribution": 0.24}
    ]
  },
  "energy": {
    "E": 0.102,
    "n_tradeoff_pairs": 1,
    "contributions": [
      {"perf_i": "...", "perf_j": "...", "E_ij": 0.102, "C_ij": -0.45}
    ]
  },
  "structural_tradeoff": {
    "cos_theta_matrix": [[1.0, -0.625], [-0.625, 1.0]],
    "inner_product_matrix": [[0.72, -0.45], [-0.45, 0.52]]
  }
}
```

#### scc（計画）

```json
{
  "has_loops": true,
  "components": [
    {
      "nodes": ["attr_1", "attr_2", "attr_3"],
      "spectral_radius": 0.85,
      "converges": true,
      "suggestions": [
        {"type": "edge_removal", "edge": ["attr_2", "attr_1"]},
        {"type": "node_merge", "nodes": ["attr_1", "attr_2"]}
      ]
    }
  ]
}
```

#### shapley（計画）

```json
{
  "perf_i": {"id": "...", "name": "燃費"},
  "perf_j": {"id": "...", "name": "重量"},
  "C_ij": -0.45,
  "cos_theta": -0.625,
  "shapley_values": [
    {"property_id": "...", "name": "エンジン効率", "phi": -0.30, "percentage": 66.7},
    {"property_id": "...", "name": "車体素材", "phi": -0.15, "percentage": 33.3}
  ],
  "computation": {
    "method": "exact",
    "n_properties": 5,
    "time_ms": 125
  }
}
```

---

## 9. ファイル構成

### 9.1 バックエンド

```
backend/app/
├── api/
│   ├── calculations.py      # ✅ 拡張済み
│   ├── mds.py               # ✅ 拡張済み
│   └── projects.py          # 修正予定（export/import）
├── models/
│   └── database.py          # 修正予定（新フィールド）
├── schemas/
│   ├── project.py           # ✅ 既存
│   └── analysis.py          # 新規追加予定
└── services/
    ├── matrix_utils.py      # ✅ 完了
    ├── structural_tradeoff.py # ✅ 完了
    ├── structural_energy.py # ✅ 完了
    ├── weighted_wl_kernel.py # ✅ 完了
    ├── mountain_calculator.py # ✅ 既存
    ├── energy_calculator.py # ✅ 既存（従来型）
    ├── scc_analyzer.py      # ✅ 完了（SCC分解）
    ├── shapley_calculator.py # ✅ 完了（Shapley値計算）
    └── data_migration.py    # 新規追加予定
```

### 9.2 フロントエンド

```
frontend/src/components/
├── network/
│   ├── NetworkEditor.vue    # 修正予定（重みモード）
│   ├── NetworkViewer.vue    # ✅ 既存
│   └── MatrixImporter.vue   # 新規追加予定
├── mountain/
│   ├── MountainView.vue     # 修正予定（パネル追加）
│   ├── DesignCaseList.vue   # ✅ 既存
│   └── DesignCaseDetail.vue # ✅ 既存
├── opm3d/
│   ├── OPM3DView.vue        # ✅ 既存
│   └── OPM3DScene.vue       # ✅ 既存
├── analysis/                # 新規ディレクトリ
│   ├── PaperMetrics.vue
│   ├── TradeoffMatrix.vue
│   ├── EnergyMatrix.vue
│   ├── ShapleyBreakdown.vue
│   ├── SCCViewer.vue
│   └── DiscretizationConfidence.vue
└── chart/                   # 新規ディレクトリ
    └── RadarChart.vue
```

---

## 10. フロントエンド実装詳細計画 (Phase 5)

### 10.1 現在のデータフロー

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           フロントエンド                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  MountainView.vue                                                       │
│  ├── DesignCaseList.vue (左パネル)                                      │
│  │   └── Create/Edit → DesignCaseForm.vue (モーダル)                   │
│  │       └── NetworkEditor.vue (ネットワーク編集モーダル)               │
│  │           └── v-model で network を親に emit                         │
│  ├── 3D Mountain (中央)                                                 │
│  └── DesignCaseDetail.vue (右パネル, 幅50%)                            │
│      ├── Basic Information                                              │
│      ├── Performance Values                                             │
│      ├── Utility Radar Chart                                            │
│      ├── Performance Analysis (NetworkHighlightViewer使用)              │
│      └── Network Structure                                              │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                             API呼び出し                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  api.ts                                                                 │
│  ├── designCaseApi.update()  → ネットワーク保存                         │
│  ├── calculationApi.calculateMountain()                                 │
│  ├── calculationApi.calculateEnergy()                                   │
│  └── 【未実装】SCC, Shapley API呼び出し                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           バックエンド                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  calculations.py                                                        │
│  ├── GET /scc/{project_id}/{case_id}                    ✅ 実装済み    │
│  ├── GET /scc-summary/{project_id}                      ✅ 実装済み    │
│  ├── GET /shapley/{project_id}/{case_id}/{i}/{j}        ✅ 実装済み    │
│  ├── GET /shapley-all/{project_id}/{case_id}            ✅ 実装済み    │
│  ├── GET /structural-tradeoff/{project_id}/{case_id}    ✅ 実装済み    │
│  └── GET /paper-metrics/{project_id}/{case_id}          ✅ 実装済み    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 UI設計詳細

#### 10.2.1 NetworkEditorへのSCC警告統合

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NetworkEditor (Modal)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │               PAVE Network Editor Canvas                          │  │
│  │                        ...                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ ⚠️ SCC Warning Banner (ρ ≥ 1 の場合のみ表示)                      │  │
│  │ 発散ループ検出: [A1 ↔ A2] ρ=1.23                                  │  │
│  │ 推奨: エッジ 'A1→A2' (weight: 0.3) の削除を検討                   │  │
│  │ [詳細を見る]  [このまま保存]                                      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ ℹ️ SCC Info Banner (0 < ρ < 1 の場合のみ、任意表示)               │  │
│  │ 収束ループ検出: [A1 ↔ A2] ρ=0.42 - 計算可能です                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│                                     [Save and Close]    [Cancel]        │
└─────────────────────────────────────────────────────────────────────────┘
```

**実装ポイント:**
- NetworkEditor内に `sccWarning` リアクティブ変数を追加
- Save時にSCC APIを呼び出し、結果に応じて警告表示
- 発散ループ(ρ≥1)の場合は警告、収束ループ(ρ<1)の場合は情報表示

#### 10.2.2 DesignCaseDetail 通常表示（幅50%）

```
┌─────────────────────────────────────────────────────────────────────────┐
│ DesignCase Details                                                   ✕  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ▼ Basic Information                                                     │
│   Elevation: 0.823  |  Energy: 0.45  |  Color: ██ #3357FF               │
│                                                                         │
│ ▶ Performance Values                                                    │
│ ▶ Utility Radar Chart                                                   │
│ ▶ Performance Analysis                                                  │
│ ▶ Network Structure                                                     │
│                                                                         │
│ ▼ Tradeoff Analysis  ← 【新規セクション】                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ [cosθ Matrix ◉] [Energy Matrix ○]  ← トグルスイッチ            │   │
│   ├─────────────────────────────────────────────────────────────────┤   │
│   │     P1    P2    P3    P4                                        │   │
│   │ P1   -   ▓▓▓  ░░░  ▒▒▒                                         │   │
│   │ P2       -    ░░░  ▒▒▒     ミニヒートマップ                     │   │
│   │ P3             -   ▒▒▒     (セルクリックで拡大)                 │   │
│   │ P4                  -                                          │   │
│   │                                                                 │   │
│   │ 凡例: ▓ トレードオフ  ░ 相乗  ▒ 中立                          │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                [🔍 詳細分析を開く]  ← 70%に拡大                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 10.2.3 DesignCaseDetail 詳細分析表示（幅70%）

```
┌───────────────────────────────────────────────────────────────────────────┐
│ DesignCase Details - Tradeoff Analysis                           [←] ✕  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│ [cosθ Matrix ◉] [Energy Matrix ○]                                         │
│                                                                           │
│ ┌─────────────────────────────┬───────────────────────────────────────┐   │
│ │                             │                                       │   │
│ │     P1   P2   P3   P4       │   Shapley寄与度分解                   │   │
│ │ P1   -  ▓▓▓ ░░░ ▒▒▒        │   (P1 vs P2 を選択中)                 │   │
│ │ P2      -  ░░░ ▒▒▒         │                                       │   │
│ │ P3         -  ▒▒▒          │   A1: ████████████ +42%               │   │
│ │ P4             -           │   A3: ███████     +25%                │   │
│ │                             │   A2: █████       -18%               │   │
│ │  ヒートマップ               │   A4: ███         -15%               │   │
│ │  クリックでペア選択         │                                       │   │
│ │                             ├───────────────────────────────────────┤   │
│ │  cosθ = -0.72               │                                       │   │
│ │  C_ij = -0.45               │   ネットワークハイライト               │   │
│ │                             │   (寄与パス強調表示)                   │   │
│ │                             │                                       │   │
│ │                             │   [P1]←─A1(+42%)─┐                    │   │
│ │                             │                  ├──V1                │   │
│ │                             │   [P2]←─A2(-18%)─┘                    │   │
│ │                             │                                       │   │
│ └─────────────────────────────┴───────────────────────────────────────┘   │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 10.3 コンポーネント構成

```
frontend/src/components/
├── network/
│   ├── NetworkEditor.vue          # 修正: SCC警告バナー追加
│   ├── NetworkViewer.vue          # 既存
│   └── NetworkHighlightViewer.vue # 既存（Shapley用に再利用）
├── mountain/
│   ├── MountainView.vue           # 修正: 右パネル幅の動的切替
│   ├── DesignCaseDetail.vue       # 修正: Tradeoff Analysisセクション追加
│   └── DesignCaseForm.vue         # 既存
└── analysis/                      # 【新規ディレクトリ】
    ├── TradeoffMatrixMini.vue     # 50%幅用ミニヒートマップ
    ├── TradeoffAnalysisPanel.vue  # 70%幅用フル分析パネル
    ├── MatrixHeatmap.vue          # cosθ/Energy切替ヒートマップ
    ├── ShapleyBreakdown.vue       # 棒グラフ
    └── SCCWarningBanner.vue       # NetworkEditor用SCC警告
```

### 10.4 エラーを避ける実装順序

```
【Step 1】API呼び出しの追加 (リスク: 低)
├── ファイル: frontend/src/utils/api.ts
├── 内容: sccApi, shapleyApi の追加
└── 理由: 新規追加のみ、既存コードに影響なし

【Step 2】新規コンポーネント作成 (リスク: 低)
├── ファイル: frontend/src/components/analysis/*.vue (新規)
├── 内容: 各分析コンポーネントを独立して作成
└── 理由: 新規ファイル、既存コードに影響なし

【Step 3】NetworkEditorにSCC警告追加 (リスク: 低〜中)
├── ファイル: frontend/src/components/network/NetworkEditor.vue
├── 内容: Save時のSCCチェック、警告バナー表示
├── 依存: Step 1 (sccApi)
└── 理由: 追加のみ、既存の保存フローは維持

【Step 4】DesignCaseDetailに新セクション追加 (リスク: 中)
├── ファイル: frontend/src/components/mountain/DesignCaseDetail.vue
├── 内容: Tradeoff Analysisセクション（折りたたみ）
├── 依存: Step 1, Step 2
└── 理由: 既存セクションの後に追加、構造変更は最小限

【Step 5】MountainViewに幅切替機能追加 (リスク: 中)
├── ファイル: frontend/src/components/mountain/MountainView.vue
├── 内容: 右パネルの幅を50%↔70%で切替
├── 依存: Step 4
└── 理由: CSS変更のみ、既存ロジックに影響なし
```

### 10.5 APIの拡張（api.ts）

```typescript
// ========== SCC分析 ==========

export const sccApi = {
  analyze: (projectId: string, caseId: string) =>
    apiClient.get<{
      has_loops: boolean;
      n_components_with_loops: number;
      components: Array<{
        nodes: string[];
        edges: Array<{ source: string; target: string }>;
        spectral_radius: number;
        converges: boolean;
        suggestions: Array<{
          type: string;
          description: string;
          priority: number;
          action_required: boolean;
        }>;
      }>;
    }>(`/calculations/scc/${projectId}/${caseId}`),

  summary: (projectId: string) =>
    apiClient.get<{
      project_id: string;
      n_cases: number;
      cases_with_loops: number;
      summary: Array<{
        case_id: string;
        case_name: string;
        has_loops: boolean;
        n_components: number;
        all_converge: boolean;
      }>;
    }>(`/calculations/scc-summary/${projectId}`),
};

// ========== Shapley値分析 ==========

export const shapleyApi = {
  computeForPair: (
    projectId: string,
    caseId: string,
    perfIId: string,
    perfJId: string,
    method: 'auto' | 'exact' | 'monte_carlo' = 'auto'
  ) =>
    apiClient.get<{
      perf_i: { idx: number; name: string };
      perf_j: { idx: number; name: string };
      C_ij: number;
      cos_theta: number;
      relationship: 'tradeoff' | 'synergy' | 'neutral';
      shapley_values: Array<{
        property_idx: number;
        property_name: string;
        phi: number;
        abs_phi: number;
        percentage: number;
        sign: 'positive' | 'negative' | 'neutral';
      }>;
      computation: {
        method: string;
        n_properties: number;
        time_ms: number;
      };
    }>(`/calculations/shapley/${projectId}/${caseId}/${perfIId}/${perfJId}?method=${method}`),

  computeAll: (
    projectId: string,
    caseId: string,
    onlyTradeoffs: boolean = true
  ) =>
    apiClient.get(`/calculations/shapley-all/${projectId}/${caseId}?only_tradeoffs=${onlyTradeoffs}`),

  estimateCost: (nProperties: number) =>
    apiClient.get<{
      n_properties: number;
      n_subsets: number;
      estimated_time_ms: number;
      warning: 'low' | 'medium' | 'high';
      recommendation: 'exact' | 'exact_with_cache' | 'monte_carlo';
    }>(`/calculations/shapley-cost/${nProperties}`),
};

// ========== 構造的トレードオフ分析 ==========

export const structuralTradeoffApi = {
  getForCase: (projectId: string, caseId: string) =>
    apiClient.get<{
      cos_theta_matrix: number[][];
      inner_product_matrix: number[][];
      performance_ids: string[];
      performance_names: string[];
      spectral_radius: number;
      converges: boolean;
    }>(`/calculations/structural-tradeoff/${projectId}/${caseId}`),

  getPaperMetrics: (projectId: string, caseId: string) =>
    apiClient.get<{
      height: { H: number; breakdown: any[] };
      energy: { E: number; contributions: any[] };
      structural_tradeoff: any;
    }>(`/calculations/paper-metrics/${projectId}/${caseId}`),
};
```

---

## 次のアクション（優先順位順）

### Phase 5 完了 ✅

以下の実装が完了:
1. ✅ **api.ts拡張** - sccApi, shapleyApi, structuralTradeoffApi 追加
2. ✅ **分析コンポーネント作成** - 5つの新規Vueコンポーネント
3. ✅ **DesignCaseFormにSCC警告追加** - 保存前のループ検出
4. ✅ **DesignCaseDetailにTradeoff Analysisセクション追加**
5. ✅ **MountainViewに幅切替機能追加** - 50%↔70%

### Phase 5 UI改善 ✅ (2026-01-11)

1. ✅ **structural_tradeoff APIレスポンス拡張**
   - `inner_product_matrix` (C_ij行列) 追加
   - `energy_matrix` (E_ij = max(0, -C_ij)) 追加
   - `performance_id_map` (ネットワークノードID → DB ID マッピング) 追加
2. ✅ **ShapleyBreakdown表示改善**
   - 性能名に重要度表示: `P1 (w=3.0) vs P2 (w=2.5)`
   - メトリクス表示: `cos θ = -0.850` | `E_ij = 0.0234`
3. ✅ **MatrixHeatmapセル選択改善**
   - 上三角への自動変換を解除（クリックしたセルをそのまま選択）
   - 対称セルの自動ハイライトを解除

### Phase 4 完了 ✅ (2026-01-11)

1. ✅ **DBモデル拡張** (database.py)
   - DesignCaseModel に新フィールド追加:
     - `structural_analysis_json` - 構造的トレードオフ分析結果
     - `paper_metrics_json` - 論文準拠指標（H, E等）
     - `scc_analysis_json` - SCC分解結果
     - `kernel_type` - WLカーネルタイプ (default: 'classic_wl')
     - `weight_mode` - エッジ重みモード (default: 'discrete')
2. ✅ **Pydanticスキーマ追加** (schemas/analysis.py 新規作成)
   - SCCResult, SCCComponent - SCC分解スキーマ
   - StructuralTradeoffResult, TradeoffPair - 構造的トレードオフスキーマ
   - PaperMetrics, HeightMetrics, EnergyMetrics - 論文準拠指標スキーマ
   - ShapleyResult, ShapleyValue - Shapley値スキーマ
   - NetworkSettings - ネットワーク設定スキーマ
3. ✅ **エクスポート/インポート対応** (data_migration.py 新規作成)
   - バージョン管理: 1.0.0 → 1.1.0 → 2.0.0
   - `migrate_import_data()` - 古いデータを最新バージョンに変換
   - `validate_import_data()` - インポートデータ検証
   - `add_export_fields_to_design_case()` - エクスポート時の新規フィールド追加

### Phase 6 完了 ✅ (2026-01-11)

1. ✅ **エッジweight入力の拡張** (NetworkEditor.vue)
   - 重みモードセレクター追加（3/5/7段階・連続値）
   - 連続値モード: スライダー + 数値入力
   - 離散モード: ドロップダウン
   - 重みモード変更時の自動値調整
   - 連続値対応の色補間
2. ✅ **離散化信頼度表示** (DiscretizationConfidence.vue)
   - 符号保存率表示
   - 順位保存（Spearman ρ）表示
   - 違反ペアの詳細表示
   - 全体解釈（Excellent/Good/Moderate/Poor）

### 残タスク

- **マトリクス入力機能** (低優先度)
  - エクセルテンプレートダウンロード
  - CSVインポート機能

---

## Phase 7: PAVEモデル準拠とバリデーション強化（✅ 完了）

### 7.1 背景と目的

現在のネットワークエディタはPAVEモデルの厳密なルールを強制していない。
論文準拠のモデリングを確実にするため、以下の改善が必要。

### 7.2 実装項目

#### Step 29: Layer名称のPAVE準拠 ✅ 完了

**変更内容**:
- Layer 2: "Property" → "Attribute" に変更
- Layer 4: "Object/Environment" → "Entity" に変更（サブタイプとしてobject/environmentは維持）

**更新ファイル**:
- `NetworkEditor.vue` - UI表示、layers定義更新、マイグレーション関数追加
- `types/project.ts` - 型定義に 'attribute' 追加、`migrateNodeType()` ヘルパー追加
- `data_migration.py` - バージョン2.1.0でnode.type 'property' → 'attribute' 自動変換

#### Step 30: エッジ方向バリデーション ✅ 完了

**PAVEモデルのルール**:

| 接続 | 許可方向 | 備考 |
|------|---------|------|
| A → P | ✅ | Attribute→Performanceのみ |
| V → A | ✅ | Variable→Attributeのみ |
| V → P | ❌ | 禁止（必ずAを経由） |
| E → P | ❌ | 禁止（E→V→A→P） |
| E → A | ❌ | 禁止（E→V→A） |
| P → X | ❌ | 禁止（Performanceはソースになれない） |
| V ↔ E | ✅ | 無向（双方向OK） |
| A ↔ A | ✅ | ループ形成可能 |
| E ↔ E | ✅ | Entity間接続可能 |

**実装内容**:

1. **フロントエンド - エッジ作成時バリデーション**
   - `NetworkEditor.vue`: `validateEdgeDirection()` 関数追加
   - `createEdge()` でバリデーション実行、不正なエッジは作成拒否 + エラーメッセージ表示

2. **バックエンド - インポート時バリデーション**
   - `data_migration.py`: `validate_pave_edges()` 関数追加
   - `validate_import_data()` でPAVEルール違反をエラーとして検出

#### Step 31: Weightモード切替の安全性強化 ✅ 完了

**実装内容**:

1. **確認ダイアログの追加**
   - `NetworkEditor.vue`: `handleWeightModeChange()` に確認ダイアログ追加
   - エッジがある場合のみ確認を要求
   - 変更内容（モード名、影響するエッジ数、精度損失の警告）を表示
   - キャンセル時は元のモードを維持

2. **変更時の動作**
   - 離散→連続: 既存の値をそのまま維持
   - 連続/離散→別の離散: 最も近い有効値に丸める（精度損失の警告付き）

#### Step 32: SCC/ループ検出UIの明確化 ✅ 実装済み

**現在の実装**:

| タイミング | 処理内容 |
|-----------|---------|
| **保存時** | `handleNetworkSave()` で `sccApi.analyzeDirect()` を呼び出し |
| **発散ループ検出時** | `SCCWarningBanner` を表示 |
| **ユーザー選択肢** | 「Continue Anyway」または修正 |

**改善提案**（オプション）:
- エッジ作成時のリアルタイムループ検出
- ループ形成エッジのハイライト表示

### 7.3 実装状況

| Step | 内容 | 状態 | 備考 |
|------|------|--------|------|
| 29 | Layer名称変更 | ✅ 完了 | Property→Attribute、Object/Env→Entity |
| 30 | エッジ方向バリデーション | ✅ 完了 | フロントエンド+バックエンド双方で検証 |
| 31 | Weightモード切替安全性 | ✅ 完了 | 確認ダイアログ追加 |
| 32 | SCC UI改善 | ✅ 既存 | Phase 5で実装済み |

---

## Phase 8: UI改善とShapley計算バグ修正（✅ 完了）

### 8.1 Performance Analysis UI改善

#### Step 33: Performance Analysis UIリファクタリング ✅ 完了

**変更内容**:

1. **NetworkHighlightViewerの削除**
   - Performance Analysis セクションからネットワークビューアを削除
   - よりコンパクトな表形式UIに変更

2. **ソート機能の追加**
   - Achievement（達成率）: 低い順にソート
   - Weight（重み）: 高い順にソート
   - Energy（エネルギー）: 高い順にソート
   - ボタンは色分け: Achievement=緑、Weight=青緑、Energy=赤

3. **表示形式の変更**
   - "Remaining"（残り高さ）→ "Achievement"（達成率%）に変更
   - 達成率 = (actual / hMax) × 100
   - バーは達成率を視覚化（緑色グラデーション）

4. **カラースキーム統一**
   - Achievement: `$sub_4`（緑）
   - Weight: `$sub_6`（青緑）
   - Energy: `$sub_1`（赤）

**更新ファイル**:
- `frontend/src/components/mountain/DesignCaseDetail.vue`
  - `perfSortKey` を `'remaining'` から `'achievement'` に変更
  - `remainingHeights` に `achievementRate` フィールド追加
  - ソートボタンのスタイル修正（font-weight変更によるボタン幅変動を防止）

#### Step 34: セクション順序の変更 ✅ 完了

**変更内容**:
- Tradeoff Analysis セクションを Performance Analysis と Network Structure の間に移動

**理由**:
- パフォーマンス分析の後にトレードオフ分析を見る方が自然な流れ
- ネットワーク構造は補助情報として最後に配置

### 8.2 Shapley計算のweight_modeバグ修正

#### Step 35: Node/Edge Shapley APIのweight_mode対応 ✅ 完了

**問題**:
- Node Shapley の C_ij と Structural Tradeoff の C_ij が異なる値を示していた
- 例: Node C_ij = 0.0021、Edge C_ij = 0.3841
- 結果として Node Error が 0.38 と大きな値になっていた

**根本原因**:
- Node/Edge Shapley API が `build_adjacency_matrices(network)` を呼び出す際に `weight_mode` を渡していなかった
- デフォルト `'discrete_7'` が使用されていたが、設計案は `'discrete_3'` を使用していた
- 異なる weight_mode → 異なる B 行列 → 異なる T 行列 → 異なる C_ij

**修正内容**:

1. **Node Shapley API** (`/calculations/node-shapley/...`)
   ```python
   # Before
   matrices = build_adjacency_matrices(network)

   # After
   weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'
   matrices = build_adjacency_matrices(network, weight_mode)
   ```

2. **Edge Shapley API** (`/calculations/edge-shapley/...`)
   - 同様の修正を適用

**更新ファイル**:
- `backend/app/api/calculations.py` - 両APIでweight_modeを設計案から取得して渡す

#### Step 36: ShapleyBreakdown表示の改善 ✅ 完了

**変更内容**:

1. **nodeCij プロップの追加**
   - Node Shapley と Edge Shapley は異なる特性関数を使用するため、安全策として C_ij を別々に表示
   - `nodeCij` プロップを追加し、Node Error は nodeCij と比較

2. **Summary表示の改善**
   - Node Shapley セクション: Σφ_node、C_ij (node)、Node Error
   - Edge Shapley セクション: Σφ_edge、C_ij (edge)、Edge Error
   - 区切り線で視覚的に分離

**更新ファイル**:
- `frontend/src/components/analysis/ShapleyBreakdown.vue`
  - `nodeCij` プロップ追加
  - `nodeExpectedSum` computed property 追加
  - Summary テンプレート更新
- `frontend/src/components/analysis/TradeoffAnalysisModal.vue`
  - `:node-cij="nodeShapleyResult?.C_ij"` を追加

### 8.3 開発環境改善

#### Step 37: TypeScript IDE設定 ✅ 完了

**問題**:
- IDE（VS Code）で `@/` パスエイリアスが認識されず、エラー表示されていた

**修正内容**:
- `frontend/tsconfig.json` を作成
- `frontend/tsconfig.node.json` を作成
- `baseUrl` と `paths` を設定してパスエイリアスを解決

### 8.4 実装状況

| Step | 内容 | 状態 | 備考 |
|------|------|--------|------|
| 33 | Performance Analysis UI | ✅ 完了 | ソート機能、達成率表示 |
| 34 | セクション順序変更 | ✅ 完了 | Tradeoff を中央に移動 |
| 35 | Shapley weight_mode修正 | ✅ 完了 | 根本原因を解決 |
| 36 | ShapleyBreakdown改善 | ✅ 完了 | C_ij分離表示 |
| 37 | TypeScript IDE設定 | ✅ 完了 | パスエイリアス対応 |

---

## Phase 9: Import/Export機能とNetwork View改善（✅ 完了）

**実装日**: 2026-01-14

### 概要

データの移行・インポート機能の強化と、ネットワークビューの連続値対応を実装。

### Step 38: データ移行システム ✅ 完了

#### 背景
プロジェクトのJSONインポート時に、以下の課題があった:
- 重みモード間の値マッピングが必要
- Needのpriority値がない場合のデフォルト設定
- ユーザーが曖昧なケースを解決できるUI

#### 実装内容

**バックエンド (`backend/app/services/data_migration.py`)**:
```python
def analyze_import_data(data: dict) -> dict:
    """インポートデータを分析し、移行に必要な情報を返す"""
    # 重みモードの検出
    # 変換候補の生成
    # ユーザー選択が必要な項目の特定

def migrate_import_data(data: dict, user_choices: dict) -> dict:
    """ユーザーの選択に基づいてデータを移行"""
    # 重み値の変換
    # priority値の設定
```

**フロントエンド (`frontend/src/components/common/ImportPreviewDialog.vue`)**:
- インポートプレビューダイアログ
- 重みモード選択UI
- Need Priority個別設定テーブル

### Step 39: Need Priority個別設定 ✅ 完了

#### 背景
- インポート時に全Needに同じデフォルトpriority(1.0)が設定されていた
- ユーザーが個別のNeedごとにpriorityを設定したいという要望

#### 実装内容

**バックエンド変更**:
- `user_choices` タイプに `needs_priority_table` を追加
- 個別のNeed ID・名前を含むレスポンス

**フロントエンド変更**:
- `NeedPriorityItem` インターフェース追加
- 個別設定用テーブルUI（`NeedPerformanceMatrix.vue` のUIに準拠）

### Step 40: Priority反映の修正 ✅ 完了

#### 背景
- Priority値がMountain View/Radar Chartに反映されていなかった
- Priority stepが0.1で、100倍の重み付けができなかった

#### 実装内容

**Mountain Calculator修正** (`backend/app/services/mountain_calculator.py`):
```python
def distribute_votes_to_needs(project: ProjectModel) -> Dict[str, float]:
    """ステークホルダーの票をニーズに按分（重み付き）
    各ニーズのpriorityも適用される
    """
    need_priorities = {need.id: (need.priority if need.priority is not None else 1.0)
                       for need in project.needs}
    # ...
    for need_id, weight in related_needs:
        vote_portion = (weight / total_weight) * stakeholder.votes
        priority = need_priorities.get(need_id, 1.0)
        need_votes[need_id] = need_votes.get(need_id, 0) + (vote_portion * priority)
```

**Step変更**:
- `NeedPerformanceMatrix.vue`: step 0.1 → 0.01
- `ImportPreviewDialog.vue`: step 0.1 → 0.01

### Step 41: Network View連続値対応 ✅ 完了

#### 背景
- エッジの重みが連続値の場合、色が適切に表示されない
- 矢印マーカーが離散値のみ対応で、連続値では表示されない

#### 実装内容

**動的マーカー生成**:
```typescript
// 全エッジの色を収集して動的にマーカーを生成
const uniqueEdgeColors = computed(() => {
  const colors = new Set<string>();
  for (const edge of props.network.edges) {
    colors.add(getEdgeColor(edge));
  }
  return Array.from(colors);
});

// SVG ID用に色文字列をエンコード
function encodeColor(color: string): string {
  return color.replace(/[^a-zA-Z0-9]/g, '_');
}
```

**色補間（グラデーション）**:
```typescript
// maxWeightはモードに応じて決定
// 7-level: 5, 5-level: 3, 3-level/continuous: 1
const maxWeight = inferredMaxWeight.value;

if (weight > 0) {
  // 正: 薄い青 (#c3dde2) → 濃い青 (#002040)
  const t = weight / maxWeight;
  // RGB補間
} else if (weight < 0) {
  // 負: 薄い赤 (#e9c1c9) → 濃い赤 (#6f0020)
  const t = Math.abs(weight) / maxWeight;
  // RGB補間
}
```

**修正ファイル**:
- `NetworkEditor.vue`: currentWeightModeに基づくmaxWeight
- `NetworkViewer.vue`: データから推測するmaxWeight
- `NetworkHighlightViewer.vue`: データから推測するmaxWeight
- `TradeoffNetworkViewer.vue`: データから推測するmaxWeight

### Phase 9 進捗まとめ

| Step | 内容 | 状態 | 備考 |
|------|------|--------|------|
| 38 | データ移行システム | ✅ 完了 | ImportPreviewDialog追加 |
| 39 | Need Priority個別設定 | ✅ 完了 | needs_priority_tableタイプ |
| 40 | Priority反映修正 | ✅ 完了 | vote分配にpriority適用、step 0.01 |
| 41 | Network View連続値対応 | ✅ 完了 | 動的マーカー、色補間 |

---

## 参考文献（design.tex内）

| トピック | 行番号 | EXTENSION_PLAN セクション |
|---------|--------|--------------------------|
| PAVE構造定義 | 1964-1980 | 2.1 |
| 線形パスモデル | 2056-2212 | 2.2 |
| スペクトル半径・収束条件 | 2169-2212 | 2.2.3 |
| SCC分解・ループ処理 | 2398-2469 | 2.3 |
| 構造的トレードオフ指標 | 2534-2620 | 2.4 |
| 内積行列 C_ij | 5788, 6089-6093 | 2.5 |
| Shapley値 | 2849-2913 | 2.6 |
| 標高の定義 | 5727-5760 | 2.7 |
| 離散化信頼度（σ_eff） | 5990-6010 | 2.11.1 |
| 符号保存確率 P_sign | Theorem 6.9 | 2.11.2 |
| 順序保存確率 P_order | Theorem 6.10 | 2.11.3 |
| エネルギーの定義 | 6083-6169 | 2.8 |
| WLカーネル | 6206-6269 | 2.9 |
| MDS | 6298-6373 | 2.10 |
