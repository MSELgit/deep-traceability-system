# 計算処理サービス - 実装詳細

## 処理フロー全体像

```
API Request
    ↓
calculations.py (API層)
    ↓
discretization_confidence.py
    ├── analyze_discretization_confidence()
    │       ↓
    │   matrix_utils.py
    │       ├── build_adjacency_matrices()
    │       │       ↓
    │       │   weight_normalization.py
    │       │       └── normalize_weight()
    │       │               └── discrete_to_continuous()
    │       ↓
    │       ├── compute_total_effect_matrix()
    │       └── compute_inner_products()
    ↓
    └── compute_sign_preservation_for_pair()
            ↓
        scipy.stats.norm.cdf()
```

---

## 1. API層の処理 (calculations.py:590-680)

```python
@router.get("/discretization-confidence/{project_id}")
def get_discretization_confidence(project_id: str, db: Session):

    # Step 1: weight_mode の検証
    VALID_WEIGHT_MODES = {'discrete_3', 'discrete_5', 'discrete_7', 'continuous'}

    # Step 2: 設計案データを収集
    design_cases_data = []
    for dc in project.design_cases:
        raw_mode = getattr(dc, 'weight_mode', None) or 'discrete_7'
        weight_mode = raw_mode if raw_mode in VALID_WEIGHT_MODES else 'discrete_7'

        design_cases_data.append({
            'id': dc.id,
            'name': dc.name,
            'network': dc.network,      # JSON形式のネットワーク
            'weight_mode': weight_mode,
        })

    # Step 3: 計算実行
    result = compute_project_discretization_confidence(design_cases_data)

    # Step 4: レスポンス整形
    return {
        'sign_preservation_probability': result['sign_preservation_probability'],
        'order_preservation_probability': result['order_preservation_probability'],
        ...
    }
```

---

## 2. プロジェクト全体の信頼度計算 (discretization_confidence.py:361-460)

```python
def compute_project_discretization_confidence(design_cases: List[Dict]) -> Dict:
    """
    入力: design_cases = [
        {'id': 'xxx', 'name': '設計案1', 'network': {...}, 'weight_mode': 'discrete_7'},
        ...
    ]
    """

    all_sign_probs = []
    all_order_probs = []

    for case in design_cases:
        mode = case.get('weight_mode') or 'discrete_7'
        network = case.get('network')

        # 各設計案を個別に分析
        result = analyze_discretization_confidence(network, mode)

        # 符号保存確率を収集
        if result['sign_preservation']['per_pair']:
            all_sign_probs.append(result['sign_preservation']['average'])

        # 順序保存確率を収集
        all_order_probs.append(result['order_preservation']['average'])

    # 全設計案の統計
    avg_sign = np.mean(all_sign_probs)  # 例: 0.906
    min_sign = min(all_sign_probs)       # 例: 0.624
    avg_order = np.mean(all_order_probs) # 例: 0.950

    return {
        'sign_preservation_probability': float(avg_sign),
        'order_preservation_probability': float(avg_order),
        'min_sign_preservation': float(min_sign),
        ...
    }
```

---

## 3. 単一ネットワークの信頼度分析 (discretization_confidence.py:181-358)

