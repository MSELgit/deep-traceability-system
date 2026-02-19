# Vue ページ・コンポーネント依存関係

## コンポーネントツリー

```
App.vue
  ├── ModeSelector.vue
  ├── Header.vue
  └── RouterView
       ├── Home.vue
       ├── ProjectList.vue
       │    └── ImportPreviewDialog.vue
       ├── ProjectDetail.vue
       │    ├── StakeholderMatrix.vue
       │    ├── PerformanceManagement.vue
       │    │    └── PerformanceTree.vue (自己再帰)
       │    ├── NeedPerformanceMatrix.vue
       │    │    └── DecompositionAnalysis.vue
       │    ├── NetworkDemo.vue
       │    │    └── NetworkViewer.vue
       │    ├── MountainView.vue
       │    │    ├── DesignCaseList.vue
       │    │    ├── DesignCaseForm.vue
       │    │    │    ├── NetworkEditor.vue
       │    │    │    │    └── NetworkJsonImportDialog.vue
       │    │    │    ├── NetworkViewer.vue
       │    │    │    └── SCCWarningBanner.vue
       │    │    └── DesignCaseDetail.vue
       │    │         ├── NetworkViewer.vue
       │    │         ├── TradeoffMatrixMini.vue
       │    │         │    └── MatrixHeatmap.vue
       │    │         └── TradeoffAnalysisModal.vue
       │    │              ├── MatrixHeatmap.vue
       │    │              ├── ShapleyBreakdown.vue
       │    │              ├── DiscretizationConfidence.vue
       │    │              ├── TradeoffNetworkViewer.vue
       │    │              └── CouplingClusteringPanel.vue
       │    │                   └── InteractiveDendrogram.vue
       │    ├── OPM3DView.vue
       │    │    └── OPM3DScene.vue
       │    ├── ComparisonView.vue
       │    └── TwoAxisEvaluation.vue
       └── PaperNetworkView.vue
            └── NetworkViewer.vue
```

## ルーティング定義

| パス | ビュー | 読み込み方式 |
|------|--------|-------------|
| `/` | `Home.vue` | 遅延読み込み |
| `/projects` | `ProjectList.vue` | 遅延読み込み |
| `/project/:id` | `ProjectDetail.vue` | 遅延読み込み |
| `/paper-network` | `PaperNetworkView.vue` | 遅延読み込み |

## 外部ライブラリ依存関係

| パッケージ | 使用コンポーネント |
|------------|-------------------|
| `vue` | 全コンポーネント |
| `vue-router` | App.vue, Home.vue, ProjectList.vue, ProjectDetail.vue, Header.vue, MountainView.vue, TwoAxisEvaluation.vue |
| `pinia` | projectStore.ts, ProjectList.vue, ProjectDetail.vue, StakeholderMatrix.vue, OPM3DView.vue, MountainView.vue, DesignCaseForm.vue, DesignCaseDetail.vue, PerformanceManagement.vue, NeedPerformanceMatrix.vue, ComparisonView.vue |
| `axios` | api.ts |
| `@fortawesome/vue-fontawesome` | 20以上のコンポーネント |
| `@fortawesome/fontawesome-svg-core` | ImportPreviewDialog.vue |
| `@fortawesome/free-solid-svg-icons` | ImportPreviewDialog.vue |
| `three` | OPM3DScene.vue, MountainView.vue |
| `three/addons/controls/OrbitControls.js` | OPM3DScene.vue, MountainView.vue |
| `d3` | InteractiveDendrogram.vue |
| `xlsx` | NetworkEditor.vue, StakeholderMatrix.vue, NeedPerformanceMatrix.vue |
| `vue-chartjs` | DesignCaseDetail.vue |
| `chart.js` | DesignCaseDetail.vue |
| `nouislider` | NeedPerformanceMatrix.vue |

---

## ビュー (Views) 詳細

### App.vue

`src/App.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `Header.vue`, `ModeSelector.vue`, `RouterView` |
| 外部ライブラリ | `vue` (ref, onMounted, computed), `vue-router` (RouterView, useRoute) |
| ストア | なし |
| API | なし |

### Home.vue

`src/views/Home.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | `vue` (ref), `vue-router` (useRouter) |
| ストア | なし |
| API | なし |
| ルーター操作 | `router.push('/projects')` |

### ProjectList.vue

`src/views/ProjectList.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `ImportPreviewDialog.vue`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, onMounted), `vue-router` (useRouter), `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (storeToRefs) |
| API | `projectApi` (export, delete, import, importPreview) |
| 型 | `ImportPreviewResponse` (from `@/utils/api`) |

