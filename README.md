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

## セットアップ

### ローカル開発環境

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

### 実行モード

#### ローカルモード（デフォルト）
```bash
npm run dev
```

#### Webモード
```bash
npm run dev:web
```

## プロジェクト構造

```
deep-traceability-system/
├── frontend/          # Vue3フロントエンド
├── backend/           # FastAPIバックエンド
├── data/              # ローカルデータ保存先
└── docs/              # ドキュメント
```

## 開発ロードマップ

- [ ] Phase 1: 基礎構築
- [ ] Phase 2: マトリクス機能
- [ ] Phase 3: 効用関数
- [ ] Phase 4: 設計案管理
- [ ] Phase 5: 山の可視化
- [ ] Phase 6: 統合・最適化

## ライセンス

MIT License
