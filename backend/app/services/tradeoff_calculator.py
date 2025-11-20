# backend/app/services/tradeoff_calculator.py

from typing import List, Dict
from collections import defaultdict
from itertools import combinations


class TradeoffCalculator:
    """性能間背反割合を計算するクラス"""
    
    @staticmethod
    def calculate_performance_tradeoff_ratio(
        design_cases: List[Dict],
        performances: List[Dict]
    ) -> Dict[str, Dict]:
        """
        全設計ケースについて性能間背反割合を計算
        
        Args:
            design_cases: 設計ケースのリスト（network_jsonを含む）
            performances: 性能のリスト
        
        Returns:
            設計ケースIDをキーとした結果の辞書
            {
                case_id: {
                    'ratio': float,  # 背反割合 (0.0-1.0、またはNaN)
                    'total_paths': int,  # 総パス数
                    'tradeoff_paths': int,  # 背反パス数
                    'is_valid': bool  # 有効な計算結果か
                }
            }
        """
        
        results = {}
        
        for case in design_cases:
            result = TradeoffCalculator.calculate_single_case_tradeoff_ratio(
                case['network'],
                performances
            )
            results[case['id']] = result
            
        return results
    
    @staticmethod
    def calculate_single_case_tradeoff_ratio(
        network: Dict,
        performances: List[Dict]
    ) -> Dict:
        """
        単一の設計ケースの性能間背反割合を計算
        
        Args:
            network: ネットワーク構造（nodes, edges）
            performances: 性能のリスト
        
        Returns:
            {
                'ratio': float,  # 背反割合
                'total_paths': int,  # 総パス数
                'tradeoff_paths': int,  # 背反パス数
                'is_valid': bool  # 有効な計算結果か
            }
        """
        nodes = network.get('nodes', [])
        edges = network.get('edges', [])
        
        # 性能ノードのIDを抽出
        performance_node_ids = {}
        for node in nodes:
            if node.get('type') == 'performance':
                perf_id = node.get('performance_id', node['id'])
                performance_node_ids[node['id']] = perf_id
        
        # 性能IDのリストを取得
        perf_ids = [p['id'] for p in performances if p.get('is_leaf', True)]
        
        
        # ネットワーク内の性能IDを使用してペアを作成
        # リーフ性能だけでなく、ネットワーク内の全ての性能ノードを対象とする
        network_perf_ids = list(set(performance_node_ids.values()))
        perf_pairs = list(combinations(network_perf_ids, 2))
        
        if not perf_pairs:
            return {
                'ratio': 0.0,
                'total_paths': 0,
                'tradeoff_paths': 0,
                'is_valid': False
            }
        
        total_paths = 0
        tradeoff_paths = 0
        
        # 各性能ペアについて分析
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
                continue
            
            # 両方の性能に接続する特性を探す
            paths = TradeoffCalculator.find_paths_through_properties(
                perf_node_1, perf_node_2, nodes, edges
            )
            
            
            for path_info in paths:
                total_paths += 1
                if path_info['is_tradeoff']:
                    tradeoff_paths += 1
        
        # 結果をまとめる
        if total_paths == 0:
            # パスが存在しない場合
            return {
                'ratio': 0.0,
                'total_paths': 0,
                'tradeoff_paths': 0,
                'is_valid': False  # 無効な結果として扱う
            }
        
        # 背反割合を計算
        ratio = tradeoff_paths / total_paths
        
        return {
            'ratio': ratio,
            'total_paths': total_paths,
            'tradeoff_paths': tradeoff_paths,
            'is_valid': True
        }
    
    @staticmethod
    def find_paths_through_properties(
        perf_node_1: str,
        perf_node_2: str,
        nodes: List[Dict],
        edges: List[Dict]
    ) -> List[Dict]:
        """
        2つの性能ノード間を特性を介して結ぶパスを探す
        
        特定の性能ペア(perf_node_1, perf_node_2)間のパスのみを返す
        
        Returns:
            パス情報のリスト。各パス情報は {
                'property_node': str,
                'edge1_weight': float,
                'edge2_weight': float,
                'is_tradeoff': bool
            }
        """
        paths = []
        
        # エッジを効率的に検索するための辞書を作成
        edges_by_source = defaultdict(list)
        edges_by_target = defaultdict(list)
        
        for edge in edges:
            edges_by_source[edge['source_id']].append(edge)
            edges_by_target[edge['target_id']].append(edge)
        
        # ノードタイプの辞書を作成
        node_types = {node['id']: node['type'] for node in nodes}
        
        # perf_node_1から出るエッジを探す
        for edge1 in edges_by_source.get(perf_node_1, []):
            property_node = edge1['target_id']
            
            # 特性ノードかチェック
            if node_types.get(property_node) != 'property':
                continue
            
            # property_nodeからperf_node_2へのエッジを探す
            for edge2 in edges_by_source.get(property_node, []):
                if edge2['target_id'] == perf_node_2:
                    weight1 = edge1.get('weight', 1.0)
                    weight2 = edge2.get('weight', 1.0)
                    
                    # 符号が逆なら背反
                    is_tradeoff = (weight1 * weight2) < 0
                    
                    paths.append({
                        'property_node': property_node,
                        'edge1_weight': weight1,
                        'edge2_weight': weight2,
                        'is_tradeoff': is_tradeoff
                    })
        
        # 逆方向のパスも考慮（特性→性能の場合）
        # 特性 -> 性能1 かつ 特性 -> 性能2
        for edge1 in edges_by_target.get(perf_node_1, []):
            property_node = edge1['source_id']
            
            if node_types.get(property_node) != 'property':
                continue
            
            for edge2 in edges_by_target.get(perf_node_2, []):
                if edge2['source_id'] == property_node:
                    weight1 = edge1.get('weight', 1.0)
                    weight2 = edge2.get('weight', 1.0)
                    
                    is_tradeoff = (weight1 * weight2) < 0
                    
                    paths.append({
                        'property_node': property_node,
                        'edge1_weight': weight1,
                        'edge2_weight': weight2,
                        'is_tradeoff': is_tradeoff,
                        'pattern': 'prop->perf1 & prop->perf2'
                    })
        
        # 混合パターン1: 性能1 -> 特性 かつ 特性 -> 性能2
        # このパターンは既に順方向で処理されているのでスキップ
                    
        # 混合パターン2: 特性 -> 性能1 かつ 性能2 -> 特性
        for edge1 in edges_by_target.get(perf_node_1, []):
            property_node = edge1['source_id']
            
            if node_types.get(property_node) != 'property':
                continue
                
            for edge2 in edges_by_source.get(perf_node_2, []):
                if edge2['target_id'] == property_node:
                    weight1 = edge1.get('weight', 1.0)
                    weight2 = edge2.get('weight', 1.0)
                    
                    is_tradeoff = (weight1 * weight2) < 0
                    
                    paths.append({
                        'property_node': property_node,
                        'edge1_weight': weight1,
                        'edge2_weight': weight2,
                        'is_tradeoff': is_tradeoff,
                        'pattern': 'prop->perf1 & perf2->prop'
                    })
        
        return paths