### ProjectDetail.vue

`src/views/ProjectDetail.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `StakeholderMatrix`, `PerformanceManagement`, `NeedPerformanceMatrix`, `NetworkDemo`, `MountainView`, `OPM3DView`, `ComparisonView`, `TwoAxisEvaluation`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, onMounted, nextTick), `vue-router` (useRoute), `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (storeToRefs) |
| API | `projectApi` (updateTwoAxisPlots), `calculationApi` (calculateEnergy) |

### PaperNetworkView.vue

`src/views/PaperNetworkView.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `NetworkViewer.vue` |
| 外部ライブラリ | `vue` (ref, onMounted) |
| ストア | なし |
| API | `fetch()` (直接呼び出し) |
| 型 | `NetworkStructure` (from `@/types/project`) |

---

## コンポーネント詳細

### common/Header.vue

`src/components/common/Header.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `RouterLink` |
| 外部ライブラリ | `vue-router` (RouterLink, useRouter) |
| Props | なし |
| Events | なし |

### common/ModeSelector.vue

`src/components/common/ModeSelector.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | なし (純粋Vue) |
| Props | なし |
| Events | `select` (mode: 'local' \| 'web') |

### common/ImportPreviewDialog.vue

`src/components/common/ImportPreviewDialog.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (computed, reactive, watch), `@fortawesome/vue-fontawesome`, `@fortawesome/fontawesome-svg-core`, `@fortawesome/free-solid-svg-icons` |
| Props | `visible: boolean`, `preview: ImportPreviewResponse` |
| Events | `confirm` (userChoices), `cancel` |

### network/NetworkViewer.vue

`src/components/network/NetworkViewer.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, computed, onMounted, onUnmounted, nextTick), `@fortawesome/vue-fontawesome` |
| 型 | `NetworkStructure`, `NetworkNode`, `Performance` (from `@/types/project`) |
| Props | `network: NetworkStructure`, `performances: Performance[]`, `hideToolbar?: boolean` |
| Exposes | `resetView` |

### network/NetworkHighlightViewer.vue

`src/components/network/NetworkHighlightViewer.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, computed, onMounted, onUnmounted, nextTick), `@fortawesome/vue-fontawesome` |
| 型 | `NetworkStructure`, `NetworkNode`, `Performance` (from `@/types/project`) |
| Props | `network: NetworkStructure`, `performances: Performance[]`, `highlightedPerfId?: string`, `hideToolbar?: boolean`, `height?: number` |
| Exposes | `resetView` |

### network/NetworkJsonImportDialog.vue

`src/components/network/NetworkJsonImportDialog.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, reactive, computed, watch), `@fortawesome/vue-fontawesome` |
| ユーティリティ | `parseAndValidateNetworkJson`, `buildFinalNetwork`, `NetworkImportPreview`, `PerformanceMatchResult` (from `@/utils/networkJsonImport`) |
| 型 | `NetworkStructure`, `WeightMode`, `Performance` (from `@/types/project`) |
| Props | `visible: boolean`, `performances: Performance[]`, `currentNetwork: NetworkStructure`, `currentWeightMode: WeightMode` |
| Events | `import` (result: { network, weightMode? }), `cancel` |

### network/NetworkEditor.vue

`src/components/network/NetworkEditor.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `NetworkJsonImportDialog.vue`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, computed, watch, onMounted, onUnmounted, nextTick), `xlsx`, `@fortawesome/vue-fontawesome` |
| 型 | `NetworkStructure`, `NetworkNode`, `NetworkEdge`, `Performance`, `WeightMode`, `WEIGHT_MODE_OPTIONS`, `migrateNodeType` (from `@/types/project`) |
| Props | `modelValue: NetworkStructure`, `performances: Performance[]`, `weightMode?: WeightMode` |
| Events | `update:modelValue` (NetworkStructure), `update:weightMode` (WeightMode) |

### analysis/InteractiveDendrogram.vue

`src/components/analysis/InteractiveDendrogram.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | `vue` (ref, onMounted, watch, computed), `d3` |
| Props | `data: DendrogramData`, `width?: number`, `height?: number` |
| Events | `threshold-change` (height, clusters) |

### analysis/SCCWarningBanner.vue

`src/components/analysis/SCCWarningBanner.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | `vue` (computed, ref) |
| 型 | `SCCAnalysisResult`, `SCCComponent` (from `@/utils/api`) |
| Props | `sccResult: SCCAnalysisResult \| null`, `showInfo?: boolean` |
| Events | `continue`, `dismiss` |

### analysis/DiscretizationConfidence.vue

