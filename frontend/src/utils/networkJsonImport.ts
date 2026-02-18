/**
 * ネットワークJSON インポート ユーティリティ
 *
 * AI等で生成した簡略化JSONを内部NetworkStructure形式に変換する。
 * Vue非依存のピュア関数で構成。
 */

import type { NetworkStructure, NetworkNode, NetworkEdge, WeightMode, Performance } from '@/types/project';
import { WEIGHT_MODE_OPTIONS } from '@/types/project';

// ============================================================
// 型定義
// ============================================================

export interface SimplifiedNode {
  label: string;
  layer: string | number;
  subtype?: string;
  // エイリアス
  name?: string;
  type?: string;
}

export interface SimplifiedEdge {
  from: string;
  to: string;
  weight?: number;
  // エイリアス
  source?: string;
  target?: string;
}

export interface ImportMessage {
  severity: 'error' | 'warning' | 'info';
  message: string;
  nodeLabel?: string;
  edgeLabels?: string;
}

export interface PerformanceMatchResult {
  inputLabel: string;
  matchedPerformance: Performance | null;
  candidates: Performance[];
  matchType: 'exact' | 'prefix' | 'name' | 'fuzzy' | 'none';
}

export interface NetworkImportPreview {
  valid: boolean;
  errors: ImportMessage[];
  warnings: ImportMessage[];
  infos: ImportMessage[];
  performanceMatches: PerformanceMatchResult[];
  convertedNetwork: NetworkStructure;
  weightMode: WeightMode | null;
  stats: {
    nodesByLayer: { P: number; A: number; V: number; E: number };
    edgeCount: number;
  };
}

interface NormalizedLayerResult {
  layer: 1 | 2 | 3 | 4;
  type: NetworkNode['type'];
}

// ============================================================
// JSON サニタイズ
// ============================================================

/**
 * AIが生成しがちなJSON問題を修正する
 * - 単行コメント (// ...)
 * - 複数行コメント (/* ... *​/)
 * - 末尾カンマ ([1, 2, ] や {a: 1, })
 */
export function sanitizeJsonString(input: string): string {
  let s = input.trim();

  // 複数行コメント除去
  s = s.replace(/\/\*[\s\S]*?\*\//g, '');

  // 単行コメント除去（文字列リテラル内のものは避ける簡易版）
  s = s.replace(/(?<="[^"]*".*?)\/\/.*$/gm, '');
  s = s.replace(/^(\s*)\/\/.*$/gm, '$1');

  // 末尾カンマ除去
  s = s.replace(/,(\s*[}\]])/g, '$1');

  return s;
}

// ============================================================
// レイヤー正規化
// ============================================================

const LAYER_MAP: Record<string, NormalizedLayerResult> = {
  // Layer 1: Performance
  'p': { layer: 1, type: 'performance' },
  'performance': { layer: 1, type: 'performance' },
  '性能': { layer: 1, type: 'performance' },
  '1': { layer: 1, type: 'performance' },
  // Layer 2: Attribute
  'a': { layer: 2, type: 'attribute' },
  'attribute': { layer: 2, type: 'attribute' },
  'attr': { layer: 2, type: 'attribute' },
  'property': { layer: 2, type: 'attribute' },
  '属性': { layer: 2, type: 'attribute' },
  '2': { layer: 2, type: 'attribute' },
  // Layer 3: Variable
  'v': { layer: 3, type: 'variable' },
  'variable': { layer: 3, type: 'variable' },
  'var': { layer: 3, type: 'variable' },
  '変数': { layer: 3, type: 'variable' },
  '3': { layer: 3, type: 'variable' },
  // Layer 4: Entity (default object)
  'e': { layer: 4, type: 'object' },
  'entity': { layer: 4, type: 'object' },
  'object': { layer: 4, type: 'object' },
  'environment': { layer: 4, type: 'environment' },
  'モノ': { layer: 4, type: 'object' },
  '環境': { layer: 4, type: 'environment' },
  '4': { layer: 4, type: 'object' },
};