```python
def analyze_discretization_confidence(network: Dict, weight_mode: str) -> Dict:
    """
    入力: network = {
        'nodes': [
            {'id': 'p1', 'layer': 1, 'label': '燃費'},
            {'id': 'a1', 'layer': 2, 'label': 'エンジン効率'},
            {'id': 'v1', 'layer': 3, 'label': '排気量'},
            ...
        ],
        'edges': [
            {'source_id': 'a1', 'target_id': 'p1', 'weight': 3},
            ...
        ]
    }
    """

    # Step 1: 連続モードの場合は誤差なし
    if weight_mode == 'continuous':
        return {'is_discrete': False, 'sign_preservation': {'average': 1.0}, ...}

    # Step 2: 離散化段階数を取得
    scheme = WEIGHT_SCHEMES.get(weight_mode, {})
    n_levels = scheme.get('n_levels', 7)  # 例: 7

    # Step 3: ネットワーク構造パラメータ
    nodes = network.get('nodes', [])
    n_attributes = sum(1 for n in nodes if n.get('layer') == 2)  # 例: 5
    avg_degree = compute_average_degree(network)                   # 例: 3.2

    # Step 4: 有効誤差 σ_eff を計算
    sigma_eff = compute_sigma_eff(n_levels, n_attributes, avg_degree)
    # σ_eff = (1/√(3×7)) × √(2/3 × 5 × 3.2²) = 0.218 × 3.67 = 0.80

    # Step 5: 隣接行列を構築
    matrices = build_adjacency_matrices(network, weight_mode)
    # matrices = {
    #     'B_PA': array([[0.6, 0.2], ...]),  # 性能×属性
    #     'B_AA': array([[0, 0.4], ...]),    # 属性×属性
    #     'B_AV': array([[0.8], ...]),       # 属性×変数
    #     'node_ids': {'P': ['p1', 'p2'], 'A': ['a1', 'a2'], 'V': ['v1']},
    #     ...
    # }

    # Step 6: 総効果行列を計算
    total_effect = compute_total_effect_matrix(
        matrices['B_PA'], matrices['B_AA'], matrices['B_AV']
    )
    T = total_effect['T']
    # T[i, j] = 変数 j が性能 i に与える総効果
    # 例: T = [[0.52, 0.31], [0.18, 0.45]]

    # Step 7: 内積・ノルムを計算
    inner_products = compute_inner_products(T)
    C = inner_products['C']        # 内積行列 C[i,j] = T[i,:] · T[j,:]
    norms = inner_products['norms'] # ノルム ||T[i,:]||
    # 例: C = [[0.38, -0.12], [-0.12, 0.24]]
    # 例: norms = [0.62, 0.49]

    # Step 8: 各ペアの符号保存確率を計算
    n_perf = len(norms)
    sign_probs = []

    for i in range(n_perf):
        for j in range(i + 1, n_perf):
            C_ij = C[i, j]  # 例: -0.12

            prob = compute_sign_preservation_for_pair(
                C_ij,           # -0.12
                norms[i],       # 0.62
                norms[j],       # 0.49
                sigma_eff       # 0.80
            )
            # prob = 0.58 (58%の確率で符号が保存される)

            sign_probs.append(prob)

    # Step 9: 統計を計算
    avg_sign = np.mean(sign_probs)  # 全ペアの平均
    min_sign = min(sign_probs)      # 最も信頼性の低いペア

    return {
        'sign_preservation': {
            'average': float(avg_sign),
            'min': float(min_sign),
            ...
        },
        ...
    }
```

---

## 4. 有効誤差 σ_eff の計算 (discretization_confidence.py:31-75)

**理論的背景（design.tex Chapter 6）:**

離散化による重み誤差 δb は一様分布 U(-d/2, d/2) に従う。
ここで d は離散化のステップ幅（例: discrete_3 では d = 2/3）。

この誤差が総効果行列 T を経由して内積 C_ij に伝播する。
誤差伝播を考慮した有効誤差 σ_eff は以下の式で計算される。

**σ_eff の公式（design.tex 準拠）:**
```
B_AA = 0 の場合（ループなし）:
  σ_eff = σ_ε × √(2/3 × l × d²)

B_AA ≠ 0 の場合（ループあり）:
  σ_eff = σ_ε × √(2/3 × l × d² × (1 + ||B_AA||_F²))

ここで:
  σ_ε = 1/(√3 × n)  ← 離散化誤差の標準偏差
  ||B_AA||_F = フロベニウスノルム = √(Σ b_ij²)
```

**パラメータの意味:**
| パラメータ | 意味 | 取得方法 |
|-----------|------|---------|
| n | 離散化レベル数 | discrete_3→3, discrete_5→5, discrete_7→7 |
| l | 属性(Attribute)ノード数 | `sum(1 for n in nodes if n['layer'] == 2)` |
| d | **接続密度** | 存在するエッジ数 / 可能なエッジ数 [0, 1] |
| ||B_AA||_F | 属性間行列のフロベニウスノルム | `np.linalg.norm(B_AA, 'fro')` |

**注意: d は「平均次数」ではなく「接続密度（connection density）」**

