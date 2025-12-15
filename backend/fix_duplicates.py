#!/usr/bin/env python3
"""
重複した性能ノードを修正するスクリプト
"""

import json
import sqlite3
from datetime import datetime

def fix_duplicate_performance_nodes(db_path, design_name):
    """
    重複した性能ノードを削除し、正しいネットワーク構造に修正
    """
    conn = sqlite3.connect(db_path)
    
    try:
        # 現在のネットワークを取得
        result = conn.execute(
            "SELECT network_json FROM design_cases WHERE name = ?", 
            (design_name,)
        ).fetchone()
        
        if not result:
            print(f"設計案 '{design_name}' が見つかりません")
            return False
        
        network = json.loads(result[0])
        
        # 性能ノードを分析
        perf_nodes = [n for n in network['nodes'] if n['type'] == 'performance']
        other_nodes = [n for n in network['nodes'] if n['type'] != 'performance']
        
        print(f"修正前: 性能ノード {len(perf_nodes)}個, その他 {len(other_nodes)}個")
        
        # 重複を除去（最初に見つかったもののみ保持）
        seen_labels = set()
        unique_perf_nodes = []
        
        for node in perf_nodes:
            if node['label'] not in seen_labels:
                unique_perf_nodes.append(node)
                seen_labels.add(node['label'])
        
        # 新しいノードリストを作成
        new_nodes = unique_perf_nodes + other_nodes
        
        # エッジを修正（削除された性能ノードを参照しているものを更新）
        valid_node_ids = {n['id'] for n in new_nodes}
        valid_edges = []
        
        for edge in network['edges']:
            if edge['source_id'] in valid_node_ids and edge['target_id'] in valid_node_ids:
                valid_edges.append(edge)
            else:
                print(f"削除されたエッジ: {edge['source_id']} -> {edge['target_id']}")
        
        # 新しいネットワーク構造
        fixed_network = {
            "nodes": new_nodes,
            "edges": valid_edges
        }
        
        print(f"修正後: 性能ノード {len(unique_perf_nodes)}個, その他 {len(other_nodes)}個, エッジ {len(valid_edges)}個")
        
        # データベースを更新
        conn.execute(
            "UPDATE design_cases SET network_json = ?, updated_at = ? WHERE name = ?",
            (json.dumps(fixed_network, ensure_ascii=False), datetime.now().isoformat(), design_name)
        )
        
        conn.commit()
        print(f"修正完了: {design_name}")
        return True
        
    except Exception as e:
        print(f"エラー: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = "data/local.db"
    
    # 3つの改善設計案の重複を修正
    designs = [
        "Smart Locker Integration System - Adjacent Storage",
        "Smart Locker Integration System - Modular Partition",
        "Smart Locker Integration System - Simple Size Upgrade"
    ]
    
    for design_name in designs:
        print(f"\n=== {design_name} の修正 ===")
        fix_duplicate_performance_nodes(db_path, design_name)