export function normalizeLayer(input: string | number, subtype?: string): NormalizedLayerResult | null {
  const key = String(input).toLowerCase().trim();
  const result = LAYER_MAP[key];
  if (!result) return null;

  // E層でsubtypeが指定されている場合のオーバーライド
  if (result.layer === 4 && subtype) {
    const st = subtype.toLowerCase().trim();
    if (st === 'environment' || st === '環境') {
      return { layer: 4, type: 'environment' };
    }
  }

  return { ...result };
}

// ============================================================
// 性能名マッチング
// ============================================================

/**
 * レーベンシュタイン距離による類似度 (0~1, 1が完全一致)
 */
export function levenshteinSimilarity(a: string, b: string): number {
  const la = a.length;
  const lb = b.length;
  if (la === 0 && lb === 0) return 1;
  if (la === 0 || lb === 0) return 0;

  const matrix: number[][] = [];
  for (let i = 0; i <= la; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= lb; j++) {
    matrix[0][j] = j;
  }
  for (let i = 1; i <= la; i++) {
    for (let j = 1; j <= lb; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost
      );
    }
  }
  const maxLen = Math.max(la, lb);
  return 1 - matrix[la][lb] / maxLen;
}

/**
 * 性能名からプレフィックス部("P1 - ")を除去して本体名を取得
 */
function extractPerformanceName(fullName: string): string {
  const match = fullName.match(/^P\d+\s*[-–—]\s*(.+)$/);
  return match ? match[1].trim() : fullName.trim();
}

export function matchPerformance(
  label: string,
  performances: Performance[]
): PerformanceMatchResult {
  const trimmed = label.trim();
  const lowerTrimmed = trimmed.toLowerCase();
  const leafPerfs = performances.filter(p => p.is_leaf);

  // 1. 完全一致
  const exactMatch = leafPerfs.find(
    p => p.name.trim().toLowerCase() === lowerTrimmed
  );
  if (exactMatch) {
    return { inputLabel: trimmed, matchedPerformance: exactMatch, candidates: [], matchType: 'exact' };
  }

  // 2. プレフィックス一致 ("P1" → "P1 - 航続距離")
  const prefixMatches = leafPerfs.filter(
    p => p.name.trim().toLowerCase().startsWith(lowerTrimmed)
  );
  if (prefixMatches.length === 1) {
    return { inputLabel: trimmed, matchedPerformance: prefixMatches[0], candidates: [], matchType: 'prefix' };
  }
  if (prefixMatches.length > 1) {
    return { inputLabel: trimmed, matchedPerformance: null, candidates: prefixMatches, matchType: 'prefix' };
  }

  // 3. 名前部分一致 ("航続距離" → "P1 - 航続距離")
  const nameMatches = leafPerfs.filter(p => {
    const extracted = extractPerformanceName(p.name).toLowerCase();
    return extracted === lowerTrimmed;
  });
  if (nameMatches.length === 1) {
    return { inputLabel: trimmed, matchedPerformance: nameMatches[0], candidates: [], matchType: 'name' };
  }
  if (nameMatches.length > 1) {
    return { inputLabel: trimmed, matchedPerformance: null, candidates: nameMatches, matchType: 'name' };
  }

  // 部分文字列一致も試す
  const partialNameMatches = leafPerfs.filter(p => {
    const extracted = extractPerformanceName(p.name).toLowerCase();
    return extracted.includes(lowerTrimmed) || lowerTrimmed.includes(extracted);
  });
  if (partialNameMatches.length === 1) {
    return { inputLabel: trimmed, matchedPerformance: partialNameMatches[0], candidates: [], matchType: 'name' };
  }
  if (partialNameMatches.length > 1) {
    return { inputLabel: trimmed, matchedPerformance: null, candidates: partialNameMatches, matchType: 'name' };
  }

  // 4. 曖昧一致 (レーベンシュタイン距離)
  const FUZZY_THRESHOLD = 0.7;
  const scored = leafPerfs
    .map(p => ({
      perf: p,
      similarity: Math.max(
        levenshteinSimilarity(lowerTrimmed, p.name.trim().toLowerCase()),
        levenshteinSimilarity(lowerTrimmed, extractPerformanceName(p.name).toLowerCase())
      )
    }))
    .filter(s => s.similarity >= FUZZY_THRESHOLD)
    .sort((a, b) => b.similarity - a.similarity);

  if (scored.length === 1) {
    return { inputLabel: trimmed, matchedPerformance: scored[0].perf, candidates: [], matchType: 'fuzzy' };
  }
  if (scored.length > 1) {
    // 最高スコアと次点の差が0.1以上なら最高スコアを採用
    if (scored[0].similarity - scored[1].similarity >= 0.1) {
      return { inputLabel: trimmed, matchedPerformance: scored[0].perf, candidates: scored.map(s => s.perf), matchType: 'fuzzy' };
    }
    return { inputLabel: trimmed, matchedPerformance: null, candidates: scored.map(s => s.perf), matchType: 'fuzzy' };
  }

  return { inputLabel: trimmed, matchedPerformance: null, candidates: [], matchType: 'none' };
}