`src/components/analysis/DiscretizationConfidence.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, computed, onMounted, watch), `@fortawesome/vue-fontawesome` |
| API | `calculationApi` (getDiscretizationConfidence) |
| Props | `projectId: string`, `caseId: string`, `autoLoad?: boolean` |

### analysis/CouplingClusteringPanel.vue

`src/components/analysis/CouplingClusteringPanel.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `InteractiveDendrogram.vue` |
| 外部ライブラリ | `vue` (ref, watch, onMounted) |
| API | `couplingApi` (getForCase) |
| 型 | `CouplingResult` (from `@/utils/api`) |
| Props | `projectId: string`, `caseId: string`, `autoLoad?: boolean` |

### analysis/MatrixHeatmap.vue

`src/components/analysis/MatrixHeatmap.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | `vue` (computed, ref, watch) |
| Props | `cosThetaMatrix`, `innerProductMatrix?`, `energyMatrix?`, `performanceNames`, `performanceIds?`, `performanceConsensus?`, `performanceIdMap?`, `hideToggle?`, `externalMode?`, `cellSize?`, `compact?` |
| Events | `cellClick`, `modeChange` |

### analysis/TradeoffMatrixMini.vue

`src/components/analysis/TradeoffMatrixMini.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `MatrixHeatmap.vue` |
| 外部ライブラリ | `vue` (computed, ref) |
| ユーティリティ | `formatEnergy` (from `@/utils/energyFormat`) |
| Props | `cosThetaMatrix?`, `innerProductMatrix?`, `energyMatrix?`, `performanceNames`, `performanceIds?`, `totalEnergy?`, `loading?`, `error?` |
| Events | `expand`, `retry`, `cellClick` |

### analysis/ShapleyBreakdown.vue

`src/components/analysis/ShapleyBreakdown.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | `vue` (computed, ref) |
| ユーティリティ | `formatEnergy` (from `@/utils/energyFormat`) |
| 型 | `NodeShapleyValue`, `EdgeShapleyValue` (from `@/utils/api`) |
| Props | `perfIName`, `perfJName`, `cosTheta`, `cij`, `nodeShapleyValues`, `edgeShapleyValues?`, `lambdaIJ?` 他 |

### analysis/TradeoffNetworkViewer.vue

`src/components/analysis/TradeoffNetworkViewer.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, computed, onMounted, nextTick), `@fortawesome/vue-fontawesome` |
| 型 | `NetworkStructure`, `NetworkNode`, `Performance` (from `@/types/project`), `NodeShapleyValue`, `EdgeShapleyValue` (from `@/utils/api`) |
| Props | `network`, `performances`, `perfIId?`, `perfJId?`, `nodeShapleyValues?`, `edgeShapleyValues?`, `performanceConsensus?`, `performanceIdMap?`, `lambdaIJ?`, `topN?` |

### analysis/TradeoffAnalysisModal.vue

`src/components/analysis/TradeoffAnalysisModal.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `MatrixHeatmap`, `ShapleyBreakdown`, `DiscretizationConfidence`, `TradeoffNetworkViewer`, `CouplingClusteringPanel`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (computed, ref, watch, onMounted, onUnmounted), `@fortawesome/vue-fontawesome` |
| ユーティリティ | `formatEnergy` (from `@/utils/energyFormat`) |
| API | `nodeShapleyApi` (computeForPair), `edgeShapleyApi` (computeForPair) |
| 型 | `NodeShapleyResult`, `NodeShapleyValue`, `EdgeShapleyResult`, `EdgeShapleyValue` (from `@/utils/api`) |
| Props | `show`, `projectId`, `caseId`, `caseName`, `cosThetaMatrix?`, `innerProductMatrix?`, `energyMatrix?`, `performanceNames`, `performanceIds?`, `performanceIdMap?`, `performanceWeights?`, `performanceConsensus?`, `totalEnergy?`, `spectralRadius?`, `network?`, `performances?` |
| Events | `close`, `update:show` |

### stakeholder/StakeholderMatrix.vue

`src/components/stakeholder/StakeholderMatrix.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref), `xlsx`, `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (storeToRefs) |

### opm3d/OPM3DView.vue

`src/components/opm3d/OPM3DView.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `OPM3DScene.vue`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, computed, watch), `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (storeToRefs) |
| API | `networkApi` (ノード/エッジのCRUD) |
| 型 | `NetworkNode`, `NetworkEdge`, `WeightMode`, `WEIGHT_MODE_OPTIONS` (from `@/types/project`) |

### opm3d/OPM3DScene.vue

`src/components/opm3d/OPM3DScene.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | `vue` (ref, onMounted, onUnmounted, watch), `three` (THREE), `three/addons/controls/OrbitControls.js` |
| 型 | `NetworkStructure`, `NetworkNode`, `NetworkEdge` (from `@/types/project`) |
| Props | `network: NetworkStructure`, `visibleLayers: number[]`, `layerSpacing: number`, `layerColors: { [key: number]: string }`, `planeSize?: number` |
| Events | `nodeSelected`, `edgeSelected` |

