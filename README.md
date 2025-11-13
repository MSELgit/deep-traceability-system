# Deep Traceability System

多種多様なステークホルダーが関わる複雑システムの意思決定支援ツール

## 概要

本システムは、Deep Traceability手法を用いて、複雑なシステム設計における意思決定の一貫性とトレーサビリティを高めるツールです。ステークホルダーのニーズから性能要求を導出し、設計案を多角的に評価することで、より良い意思決定を支援します。

## 主要機能

### 1. **ステークホルダー・ニーズ管理**
   - ステークホルダーの登録と管理
   - ニーズの定義と関連付け
   - 投票数による重要度の定量化
   - ニーズ駆動型分解度評価（HHI指標）による優先順位付け

### 2. **性能要求管理**
   - 階層的な性能構造の定義（親子関係）
   - 性能とニーズの関連付け（上昇/下降指向）
   - 効用関数の設計（連続値・離散値・ステップ関数対応）
   - グラフィカルな効用関数エディタ

### 3. **設計案作成・評価**
   - 性能値の入力と管理
   - 4層ネットワーク構造の構築
     - Layer 1: 性能
     - Layer 2: 特性
     - Layer 3: 変数 
     - Layer 4: モノ・環境
   - ノード・エッジの追加/編集/削除
   - 設計案のコピー・流用機能
   - カラーカスタマイズ

### 4. **3Dネットワーク可視化**
   - 設計案の4層構造を3D空間で表示
   - インタラクティブな操作（回転・ズーム・パン）
   - ノード選択によるプロパティ表示・編集
   - エッジの重み設定（-3〜3の7段階）
   - レイヤー別の表示/非表示切り替え
   - 3D座標の保存と復元

### 5. **山の可視化（エネルギー評価）**
   - 設計案を半球状の山に配置
   - 高さ（H値）による総合評価の可視化
   - エネルギーに基づく球体サイズの動的表示
   - MDS（多次元尺度法）による類似案の配置
   - 座標の自動計算と手動調整
   - 設計案間の相対的な位置関係の把握

### 6. **2軸評価（Trade-off分析）**
   - 任意の2性能を選択して散布図表示
   - 設計案の分布とトレードオフの可視化
   - 特殊軸（総合満足度・コスト等）のサポート
   - 複数の評価視点の保存と切り替え
   - エクスポート機能（画像・データ）

### 7. **データ管理**
   - プロジェクト単位でのデータ管理
   - インポート/エクスポート機能
   - ローカル/Webモードの切り替え
   - リアルタイムデータ同期

## 技術スタック

### フロントエンド
- Vue 3 + TypeScript
- Three.js（3D可視化）
- D3.js（グラフ編集、ネットワーク図）
- Pinia（状態管理）
- Vite（ビルドツール）

### バックエンド
- FastAPI（Python）
- NumPy, scikit-learn（計算エンジン）
- SQLite（ローカル版）/ PostgreSQL（Web版）

## 必要な環境

- Node.js 18以上
- Python 3.10以上
- Docker Desktop（推奨）またはSQLite

## セットアップ

### 方法1: Dockerを使う

```bash
git clone https://github.com/MSELgit/deep-traceability-system.git
cd deep-traceability-system
docker-compose -f docker-compose.local.yml up
```

自動的に以下が起動します:
- フロントエンド: http://localhost:5173
- バックエンド: http://localhost:8000
- SQLiteデータベース（自動生成）

### 方法2: 手動セットアップ

フロントエンドとバックエンドを別々に起動します。

#### フロントエンド
```bash
cd frontend
npm install
npm run dev
```

#### バックエンド
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 実行モード

### ローカルモード（デフォルト）
```bash
# 方法1（Docker）の場合
docker-compose -f docker-compose.local.yml up

# 方法2（手動）の場合
npm run dev
```

データは端末内のSQLiteに保存されます。

### Webモード
```bash
# 方法1（Docker）の場合
docker-compose -f docker-compose.web.yml up

# 方法2（手動）の場合
npm run dev:web
```

PostgreSQLを使用し、複数デバイスから共同編集が可能です。

## プロジェクト構造

```
deep-traceability-system/
├── frontend/          # Vue3フロントエンド
│   ├── src/
│   │   ├── components/   # UIコンポーネント
│   │   │   ├── stakeholders/  # ステークホルダー管理
│   │   │   ├── performance/   # 性能・効用関数管理
│   │   │   ├── designcase/    # 設計案管理
│   │   │   ├── opm3d/         # 3Dネットワーク可視化
│   │   │   ├── mountain/      # 山の可視化
│   │   │   └── twoaxis/       # 2軸評価
│   │   ├── stores/       # 状態管理（Pinia）
│   │   ├── types/        # TypeScript型定義
│   │   └── utils/        # ユーティリティ関数
├── backend/           # FastAPIバックエンド
│   ├── app/
│   │   ├── api/          # APIエンドポイント
│   │   ├── models/       # データベースモデル
│   │   ├── schemas/      # Pydanticスキーマ
│   │   └── algorithms/   # 計算アルゴリズム
├── data/              # ローカルデータ保存先
└── docs/              # ドキュメント
```

## 使い方

1. **新規プロジェクトの作成**
   - ホーム画面から「新規プロジェクト作成」をクリック
   - プロジェクト名と説明を入力

2. **ステークホルダーとニーズの定義**
   - 「ステークホルダー」タブでステークホルダーを追加
   - 「ニーズ」タブでニーズを定義し、ステークホルダーと関連付け

3. **性能構造の構築**
   - 「性能」タブで性能要求を階層的に定義
   - ニーズと性能の関連付けと効用関数の設計

4. **設計案の作成**
   - 「設計案」タブで新規設計案を作成
   - 性能値を入力し、4層ネットワークを構築

5. **評価と分析**
   - 「山の可視化」タブで総合評価を確認
   - 「2軸評価」タブでトレードオフ分析
   - 「3D Network」タブで構造を可視化

## トラブルシューティング

### データベース接続エラー
```bash
# データベースを初期化
cd backend
python -c "from app.models.database import init_db; init_db()"
```

### ポートが使用中の場合
```bash
# 使用中のポートを確認
lsof -i :5173  # フロントエンド
lsof -i :8000  # バックエンド
```

## ライセンス

MIT License