// ============================================================
// PAVE バリデーション
// ============================================================

function validatePaveEdge(
  fromLayer: number,
  toLayer: number,
  fromLabel: string,
  toLabel: string
): ImportMessage | null {
  if (fromLayer === 1) {
    return {
      severity: 'error',
      message: `性能ノードはエッジの始点にできません（効果を受け取るのみ）`,
      edgeLabels: `${fromLabel} → ${toLabel}`
    };
  }
  if (fromLayer === 3 && toLayer === 1) {
    return {
      severity: 'error',
      message: `変数から性能への直接接続は無効です。属性を介してください（V → A → P）`,
      edgeLabels: `${fromLabel} → ${toLabel}`
    };
  }
  if (fromLayer === 4 && toLayer === 1) {
    return {
      severity: 'error',
      message: `モノ・環境から性能への直接接続は無効です（E → V → A → P）`,
      edgeLabels: `${fromLabel} → ${toLabel}`
    };
  }
  if (fromLayer === 4 && toLayer === 2) {
    return {
      severity: 'error',
      message: `モノ・環境から属性への直接接続は無効です。変数を介してください（E → V → A）`,
      edgeLabels: `${fromLabel} → ${toLabel}`
    };
  }
  if (fromLayer === 3 && toLayer === 3) {
    return {
      severity: 'error',
      message: `変数同士の接続は無効です。変数は独立した設計パラメータです`,
      edgeLabels: `${fromLabel} → ${toLabel}`
    };
  }
  if (fromLayer === 2 && toLayer === 3) {
    return {
      severity: 'error',
      message: `属性から変数への接続は無効です。因果フローは V → A → P です`,
      edgeLabels: `${fromLabel} → ${toLabel}`
    };
  }
  return null;
}

// ============================================================
// メインパイプライン
// ============================================================

