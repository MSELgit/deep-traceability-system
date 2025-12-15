#!/usr/bin/env python3
"""
改善設計案の性能ノードのperformance_idを基本設計案と同じにするスクリプト
"""

import json
import sqlite3
from datetime import datetime

def fix_performance_ids(db_path):
    """
    改善設計案の性能ノードのperformance_idを基本設計案と同じにする
    """
    conn = sqlite3.connect(db_path)
    
    try:
        # 基本設計案の性能ノードのマッピングを取得
        base_result = conn.execute(
            "SELECT network_json FROM design_cases WHERE name = ?", 
            ('Smart Locker Integration System',)
        ).fetchone()
        
        if not base_result:
            print("基本設計案が見つかりません")
            return False
        
        base_network = json.loads(base_result[0])
        base_perf_nodes = [n for n in base_network['nodes'] if n['type'] == 'performance']
        
        # ラベルからperformance_idへのマッピングを作成
        label_to_perf_id = {}
        for node in base_perf_nodes:
            label_to_perf_id[node['label']] = node['performance_id']
        
        print(f"基本設計案から{len(label_to_perf_id)}個の性能マッピングを取得")
        
        # 改善設計案を修正
        improvement_designs = [
            'Smart Locker Integration System - Adjacent Storage',
            'Smart Locker Integration System - Modular Partition',
            'Smart Locker Integration System - Simple Size Upgrade'
        ]
        
        for design_name in improvement_designs:
            result = conn.execute(
                "SELECT network_json FROM design_cases WHERE name = ?",
                (design_name,)
            ).fetchone()
            
            if not result:
                print(f"設計案 '{design_name}' が見つかりません")
                continue
            
            network = json.loads(result[0])
            
            # 性能ノードのperformance_idを修正
            fixed_count = 0
            for node in network['nodes']:
                if node['type'] == 'performance':
                    label = node['label']
                    if label in label_to_perf_id:
                        old_perf_id = node.get('performance_id')
                        new_perf_id = label_to_perf_id[label]
                        node['performance_id'] = new_perf_id
                        
                        # node_idも修正（performance_idと同じにする）
                        old_node_id = node['id']
                        new_node_id = f"perf-{new_perf_id}"
                        node['id'] = new_node_id
                        
                        # エッジの参照も更新
                        for edge in network['edges']:
                            if edge['source_id'] == old_node_id:
                                edge['source_id'] = new_node_id
                            if edge['target_id'] == old_node_id:
                                edge['target_id'] = new_node_id
                        
                        fixed_count += 1
                        
                        print(f"  {label}: {old_perf_id} -> {new_perf_id}")
                    else:
                        print(f"  警告: {label} のマッピングが見つかりません")
            
            # データベースを更新
            conn.execute(
                "UPDATE design_cases SET network_json = ?, updated_at = ? WHERE name = ?",
                (json.dumps(network, ensure_ascii=False), datetime.now().isoformat(), design_name)
            )
            
            print(f"{design_name}: {fixed_count}個の性能ノードを修正")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"エラー: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = "data/local.db"
    
    print("=== 性能ノードのperformance_ID修正 ===")
    success = fix_performance_ids(db_path)
    
    if success:
        print("\n修正が完了しました。エネルギー計算が正常に動作するはずです。")
    else:
        print("\n修正に失敗しました。")