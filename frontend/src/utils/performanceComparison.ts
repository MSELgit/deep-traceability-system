// frontend/src/utils/performanceComparison.ts

import type { Performance } from '../types/project';

/**
 * Create a structural signature for a performance that doesn't depend on ID
 */
function createPerformanceSignature(perf: Performance, allPerformances: Performance[]): string {
  // Build parent path (names from root to this performance)
  const parentPath: string[] = [];
  let currentParentId = perf.parent_id;
  
  while (currentParentId) {
    const parent = allPerformances.find(p => p.id === currentParentId);
    if (parent) {
      parentPath.unshift(parent.name);
      currentParentId = parent.parent_id;
    } else {
      break;
    }
  }
  
  // Create signature: parentPath/name/level/unit/is_leaf
  return `${parentPath.join('/')}/${perf.name}/${perf.level}/${perf.unit || 'none'}/${perf.is_leaf}`;
}

/**
 * Compare two performance trees based on structure, not IDs
 * Names, parent-child relationships, levels, units, and leaf status must match
 */
export function comparePerformanceTrees(
  current: Performance[],
  snapshot: Performance[]
): { isMatch: boolean; differences: string[] } {
  const differences: string[] = [];

  // Check performance count
  if (current.length !== snapshot.length) {
    differences.push(`Number of performances differs (Current: ${current.length}, Snapshot: ${snapshot.length})`);
    return { isMatch: false, differences };
  }

  // Create structural signatures for all performances
  const currentSignatures = new Map<string, Performance>();
  const snapshotSignatures = new Map<string, Performance>();
  
  current.forEach(perf => {
    const signature = createPerformanceSignature(perf, current);
    currentSignatures.set(signature, perf);
  });
  
  snapshot.forEach(perf => {
    const signature = createPerformanceSignature(perf, snapshot);
    snapshotSignatures.set(signature, perf);
  });
  
  // Check if all current signatures exist in snapshot
  for (const [signature, perf] of currentSignatures) {
    if (!snapshotSignatures.has(signature)) {
      differences.push(`Performance "${perf.name}" structure has changed or been removed`);
    }
  }
  
  // Check if all snapshot signatures exist in current
  for (const [signature, perf] of snapshotSignatures) {
    if (!currentSignatures.has(signature)) {
      differences.push(`Performance "${perf.name}" from snapshot not found in current tree`);
    }
  }
  
  // Additional check: Ensure leaf performances maintain their IDs for value mapping
  // This creates a mapping between old and new IDs
  const idMapping = new Map<string, string>(); // snapshot ID -> current ID
  
  for (const [signature, currentPerf] of currentSignatures) {
    const snapshotPerf = snapshotSignatures.get(signature);
    if (snapshotPerf && currentPerf.is_leaf) {
      idMapping.set(snapshotPerf.id, currentPerf.id);
    }
  }

  return {
    isMatch: differences.length === 0,
    differences
  };
}

/**
 * Check if a design case is editable
 * Now based on structural comparison, not ID comparison
 */
export function isDesignCaseEditable(
  currentPerformances: Performance[],
  snapshotPerformances: Performance[]
): boolean {
  const result = comparePerformanceTrees(currentPerformances, snapshotPerformances);
  return result.isMatch;
}

/**
 * Generate warning message for performance tree mismatch
 */
export function getPerformanceMismatchMessage(
  currentPerformances: Performance[],
  snapshotPerformances: Performance[]
): string {
  const result = comparePerformanceTrees(currentPerformances, snapshotPerformances);
  
  if (result.isMatch) {
    return '';
  }

  return `⚠️ Cannot edit this design case because the performance tree structure has changed.\n\nChanges:\n${result.differences.map(d => `• ${d}`).join('\n')}`;
}

/**
 * Create ID mapping between snapshot and current performances
 * This is useful when we need to map old performance values to new IDs
 */
export function createPerformanceIdMapping(
  currentPerformances: Performance[],
  snapshotPerformances: Performance[]
): Map<string, string> {
  const idMapping = new Map<string, string>(); // snapshot ID -> current ID
  
  // Create signature maps
  const currentSignatures = new Map<string, Performance>();
  const snapshotSignatures = new Map<string, Performance>();
  
  currentPerformances.forEach(perf => {
    const signature = createPerformanceSignature(perf, currentPerformances);
    currentSignatures.set(signature, perf);
  });
  
  snapshotPerformances.forEach(perf => {
    const signature = createPerformanceSignature(perf, snapshotPerformances);
    snapshotSignatures.set(signature, perf);
  });
  
  // Map IDs for matching signatures
  for (const [signature, snapshotPerf] of snapshotSignatures) {
    const currentPerf = currentSignatures.get(signature);
    if (currentPerf) {
      idMapping.set(snapshotPerf.id, currentPerf.id);
    }
  }
  
  return idMapping;
}

/**
 * Remap performance IDs in network structure
 * Updates performance_id fields in nodes based on ID mapping
 */
export function remapNetworkPerformanceIds(
  network: { nodes: any[], edges: any[] },
  idMapping: Map<string, string>,
  reverse: boolean = false
): { nodes: any[], edges: any[] } {
  // Deep clone the network to avoid modifying the original
  const clonedNetwork = JSON.parse(JSON.stringify(network));
  
  // Remap performance_id in nodes
  clonedNetwork.nodes.forEach((node: any) => {
    if (node.performance_id) {
      const mappedId = reverse 
        ? Array.from(idMapping.entries()).find(([_, curr]) => curr === node.performance_id)?.[0]
        : idMapping.get(node.performance_id);
      
      if (mappedId) {
        node.performance_id = mappedId;
      }
    }
  });
  
  return clonedNetwork;
}