export function parseAndValidateNetworkJson(
  jsonString: string,
  performances: Performance[],
  currentWeightMode: WeightMode
): NetworkImportPreview {
  const errors: ImportMessage[] = [];
  const warnings: ImportMessage[] = [];
  const infos: ImportMessage[] = [];
  const performanceMatches: PerformanceMatchResult[] = [];
  const nodes: NetworkNode[] = [];
  const edges: NetworkEdge[] = [];
  const stats = { nodesByLayer: { P: 0, A: 0, V: 0, E: 0 }, edgeCount: 0 };

  const emptyResult = (): NetworkImportPreview => ({
    valid: false,
    errors,
    warnings,
    infos,
    performanceMatches,
    convertedNetwork: { nodes: [], edges: [] },
    weightMode: null,
    stats,
  });

  // --- Step 1: JSONパース ---
  if (!jsonString.trim()) {
    errors.push({ severity: 'error', message: 'JSONを入力してください' });
    return emptyResult();
  }

  let parsed: any;
  try {
    const sanitized = sanitizeJsonString(jsonString);
    parsed = JSON.parse(sanitized);
  } catch (e: any) {
    const msg = e.message || '';
    errors.push({ severity: 'error', message: `JSONの構文エラーです: ${msg}` });
    return emptyResult();
  }

  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    errors.push({ severity: 'error', message: 'JSONはオブジェクト形式（{...}）である必要があります' });
    return emptyResult();
  }

  // ラッパーオブジェクトの検出 ({"network": {...}})
  if (!parsed.nodes && parsed.network && typeof parsed.network === 'object') {
    infos.push({ severity: 'info', message: 'ラッパーオブジェクトを検出しました。"network" の内容を使用します' });
    parsed = { ...parsed.network, ...(!parsed.network.weight_mode && parsed.weight_mode ? { weight_mode: parsed.weight_mode } : {}) };
  }

  // --- Step 1.5: weight_mode ---
  let weightMode: WeightMode | null = null;
  if (parsed.weight_mode) {
    const wm = String(parsed.weight_mode).toLowerCase().trim();
    if (['discrete_3', 'discrete_5', 'discrete_7', 'continuous'].includes(wm)) {
      weightMode = wm as WeightMode;
    } else {
      warnings.push({ severity: 'warning', message: `不明なweight_mode "${parsed.weight_mode}" を無視しました。現在の設定を使用します` });
    }
  }
  const effectiveWeightMode = weightMode || currentWeightMode;

  // --- Step 2: ノード解析 ---
  if (!Array.isArray(parsed.nodes)) {
    errors.push({ severity: 'error', message: '`nodes` 配列が必要です' });
    return emptyResult();
  }

  // ラベル→ノード のマッピング (エッジ解決用)
  const labelToNode = new Map<string, NetworkNode>();
  const timestamp = Date.now();
  let nodeCounter = 0;

  for (let i = 0; i < parsed.nodes.length; i++) {
    const raw = parsed.nodes[i];
    if (typeof raw !== 'object' || raw === null) {
      errors.push({ severity: 'error', message: `ノード #${i + 1}: オブジェクト形式である必要があります` });
      continue;
    }

    // ラベル解決 (name エイリアス)
    const label = String(raw.label || raw.name || '').trim();
    if (!label) {
      errors.push({ severity: 'error', message: `ノード #${i + 1}: "label" が必要です` });
      continue;
    }

    // レイヤー解決 (type エイリアス)
    const layerInput = raw.layer ?? raw.type;
    if (layerInput === undefined || layerInput === null) {
      errors.push({ severity: 'error', message: `ノード "${label}": "layer" が必要です（P/A/V/E を使用してください）` });
      continue;
    }

    const normalized = normalizeLayer(layerInput, raw.subtype);
    if (!normalized) {
      errors.push({ severity: 'error', message: `ノード "${label}": 不明なレイヤー "${layerInput}"（P/A/V/E を使用してください）` });
      continue;
    }

    // 重複チェック
    if (labelToNode.has(label)) {
      warnings.push({ severity: 'warning', message: `ノード "${label}": ラベルが重複しています。スキップします`, nodeLabel: label });
      continue;
    }

    // 性能ノードのマッチング
    let performanceId: string | undefined;
    if (normalized.layer === 1) {
      const matchResult = matchPerformance(label, performances);
      performanceMatches.push(matchResult);
      if (matchResult.matchedPerformance) {
        performanceId = matchResult.matchedPerformance.id;
      } else if (matchResult.candidates.length === 0) {
        errors.push({ severity: 'error', message: `性能ノード "${label}": 一致する性能が見つかりません`, nodeLabel: label });
      }
      // candidates.length > 0 の場合はユーザー選択待ち (エラーにはしない)
    }

    const nodeId = normalized.layer === 1 && performanceId
      ? `perf-${performanceId}`
      : `node-${timestamp}-${nodeCounter++}`;

    const node: NetworkNode = {
      id: nodeId,
      layer: normalized.layer,
      type: normalized.type,
      label,
      x: 0,
      y: 0,
      ...(performanceId ? { performance_id: performanceId } : {}),
    };

    nodes.push(node);
    labelToNode.set(label, node);

    // 統計
    const layerKey = (['P', 'A', 'V', 'E'] as const)[normalized.layer - 1];
    stats.nodesByLayer[layerKey]++;
  }

  // --- Step 3: エッジ解析 ---
  const rawEdges = parsed.edges;
  if (rawEdges !== undefined && !Array.isArray(rawEdges)) {
    errors.push({ severity: 'error', message: '`edges` は配列である必要があります' });
  } else if (!rawEdges || rawEdges.length === 0) {
    infos.push({ severity: 'info', message: 'エッジが定義されていません（ノードのみインポートします）' });
  } else {
    const seenEdges = new Set<string>();
    let edgeCounter = 0;

    for (let i = 0; i < rawEdges.length; i++) {
      const raw = rawEdges[i];
      if (typeof raw !== 'object' || raw === null) {
        errors.push({ severity: 'error', message: `エッジ #${i + 1}: オブジェクト形式である必要があります` });
        continue;
      }

      // from/to 解決 (source/target エイリアス)
      const fromLabel = String(raw.from || raw.source || '').trim();
      const toLabel = String(raw.to || raw.target || '').trim();

      if (!fromLabel || !toLabel) {
        errors.push({ severity: 'error', message: `エッジ #${i + 1}: "from" と "to" が必要です` });
        continue;
      }

      const fromNode = labelToNode.get(fromLabel);
      const toNode = labelToNode.get(toLabel);

      if (!fromNode) {
        errors.push({ severity: 'error', message: `エッジ #${i + 1}: ノード "${fromLabel}" が見つかりません`, edgeLabels: `${fromLabel} → ${toLabel}` });
        continue;
      }
      if (!toNode) {
        errors.push({ severity: 'error', message: `エッジ #${i + 1}: ノード "${toLabel}" が見つかりません`, edgeLabels: `${fromLabel} → ${toLabel}` });
        continue;
      }

      // 自己ループチェック
      if (fromNode.id === toNode.id) {
        errors.push({ severity: 'error', message: `エッジ "${fromLabel}" → "${toLabel}": 自己ループは許可されていません`, edgeLabels: `${fromLabel} → ${toLabel}` });
        continue;
      }

      // 重複チェック
      const edgeKey = `${fromNode.id}->${toNode.id}`;
      if (seenEdges.has(edgeKey)) {
        warnings.push({ severity: 'warning', message: `エッジ "${fromLabel}" → "${toLabel}": 重複するエッジをスキップしました`, edgeLabels: `${fromLabel} → ${toLabel}` });
        continue;
      }
      seenEdges.add(edgeKey);

      // PAVEバリデーション
      const paveError = validatePaveEdge(fromNode.layer, toNode.layer, fromLabel, toLabel);
      if (paveError) {
        errors.push(paveError);
        continue;
      }

      // 重み処理
      let weight: number | undefined;
      const isUndirected = (fromNode.layer === 3 && toNode.layer === 4)
        || (fromNode.layer === 4 && toNode.layer === 3)
        || (fromNode.layer === 4 && toNode.layer === 4);

      if (isUndirected) {
        if (raw.weight !== undefined && raw.weight !== null && raw.weight !== 0) {
          infos.push({ severity: 'info', message: `エッジ "${fromLabel}" → "${toLabel}": V-E/E-E エッジは無向のため重みは無視されます`, edgeLabels: `${fromLabel} → ${toLabel}` });
        }
        weight = undefined;
      } else if (raw.weight !== undefined && raw.weight !== null) {
        weight = Number(raw.weight);
        if (isNaN(weight)) {
          warnings.push({ severity: 'warning', message: `エッジ "${fromLabel}" → "${toLabel}": 重み "${raw.weight}" は数値ではありません。0にしました`, edgeLabels: `${fromLabel} → ${toLabel}` });
          weight = 0;
        } else {
          // 重みモードに応じたクランプ/丸め
          weight = clampWeight(weight, effectiveWeightMode, fromLabel, toLabel, warnings);
        }
      } else {
        weight = 0;
      }

      const edge: NetworkEdge = {
        id: `edge-${timestamp}-${edgeCounter++}`,
        source_id: fromNode.id,
        target_id: toNode.id,
        type: 'type1',
        ...(weight !== undefined ? { weight } : {}),
      };

      edges.push(edge);
      stats.edgeCount++;
    }
  }

  // 未解決の性能マッチがあるかチェック
  const hasUnresolvedMatches = performanceMatches.some(
    m => !m.matchedPerformance && m.candidates.length > 0
  );

  const valid = errors.length === 0 && !hasUnresolvedMatches;

  return {
    valid,
    errors,
    warnings,
    infos,
    performanceMatches,
    convertedNetwork: { nodes, edges, weight_mode: effectiveWeightMode },
    weightMode,
    stats,
  };
}

