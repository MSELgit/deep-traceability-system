#!/usr/bin/env python3
"""
JSONファイルのネットワークデータでデータベースの設計案を更新するスクリプト
"""

import json
import sqlite3
from datetime import datetime

def convert_json_to_network_structure(json_data):
    """
    JSONファイルの形式をデータベースのnetwork_json形式に変換
    """
    nodes = []
    edges = []
    
    # 正しい性能ノード22個（基本設計案と同じ順序）
    performance_names = [
        "Accuracy", "Carbon Footprint", "Community Burden", "Convenience",
        "Cost Efficiency", "Coverage Performance", "Customer Support", 
        "Environmental Compliance", "Inclusivity", "Information Security",
        "Investment Requirements", "Loading Performance", "Operational Safety",
        "Package Protection", "Price Competitiveness", "Reliability",
        "Resource Efficiency", "Scalability", "Service Diversity", 
        "Speed Performance", "Transparency", "Worker Welfare"
    ]
    
    # 性能ノードの座標配置（6列x4行）
    for i, perf_name in enumerate(performance_names):
        node = {
            "id": f"perf-{i}",
            "layer": 1,
            "type": "performance", 
            "label": perf_name,
            "x": 100.0 + (i % 6) * 180.0,
            "y": 100.0 + (i // 6) * 80.0,
            "performance_id": f"perf-{i}"
        }
        nodes.append(node)
    
    # JSONからnodesを変換（性能ノード以外のみ）
    node_counter = 0
    for json_node in json_data.get("nodes", []):
        # 層ごとの適切な座標配置
        if json_node["layer"] == 2:  # property
            base_x, base_y = 100.0, 350.0
        elif json_node["layer"] == 3:  # variable  
            base_x, base_y = 100.0, 450.0
        elif json_node["layer"] == 4:  # object/environment
            base_x, base_y = 100.0, 550.0
        else:
            base_x, base_y = 100.0, 300.0
        
        node = {
            "id": f"node-{node_counter}",
            "layer": json_node["layer"],
            "type": json_node["type"],
            "label": json_node["label"],
            "x": base_x + (node_counter % 8) * 150.0,
            "y": base_y + (node_counter // 8) * 60.0,
            "performance_id": None
        }
        if "note" in json_node:
            node["note"] = json_node["note"]
        nodes.append(node)
        node_counter += 1
    
    # JSONからedgesを変換
    for json_edge in json_data.get("edges", []):
        # sourceとtargetのノードIDを検索
        source_node = None
        target_node = None
        
        for node in nodes:
            if node["label"] == json_edge["source"]:
                source_node = node
            if node["label"] == json_edge["target"]:
                target_node = node
        
        if source_node and target_node:
            edge = {
                "id": f"edge-{len(edges)}",
                "source_id": source_node["id"],
                "target_id": target_node["id"], 
                "type": "type1",
                "weight": json_edge.get("weight")
            }
            if "note" in json_edge:
                edge["note"] = json_edge["note"]
            edges.append(edge)
    
    return {"nodes": nodes, "edges": edges}

def update_design_case_network(db_path, design_name, json_file_path):
    """
    指定された設計案のネットワークデータを更新
    """
    # JSONファイルを読み込み
    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # ネットワーク構造に変換
    network_structure = convert_json_to_network_structure(json_data)
    
    # データベース接続
    conn = sqlite3.connect(db_path)
    
    try:
        # 設計案を検索
        cursor = conn.execute(
            "SELECT id FROM design_cases WHERE name = ?", 
            (design_name,)
        )
        result = cursor.fetchone()
        
        if not result:
            print(f"設計案 '{design_name}' が見つかりません")
            return False
        
        design_id = result[0]
        
        # ネットワークデータを更新
        conn.execute(
            "UPDATE design_cases SET network_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(network_structure, ensure_ascii=False), datetime.now().isoformat(), design_id)
        )
        
        conn.commit()
        print(f"設計案 '{design_name}' のネットワークを更新しました")
        print(f"  ノード数: {len(network_structure['nodes'])}")
        print(f"  エッジ数: {len(network_structure['edges'])}")
        return True
        
    except Exception as e:
        print(f"エラー: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # データベースパス
    db_path = "data/local.db"
    
    # 更新対象の設計案とJSONファイル
    updates = [
        ("Smart Locker Integration System - Adjacent Storage", "outputs/AdjacentStorage.json"),
        ("Smart Locker Integration System - Modular Partition", "outputs/ModularPartition.json"), 
        ("Smart Locker Integration System - Simple Size Upgrade", "outputs/SimpleSizeUpgrade.json")
    ]
    
    for design_name, json_file in updates:
        print(f"\n=== {design_name} の更新 ===")
        success = update_design_case_network(db_path, design_name, json_file)
        if not success:
            print(f"失敗: {design_name}")