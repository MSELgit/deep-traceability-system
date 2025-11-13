# backend/fix_factor_nodes.py
import sqlite3
import json
import os

# データベースファイルのパス
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'local.db')

def fix_factor_nodes():
    print(f"データベース: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ データベースファイルが見つかりません: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 設計案を取得
    cursor.execute("SELECT id, name, network_json FROM design_cases WHERE network_json IS NOT NULL")
    design_cases = cursor.fetchall()
    
    print(f"\n=== 全{len(design_cases)}件の設計案をチェック中 ===\n")
    
    updated_count = 0
    
    for case_id, case_name, network_json_str in design_cases:
        if not network_json_str:
            continue
        
        network = json.loads(network_json_str)
        nodes = network.get('nodes', [])
        
        modified = False
        factor_nodes_found = []
        
        for node in nodes:
            if node.get('type') == 'factor':
                factor_nodes_found.append(node.get('label', 'Unknown'))
                layer = node.get('layer', 2)
                
                # レイヤーに応じてタイプを変更
                if layer == 1:
                    node['type'] = 'performance'
                elif layer == 2:
                    node['type'] = 'property'
                elif layer == 3:
                    node['type'] = 'variable'
                elif layer == 4:
                    node['type'] = 'object'
                else:
                    node['type'] = 'property'  # デフォルト
                
                modified = True
        
        if modified:
            print(f"📝 設計案: {case_name}")
            print(f"   修正したノード: {', '.join(factor_nodes_found)}")
            
            # 更新
            updated_network_json = json.dumps(network, ensure_ascii=False)
            cursor.execute(
                "UPDATE design_cases SET network_json = ? WHERE id = ?",
                (updated_network_json, case_id)
            )
            updated_count += 1
    
    if updated_count > 0:
        conn.commit()
        print(f"\n✅ {updated_count}件の設計案を修正しました")
    else:
        print("\n✅ type='factor'のノードは見つかりませんでした")
    
    # 修正後の確認
    print("\n=== 修正後のノードタイプ集計 ===")
    cursor.execute("SELECT id, name, network_json FROM design_cases WHERE network_json IS NOT NULL")
    all_types = {}
    
    for _, case_name, network_json_str in cursor.fetchall():
        if not network_json_str:
            continue
        network = json.loads(network_json_str)
        for node in network.get('nodes', []):
            node_type = node.get('type', 'unknown')
            if node_type not in all_types:
                all_types[node_type] = 0
            all_types[node_type] += 1
    
    for node_type, count in sorted(all_types.items()):
        print(f"  {node_type}: {count}個")
    
    conn.close()

if __name__ == "__main__":
    fix_factor_nodes()