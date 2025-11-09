# Deep Traceability System

多種多様なステークホルダーが関わる複雑システムの意思決定支援ツール

## 概要

本システムは、Deep Traceability手法とニーズ駆動型分解度評価（HHI指標）を用いて、
複雑なシステム設計における意思決定の一貫性とトレーサビリティを高めるツールです。

## 主要機能

1. **ステークホルダー分析**
   - 関係者とニーズのマトリクス管理
   - 票数による重要度評価

2. **性能管理**
   - 階層的な性能構造
   - HHI指標によるp²値計算
   - 詳細化優先度の可視化

3. **効用関数設計**
   - グラフィカルな関数エディタ
   - 連続値・離散値対応

4. **設計案管理**
   - 4層ネットワーク構造（性能→特性→変数→モノ/環境）
   - 設計案のコピー・流用機能

5. **山の可視化（3D）**
   - 円錐状の標高マップ
   - MDS（多次元尺度法）による類似案の配置
   - インタラクティブな探索機能

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
├── backend/           # FastAPIバックエンド
├── data/              # ローカルデータ保存先
└── docs/              # ドキュメント
```