接続密度の計算:
```
可能なエッジ数 = |A|×|P| + |A|×|A| + |V|×|A|
              （A→P）   （A→A）   （V→A）

d = 実際の非ゼロエッジ数 / 可能なエッジ数
```

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

    入力例（loop設計案, discrete_3）:
        n_discrete_levels = 3       (3段階離散化)
        n_attributes = 3            (属性ノード3個)
        connection_density = 0.333  (10/30 エッジ)
        B_AA_frobenius_norm = 1.155 (ループあり)
    """

    if n_discrete_levels <= 0 or n_attributes <= 0 or connection_density <= 0:
        return 0.0

    # σ_ε = 1/(√3 × n) = 1/(√3 × 3) = 0.1925
    sigma_epsilon = 1.0 / (np.sqrt(3) * n_discrete_levels)

    # 基本項: 2/3 × l × d² = 2/3 × 3 × 0.333² = 0.222
    base_term = (2.0 / 3.0) * n_attributes * (connection_density ** 2)

    # ループ補正係数: 1 + ||B_AA||_F² = 1 + 1.155² = 2.333
    loop_factor = 1.0 + B_AA_frobenius_norm ** 2

    # σ_eff = σ_ε × √(base_term × loop_factor)
    #       = 0.1925 × √(0.222 × 2.333)
    #       = 0.1925 × 0.720
    #       = 0.1386
    return sigma_epsilon * np.sqrt(base_term * loop_factor)
```

**数値例（loop設計案）:**
```
ノード数: P=5, A=3, V=2
可能なエッジ数: 3×5 + 3×3 + 2×3 = 15 + 9 + 6 = 30
実際のエッジ数: A→P=5, A→A=3, V→A=2 → 合計 10

d = 10 / 30 = 0.333

B_AA行列（連続値）:
  [[ 0.000, -0.667,  0.000 ],
   [ 0.000,  0.000, -0.667 ],
   [ 0.667,  0.000,  0.000 ]]

||B_AA||_F = √(0.667² + 0.667² + 0.667²) = √1.333 = 1.155

計算:
  n = 3, l = 3, d = 0.333, ||B_AA||_F = 1.155

  σ_ε = 1/(√3 × 3) = 0.1925
  基本項 = 2/3 × 3 × 0.333² = 0.222
  ループ補正 = 1 + 1.155² = 2.333
  σ_eff = 0.1925 × √(0.222 × 2.333) = 0.1925 × 0.720 = 0.1386
```

σ_eff が大きいほど離散化誤差の影響が大きい。
- レベル数 n を増やす → σ_eff 減少
- 属性ノード数 l が増える → σ_eff 増加
- 接続密度 d が増える → σ_eff 増加
- **ループ構造 ||B_AA||_F が増える → σ_eff 増加**（誤差が循環・増幅）

---

## 5. 符号保存確率 P_sign の計算 (discretization_confidence.py:99-134)

**理論（Theorem 6.9）:**

内積 C_ij = T_i · T_j の符号（正 or 負）が離散化によって反転しない確率。

```
P_sign = Φ(|C_ij| / σ_δC)
```

ここで:
- Φ: 標準正規分布の累積分布関数
- C_ij: 性能ペア(i,j)の内積（**cos θ ではない！**）
- σ_δC: 内積の誤差標準偏差

**重要: C_ij は内積であり、cos θ ではない**

```
σ_δC = σ_eff × √(||T_i||² + ||T_j||²)
```

この式は誤差伝播から導出される。T_i と T_j の両方に誤差が乗るため、
両者のノルムの二乗和の平方根で重み付けされる。

```python
def compute_sign_preservation_for_pair(
    C_ij: float,      # 内積値（例: -0.5762）
    norm_i: float,    # ||T_i||（例: 0.7591）
    norm_j: float,    # ||T_j||（例: 0.7591）
    sigma_eff: float  # 有効誤差（例: 0.0907）
) -> float:
    """
    P_sign = Φ(|C_ij| / σ_δC)
    """

    if sigma_eff <= 0:
        return 1.0  # 誤差なし → 確実に保存

    # norm_sum_sq = 0.7591² + 0.7591² = 1.1524
    norm_sum_sq = norm_i ** 2 + norm_j ** 2

    if norm_sum_sq <= 0:
        return 1.0

    # σ_δC = 0.0907 × √1.1524 = 0.0907 × 1.07 = 0.0974
    sigma_delta_C = sigma_eff * np.sqrt(norm_sum_sq)

    # z = |-0.5762| / 0.0974 = 5.92
    z = abs(C_ij) / sigma_delta_C

    # P_sign = Φ(5.92) ≈ 1.0 (100%)
    return float(stats.norm.cdf(z))
```

**数値例（loop設計案 P1 vs P2）:**
```
入力:
  C_ij = -0.5762（内積、負 = トレードオフ）
  ||T_1|| = 0.7591
  ||T_2|| = 0.7591
  σ_eff = 0.0907

計算:
  ||T_1||² + ||T_2||² = 0.576 + 0.576 = 1.152
  σ_δC = 0.0907 × √1.152 = 0.0907 × 1.07 = 0.0974
  z = |-0.5762| / 0.0974 = 5.92
  P_sign = Φ(5.92) ≈ 100%

解釈: ほぼ100%の確率で、P1-P2間のトレードオフ関係（負の内積）が
      離散化後も正しく検出される
```

**よくある間違い:**
- ❌ `P_sign = Φ(|cos θ| / σ_eff)` ← cos θ を使うのは間違い
- ✅ `P_sign = Φ(|C_ij| / σ_δC)` ← 内積 C_ij を使う

---

## 6. 順序保存確率 P_order の計算 (discretization_confidence.py:137-178)

**理論（Theorem 6.10）:**

2つのペア間の内積の大小関係が保存される確率。
例: C_{12} < C_{34} という順序が離散化後も維持されるか。

```
P_order = Φ(|Δ| / σ_δΔ)
```

ここで:
- Δ = |C_p1 - C_p2|: 2つのペアの内積の差
- σ_δΔ: 差の誤差標準偏差

```
σ_δΔ = σ_eff × √(||T_i1||² + ||T_j1||² + ||T_i2||² + ||T_j2||²)
```

4つのノルムの二乗和を使う（2つのペアで4つの性能ベクトル）。

```python
def compute_order_preservation_for_pairs(
    C_p1: float,      # ペア1の内積（例: -0.5762）
    C_p2: float,      # ペア2の内積（例: 0.3841）
    norm_i1: float,   # ペア1の ||T_i||（例: 0.7591）
    norm_j1: float,   # ペア1の ||T_j||（例: 0.7591）
    norm_i2: float,   # ペア2の ||T_i||（例: 0.7591）
    norm_j2: float,   # ペア2の ||T_j||（例: 0.5060）
    sigma_eff: float  # 有効誤差（例: 0.0907）
) -> float:
    """
    P_order = Φ(|Δ| / σ_δΔ)
    """

    if sigma_eff <= 0:
        return 1.0

    # Δ = |-0.5762 - 0.3841| = 0.9603
    delta = abs(C_p1 - C_p2)

    # norm_sum_sq = 0.7591² + 0.7591² + 0.7591² + 0.5060² = 1.98
    norm_sum_sq = norm_i1**2 + norm_j1**2 + norm_i2**2 + norm_j2**2

    if norm_sum_sq <= 0:
        return 1.0

    # σ_δΔ = 0.0907 × √1.98 = 0.0907 × 1.41 = 0.128
    sigma_delta = sigma_eff * np.sqrt(norm_sum_sq)

    # z = 0.9603 / 0.128 = 7.51
    z = delta / sigma_delta

    # P_order = Φ(7.51) ≈ 1.0 (100%)
    return float(stats.norm.cdf(z))
```

**数値例（loop設計案 (P1-P2) vs (P1-P3)）:**
```
入力:
  C_{P1-P2} = -0.5762（トレードオフ）
  C_{P1-P3} = 0.3841（シナジー）
  ||T_1|| = 0.7591, ||T_2|| = 0.7591
  ||T_1|| = 0.7591, ||T_3|| = 0.5060
  σ_eff = 0.0907

計算:
  Δ = |-0.5762 - 0.3841| = 0.9603
  norm_sum_sq = 0.576 + 0.576 + 0.576 + 0.256 = 1.98
  σ_δΔ = 0.0907 × √1.98 = 0.128
  z = 0.9603 / 0.128 = 7.51
  P_order = Φ(7.51) ≈ 100%

解釈: ほぼ100%の確率で、「P1-P2の方がP1-P3より内積が小さい」
      という順序が離散化後も正しく維持される
```

---

## 7. 隣接行列の構築 (matrix_utils.py:80-200)

**処理対象のエッジ（PAVEモデル準拠）:**
```
有効:
  A → P (layer 2 → 1): B_PA に格納
  A → A (layer 2 → 2): B_AA に格納
  V → A (layer 3 → 2): B_AV に格納

無視（行列に格納されない）:
  V → V (layer 3 → 3): 無効 - Variableは独立
  A → V (layer 2 → 3): 無効 - 因果の逆流
  V → P (layer 3 → 1): 無効 - Aを経由すべき
  E → X: Entity関連は計算対象外（接続情報のみ）
```

**バリデーション:**
- フロントエンド: `NetworkEditor.vue` の `validateEdgeDirection()` でエッジ作成時に検証
- バックエンド: `data_migration.py` の `validate_pave_edges()` でインポート時に検証

```python
def build_adjacency_matrices(network: Dict, weight_mode: str) -> Dict:
    """
    ネットワークから3つの隣接行列を構築
    ※ 無効なエッジ (V→V, A→V等) は無視される
    """

    nodes = network.get('nodes', [])
    edges = network.get('edges', [])

    # Step 1: レイヤー別にノードを分類
    perf_nodes = [n for n in nodes if n.get('layer') == 1]   # 性能
    attr_nodes = [n for n in nodes if n.get('layer') == 2]   # 属性
    var_nodes = [n for n in nodes if n.get('layer') == 3]    # 変数

    n_perf = len(perf_nodes)  # 例: 2
    n_attr = len(attr_nodes)  # 例: 3
    n_var = len(var_nodes)    # 例: 2

    # Step 2: ノードIDとインデックスのマッピング
    perf_idx = {n['id']: i for i, n in enumerate(perf_nodes)}
    attr_idx = {n['id']: i for i, n in enumerate(attr_nodes)}
    var_idx = {n['id']: i for i, n in enumerate(var_nodes)}

    # Step 3: 行列を初期化
    B_PA = np.zeros((n_perf, n_attr))  # 性能×属性
    B_AA = np.zeros((n_attr, n_attr))  # 属性×属性
    B_AV = np.zeros((n_attr, n_var))   # 属性×変数

    # Step 4: エッジを行列に変換
    for edge in edges:
        source_id = edge.get('source_id')
        target_id = edge.get('target_id')
        weight = edge.get('weight', 0)

        # 重みを正規化 (例: 3 → 0.6 for discrete_7)
        normalized_weight = normalize_weight(weight, weight_mode)

        # エッジの種類に応じて適切な行列に格納
        if target_id in perf_idx and source_id in attr_idx:
            # 属性 → 性能
            i = perf_idx[target_id]
            j = attr_idx[source_id]
            B_PA[i, j] = normalized_weight

        elif target_id in attr_idx and source_id in attr_idx:
            # 属性 → 属性
            i = attr_idx[target_id]
            j = attr_idx[source_id]
            B_AA[i, j] = normalized_weight

        elif target_id in attr_idx and source_id in var_idx:
            # 変数 → 属性
            i = attr_idx[target_id]
            j = var_idx[source_id]
            B_AV[i, j] = normalized_weight

    return {
        'B_PA': B_PA,
        'B_AA': B_AA,
        'B_AV': B_AV,
        'node_ids': {
            'P': [n['id'] for n in perf_nodes],
            'A': [n['id'] for n in attr_nodes],
            'V': [n['id'] for n in var_nodes],
        },
        ...
    }
```

---

## 8. 重み正規化 (weight_normalization.py:91-129)

```python
def discrete_to_continuous(weight: float, mode: str) -> float:
    """
    離散値 → 連続値 [-1, 1] に変換

    discrete_7 のマッピング:
        -5 → -1.0
        -3 → -0.6
        -1 → -0.2
         0 →  0.0
        +1 → +0.2
        +3 → +0.6
        +5 → +1.0
    """

    # None チェック
    if weight is None:
        return 0.0

    # 無効なモードは discrete_7 にフォールバック
    if mode not in WEIGHT_SCHEMES:
        mode = 'discrete_7'

    # 連続モードはそのままクリップ
    if mode == 'continuous':
        return float(np.clip(weight, -1.0, 1.0))

    # 離散→連続マッピングを取得
    mapping = DISCRETE_TO_CONTINUOUS_MAPS.get(mode, {})
    # 例: {-5: -1.0, -3: -0.6, -1: -0.2, 0: 0.0, 1: 0.2, 3: 0.6, 5: 1.0}

    # 完全一致の場合
    if weight in mapping:
        return mapping[weight]  # 例: 3 → 0.6

    # 最も近い離散値を見つける
    discrete_values = WEIGHT_SCHEMES[mode]['discrete_values']
    closest = min(discrete_values, key=lambda x: abs(x - weight))
    return mapping.get(closest, 0.0)
```

---

## 9. 総効果行列の計算 (matrix_utils.py:255-302)

```python
def compute_total_effect_matrix(B_PA, B_AA, B_AV) -> Dict:
    """
    T = B_PA × (I - B_AA)^(-1) × B_AV

    入力例:
        B_PA: [[0.6, 0.2, 0],      # 2×3 (2性能, 3属性)
               [0, 0.4, 0.8]]
        B_AA: [[0, 0.3, 0],        # 3×3 (属性間相互作用)
               [0, 0, 0.2],
               [0, 0, 0]]
        B_AV: [[0.8, 0],           # 3×2 (3属性, 2変数)
               [0.4, 0.6],
               [0, 0.5]]
    """

    n_attr = B_AA.shape[0]
    I = np.eye(n_attr)

    # Step 1: スペクトル半径をチェック
    eigenvalues = np.linalg.eigvals(B_AA)
    spectral_radius = np.max(np.abs(eigenvalues))
    # 例: spectral_radius = 0.3

    convergence = spectral_radius < 1.0

    # Step 2: (I - B_AA)^(-1) を計算
    if convergence:
        # 直接逆行列
        try:
            inv_term = np.linalg.inv(I - B_AA)
        except np.linalg.LinAlgError:
            # Neumann級数で近似
            inv_term = I.copy()
            power = B_AA.copy()
            for _ in range(20):
                inv_term += power
                power = power @ B_AA
    else:
        # 発散する場合は警告（Neumann級数で近似）
        inv_term = I.copy()
        power = B_AA.copy()
        for _ in range(10):
            inv_term += power
            power = power @ B_AA

    # Step 3: T = B_PA × inv_term × B_AV
    T = B_PA @ inv_term @ B_AV
    # 結果例: T = [[0.52, 0.31],   # 2×2 (2性能, 2変数)
    #              [0.18, 0.45]]
    # T[0,0] = 0.52: 変数1が性能1に与える総効果

    return {
        'T': T,
        'spectral_radius': float(spectral_radius),
        'convergence': convergence,
        ...
    }
```

---

## 10. 内積行列の計算 (matrix_utils.py:309-361)

```python
def compute_inner_products(T: np.ndarray) -> Dict:
    """
    内積行列 C と cos θ 行列を計算

    入力例:
        T = [[0.52, 0.31],   # 性能1の効果ベクトル: [0.52, 0.31]
             [0.18, 0.45]]   # 性能2の効果ベクトル: [0.18, 0.45]
    """

    n_perf = T.shape[0]

    # Step 1: 各性能のノルムを計算
    norms = np.array([np.linalg.norm(T[i, :]) for i in range(n_perf)])
    # norms[0] = √(0.52² + 0.31²) = √(0.27 + 0.10) = 0.61
    # norms[1] = √(0.18² + 0.45²) = √(0.03 + 0.20) = 0.48

    # Step 2: 内積行列 C を計算
    C = T @ T.T
    # C[0,1] = 0.52×0.18 + 0.31×0.45 = 0.094 + 0.140 = 0.234
    # 結果: C = [[0.37, 0.23],
    #            [0.23, 0.24]]

    # Step 3: cos θ 行列を計算
    cos_theta = np.zeros((n_perf, n_perf))
    for i in range(n_perf):
        for j in range(n_perf):
            if norms[i] > 0 and norms[j] > 0:
                cos_theta[i, j] = C[i, j] / (norms[i] * norms[j])
            else:
                cos_theta[i, j] = 0.0

    # cos_theta[0,1] = 0.234 / (0.61 × 0.48) = 0.234 / 0.293 = 0.80
    # → シナジー関係（正の相関）

    return {
        'C': C,              # 内積行列
        'cos_theta': cos_theta,  # cos θ 行列
        'norms': norms,      # ノルムベクトル
    }
```

---

## 実行例

```python
# テストコード
from app.services.discretization_confidence import analyze_discretization_confidence

network = {
    'nodes': [
        {'id': 'p1', 'layer': 1, 'label': '燃費'},
        {'id': 'p2', 'layer': 1, 'label': '加速性能'},
        {'id': 'a1', 'layer': 2, 'label': 'エンジン効率'},
        {'id': 'a2', 'layer': 2, 'label': '車両重量'},
        {'id': 'v1', 'layer': 3, 'label': '排気量'},
    ],
    'edges': [
        {'source_id': 'a1', 'target_id': 'p1', 'weight': 5},   # 強い正の効果
        {'source_id': 'a1', 'target_id': 'p2', 'weight': 3},   # 中程度の正
        {'source_id': 'a2', 'target_id': 'p1', 'weight': -3},  # 中程度の負
        {'source_id': 'a2', 'target_id': 'p2', 'weight': -5},  # 強い負
        {'source_id': 'v1', 'target_id': 'a1', 'weight': 3},
        {'source_id': 'v1', 'target_id': 'a2', 'weight': 5},
    ]
}

result = analyze_discretization_confidence(network, 'discrete_7')

print(f"σ_eff: {result['sigma_eff']:.4f}")
print(f"Sign Preservation: {result['sign_preservation']['average']:.1%}")
print(f"Interpretation: {result['interpretation']}")

# 出力:
# σ_eff: 0.5443
# Sign Preservation: 87.3%
# Interpretation: 7-level discretization is generally reliable (P_sign ≥ 85%)
```

---

## 完全な計算例: loop設計案（discrete_3）

以下は「loop」設計案に対する完全な計算過程。

### 入力データ
```
ノード:
  Performance (layer 1): P1, P2, P3, P4, P5
  Attribute (layer 2): A1, A2, A3
  Variable (layer 3): V1, V2

エッジ（離散値）:
  V1 → A1: +1
  V2 → A3: -1
  A1 → A2: +1
  A2 → A3: -1
  A3 → A1: -1  ← ループ構造
  A1 → P1: +1
  A1 → P2: -1
  A2 → P3: +1
  A2 → P4: +1
  A3 → P5: +1

weight_mode: discrete_3
```

### Step 1: 重みの連続値変換
```
discrete_3 マッピング:
  -1 → -2/3 ≈ -0.667
   0 →  0
  +1 → +2/3 ≈ +0.667
```

### Step 2: B行列の構築
```
B_PA (5×3):         A1      A3      A2
         P1: [  0.667,  0.000,  0.000 ]
         P2: [ -0.667,  0.000,  0.000 ]
         P3: [  0.000,  0.000,  0.667 ]
         P4: [  0.000,  0.000,  0.667 ]
         P5: [  0.000,  0.667,  0.000 ]

B_AA (3×3):         A1      A3      A2
         A1: [  0.000, -0.667,  0.000 ]  ← A3→A1 = -0.667
         A3: [  0.000,  0.000, -0.667 ]  ← A2→A3 = -0.667
         A2: [  0.667,  0.000,  0.000 ]  ← A1→A2 = +0.667

B_AV (3×2):         V1      V2
         A1: [  0.667,  0.000 ]
         A3: [  0.000, -0.667 ]
         A2: [  0.000,  0.000 ]
```

### Step 3: T行列の計算
```
ループゲイン = 0.667 × (-0.667) × (-0.667) = 0.296 < 1 ✓

(I - B_AA)^(-1) =
  [[ 1.421, -0.947,  0.632 ],
   [-0.632,  1.421, -0.947 ],
   [ 0.947, -0.632,  1.421 ]]

T = B_PA × (I - B_AA)^(-1) × B_AV

T (5×2):            V1      V2
         P1: [  0.632,  0.421 ]
         P2: [ -0.632, -0.421 ]
         P3: [  0.421,  0.281 ]
         P4: [  0.421,  0.281 ]
         P5: [ -0.281, -0.632 ]
```

### Step 4: C行列（内積）とcos θ
```
C = T × T^T

C (5×5):
         P1      P2      P3      P4      P5
    P1: 0.576  -0.576   0.384   0.384  -0.443
    P2:-0.576   0.576  -0.384  -0.384   0.443
    P3: 0.384  -0.384   0.256   0.256  -0.296
    P4: 0.384  -0.384   0.256   0.256  -0.296
    P5:-0.443   0.443  -0.296  -0.296   0.478

ノルム ||T_i||:
  P1: 0.759, P2: 0.759, P3: 0.506, P4: 0.506, P5: 0.691

cos θ (5×5):
              P1      P2      P3      P4      P5
         P1: 1.000  -1.000   1.000   1.000  -0.845
         P2:-1.000   1.000  -1.000  -1.000   0.845
         P3: 1.000  -1.000   1.000   1.000  -0.845
         P4: 1.000  -1.000   1.000   1.000  -0.845
         P5:-0.845   0.845  -0.845  -0.845   1.000
```

### Step 5: σ_eff の計算
```
パラメータ:
  n = 3（離散化レベル数）
  l = 3（属性ノード数）
  d = 0.333（接続密度 = 10/30）
  ||B_AA||_F = 1.155（ループあり）

B_AA行列: 3つの非ゼロエッジ（A3→A1, A2→A3, A1→A2）、各 ±0.667

||B_AA||_F = √(0.667² + 0.667² + 0.667²) = √1.333 = 1.155

σ_ε = 1/(√3 × 3) = 0.1925
基本項 = 2/3 × 3 × 0.333² = 0.222
ループ補正 = 1 + 1.155² = 2.333

σ_eff = 0.1925 × √(0.222 × 2.333)
      = 0.1925 × 0.720
      = 0.1386
```

### Step 6: P_sign の計算

σ_eff = 0.1386 を使用

| ペア | C_ij | ||T_i||²+||T_j||² | σ_δC | z | P_sign |
|------|------|-------------------|------|------|--------|
| P1-P2 | -0.576 | 1.152 | 0.149 | 3.87 | **99.99%** |
| P1-P3 | 0.384 | 0.832 | 0.126 | 3.04 | 99.9% |
| P1-P4 | 0.384 | 0.832 | 0.126 | 3.04 | 99.9% |
| P1-P5 | -0.443 | 1.054 | 0.142 | 3.12 | 99.9% |
| P2-P3 | -0.384 | 0.832 | 0.126 | 3.04 | 99.9% |
| P2-P4 | -0.384 | 0.832 | 0.126 | 3.04 | 99.9% |
| P2-P5 | 0.443 | 1.054 | 0.142 | 3.12 | 99.9% |
| P3-P4 | 0.256 | 0.512 | 0.099 | 2.58 | 99.5% |
| P3-P5 | -0.296 | 0.734 | 0.119 | 2.49 | 99.4% |
| P4-P5 | -0.296 | 0.734 | 0.119 | 2.49 | 99.4% |

**P_sign サマリー:** 最小 99.4%, 最大 99.99%, 平均 99.8%

### Step 7: P_order の計算（代表例）

σ_eff = 0.1386 を使用

| ペア組 | Δ | σ_δΔ | z | P_order |
|--------|------|------|------|---------|
| (P1-P2) vs (P1-P3) | 0.960 | 0.195 | 4.92 | **100%** |
| (P1-P2) vs (P1-P5) | 0.133 | 0.206 | 0.65 | 74.2% |
| (P1-P2) vs (P2-P3) | 0.192 | 0.195 | 0.98 | 83.6% |

**P_order サマリー:** 最小 50.0%, 最大 100%, 平均 90.0%

### 結論

loop設計案（discrete_3）の離散化信頼度:
- **σ_eff = 0.1386**: ループ構造による誤差増幅を考慮
  - ||B_AA||_F = 1.155（ループあり）
  - ループなしの場合 σ_eff = 0.0907
- **P_sign = 99.4-99.99%**: 全ペアで符号保存が確実
- **P_order = 50-100%**: 順序保存も高い（平均 90%）
- **評価**: discrete_3 でも十分な信頼性あり

比較参考（d = 0.333, ||B_AA||_F = 1.155 の場合）:
| モード | n | σ_eff | 期待 P_sign |
|--------|---|-------|-------------|
| discrete_3 | 3 | 0.139 | ~99.5% |
| discrete_5 | 5 | 0.083 | ~99.9% |
| discrete_7 | 7 | 0.059 | ~100% |
| continuous | ∞ | 0 | 100% |

**注意**:
- σ_eff は接続密度 d に大きく依存する。密なネットワーク（d → 1）ほど σ_eff が増加し、P_sign が低下する。
- **ループ構造（B_AA ≠ 0）は誤差を増幅する**。||B_AA||_F が大きいほど σ_eff が増加する。