### twoaxis/TwoAxisEvaluation.vue

`src/components/twoaxis/TwoAxisEvaluation.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, watch, computed), `vue-router` (useRoute), `@fortawesome/vue-fontawesome` |
| API | `calculationApi` (calculateTradeoff) |
| 型 | `DesignCase`, `Performance` (from `@/types/project`) |
| Props | `viewId`, `designCases`, `performances`, `initialX?`, `initialY?`, `onRemove` |
| Events | `axis-change` |

### comparison/ComparisonView.vue

`src/components/comparison/ComparisonView.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, computed), `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (storeToRefs) |
| API | `structuralTradeoffApi` (getForCase) |
| 設定 | `CONFIG` (from `@/config/environment`) |
| 型 | `NetworkNode`, `NetworkEdge` (from `@/types/project`) |

### mountain/MountainView.vue

`src/components/mountain/MountainView.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `DesignCaseList.vue`, `DesignCaseForm.vue`, `DesignCaseDetail.vue` |
| 外部ライブラリ | `vue` (ref, computed, onMounted, onUnmounted, watch, nextTick), `vue-router` (useRoute), `three` (THREE), `three/addons/controls/OrbitControls.js` |
| ストア | `useProjectStore` (storeToRefs) |
| 設定 | `CONFIG` (from `@/config/environment`) |
| 型 | `DesignCase`, `DesignCaseCreate`, `Performance` (from `@/types/project`) |
| Props | `isActive?: boolean` |

### mountain/DesignCaseForm.vue

`src/components/mountain/DesignCaseForm.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `NetworkEditor.vue`, `NetworkViewer.vue`, `SCCWarningBanner.vue` |
| 外部ライブラリ | `vue` (ref, computed, watch, onMounted, onUnmounted, inject) |
| ストア | `useProjectStore` (storeToRefs) |
| API | `sccApi` (analyzeDirect) |
| ユーティリティ | `isDesignCaseEditable`, `getPerformanceMismatchMessage`, `createPerformanceIdMapping`, `remapNetworkPerformanceIds` (from `@/utils/performanceComparison`) |
| 型 | `DesignCase`, `Performance`, `DesignCaseCreate`, `NeedPerformanceRelation`, `UtilityFunction`, `NetworkStructure`, `WeightMode`, `migrateNetworkEdges`, `needsEdgeMigration` (from `@/types/project`) |
| Props | `designCase: DesignCase \| null`, `performances: Performance[]` |
| Events | `save`, `cancel` |

### mountain/DesignCaseList.vue

`src/components/mountain/DesignCaseList.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | なし |
| 型 | `DesignCase` (from `@/types/project`) |
| Props | `designCases: DesignCase[]`, `sortBy: string`, `hMax: number \| null` |
| Events | `toggle-panel`, `create`, `edit`, `copy`, `delete`, `focus`, `sort-change` |

### mountain/DesignCaseDetail.vue

`src/components/mountain/DesignCaseDetail.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `NetworkViewer.vue`, `TradeoffMatrixMini.vue`, `TradeoffAnalysisModal.vue`, `FontAwesomeIcon`, `Radar` (vue-chartjs) |
| 外部ライブラリ | `vue` (ref, computed, onMounted, watch), `vue-chartjs` (Radar), `chart.js` (Chart, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend), `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (直接アクセス) |
| API | `calculationApi` (calculateCaseEnergy), `structuralTradeoffApi` (getForCase) |
| ユーティリティ | `isDesignCaseEditable` (from `@/utils/performanceComparison`), `formatEnergy` (from `@/utils/energyFormat`) |
| 型 | `DesignCase`, `Performance` (from `@/types/project`) |
| Props | `designCase: DesignCase`, `performances: Performance[]`, `performanceHMax: { [key: string]: number }` |
| Events | `close`, `edit`, `copy`, `delete`, `tradeoffCellClick` |

### performance/PerformanceManagement.vue

`src/components/performance/PerformanceManagement.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `PerformanceTree.vue`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref), `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (storeToRefs) |
| 型 | `Performance` (from `@/types/project`) |

### performance/PerformanceTree.vue

