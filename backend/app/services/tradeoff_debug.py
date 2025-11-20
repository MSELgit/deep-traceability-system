# backend/app/services/tradeoff_debug.py
# Updated to use the same logic as TradeoffCalculator

from typing import List, Dict
from collections import defaultdict
from itertools import combinations
import json
from .tradeoff_calculator import TradeoffCalculator


def debug_tradeoff_calculation(
    network: Dict,
    performances: List[Dict],
    case_name: str = ""
) -> Dict:
    """
    性能間背反割合の計算をデバッグ
    新しいTradeoffCalculatorのロジックを使用
    """
    # 通常の計算を実行
    result = TradeoffCalculator.calculate_single_case_tradeoff_ratio(
        network,
        performances
    )
    
    # デバッグ情報を追加
    nodes = network.get('nodes', [])
    edges = network.get('edges', [])
    
    print(f"\n=== デバッグ開始: {case_name} ===")
    print(f"ノード数: {len(nodes)}")
    print(f"エッジ数: {len(edges)}")
    
    # 性能ノードのIDを抽出
    performance_node_ids = {
        node['id']: node['performance_id'] 
        for node in nodes 
        if node.get('type') == 'performance' and node.get('performance_id')
    }
    
    print(f"\n性能ノード: {len(performance_node_ids)}")
    for node_id, perf_id in performance_node_ids.items():
        print(f"  - ノードID: {node_id}, 性能ID: {perf_id}")
    
    # 性能IDのリストを取得
    perf_ids = [p['id'] for p in performances if p.get('is_leaf', True)]
    print(f"\nリーフ性能: {len(perf_ids)}")
    for pid in perf_ids:
        print(f"  - {pid}")
    
    # 全性能ペアの組み合わせ
    perf_pairs = list(combinations(perf_ids, 2))
    print(f"\n性能ペア数: {len(perf_pairs)}")
    
    # ノードタイプの集計
    node_types_count = defaultdict(int)
    for node in nodes:
        node_types_count[node.get('type', 'unknown')] += 1
    
    print(f"\nノードタイプ別集計:")
    for ntype, count in node_types_count.items():
        print(f"  - {ntype}: {count}")
    
    # エッジの詳細を表示
    print(f"\nエッジ詳細:")
    edges_by_source = defaultdict(list)
    edges_by_target = defaultdict(list)
    
    for edge in edges:
        edges_by_source[edge['source_id']].append(edge)
        edges_by_target[edge['target_id']].append(edge)
        
        # ソースとターゲットのノードタイプを取得
        source_node = next((n for n in nodes if n['id'] == edge['source_id']), None)
        target_node = next((n for n in nodes if n['id'] == edge['target_id']), None)
        
        if source_node and target_node:
            print(f"  - {source_node.get('type', '?')}({edge['source_id']}) -> {target_node.get('type', '?')}({edge['target_id']}), weight: {edge.get('weight', 'N/A')}")
    
    # 特性ノードを経由する性能間のパスを詳細に調査
    total_paths = 0
    tradeoff_paths = 0
    path_details = []
    
    node_type_dict = {node['id']: node.get('type') for node in nodes}
    
    for perf_id_1, perf_id_2 in perf_pairs:
        # 性能IDに対応するノードIDを探す
        perf_node_1 = None
        perf_node_2 = None
        
        for node_id, perf_id in performance_node_ids.items():
            if perf_id == perf_id_1:
                perf_node_1 = node_id
            elif perf_id == perf_id_2:
                perf_node_2 = node_id
        
        if not perf_node_1 or not perf_node_2:
            print(f"\n性能ペア ({perf_id_1}, {perf_id_2}) のノードが見つかりません")
            continue
        
        print(f"\n性能ペア: {perf_id_1} ({perf_node_1}) <-> {perf_id_2} ({perf_node_2})")
        
        # 両方向のパスを探す
        pair_paths = []
        
        # 順方向: perf1 -> property -> perf2
        for edge1 in edges_by_source.get(perf_node_1, []):
            property_node = edge1['target_id']
            
            if node_type_dict.get(property_node) != 'property':
                continue
            
            for edge2 in edges_by_source.get(property_node, []):
                if edge2['target_id'] == perf_node_2:
                    weight1 = edge1.get('weight', 1.0)
                    weight2 = edge2.get('weight', 1.0)
                    is_tradeoff = (weight1 * weight2) < 0
                    
                    path_info = {
                        'type': 'forward',
                        'path': f"{perf_node_1} -({weight1})-> {property_node} -({weight2})-> {perf_node_2}",
                        'property_node': property_node,
                        'weight1': weight1,
                        'weight2': weight2,
                        'is_tradeoff': is_tradeoff
                    }
                    pair_paths.append(path_info)
                    print(f"  - 順方向パス: {path_info['path']}, 背反: {is_tradeoff}")
        
        # 逆方向: property -> perf1 and property -> perf2
        for edge1 in edges_by_target.get(perf_node_1, []):
            property_node = edge1['source_id']
            
            if node_type_dict.get(property_node) != 'property':
                continue
            
            for edge2 in edges_by_target.get(perf_node_2, []):
                if edge2['source_id'] == property_node:
                    weight1 = edge1.get('weight', 1.0)
                    weight2 = edge2.get('weight', 1.0)
                    is_tradeoff = (weight1 * weight2) < 0
                    
                    # 重複チェック
                    duplicate = False
                    for existing_path in pair_paths:
                        if existing_path['property_node'] == property_node:
                            duplicate = True
                            break
                    
                    if not duplicate:
                        path_info = {
                            'type': 'reverse',
                            'path': f"{property_node} -({weight1})-> {perf_node_1} & {property_node} -({weight2})-> {perf_node_2}",
                            'property_node': property_node,
                            'weight1': weight1,
                            'weight2': weight2,
                            'is_tradeoff': is_tradeoff
                        }
                        pair_paths.append(path_info)
                        print(f"  - 逆方向パス: {path_info['path']}, 背反: {is_tradeoff}")
        
        for path in pair_paths:
            total_paths += 1
            if path['is_tradeoff']:
                tradeoff_paths += 1
            path_details.append(path)
    
    print(f"\n=== 集計結果 ===")
    print(f"総パス数: {total_paths}")
    print(f"背反パス数: {tradeoff_paths}")
    if total_paths > 0:
        print(f"背反割合: {tradeoff_paths / total_paths:.3f}")
    else:
        print("背反割合: N/A (パスなし)")
    
    # 新しいロジックの結果とデバッグ情報を統合
    return {
        'case_name': case_name,
        'node_count': len(nodes),
        'edge_count': len(edges),
        'performance_nodes': len(performance_node_ids),
        'leaf_performances': len(perf_ids),
        'performance_pairs': len(perf_pairs),
        'total_paths': result['total_paths'],  # 新しいロジックの結果を使用
        'tradeoff_paths': result['tradeoff_paths'],
        'ratio': result['ratio'],
        'is_valid': result['is_valid'],
        'path_details': path_details,  # デバッグ用の詳細情報
        'node_types': dict(node_types_count)
    }


if __name__ == "__main__":
    # テスト用
    pass