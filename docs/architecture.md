# Deep Traceability System - アーキテクチャ

## システム構成

### 全体構造

```
┌─────────────────────────────────────────┐
│         Frontend (Vue 3 + TS)            │
│  ┌────────────────────────────────────┐ │
│  │  Components                         │ │
│  │  - StakeholderMatrix               │ │
│  │  - PerformanceTree                 │ │
│  │  - UtilityFunctionEditor           │ │
│  │  - NetworkEditor                   │ │
│  │  - Mountain3D (Three.js)           │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  Stores (Pinia)                    │ │
│  │  - projectStore                    │ │
│  └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │ HTTP REST API
                  ▼
┌─────────────────────────────────────────┐
│      Backend (FastAPI + Python)         │
│  ┌────────────────────────────────────┐ │
│  │  API Endpoints                     │ │
│  │  - /projects                       │ │
│  │  - /calculations                   │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  Services                          │ │
│  │  - hhi_calculator                  │ │
│  │  - mountain_calculator             │ │
│  │  - vote_distributor                │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  Database (SQLAlchemy)             │ │
│  │  - SQLite (local) / PostgreSQL(web)│ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## データフロー

### 1. ステークホルダー分析フロー

```
[ユーザー入力]
    │
    ├─ ステークホルダー登録（votes=100）
    ├─ ニーズ登録
    └─ ステークホルダー×ニーズ関係
    │
    ▼
[票数計算]
    │
    ├─ 各ステークホルダーの票を関連ニーズに按分
    └─ 各ニーズの票数を集計
    │
    ▼
[性能との紐付け]
    │
    ├─ ニーズ×性能関係（↑↓方向付き）
    └─ 票を性能に按分
    │
    ▼
[有効投票数計算]
    │
    └─ I(a,b) = (a+b) * [1 + H(x)]  # Shannon entropy
    │
    ▼
[HHI計算]
    │
    └─ HHI = Σ(w_i / W_total)²
    │
    ▼
[p²値表示] → ユーザーが詳細化判断
```

### 2. 山の可視化フロー

```
[設計案入力]
    │
    ├─ 各性能の値
    └─ ネットワーク構造
    │
    ▼
[効用値計算]
    │
    └─ 効用関数に基づき u_i = f(性能値)
    │
    ▼
[標高計算]
    │
    └─ H = Σ W_i * u_i
    │
    ▼
[MDS計算]
    │
    ├─ 効用ベクトル間の距離行列作成
    ├─ 2次元座標に削減
    └─ 角度情報に変換
    │
    ▼
[円錐マッピング]
    │
    ├─ r = R_base * (1 - H/H_max)
    ├─ x = r * cos(θ)
    ├─ z = r * sin(θ)
    └─ y = H
    │
    ▼
[Three.js レンダリング] → ユーザーが回転・クリック
```

## データベーススキーマ

### テーブル構成

```sql
projects
├── id (PK)
├── name
├── description
├── created_at
└── updated_at

stakeholders
├── id (PK)
├── project_id (FK)
├── name
├── category
├── votes
└── description

needs
├── id (PK)
├── project_id (FK)
├── name
├── category
└── description

stakeholder_need_relations
├── id (PK)
├── project_id (FK)
├── stakeholder_id
└── need_id

performances
├── id (PK)
├── project_id (FK)
├── name
├── parent_id (階層構造)
├── level
├── is_leaf
├── unit
├── description
└── utility_function_json (JSON)

need_performance_relations
├── id (PK)
├── project_id (FK)
├── need_id
├── performance_id
└── direction ('up' | 'down')

design_cases
├── id (PK)
├── project_id (FK)
├── name
├── description
├── performance_values_json (JSON)
├── network_json (JSON)
├── mountain_position_json (JSON)
├── utility_vector_json (JSON)
├── created_at
└── updated_at
```

## 主要アルゴリズム

### HHI計算

```python
# 1. 票の按分
votes_per_need = stakeholder.votes / len(related_needs)

# 2. 有効投票数
x = up_votes / (up_votes + down_votes)
H(x) = -x*log2(x) - (1-x)*log2(1-x)
I = (up_votes + down_votes) * (1 + H(x))

# 3. HHI
HHI = Σ(w_i / W_total)²

# 4. p²値
p² = (max_weight / total_weight)²
```

### MDS + 円錐マッピング

```python
# 1. 距離行列
D = pdist(U_matrix, metric='euclidean')

# 2. MDS
coords_2d = MDS(n_components=2).fit_transform(D)

# 3. 極座標変換
θ = arctan2(y, x)

# 4. 回転（最高標高を正面に）
θ_rotated = θ - θ[max_H_index]

# 5. 円錐座標
r = R_base * (1 - H / H_max)
x = r * cos(θ)
y = H
z = r * sin(θ)
```

## 開発フェーズ

### Phase 1: 基礎構築 ✅ (完了)
- プロジェクト構造
- データモデル（TypeScript + Pydantic）
- データベース（SQLAlchemy）
- 基本CRUD API
- 環境設定

### Phase 2: マトリクス機能（次）
- ステークホルダー×ニーズマトリクス UI
- ニーズ×性能マトリクス UI
- HHI計算の実装
- 性能ツリー表示

### Phase 3: 効用関数
- D3.jsグラフエディタ
- 効用値計算エンジン

### Phase 4: 設計案管理
- ネットワークエディタ（4層構造）
- 性能値入力
- コピー機能

### Phase 5: 山の可視化
- Three.js円錐レンダリング
- MDS + 標高計算
- クリック検出
- サイドバー詳細表示

### Phase 6: 統合・最適化
- ローカル⇔Web同期
- パフォーマンス最適化
- エラーハンドリング

## 次のステップ

Phase 2の実装に進みます：
1. StakeholderMatrix.vue コンポーネント
2. NeedPerformanceMatrix.vue コンポーネント
3. PerformanceTree.vue コンポーネント
4. HHI計算結果の表示