// ============================================================
// 重みクランプ
// ============================================================

function clampWeight(
  weight: number,
  mode: WeightMode,
  fromLabel: string,
  toLabel: string,
  warnings: ImportMessage[]
): number {
  if (mode === 'continuous') {
    if (weight < -1 || weight > 1) {
      const clamped = Math.max(-1, Math.min(1, weight));
      warnings.push({
        severity: 'warning',
        message: `エッジ "${fromLabel}" → "${toLabel}": 重み ${weight} を ${clamped} に制限しました`,
        edgeLabels: `${fromLabel} → ${toLabel}`
      });
      return clamped;
    }
    return weight;
  }

  // 離散モード: 最も近い有効値に丸める
  const validValues = WEIGHT_MODE_OPTIONS[mode].values;
  if (validValues.length === 0) return weight;

  let nearest = validValues[0];
  let minDist = Math.abs(weight - nearest);
  for (const v of validValues) {
    const dist = Math.abs(weight - v);
    if (dist < minDist) {
      minDist = dist;
      nearest = v;
    }
  }

  if (nearest !== weight) {
    warnings.push({
      severity: 'warning',
      message: `エッジ "${fromLabel}" → "${toLabel}": 重み ${weight} を最も近い有効値 ${nearest} に丸めました`,
      edgeLabels: `${fromLabel} → ${toLabel}`
    });
  }

  return nearest;
}

