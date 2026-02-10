# Deep Traceability System - 詳細技術ドキュメント

**作成日**: 2025年12月23日
**バージョン**: 1.2 (望ましさ方向対応・エネルギー4象限分解・構造/エネルギーモード切替)

---

## 目次

1. [システム概要](#1-システム概要)
2. [理論的背景](#2-理論的背景)
3. [システムアーキテクチャ](#3-システムアーキテクチャ)
4. [データモデル](#4-データモデル)
5. [バックエンド詳細](#5-バックエンド詳細)
6. [フロントエンド詳細](#6-フロントエンド詳細)
7. [計算アルゴリズム](#7-計算アルゴリズム)
8. [ユーザーワークフロー](#8-ユーザーワークフロー)
9. [API リファレンス](#9-api-リファレンス)
10. [セットアップガイド](#10-セットアップガイド)

---

## 1. システム概要

### 1.1 目的

Deep Traceability System は、複雑なシステム設計における**多目的意思決定支援ツール**です。

複数のステークホルダー（利害関係者）が異なる優先順位を持つ状況で、設計案の評価・比較を行い、トレードオフを可視化することで、より良い意思決定を支援します。

### 1.2 主要な特徴

| 機能 | 説明 |
|-----|------|
| **ステークホルダー分析** | 関係者の投票権に基づく重み付け |
| **ニーズ・性能マトリクス** | 要求と性能指標の関連付け |
| **効用関数設計** | 性能値から満足度への変換関数 |
| **4層ネットワーク構造** | 因果関係のモデル化 |
| **3D山の可視化** | 設計案の総合評価を3D表示 |
| **トレードオフ分析** | 性能間の競合関係の定量化 |
| **Shapley値分解** | トレードオフへの属性寄与度分析 |
| **カップリング/クラスタリング** | トレードオフ間の結合度と性能グループ化 |
| **エネルギー計算** | 設計案の内部整合性評価（4象限分解対応） |
| **望ましさ方向対応** | 性能の望大/望小混在への対応 |
| **構造/エネルギーモード切替** | Shapley・ネットワークで2視点の切替表示 |

### 1.3 想定ユースケース

- 船舶設計における複数性能の最適化
- 再生可能エネルギーシステムの設計比較
- 複雑な製品設計での意思決定支援
- 研究開発における設計空間の探索

---

## 2. 理論的背景

### 2.1 Deep Traceability とは

Deep Traceability は、システム設計における**意思決定の根拠を追跡可能にする手法**です。

```
ステークホルダー → ニーズ → 性能 → 設計変数
     ↓              ↓         ↓
   投票数        優先度     効用関数
```

この連鎖により、「なぜこの設計案が良いのか」を定量的に説明できます。

### 2.2 効用関数（Utility Function）

効用関数は、**性能値を満足度（0〜1）に変換する関数**です。

#### 連続型効用関数
```
U(x) = f(性能値)  →  0.0 〜 1.0

例：速度 100km/h → 効用 0.8
    速度 150km/h → 効用 1.0
```

制御点を設定し、線形補間で中間値を計算します。

#### 離散型効用関数
```
ラベル    効用値
"低"   →  0.2
"中"   →  0.5
"高"   →  1.0
```

カテゴリカルな性能値に対応します。

### 2.3 票数配分メカニズム

ステークホルダーの投票数は、以下の流れで性能に配分されます：

```
1. ステークホルダー → ニーズ
   - 関係の重み（○=1.0, △=0.5）で按分

2. ニーズ → 性能
   - 方向性（↑=上昇が良い, ↓=下降が良い）を考慮
   - シャノンエントロピーで方向の一貫性を評価
   - 票数を性能に分配
```

### 2.4 標高（Height）の計算

設計案の総合評価値である「標高 H」は：

```
H = Σ (票数_i × 効用値_i) / Σ 票数_i

ここで：
- 票数_i: 性能 i に配分された票数
- 効用値_i: 設計案の性能値から効用関数で算出
```

標高が高いほど、ステークホルダー全体の満足度が高い設計案です。

### 2.5 4層ネットワーク構造

設計案の因果関係を4層で表現します：

| レイヤー | 名称 | 説明 | 例 |
|---------|------|------|-----|
| Layer 1 | 性能 (Performance) | 評価対象の性能指標 | 速度、燃費、コスト |
| Layer 2 | 特性 (Property) | 性能に影響する特性 | 重量、空力係数 |
| Layer 3 | 変数 (Variable) | 設計で制御する変数 | エンジン出力、車体形状 |
| Layer 4 | モノ・環境 (Object/Environment) | 物理的要素と外部条件 | エンジン、路面状態 |

エッジの重み（-3 〜 +3）が因果の強さと方向を表します：
- **正の値**: 増加→増加の関係
- **負の値**: 増加→減少の関係（トレードオフ）

### 2.6 構造的エネルギー計算

エネルギーは設計案の**内部整合性**を、ステークホルダーの望ましさ方向を考慮して測定します。

#### 4象限エネルギー式

```
E_ij = (W_i × W_j × |C_ij| - δ_i × δ_j × C_ij) / (2 × (ΣW_k)²)

ここで：
- W_i: 性能iの重み（望大票数 + 望小票数）
- δ_i: 性能iの正味方向票（望大票数 - 望小票数）
- C_ij: 性能i,jの内積（総効果行列T_iとT_jの内積）
- ΣW_k: 全性能の重みの合計
```

#### 特殊ケース

- **全票同方向**（|δ_i| = W_i）：旧式 `W_i × W_j × max(0, -C_ij) / (ΣW_k)²` と完全一致
- **混在票あり**：構造的対立の一部がシナジーとして相殺され、エネルギーが減少

#### 方向合意度

各性能の望ましさ方向の一貫性を `consensus_i = δ_i / W_i` （[-1, +1]の範囲）で表します。

| 値 | 意味 |
|----|------|
| +1.0 | 全票望大 |
| -1.0 | 全票望小 |
| 0.0 | 望大票と望小票が同数 |

#### 旧式エネルギー（Coulomb型）

旧式のエネルギー計算（`energy_calculator.py`）はCoulomb型モデルで、比較用エンドポイントでのみ使用されます。

```
Energy = Σ (q_i × q_j × Match(i,j)) / r_ij
```

### 2.7 トレードオフ比率

性能間の競合関係を定量化します：

```
Tradeoff Ratio = 競合パス数 / 総パス数

競合パス: 2つの性能に対して、一方を改善すると他方が悪化するパス
```

比率が高いほど、設計上のトレードオフが多い状態です。

### 2.8 MDS（多次元尺度法）

設計案のネットワーク構造の類似性に基づき、2D/3D座標を算出します。

**Weisfeiler-Lehman カーネル**を使用：
1. 各ノードにラベルを付与
2. 近傍ノードのラベルを集約して新ラベル生成
3. 反復してグラフの特徴を抽出
4. カーネル行列から距離行列を計算
5. MDSで座標に変換

### 2.9 Shapley値分解

トレードオフの原因となるノード/エッジの**寄与度**をゲーム理論的に分解します。

```
φ_k = Σ_{S⊆N\{k}} [|S|!(n-|S|-1)!/n!] × [v(S∪{k}) - v(S)]

ここで：
- k: 対象のノードまたはエッジ
- N: 全要素の集合
- S: kを含まない連合（部分集合）
- v(S): 連合Sのみを使用した場合の内積 C_ij
```

**特徴：**
- φ_k > 0: 要素kが協調方向に寄与
- φ_k < 0: 要素kが対立方向に寄与
- Σ φ_k = C_ij（総内積と一致 — 加法性）

#### ノードShapley と エッジShapley

2種類のShapley分解を提供します：
- **ノードShapley（V ∪ A）**：変数・属性ノードの寄与度
- **エッジShapley**：エッジの寄与度

#### 構造/エネルギーモード

Shapley値は2つの視点で表示できます：

| モード | 表示値 | 色 | 意味 |
|--------|--------|-----|------|
| 構造寄与 (φ) | φ_e | 青(−)/橙(+) | C_ijへの構造的寄与（中立） |
| エネルギー寄与 (λφ) | λ_ij × φ_e | 赤(+)/ティール(−) | E_ijへの価値的寄与 |

ここで `λ_ij = E_ij / C_ij` はエネルギー強度係数。λは定数スカラーなので、寄与の順位・割合は両モードで同一です。

### 2.10 カップリングとクラスタリング

トレードオフ間の**結合度**を計算し、性能を**階層的にグループ化**します。

#### 正規化カップリング
```
NormCoupling(TO_ij, TO_kl) = Σ|φ_a(C_ij)|·|φ_a(C_kl)| / (||φ_ij|| · ||φ_kl||)

ここで：
- TO_ij: 性能iとjのトレードオフ
- φ_a: 属性aのShapley寄与ベクトル
```

2つのトレードオフが同じ属性によって引き起こされているほど、カップリングが高くなります。

#### 間接結合度
```
Connection(P_i, P_k) = max_{j,l} K_{(ij),(kl)}

性能P_iとP_kが関与するトレードオフ間の最大カップリング
```

#### 階層的クラスタリング
- **距離行列**: D = 1 - Connection
- **連結法**: 平均連結法（Average Linkage）
- **最適クラスタ数**: Silhouette係数で決定
- **可視化**: インタラクティブデンドログラム

---

## 3. システムアーキテクチャ

### 3.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│                    フロントエンド                        │
│   Vue 3 + TypeScript + Three.js + D3.js + Pinia        │
│                   (localhost:5173)                      │
└─────────────────────────────────────────────────────────┘
                          │
                          │ REST API (JSON)
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     バックエンド                         │
│            FastAPI + NumPy + scikit-learn              │
│                   (localhost:8000)                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    データベース                          │
│              SQLite (ローカル) / PostgreSQL             │
└─────────────────────────────────────────────────────────┘
```

### 3.2 技術スタック

#### フロントエンド
| ライブラリ | 用途 |
|-----------|------|
| Vue 3 | UIフレームワーク |
| TypeScript | 型安全性 |
| Three.js | 3D可視化（山、ネットワーク） |
| D3.js | グラフ編集、ネットワーク図 |
| Pinia | 状態管理 |
| Vite | ビルドツール |
| Axios | API通信 |
| html2canvas | 画像エクスポート |
| XLSX | Excelエクスポート |

#### バックエンド
| ライブラリ | 用途 |
|-----------|------|
| FastAPI | Web API フレームワーク |
| SQLAlchemy | ORM |
| Pydantic | データバリデーション |
| NumPy | 数値計算 |
| scikit-learn | MDS計算 |
| grakel | WLカーネル計算 |

### 3.3 ディレクトリ構造

```
deep-traceability-system/
├── frontend/                    # フロントエンド
│   ├── src/
│   │   ├── components/          # UIコンポーネント
│   │   │   ├── stakeholder/     # ステークホルダー管理
│   │   │   ├── performance/     # 性能管理
│   │   │   ├── matrix/          # マトリクス表示
│   │   │   ├── mountain/        # 山の可視化
│   │   │   ├── twoaxis/         # 2軸評価
│   │   │   ├── network/         # ネットワーク編集
│   │   │   ├── analysis/        # トレードオフ分析
│   │   │   ├── opm3d/           # 3Dネットワーク
│   │   │   └── common/          # 共通コンポーネント
│   │   ├── views/               # ページコンポーネント
│   │   ├── stores/              # 状態管理
│   │   ├── types/               # TypeScript型定義
│   │   └── utils/               # ユーティリティ
│   └── public/                  # 静的ファイル
│
├── backend/                     # バックエンド
│   ├── app/
│   │   ├── api/                 # APIエンドポイント
│   │   │   ├── projects.py      # プロジェクト管理API
│   │   │   ├── calculations.py  # 計算API
│   │   │   └── mds.py           # MDS/WLカーネルAPI
│   │   ├── models/              # データベースモデル
│   │   │   └── database.py      # SQLAlchemyモデル
│   │   ├── schemas/             # Pydanticスキーマ
│   │   │   └── project.py       # データ検証スキーマ
│   │   ├── services/            # ビジネスロジック
│   │   │   ├── mountain_calculator.py   # 山座標計算
│   │   │   ├── energy_calculator.py     # エネルギー計算（旧Coulomb型）
│   │   │   ├── structural_energy.py     # 構造的エネルギー計算（4象限分解）
│   │   │   ├── structural_tradeoff.py   # 構造的トレードオフ分析
│   │   │   ├── matrix_utils.py          # 隣接行列・総効果行列ユーティリティ
│   │   │   ├── shapley_calculator.py    # Shapley値分解
│   │   │   ├── coupling_calculator.py   # カップリング/クラスタリング
│   │   │   ├── tradeoff_calculator.py   # トレードオフ比率計算
│   │   │   ├── weight_normalization.py  # 重み正規化
│   │   │   └── scc_analyzer.py          # 強連結成分分析
│   │   └── main.py              # アプリケーションエントリ
│   └── requirements.txt         # Python依存関係
│
└── docs/                        # ドキュメント
```

---

## 4. データモデル

### 4.1 エンティティ関係図

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Project    │────<│ Stakeholder  │     │    Need      │
│              │     │              │     │              │
│ - id         │     │ - id         │     │ - id         │
│ - name       │     │ - name       │     │ - name       │
│ - description│     │ - category   │     │ - category   │
└──────────────┘     │ - votes      │     │ - priority   │
       │             └──────────────┘     └──────────────┘
       │                    │                    │
       │                    └────────┬───────────┘
       │                             │
       │                    ┌────────▼────────┐
       │                    │ StakeholderNeed │
       │                    │    Relation     │
       │                    │ - weight (1.0/0.5)
       │                    └─────────────────┘
       │
       ├────────────────────────────────────────┐
       │                                        │
┌──────▼──────┐     ┌──────────────┐     ┌─────▼──────┐
│ Performance │────<│ NeedPerf     │>────│ DesignCase │
│             │     │  Relation    │     │            │
│ - id        │     │              │     │ - id       │
│ - name      │     │ - direction  │     │ - name     │
│ - parent_id │     │ - utility_fn │     │ - color    │
│ - level     │     └──────────────┘     │ - network  │
│ - is_leaf   │                          │ - perf_vals│
│ - unit      │                          └────────────┘
└─────────────┘
```

### 4.2 主要エンティティ

#### Project（プロジェクト）
```typescript
{
  id: string;              // UUID
  name: string;            // プロジェクト名
  description?: string;    // 説明
  created_at: datetime;    // 作成日時
  updated_at: datetime;    // 更新日時
  two_axis_plots: TwoAxisPlot[];  // 2軸プロット設定
}
```

#### Stakeholder（ステークホルダー）
```typescript
{
  id: string;
  name: string;            // 名前
  category?: string;       // カテゴリ
  votes: number;           // 投票数（デフォルト100）
  description?: string;
}
```

#### Need（ニーズ）
```typescript
{
  id: string;
  name: string;
  category?: string;
  description?: string;
  priority: number;        // 優先度 (0.0〜1.0)
}
```

#### Performance（性能）
```typescript
{
  id: string;
  name: string;
  parent_id?: string;      // 親性能のID（階層構造）
  level: number;           // 階層の深さ（0=ルート）
  is_leaf: boolean;        // 末端ノードか
  unit?: string;           // 単位（km/h, kg, 等）
  description?: string;
  utility_function?: UtilityFunction;
}
```

#### DesignCase（設計案）
```typescript
{
  id: string;
  name: string;
  description?: string;
  color: string;           // 表示色（HEX）
  performance_values: {    // 性能値
    [performanceId: string]: number | string;
  };
  network: NetworkStructure;  // ネットワーク構造
  performance_snapshot: Performance[];  // 作成時の性能ツリー
  mountain_position?: MountainPosition;  // 山座標
  utility_vector?: { [perfId: string]: number };  // 効用ベクトル
  partial_heights?: { [perfId: string]: number }; // 部分標高
  energy?: {
    total_energy: number;
    partial_energies: { [perfId: string]: number };
  };
}
```

#### NetworkStructure（ネットワーク構造）
```typescript
{
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

// ノード
{
  id: string;
  layer: 1 | 2 | 3 | 4;    // レイヤー番号
  type: 'performance' | 'property' | 'variable' | 'object' | 'environment';
  label: string;
  x: number;               // 2D座標
  y: number;
  x3d?: number;            // 3D座標
  y3d?: number;
  performance_id?: string; // Layer1のみ
}

// エッジ
{
  id: string;
  source_id: string;
  target_id: string;
  type: 'type1' | 'type2' | 'type3' | 'type4';
  weight?: -3 | -1 | -0.33 | 0 | 0.33 | 1 | 3;
}
```

---

## 5. バックエンド詳細

### 5.1 API エンドポイント一覧

#### プロジェクト管理 (`/api/projects`)

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | プロジェクト一覧取得 |
| POST | `/` | 新規プロジェクト作成 |
| GET | `/{id}` | プロジェクト詳細取得 |
| PUT | `/{id}` | プロジェクト更新 |
| DELETE | `/{id}` | プロジェクト削除 |
| GET | `/{id}/export` | JSONエクスポート |
| POST | `/import` | JSONインポート |

#### ステークホルダー管理

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/{id}/stakeholders` | 一覧取得 |
| POST | `/{id}/stakeholders` | 追加 |
| PUT | `/{id}/stakeholders/{sh_id}` | 更新 |
| DELETE | `/{id}/stakeholders/{sh_id}` | 削除 |

#### ニーズ管理

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/{id}/needs` | 一覧取得 |
| POST | `/{id}/needs` | 追加 |
| PUT | `/{id}/needs/{need_id}` | 更新 |
| DELETE | `/{id}/needs/{need_id}` | 削除 |

#### 性能管理

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/{id}/performances` | 一覧取得 |
| POST | `/{id}/performances` | 追加 |
| PUT | `/{id}/performances/{perf_id}` | 更新 |
| DELETE | `/{id}/performances/{perf_id}` | 削除（子も削除） |

#### 設計案管理

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/{id}/design-cases` | 一覧取得 |
| POST | `/{id}/design-cases` | 作成 |
| PUT | `/{id}/design-cases/{case_id}` | 更新 |
| DELETE | `/{id}/design-cases/{case_id}` | 削除 |
| POST | `/{id}/design-cases/{case_id}/copy` | 複製 |

#### 計算 (`/api/calculations`)

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/mountain/{id}` | 山座標計算 |
| POST | `/energy/{id}` | 全設計案のエネルギー計算 |
| GET | `/energy/{id}/{case_id}` | 単一設計案のエネルギー |
| POST | `/tradeoff/{id}` | トレードオフ比率計算 |
| GET | `/structural-tradeoff/{id}/{case_id}` | 構造的トレードオフ分析（cosθ, E_ij, consensus） |
| GET | `/structural-energy/{id}/{case_id}` | 構造的エネルギー計算（4象限分解） |
| GET | `/shapley/{id}/{case_id}/{pi}/{pj}` | ノードShapley値分解（V ∪ A） |
| GET | `/edge-shapley/{id}/{case_id}/{pi}/{pj}` | エッジShapley値分解 |
| GET | `/coupling/{id}/{case_id}` | カップリング/クラスタリング |

#### MDS/カーネル (`/api/mds`)

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/compute_network_comparison` | WLカーネル計算 |

### 5.2 サービス層の詳細

#### mountain_calculator.py

**主要関数：**

```python
def calculate_mountain_positions(project, db, networks=None):
    """
    全設計案の山座標を計算

    処理フロー:
    1. distribute_votes_to_needs() - ステークホルダー票をニーズに分配
    2. distribute_votes_to_performances() - ニーズ票を性能に分配
    3. calculate_utility_vector() - 性能値から効用値を算出
    4. calculate_elevation() - 効用値を票数で重み付けして標高算出
    5. MDS座標計算 - ネットワーク構造から2D位置を決定
    6. エネルギー計算 - 内部整合性を評価

    戻り値:
    {
        'positions': [
            {
                'x': float, 'y': float, 'z': float,
                'H': float,  # 標高
                'utility_vector': {...},
                'partial_heights': {...},
                'performance_weights': {...},
                'energy': {'total_energy': float, 'partial_energies': {...}}
            },
            ...
        ],
        'H_max': float  # 最大可能標高
    }
    """
```

**票数分配のアルゴリズム：**

```python
def distribute_votes_to_needs(stakeholders, needs, relations):
    """
    ステークホルダーの票をニーズに分配

    計算式:
    need_votes[n] = Σ (stakeholder_votes[s] × relation_weight[s,n])
                    / (関連するステークホルダー数)
    """

def distribute_votes_to_performances(needs, performances, relations):
    """
    ニーズの票を性能に分配

    方向性を考慮:
    - direction='up': 増加が良い → 正の票
    - direction='down': 減少が良い → 負の票

    シャノンエントロピーで一貫性を評価し、票数を調整
    """
```

#### energy_calculator.py（旧式Coulomb型）

**旧式エネルギー計算（比較用）：**

```python
def calculate_energy_for_case(case, performances, db):
    """
    Coulomb型モデルによるエネルギー計算（比較用エンドポイントでのみ使用）

    アルゴリズム:
    1. Layer1（性能）とLayer2（特性）のノードを抽出
    2. 性能ペアごとに共通の特性を特定
    3. 共通特性を経由するパスの重みを計算
    4. Match値を算出: Match = -tanh(ln(3/2) × Σ sgn(W) × √|W|)
    5. エネルギー = Σ (q_i × q_j × Match) / distance
    """
```

#### structural_energy.py（主要エネルギー計算）

**4象限エネルギー分解：**

```python
def compute_structural_energy(network, performance_weights, performance_deltas, weight_mode):
    """
    構造的エネルギーを4象限分解で計算

    エネルギー式:
    E_ij = (W_i * W_j * |C_ij| - δ_i * δ_j * C_ij) / (2 * (ΣW_k)²)

    各ペアの追加情報:
    - consensus_i/j: 方向合意度 (δ/W)
    - lambda_ij: エネルギー強度係数 (E_ij / C_ij)
    - offset_rate: 相殺率 (1 - E_ij / E_max)

    戻り値:
    {
        'total_energy': float,
        'energy_contributions': [{perf_i_id, perf_j_id, contribution, lambda_ij, ...}],
        'normalization_factor': float
    }
    """
```

#### structural_tradeoff.py

**構造的トレードオフ分析：**

```python
class StructuralTradeoffCalculator:
    """
    総効果行列による統合的なトレードオフ分析

    分析結果:
    - total_effect_matrix: 総効果行列 T
    - cos_theta_matrix: cosθ行列（構造的対立/協調）
    - inner_product_matrix: 内積行列 C_ij = T_i · T_j
    - energy_matrix: エネルギー行列 E_ij（4象限分解）
    - performance_consensus: 方向合意度マップ {perf_id: δ/W}
    - tradeoff_pairs / synergy_pairs: ペア情報
    """
```

#### tradeoff_calculator.py

**トレードオフ分析：**

```python
class TradeoffCalculator:
    def calculate_single_case_tradeoff_ratio(self, network, performances):
        """
        単一設計案のトレードオフ比率を計算

        パスの探索:
        1. 性能ペアを列挙
        2. 4種類の接続パターンをチェック:
           - perf→prop→perf (特性経由)
           - prop→perf (特性から性能)
           - perf→prop (性能から特性)
           - 直接接続
        3. パスの重みの符号をチェック
        4. 反対符号のパス = トレードオフ

        戻り値:
        {
            'ratio': float (0.0〜1.0),
            'total_paths': int,
            'tradeoff_paths': int,
            'is_valid': bool
        }
        """
```

#### shapley_calculator.py

**Shapley値分解：**

```python
def calculate_shapley_decomposition(network, perf_i_idx, perf_j_idx, perf_labels):
    """
    トレードオフC_ijへの各属性の寄与度をShapley値で計算

    アルゴリズム:
    1. 性能i,jに接続する属性ノードを抽出
    2. 全連合（部分集合）を列挙（2^n パターン）
    3. 各連合でのC_ij値を計算（部分ネットワーク）
    4. Shapley公式で各属性の寄与度を算出

    戻り値:
    {
        'shapley_values': [{node_id, label, value, percentage}, ...],
        'total_C_ij': float,
        'coalition_details': {...}
    }
    """
```

#### coupling_calculator.py

**カップリングとクラスタリング：**

```python
def compute_coupling_for_case(network, matrices, cos_theta_matrix, ...):
    """
    設計案のカップリングとクラスタリングを計算

    処理フロー:
    1. トレードオフペア（cos θ < 0）を抽出
    2. 各トレードオフのShapley寄与ベクトルを計算
    3. 正規化カップリング行列を構築
    4. 性能間の間接結合度行列を計算
    5. 階層的クラスタリング（平均連結法）
    6. Silhouette係数で最適クラスタ数を決定
    7. デンドログラムデータを生成

    戻り値:
    CouplingResult {
        coupling_matrix: np.ndarray,       # トレードオフ間カップリング
        performance_connection_matrix: np.ndarray,  # 性能間結合度
        clusters: List[int],               # クラスタ割当
        optimal_n_clusters: int,
        silhouette_score: float,
        dendrogram_data: Dict              # 可視化用データ
    }
    """
```

---

## 6. フロントエンド詳細

### 6.1 ページ構成

#### ホーム画面 (Home.vue)
- ヒーローセクションとアニメーション
- 機能紹介グリッド
- ワークフロー説明

#### プロジェクト一覧 (ProjectList.vue)
- プロジェクトカード表示
- 新規作成・インポート・エクスポート・削除

#### プロジェクト詳細 (ProjectDetail.vue)
- タブ切り替えで各機能にアクセス
- Stakeholders / Performance / Matrix / Mountain View / 2-axis / 3D OPM / Network

### 6.2 主要コンポーネント

#### StakeholderMatrix.vue
**機能：**
- ステークホルダーとニーズの関係マトリクス表示
- セルクリックで関係の重み（○/△/なし）を切り替え
- 投票数の編集
- Excel/画像エクスポート

**表示例：**
```
              │ SH1(100票) │ SH2(80票) │ ...
─────────────┼───────────┼──────────┼────
ニーズA(カテゴリ) │     ○     │     △    │ ...
ニーズB(カテゴリ) │     △     │     ○    │ ...
```

#### NeedPerformanceMatrix.vue
**機能：**
- ニーズと性能の関係マトリクス
- 方向（↑/↓）の設定
- 効用関数の割り当て
- 階層的な性能表示

**表示例：**
```
       │ 総票数 │ 優先度 │ 性能1 │ 性能1-1 │ 性能1-2 │ ...
───────┼───────┼───────┼──────┼────────┼────────┼────
ニーズA │  180   │  0.36  │   -   │   ↑    │   ↓    │ ...
ニーズB │  150   │  0.30  │   -   │   ↑    │   -    │ ...
```

#### MountainView.vue
**機能：**
- Three.jsによる3D半球表示
- 設計案を球体としてプロット
- 標高による位置決め
- エネルギーによる球体サイズ

**左パネル：** 設計案リスト（ソート可能）
**中央：** 3D山の可視化
**右パネル：** 選択した設計案の詳細

**球体サイズの計算：**
```typescript
// エネルギー差分が20%未満なら強調変換
const variationRatio = energyRange / maxEnergy;
const enhancementPower = variationRatio < 0.2 ? 0.5 : 1.0;

const normalizedEnergy = Math.pow(
  (energy - minEnergy) / energyRange,
  enhancementPower
);
const sphereRadius = 0.35 + normalizedEnergy * 0.4;
```

#### TwoAxisEvaluation.vue
**機能：**
- 任意の2軸を選択して散布図表示
- 軸の選択肢：
  - 任意の性能指標
  - `__height` - 標高
  - `__energy` - エネルギー
  - `__tradeoff` - トレードオフ比率
- 設計案を点でプロット
- ホバーで詳細表示

#### NetworkEditor.vue
**機能：**
- 4層ネットワークの編集
- ノードの追加・移動・削除
- エッジの接続・重み設定
- Layer1（性能）は自動生成

**レイヤー色：**
- Layer 1（性能）: 黄色
- Layer 2（特性）: シアン
- Layer 3（変数）: マゼンタ
- Layer 4（モノ・環境）: オレンジ

**エッジ重み選択肢：**
```
+3 (強い正), +1 (正), +0.33 (弱い正),
0 (なし),
-0.33 (弱い負), -1 (負), -3 (強い負)
```

#### TradeoffAnalysisModal.vue
**機能：**
- 構造的トレードオフ分析のモーダルダイアログ
- cos θ / Energy マトリクス切替ヒートマップ
- 4タブ構成の詳細パネル

**タブ構成：**
1. **Contribution** - Shapley値分解（構造/エネルギーモード切替）
2. **Network** - ネットワーク上でのShapley寄与ハイライト（構造/エネルギーモード切替）
3. **Coupling** - カップリング/クラスタリング分析
4. **Confidence** - 離散化信頼度

**サブコンポーネント：**
- `MatrixHeatmap.vue` - 行列ヒートマップ（青/橙cosθ、白/赤Energy、方向インジケータ行）
- `ShapleyBreakdown.vue` - Shapley値の棒グラフ（構造φ: 青/橙、エネルギーλφ: 赤/ティール）
- `TradeoffNetworkViewer.vue` - ネットワーク寄与ハイライト（構造/エネルギーモード切替、凡例付き）
- `CouplingClusteringPanel.vue` - カップリング/クラスタリング
- `DiscretizationConfidence.vue` - 離散化信頼度
- `SCCWarningBanner.vue` - SCC警告表示

**色設計原則：**
- 構造的量（cosθ, φ_e）→ 青(対立)/橙(協調) — 中立色
- 価値的量（E_ij, λφ_e）→ 赤(悪化)/ティール(緩和) — 価値判断色

#### CouplingClusteringPanel.vue
**機能：**
- トレードオフ間のカップリング行列表示
- 性能間の間接結合度行列表示
- クラスタ一覧（色分け表示）
- インタラクティブデンドログラム

**タブ構成：**
1. **Dendrogram** - 階層的クラスタリングの木構造
2. **Clusters** - 最適クラスタ数での分類結果
3. **Coupling Matrix** - トレードオフ間カップリング
4. **Connection Matrix** - 性能間結合度

#### InteractiveDendrogram.vue
**機能：**
- SVGベースのデンドログラム描画
- カット高さの動的調整（スライダー）
- Silhouette係数の曲線表示
- 最適高さの自動提案

### 6.3 状態管理 (projectStore.ts)

**State:**
```typescript
{
  currentProject: Project | null;  // 現在のプロジェクト
  projects: Project[];             // プロジェクト一覧
  loading: boolean;
  error: string | null;
}
```

**Computed:**
```typescript
stakeholders      // currentProjectのステークホルダー
needs             // currentProjectのニーズ
performances      // currentProjectの性能
designCases       // currentProjectの設計案
leafPerformances  // is_leaf=trueの性能のみ
performanceTree   // 階層構造に変換した性能ツリー
```

**Actions:**
- CRUD操作（ステークホルダー、ニーズ、性能、設計案）
- 関係の管理（StakeholderNeed, NeedPerformance）
- 計算トリガー（Mountain, Energy, HHI）
- 効用関数の保存・読み込み

---

## 7. 計算アルゴリズム

### 7.1 標高計算の詳細

```
入力:
- stakeholders: [{id, votes}, ...]
- needs: [{id, priority}, ...]
- performances: [{id, is_leaf}, ...]
- stakeholder_need_relations: [{sh_id, need_id, weight}, ...]
- need_performance_relations: [{need_id, perf_id, direction}, ...]
- utility_functions: {...}
- design_case: {performance_values: {...}}

処理:

1. ステークホルダー → ニーズ票配分
   for each need:
     votes = Σ (sh.votes × relation.weight) for related stakeholders

2. ニーズ → 性能票配分
   for each performance:
     up_votes = Σ need_votes for relations where direction='up'
     down_votes = Σ need_votes for relations where direction='down'

     # シャノンエントロピーによる調整
     total = up_votes + down_votes
     p_up = up_votes / total
     entropy = -Σ p × log(p)

     effective_votes = total × (1 - entropy/log(2))

3. 効用値の計算
   for each performance:
     value = design_case.performance_values[perf_id]
     utility = interpolate(utility_function, value)  # 0〜1

4. 標高の計算
   H = Σ (effective_votes × utility) / Σ effective_votes
```

### 7.2 エネルギー計算の詳細

```
入力:
- network: {nodes, edges}
- performances: [...]

処理:

1. Layer1（性能）とLayer2（特性）ノードを抽出

2. 性能ペアごとに共通特性を探索
   for i, j in performance_pairs:
     common_props = find_nodes_connected_to_both(perf_i, perf_j)

3. Match値の計算
   for each common_prop:
     weight_to_i = edge_weight(prop → perf_i)
     weight_to_j = edge_weight(prop → perf_j)
     product = weight_to_i × weight_to_j

     contribution = sign(product) × sqrt(|product|)

   match = -tanh(ln(3/2) × Σ contributions)

4. エネルギーの計算
   q = performance_weights (投票数)

   partial_energy[i] = Σ (q[i] × q[j] × match[i,j]) / distance[i,j]
   total_energy = Σ partial_energy
```

### 7.3 WLカーネル計算

```
入力:
- networks: [NetworkStructure, ...]
- iterations: int (1〜4)

処理:

1. グラフ変換
   for each network:
     G = networkx.Graph()
     for node in network.nodes:
       G.add_node(node.id, label=f"{node.layer}_{node.type}")
     for edge in network.edges:
       G.add_edge(edge.source_id, edge.target_id)

2. WLカーネル計算 (grakelライブラリ)
   kernel = WeisfeilerLehman(n_iter=iterations)
   K = kernel.fit_transform(graphs)  # カーネル行列

3. 距離行列への変換
   D[i,j] = sqrt(K[i,i] + K[j,j] - 2×K[i,j])

4. MDS座標計算
   coords = MDS(dissimilarity='precomputed').fit_transform(D)

戻り値:
{
  'kernel_matrix': K,
  'distance_matrix': D,
  'coordinates': coords,
  'stress': float
}
```

---

## 8. ユーザーワークフロー

### 8.1 基本的な使用フロー

```
1. プロジェクト作成
   └─ 名前と説明を入力

2. ステークホルダー定義
   ├─ ステークホルダーを追加（名前、投票数）
   ├─ ニーズを追加（名前、カテゴリ）
   └─ マトリクスで関係を設定（○/△）

3. 性能構造の構築
   ├─ ルート性能を追加
   ├─ 子性能を追加（階層化）
   └─ 単位を設定

4. ニーズ-性能マトリクス
   ├─ 関係と方向（↑/↓）を設定
   └─ 効用関数を定義

5. 設計案の作成
   ├─ 性能値を入力
   ├─ ネットワーク構造を描画
   │   ├─ Layer2（特性）ノード追加
   │   ├─ Layer3（変数）ノード追加
   │   ├─ Layer4（モノ）ノード追加
   │   └─ エッジ接続と重み設定
   └─ 保存

6. 分析・評価
   ├─ Mountain View: 3D可視化で総合評価
   ├─ 2軸評価: トレードオフ分析
   └─ ネットワーク比較: 構造的類似性
```

### 8.2 効用関数の設計

**連続型の場合：**
1. マトリクスで性能セルをクリック
2. 「連続」タブを選択
3. 軸の範囲を設定（min, max）
4. 制御点をドラッグして曲線を描画
5. 保存

**離散型の場合：**
1. マトリクスで性能セルをクリック
2. 「離散」タブを選択
3. 選択肢を追加（ラベルと効用値）
4. 保存

### 8.3 設計案の比較

**Mountain Viewでの比較：**
- 高さ = 総合的な良さ
- 水平位置 = ネットワーク構造の類似性
- 球体サイズ = エネルギー（内部整合性）

**2軸評価での比較：**
- 任意の性能ペアで散布図
- パレートフロンティアの確認
- トレードオフの可視化

---

## 9. API リファレンス

### 9.1 計算エンドポイント

#### POST /api/calculations/mountain/{project_id}

**リクエスト:**
```json
{
  "networks": [
    {
      "case_id": "uuid",
      "network": {"nodes": [...], "edges": [...]}
    }
  ]
}
```

**レスポンス:**
```json
{
  "positions": [
    {
      "x": 0.5,
      "y": 0.3,
      "z": 0.8,
      "H": 0.75,
      "utility_vector": {"perf1": 0.8, "perf2": 0.6},
      "partial_heights": {"perf1": 0.4, "perf2": 0.35},
      "performance_weights": {"perf1": 150, "perf2": 120},
      "energy": {
        "total_energy": 12500.5,
        "partial_energies": {"perf1": 6000, "perf2": 6500.5}
      }
    }
  ],
  "H_max": 1.0
}
```

#### POST /api/calculations/energy/{project_id}

**レスポンス:**
```json
{
  "case_id_1": {
    "total_energy": 12500.5,
    "partial_energies": {"perf1": 6000, "perf2": 6500.5},
    "match_matrix": [[1.0, 0.3], [0.3, 1.0]]
  },
  "case_id_2": {...}
}
```

#### POST /api/mds/compute_network_comparison

**リクエスト:**
```json
{
  "networks": [
    {"nodes": [...], "edges": [...]},
    {"nodes": [...], "edges": [...]}
  ],
  "iterations": 3
}
```

**レスポンス:**
```json
{
  "kernel_matrix": [[1.0, 0.8], [0.8, 1.0]],
  "distance_matrix": [[0, 0.45], [0.45, 0]],
  "coordinates": [[0.2, 0.3], [-0.2, -0.3]],
  "stress": 0.05
}
```

---

## 10. セットアップガイド

### 10.1 必要環境

- **Node.js**: 18以上
- **Python**: 3.10以上
- **Docker Desktop**: 推奨（または SQLite）

### 10.2 Docker でのセットアップ

```bash
# リポジトリクローン
git clone https://github.com/your-repo/deep-traceability-system.git
cd deep-traceability-system

# Docker起動
docker-compose -f docker-compose.local.yml up

# アクセス
# フロントエンド: http://localhost:5173
# バックエンド: http://localhost:8000
```

### 10.3 手動セットアップ

**バックエンド:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**フロントエンド:**
```bash
cd frontend
npm install
npm run dev
```

### 10.4 トラブルシューティング

**ポート競合:**
```bash
lsof -i :5173  # フロントエンド
lsof -i :8000  # バックエンド
```

**データベース初期化:**
```bash
cd backend
python -c "from app.models.database import init_db; init_db()"
```

**キャッシュクリア:**
```bash
# フロントエンド
rm -rf frontend/node_modules/.vite
npm run dev

# バックエンド
find . -name "__pycache__" -exec rm -rf {} +
```

---

## 付録

### A. 用語集

| 用語 | 説明 |
|-----|------|
| ステークホルダー | システムに関わる利害関係者 |
| ニーズ | ステークホルダーの要求・期待 |
| 性能 | 測定可能な評価指標 |
| 効用関数 | 性能値を満足度に変換する関数 |
| 設計案 | 評価対象の設計オプション |
| 標高 (H) | 設計案の総合評価スコア |
| エネルギー | 設計案の内部整合性指標 |
| トレードオフ | 性能間の競合関係 |

### B. 参考文献

- Multi-Attribute Utility Theory (MAUT)
- Quality Function Deployment (QFD)
- Weisfeiler-Lehman Graph Kernel
- Multi-Dimensional Scaling (MDS)

---

*このドキュメントは Deep Traceability System の技術仕様を記載したものです。*
*最終更新: 2026年2月10日*
