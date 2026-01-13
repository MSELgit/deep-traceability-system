# Tradeoff Analysis Modal UI 拡張プラン

## 1. 現状の実装

### 1.1 パネル幅拡張の仕組み

現在、Tradeoff Analysisの詳細表示は以下の流れで動作:

```
DesignCaseDetail.vue
  └── TradeoffMatrixMini (プレビュー表示)
       └── "Open Detailed Analysis" ボタン
            └── emit('expand') → MountainView
                 └── rightPanelExpanded = true
                      └── CSS: .right-panel.expanded { width: 70% }
```

**関連ファイル:**
- `MountainView.vue`: パネル幅制御 (lines 910-933)
- `DesignCaseDetail.vue`: 展開状態の管理 (lines 242-278)

### 1.2 現在のTradeoffAnalysisPanelレイアウト

```
┌─────────────────────────────────────────────────┐
│ [←Back] Tradeoff Analysis                       │
├─────────────────────┬───────────────────────────┤
│                     │ Contribution Breakdown    │
│   Matrix Heatmap    ├───────────────────────────┤
│   (45%)             │ Network Highlight         │
│                     │                           │
├─────────────────────┴───────────────────────────┤
│ Total Pairs: X | Tradeoffs: X | Synergies: X   │
└─────────────────────────────────────────────────┘
```

### 1.3 既存のモーダルパターン

`DesignCaseForm.vue` にNetwork Editorモーダルが実装済み:

```vue
<div v-if="showNetworkEditor" class="network-editor-modal" @click.self="closeModal">
  <div class="modal-content">
    <div class="modal-header">...</div>
    <div class="modal-body">...</div>
  </div>
</div>
```

CSS特徴:
- `position: fixed` + `inset: 0` でフルスクリーンオーバーレイ
- `background: rgba(0, 0, 0, 0.85)` の暗い背景
- `backdrop-filter: blur(8px)` でぼかし効果
- `.modal-content`: `width: 90vw`, `height: 85vh`

---

## 2. 変更内容

### 2.1 廃止する機能

1. **パネル幅拡張**: `rightPanelExpanded` による70%幅への拡張を廃止
2. **DesignCaseDetail内のTradeoffAnalysisPanel埋め込み**: 削除

### 2.2 新規追加

1. **TradeoffAnalysisModal.vue**: 新規モーダルコンポーネント
2. **自動データ取得**: モーダルオープン時にDiscretization Confidenceを自動ロード

---

## 3. 新UIレイアウト設計

### 3.1 モーダル構造