// ============================================================
// 最終ネットワーク構築（性能マッチ選択後）
// ============================================================

/**
 * ユーザーの性能マッチ選択を反映した最終NetworkStructureを構築
 * @param preview バリデーション結果
 * @param perfSelections { inputLabel → performance_id } のユーザー選択マッピング
 */
export function buildFinalNetwork(
  preview: NetworkImportPreview,
  perfSelections: Record<string, string>
): NetworkStructure {
  const nodes = preview.convertedNetwork.nodes.map(node => {
    if (node.layer !== 1) return { ...node };

    // 性能ノード: マッチ結果またはユーザー選択からIDを解決
    const match = preview.performanceMatches.find(m => m.inputLabel === node.label);
    if (match) {
      const perfId = match.matchedPerformance?.id || perfSelections[match.inputLabel];
      if (perfId) {
        return {
          ...node,
          id: `perf-${perfId}`,
          performance_id: perfId,
        };
      }
    }
    return { ...node };
  });

  // エッジのsource_id/target_idを更新（性能ノードのID変更に追従）
  const oldToNewId = new Map<string, string>();
  preview.convertedNetwork.nodes.forEach((oldNode, i) => {
    if (oldNode.id !== nodes[i].id) {
      oldToNewId.set(oldNode.id, nodes[i].id);
    }
  });

  const edges = preview.convertedNetwork.edges.map(edge => ({
    ...edge,
    source_id: oldToNewId.get(edge.source_id) || edge.source_id,
    target_id: oldToNewId.get(edge.target_id) || edge.target_id,
  }));

  return {
    nodes,
    edges,
    weight_mode: preview.convertedNetwork.weight_mode,
  };
}
