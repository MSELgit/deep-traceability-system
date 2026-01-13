# backend/app/services/scc_analyzer.py
"""
強連結成分（SCC）分解によるループ検出と解析

論文 design.tex 2398-2469行に基づく実装:
- Tarjanアルゴリズムによる O(|V| + |E|) のSCC検出
- ループ内の収束条件（スペクトル半径）チェック
- ループ解消方法の提案生成
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

# 統一重み正規化モジュールをインポート
from app.services.weight_normalization import discrete_to_continuous as _normalize_weight


class LoopResolutionType(str, Enum):
    """ループ解消方法のタイプ"""
    EDGE_REMOVAL = "edge_removal"       # エッジ削除（因果方向の再検討）
    NODE_MERGE = "node_merge"           # ノード統合（代表属性への縮約）
    CONSTRAINT = "constraint"           # 拘束条件として分離
    CONVERGENT = "convergent"           # 収束するループ（Neumann級数で処理可能）


@dataclass
class SCCComponent:
    """強連結成分の情報"""
    nodes: List[str]
    edges: List[Tuple[str, str]]  # (source, target) のリスト
    spectral_radius: Optional[float]
    converges: bool
    suggestions: List[Dict[str, Any]]


@dataclass
class SCCAnalysisResult:
    """SCC分解の結果"""
    has_loops: bool
    components: List[SCCComponent]
    all_nodes: List[str]
    dag_after_condensation: List[Tuple[int, int]]  # 縮約後のDAG


class TarjanSCC:
    """Tarjanのアルゴリズムによる強連結成分分解"""

    def __init__(self, graph: Dict[str, List[str]]):
        """
        Args:
            graph: 隣接リスト形式のグラフ {node: [neighbors]}
        """
        self.graph = graph
        self.index_counter = 0
        self.stack: List[str] = []
        self.lowlink: Dict[str, int] = {}
        self.index: Dict[str, int] = {}
        self.on_stack: Dict[str, bool] = {}
        self.sccs: List[List[str]] = []

    def find_sccs(self) -> List[List[str]]:
        """全ての強連結成分を検出"""
        for node in self.graph:
            if node not in self.index:
                self._strongconnect(node)
        return self.sccs

    def _strongconnect(self, node: str):
        """Tarjanの再帰関数"""
        self.index[node] = self.index_counter
        self.lowlink[node] = self.index_counter
        self.index_counter += 1
        self.stack.append(node)
        self.on_stack[node] = True

        # 隣接ノードを探索
        for neighbor in self.graph.get(node, []):
            if neighbor not in self.index:
                # まだ訪問していない
                self._strongconnect(neighbor)
                self.lowlink[node] = min(self.lowlink[node], self.lowlink[neighbor])
            elif self.on_stack.get(neighbor, False):
                # スタック上にある = 同じSCCの可能性
                self.lowlink[node] = min(self.lowlink[node], self.index[neighbor])

        # ルートノードの場合、SCCを出力
        if self.lowlink[node] == self.index[node]:
            scc = []
            while True:
                w = self.stack.pop()
                self.on_stack[w] = False
                scc.append(w)
                if w == node:
                    break
            self.sccs.append(scc)


def build_attribute_graph(network: Dict) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """
    ネットワークからAttribute層（Layer 2）のグラフを構築

    Args:
        network: ネットワーク構造 {nodes: [...], edges: [...]}

    Returns:
        (adjacency_list, node_labels): 隣接リストとノードラベルのマッピング
    """
    nodes = network.get('nodes', [])
    edges = network.get('edges', [])

    # Layer 2（Property/Attribute）のノードを抽出
    attr_nodes = {}
    for node in nodes:
        if node.get('layer') == 2:
            attr_nodes[node['id']] = node.get('label', node['id'])

    # Attribute間のエッジを抽出（type2 = A→A）
    graph: Dict[str, List[str]] = {node_id: [] for node_id in attr_nodes}

    for edge in edges:
        source = edge.get('source_id')
        target = edge.get('target_id')

        # 両方がAttributeノードの場合のみ
        if source in attr_nodes and target in attr_nodes:
            graph[source].append(target)

    return graph, attr_nodes


def compute_local_spectral_radius(
    network: Dict,
    scc_nodes: List[str]
) -> float:
    """
    SCC内の部分行列のスペクトル半径を計算

    Args:
        network: ネットワーク構造
        scc_nodes: SCC内のノードID

    Returns:
        スペクトル半径 ρ(B_AA^(C_k))
    """
    if len(scc_nodes) < 2:
        return 0.0

    edges = network.get('edges', [])

    # ノードIDからインデックスへのマッピング
    node_to_idx = {node_id: idx for idx, node_id in enumerate(scc_nodes)}
    n = len(scc_nodes)

    # 部分行列を構築
    B_AA_local = np.zeros((n, n))

    for edge in edges:
        source = edge.get('source_id')
        target = edge.get('target_id')
        weight = edge.get('weight', 0)

        if source in node_to_idx and target in node_to_idx:
            i = node_to_idx[target]  # 行: target（影響を受ける側）
            j = node_to_idx[source]  # 列: source（影響を与える側）
            # 離散値を連続値に変換
            continuous_weight = _discrete_to_continuous(weight)
            B_AA_local[i, j] = continuous_weight

    # スペクトル半径を計算
    try:
        eigenvalues = np.linalg.eigvals(B_AA_local)
        spectral_radius = float(np.max(np.abs(eigenvalues)))
    except np.linalg.LinAlgError:
        spectral_radius = float('inf')

    return spectral_radius


def _discrete_to_continuous(weight: float, mode: str = 'discrete_7') -> float:
    """
    離散値エッジ重みを連続値に変換

    統一重み正規化モジュールを使用。
    デフォルトは7段階モード（SCC分析は最も細かい離散化を想定）。

    Args:
        weight: エッジの重み
        mode: 離散化モード（'discrete_3', 'discrete_5', 'discrete_7', 'continuous'）

    Returns:
        連続値 [-1, 1]
    """
    if weight is None:
        return 0.0
    return _normalize_weight(weight, mode)


def generate_resolution_suggestions(
    network: Dict,
    scc_nodes: List[str],
    spectral_radius: float
) -> List[Dict[str, Any]]:
    """
    ループ解消方法の提案を生成

    論文 design.tex 2428-2463行に基づく提案:
    1. 因果方向の再検討（エッジ削除）
    2. 代表属性への縮約（ノード統合）
    3. 拘束条件として分離
    4. 収束するループとして処理
    """
    suggestions = []
    edges = network.get('edges', [])
    nodes = network.get('nodes', [])

    # ノードラベルのマッピング
    node_labels = {n['id']: n.get('label', n['id']) for n in nodes}

    # SCC内のエッジを抽出
    scc_set = set(scc_nodes)
    internal_edges = []
    for edge in edges:
        source = edge.get('source_id')
        target = edge.get('target_id')
        if source in scc_set and target in scc_set:
            internal_edges.append((source, target, edge.get('weight', 0)))

    # 提案1: 収束するループの場合
    if spectral_radius < 1.0:
        suggestions.append({
            "type": LoopResolutionType.CONVERGENT,
            "description": f"このループはスペクトル半径 ρ = {spectral_radius:.3f} < 1 のため収束します。Neumann級数展開で処理可能です。",
            "priority": 1,
            "action_required": False
        })

    # 提案2: エッジ削除（最も弱い因果関係を候補に）
    if internal_edges:
        # 重みの絶対値が最小のエッジを候補に
        weakest_edge = min(internal_edges, key=lambda e: abs(e[2]) if e[2] else 0)
        source_label = node_labels.get(weakest_edge[0], weakest_edge[0])
        target_label = node_labels.get(weakest_edge[1], weakest_edge[1])

        suggestions.append({
            "type": LoopResolutionType.EDGE_REMOVAL,
            "description": f"因果関係 '{source_label}' → '{target_label}' の削除を検討してください（重み: {weakest_edge[2]}）",
            "edge": [weakest_edge[0], weakest_edge[1]],
            "edge_labels": [source_label, target_label],
            "priority": 2 if spectral_radius >= 1.0 else 3,
            "action_required": spectral_radius >= 1.0
        })

    # 提案3: ノード統合
    if len(scc_nodes) >= 2:
        node_labels_list = [node_labels.get(n, n) for n in scc_nodes]
        suggestions.append({
            "type": LoopResolutionType.NODE_MERGE,
            "description": f"ノード群 {node_labels_list} を単一の代表属性に統合することを検討してください",
            "nodes": scc_nodes,
            "node_labels": node_labels_list,
            "priority": 3 if spectral_radius >= 1.0 else 4,
            "action_required": False
        })

    # 提案4: 拘束条件として分離（物理的保存則の可能性）
    if len(scc_nodes) == 2:
        suggestions.append({
            "type": LoopResolutionType.CONSTRAINT,
            "description": "2ノード間の双方向関係は物理的な拘束条件（保存則等）を表している可能性があります。因果ネットワークから切り離し、別途扱うことを検討してください。",
            "nodes": scc_nodes,
            "priority": 4,
            "action_required": False
        })

    # 優先度でソート
    suggestions.sort(key=lambda x: x.get('priority', 99))

    return suggestions


def analyze_scc(network: Dict) -> SCCAnalysisResult:
    """
    ネットワークのSCC分解を実行し、ループ構造を分析

    Args:
        network: ネットワーク構造 {nodes: [...], edges: [...]}

    Returns:
        SCCAnalysisResult: 分析結果
    """
    # Attribute層のグラフを構築
    graph, node_labels = build_attribute_graph(network)

    if not graph:
        return SCCAnalysisResult(
            has_loops=False,
            components=[],
            all_nodes=[],
            dag_after_condensation=[]
        )

    # Tarjanのアルゴリズムでscc検出
    tarjan = TarjanSCC(graph)
    sccs = tarjan.find_sccs()

    # ループを含むSCC（|C| >= 2）を抽出
    components = []
    has_loops = False

    for scc_nodes in sccs:
        if len(scc_nodes) >= 2:
            has_loops = True

            # SCC内のエッジを抽出
            scc_set = set(scc_nodes)
            edges = network.get('edges', [])
            internal_edges = []
            for edge in edges:
                source = edge.get('source_id')
                target = edge.get('target_id')
                if source in scc_set and target in scc_set:
                    internal_edges.append((source, target))

            # スペクトル半径を計算
            spectral_radius = compute_local_spectral_radius(network, scc_nodes)
            converges = spectral_radius < 1.0

            # 解消方法の提案を生成
            suggestions = generate_resolution_suggestions(
                network, scc_nodes, spectral_radius
            )

            component = SCCComponent(
                nodes=scc_nodes,
                edges=internal_edges,
                spectral_radius=spectral_radius,
                converges=converges,
                suggestions=suggestions
            )
            components.append(component)

    # 縮約後のDAGを構築（SCC間の関係）
    scc_map = {}  # node_id -> scc_index
    for idx, scc_nodes in enumerate(sccs):
        for node in scc_nodes:
            scc_map[node] = idx

    dag_edges = set()
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            src_scc = scc_map.get(node)
            dst_scc = scc_map.get(neighbor)
            if src_scc is not None and dst_scc is not None and src_scc != dst_scc:
                dag_edges.add((src_scc, dst_scc))

    return SCCAnalysisResult(
        has_loops=has_loops,
        components=components,
        all_nodes=list(node_labels.keys()),
        dag_after_condensation=list(dag_edges)
    )


def scc_result_to_dict(result: SCCAnalysisResult) -> Dict[str, Any]:
    """SCCAnalysisResultを辞書形式に変換（API用）"""
    return {
        "has_loops": result.has_loops,
        "n_components_with_loops": len(result.components),
        "components": [
            {
                "nodes": comp.nodes,
                "edges": [{"source": e[0], "target": e[1]} for e in comp.edges],
                "spectral_radius": comp.spectral_radius,
                "converges": comp.converges,
                "suggestions": comp.suggestions
            }
            for comp in result.components
        ],
        "all_attribute_nodes": result.all_nodes,
        "dag_after_condensation": [
            {"from_scc": e[0], "to_scc": e[1]}
            for e in result.dag_after_condensation
        ]
    }