```
┌──────────────────────────────────────────────────────────────────────┐
│ Tradeoff Analysis - {Case Name}                              [✕]    │
├────────────────────────────────┬─────────────────────────────────────┤
│                                │  ┌─────────────────────────────┐   │
│                                │  │ Contribution Breakdown      │   │
│       Matrix Heatmap           │  │ (Shapley Values)            │   │
│       (左側 40%)               │  └─────────────────────────────┘   │
│                                │  ┌─────────────────────────────┐   │
│     - cos θ / Energy 切替      │  │ Network Highlight           │   │
│     - セルクリックで詳細表示    │  │ (選択ペアのパス表示)         │   │
│                                │  └─────────────────────────────┘   │
│                                │  ┌─────────────────────────────┐   │
│                                │  │ Discretization Confidence   │   │
│                                │  │ (自動ロード)                │   │
│                                │  └─────────────────────────────┘   │
├────────────────────────────────┴─────────────────────────────────────┤
│ Total Pairs: X | Tradeoffs: X | Synergies: X | Total Energy: X E    │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 レスポンシブ比率

- モーダル全体: `width: 90vw`, `height: 85vh`
- 左カラム (Matrix): `flex: 0 0 60%`
- 右カラム (詳細): `flex: 1` (40%)
  - Shapley Breakdown: `flex: 0 0 auto` (内容に応じた高さ)
  - Network Highlight: `flex: 1` (残りスペース)
  - Discretization Confidence: `flex: 0 0 auto` (内容に応じた高さ)

### 3.3 決定事項

- **モーダルの閉じ方**: 背景クリック、✕ボタン、ESCキー すべて対応
- **セル選択状態**: モーダル再オープン時にリセット
- **Network Highlight初期状態**: 全体ネットワークを薄く表示（将来拡張予定）
- **ヘッダーボタン**: 一旦後回し（CSVエクスポート等は将来対応）

---

## 4. 実装タスク

### Phase 1: モーダルコンポーネント作成

1. **新規ファイル作成**: `src/components/analysis/TradeoffAnalysisModal.vue`
   - 既存の `TradeoffAnalysisPanel.vue` をベースに改修
   - モーダルラッパー追加
   - Discretization Confidence統合

2. **プロパティ設計**:
   ```typescript
   interface Props {
     show: boolean;
     projectId: string;
     caseId: string;
     caseName: string;
     cosThetaMatrix: number[][];
     innerProductMatrix?: number[][];
     energyMatrix?: number[][];
     performanceNames: string[];
     performanceIds?: string[];
     performanceIdMap?: { [networkNodeId: string]: string };
     performanceWeights?: { [dbPerfId: string]: number };
     totalEnergy?: number;
     spectralRadius?: number;
     network?: any;
     performances?: any[];
   }
   ```

3. **イベント設計**:
   ```typescript
   emits: ['close', 'update:show']
   ```

### Phase 2: DesignCaseDetail修正

1. **削除**:
   - `expanded` prop の依存箇所
   - `TradeoffAnalysisPanel` のインライン表示
   - `expandAnalysis` / `collapseAnalysis` イベント

2. **追加**:
   - `showTradeoffModal` state
   - `TradeoffAnalysisModal` コンポーネント使用

3. **修正**:
   - "Open Detailed Analysis" ボタン → モーダルを開く

### Phase 3: MountainView修正

1. **削除**:
   - `rightPanelExpanded` state
   - `handleExpandAnalysis` / `handleCollapseAnalysis` handlers
   - `.right-panel.expanded` CSS class

2. **CSS調整**:
   - `.right-panel.open` のみ残す (50%幅)

### Phase 4: Discretization Confidence自動ロード

1. `DiscretizationConfidence.vue`:
   - `autoLoad` propをtrueで使用
   - モーダルオープン時に自動fetch

---

## 5. 質問事項

### Q1: モーダルの閉じ方
現在のNetwork Editorモーダルでは:
- 背景クリックで閉じる
- ✕ボタンで閉じる
- ESCキーで閉じる？

**Tradeoff Analysisモーダルも同様でよいか？**

### Q2: セル選択状態の保持
モーダルを閉じた後に再度開いた場合:
- 前回選択したセル（Shapley表示中のペア）をリセットするか？
- それとも保持するか？

### Q3: Network Highlightの初期状態
セルが未選択の場合:
- 空のプレースホルダー表示？
- それとも全体ネットワークを薄く表示？

### Q4: モーダルヘッダーにボタンを追加するか？
例:
- Matrix全体をCSVエクスポート
- スクリーンショット保存

---

## 6. ファイル変更一覧

| ファイル | 変更内容 |
|---------|---------|
| `src/components/analysis/TradeoffAnalysisModal.vue` | **新規作成** |
| `src/components/analysis/TradeoffAnalysisPanel.vue` | 削除 or 内部コンポーネントとして維持 |
| `src/components/mountain/DesignCaseDetail.vue` | モーダル呼び出しに変更 |
| `src/components/mountain/MountainView.vue` | expanded関連削除 |
| `src/components/analysis/DiscretizationConfidence.vue` | 変更なし (autoLoad対応済み) |

---

## 7. 参考: 既存モーダルCSS

```scss
.network-editor-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: lighten($gray, 8%);
  width: 90vw;
  height: 85vh;
  max-height: 85vh;
  border-radius: 1.2vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: clamp(1rem, 2vh, 1.5rem) clamp(1.2rem, 2vw, 1.8rem);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.modal-body {
  flex: 1;
  overflow: auto;
  padding: 0;
}
```
