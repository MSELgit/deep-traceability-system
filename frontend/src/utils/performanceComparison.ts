// frontend/src/utils/performanceComparison.ts

import type { Performance } from '../types/project';

/**
 * 2つの性能ツリーが一致しているかチェックする
 * ID、名前、親子関係が完全に一致する必要がある
 */
export function comparePerformanceTrees(
  current: Performance[],
  snapshot: Performance[]
): { isMatch: boolean; differences: string[] } {
  const differences: string[] = [];

  // 性能数が異なる
  if (current.length !== snapshot.length) {
    differences.push(`性能数が異なります（現在: ${current.length}, 作成時: ${snapshot.length}）`);
    return { isMatch: false, differences };
  }

  // IDでソートして比較
  const sortedCurrent = [...current].sort((a, b) => a.id.localeCompare(b.id));
  const sortedSnapshot = [...snapshot].sort((a, b) => a.id.localeCompare(b.id));

  for (let i = 0; i < sortedCurrent.length; i++) {
    const curr = sortedCurrent[i];
    const snap = sortedSnapshot[i];

    // IDが異なる
    if (curr.id !== snap.id) {
      differences.push(`性能ID不一致: ${curr.id} !== ${snap.id}`);
      continue;
    }

    // 名前が異なる
    if (curr.name !== snap.name) {
      differences.push(`性能「${curr.id}」の名前が変更されています（現在: ${curr.name}, 作成時: ${snap.name}）`);
    }

    // 親IDが異なる
    if (curr.parent_id !== snap.parent_id) {
      differences.push(
        `性能「${curr.name}」の親が変更されています（現在: ${curr.parent_id || 'なし'}, 作成時: ${snap.parent_id || 'なし'}）`
      );
    }

    // 単位が異なる
    if (curr.unit !== snap.unit) {
      differences.push(`性能「${curr.name}」の単位が変更されています（現在: ${curr.unit || 'なし'}, 作成時: ${snap.unit || 'なし'}）`);
    }

    // 葉ノードフラグが異なる
    if (curr.is_leaf !== snap.is_leaf) {
      differences.push(`性能「${curr.name}」の葉ノード状態が変更されています`);
    }
  }

  return {
    isMatch: differences.length === 0,
    differences
  };
}

/**
 * 設計案が編集可能かどうか判定
 */
export function isDesignCaseEditable(
  currentPerformances: Performance[],
  snapshotPerformances: Performance[]
): boolean {
  const result = comparePerformanceTrees(currentPerformances, snapshotPerformances);
  return result.isMatch;
}

/**
 * 性能ツリー不一致時の警告メッセージを生成
 */
export function getPerformanceMismatchMessage(
  currentPerformances: Performance[],
  snapshotPerformances: Performance[]
): string {
  const result = comparePerformanceTrees(currentPerformances, snapshotPerformances);
  
  if (result.isMatch) {
    return '';
  }

  return `⚠️ この設計案の作成後に性能ツリーが変更されているため、編集できません。\n\n変更内容:\n${result.differences.map(d => `• ${d}`).join('\n')}`;
}
