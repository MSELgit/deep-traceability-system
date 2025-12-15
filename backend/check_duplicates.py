import sqlite3
import json

conn = sqlite3.connect('data/local.db')

result = conn.execute(
    'SELECT network_json FROM design_cases WHERE name = ?', 
    ('Smart Locker Integration System - Adjacent Storage',)
).fetchone()

if result:
    network = json.loads(result[0])
    
    # 性能ノードを全て抽出
    perf_nodes = [n for n in network['nodes'] if n['type'] == 'performance']
    print(f'実際の性能ノード数: {len(perf_nodes)}')
    
    # ラベルの重複をチェック
    perf_labels = [n['label'] for n in perf_nodes]
    unique_labels = set(perf_labels)
    
    print(f'ユニークな性能ラベル数: {len(unique_labels)}')
    
    if len(perf_labels) != len(unique_labels):
        print('\n=== 重複が発生しています！ ===')
        for label in unique_labels:
            count = perf_labels.count(label)
            if count > 1:
                print(f'  {label}: {count}回')
        
        print('\n=== 全性能ノード詳細 ===')
        for i, node in enumerate(perf_nodes):
            print(f'{i+1:2d}. ID: {node["id"]}, Label: {node["label"]}')

conn.close()