`src/components/performance/PerformanceTree.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし (自己再帰) |
| 外部ライブラリ | `@fortawesome/vue-fontawesome` |
| 型 | `Performance` (from `@/types/project`) |
| Props | `performances: Performance[]` |
| Events | `add-child`, `edit`, `delete` |

### matrix/NeedPerformanceMatrix.vue

`src/components/matrix/NeedPerformanceMatrix.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `DecompositionAnalysis.vue`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (computed, ref, onMounted, nextTick, watch), `nouislider`, `xlsx`, `@fortawesome/vue-fontawesome` |
| ストア | `useProjectStore` (storeToRefs) |
| 設定 | `CONFIG` (from `@/config/environment`) |
| 型 | `Performance` (from `@/types/project`) |
| Events | `navigate-to-performance` |

### matrix/DecompositionAnalysis.vue

`src/components/matrix/DecompositionAnalysis.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | なし |
| 外部ライブラリ | `vue` (computed) |
| Props | `analysis`, `needsCount`, `hasStakeholdersOrPerformances` |
| Events | `navigate-to-performance` |

### demo/NetworkDemo.vue

`src/components/demo/NetworkDemo.vue`

| カテゴリ | 依存先 |
|----------|--------|
| 子コンポーネント | `NetworkViewer.vue`, `FontAwesomeIcon` |
| 外部ライブラリ | `vue` (ref, onMounted, nextTick), `@fortawesome/vue-fontawesome` |
| 設定 | `CONFIG` (from `@/config/environment`) |
| 型 | `NetworkStructure`, `NetworkNode`, `NetworkEdge` (from `@/types/project`) |

---

## ストア利用マップ

`useProjectStore` を直接使用するコンポーネント:

| コンポーネント | 用途 |
|----------------|------|
| `ProjectList.vue` | projects, loading, error の参照 |
| `ProjectDetail.vue` | currentProject の参照 |
| `StakeholderMatrix.vue` | ステークホルダー/ニーズの CRUD |
| `OPM3DView.vue` | currentProject, designCases の参照 |
| `MountainView.vue` | currentProject の参照 |
| `DesignCaseForm.vue` | currentProject の参照 |
| `DesignCaseDetail.vue` | currentProject.performances の参照 |
| `PerformanceManagement.vue` | パフォーマンスの CRUD |
| `NeedPerformanceMatrix.vue` | ニーズ-パフォーマンス関係の CRUD |
| `ComparisonView.vue` | currentProject, designCases の参照 |

## API利用マップ

各コンポーネントが直接呼び出すAPIモジュール:

| コンポーネント | APIモジュール | 操作 |
|----------------|---------------|------|
| `ProjectList.vue` | `projectApi` | export, delete, import, importPreview |
| `ProjectDetail.vue` | `projectApi`, `calculationApi` | updateTwoAxisPlots, calculateEnergy |
| `DesignCaseForm.vue` | `sccApi` | analyzeDirect |
| `DesignCaseDetail.vue` | `calculationApi`, `structuralTradeoffApi` | calculateCaseEnergy, getForCase |
| `TwoAxisEvaluation.vue` | `calculationApi` | calculateTradeoff |
| `ComparisonView.vue` | `structuralTradeoffApi` | getForCase |
| `OPM3DView.vue` | `networkApi` | ノード/エッジのCRUD |
| `DiscretizationConfidence.vue` | `calculationApi` | getDiscretizationConfidence |
| `CouplingClusteringPanel.vue` | `couplingApi` | getForCase |
| `TradeoffAnalysisModal.vue` | `nodeShapleyApi`, `edgeShapleyApi` | computeForPair |
| `PaperNetworkView.vue` | `fetch()` (直接) | JSON読み込み |

## 内部ユーティリティ依存関係

| ユーティリティ | 使用コンポーネント |
|----------------|-------------------|
| `@/utils/api` | ProjectList, ProjectDetail, DesignCaseForm, DesignCaseDetail, TwoAxisEvaluation, ComparisonView, OPM3DView, DiscretizationConfidence, CouplingClusteringPanel, TradeoffAnalysisModal |
| `@/utils/energyFormat` | TradeoffMatrixMini, ShapleyBreakdown, TradeoffAnalysisModal, DesignCaseDetail |
| `@/utils/performanceComparison` | DesignCaseForm, DesignCaseDetail |
| `@/utils/networkJsonImport` | NetworkJsonImportDialog |
| `@/config/environment` | NetworkDemo, MountainView, NeedPerformanceMatrix, ComparisonView |
| `@/types/project` | ほぼ全コンポーネント |
