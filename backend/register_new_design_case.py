#!/usr/bin/env python3
"""
新設計案「カイト・停留・浮体が動く」登録スクリプト

txtファイルのPAVEモデル情報に基づいてネットワーク構造を構築
"""

import sqlite3
import json
import uuid
from datetime import datetime

# データベース接続
conn = sqlite3.connect('data/local.db')
conn.row_factory = sqlite3.Row

# プロジェクトID
PROJECT_ID = '5a8b0f7b-5994-4eba-b0f6-2ee15340c07f'

# 性能ID対応 (txtのP番号 → DB ID)
PERF_IDS = {
    'P1': '0cc6585b-2acb-4b8f-b14a-242bf03284b9',  # エネルギー変換効率
    'P2': '3b99dfec-89ad-4030-8da6-1173ead9d4ac',  # CO2排出性
    'P3': 'd387289f-3f72-457d-a5be-3638eba5415a',  # 海域占有面積
    'P4': 'e1a59954-f15c-47ec-aa90-2be395fcdcef',  # 発電単価
    'P5': 'ddbfbb68-21ff-4157-b19e-39b79dbdb3b2',  # 航路閉塞率
    'P6': 'a734a37b-2752-4de5-b057-60e5cf993584',  # 視認性
    'P7': '3242b7be-b1c2-4607-b8c9-7717e7a67b46',  # 耐波浪性
    'P8': 'dc90b099-42c2-43b6-b7d1-a46642bb0f23',  # 就労機会の多さ
    'P9': '9404bf91-8e1d-4625-875b-5eedea677b0d',  # 鳥類視認性
    'P10': '7c20d95b-b674-464a-8a53-b1608aed6c04', # 海洋生物視認性
}

# txtからの性能値
PERFORMANCE_VALUES = {
    PERF_IDS['P1']: 0.33,      # エネルギー変換効率
    PERF_IDS['P2']: 222.0,     # CO2排出性 [10^3kton]
    PERF_IDS['P3']: 10.8,      # 海域占有面積 [10^3km^2]
    PERF_IDS['P4']: 36.9,      # 発電単価 [JPY/kWh]
    PERF_IDS['P5']: 0.95,      # 航路閉塞率
    PERF_IDS['P6']: 25.0,      # 視認性 [m]
    PERF_IDS['P7']: 1.0,       # 耐波浪性（不明→仮値）
    PERF_IDS['P8']: 1500.0,    # 就労機会の多さ [人/年]
    PERF_IDS['P9']: 890.0,     # 鳥類視認性 [m²]
    PERF_IDS['P10']: 453.0,    # 海洋生物視認性 [m³]
}


def create_network_structure():
    """
    txtのPAVEモデルに基づいてネットワーク構造を構築

    Layer 1: Performance (性能)
    Layer 2: Attribute (属性)
    Layer 3: Variable (設計変数)
    Layer 4: Entity (構成要素/モノ・環境)
    """

    # キャンバスサイズとレイアウト設定
    canvas_width = 1200
    layer_y = {1: 100, 2: 300, 3: 500, 4: 700}

    nodes = []
    edges = []

    # === Layer 1: Performance (性能) ===
    # 既存の性能ノードを使用（performance_idを設定）
    perf_positions = [
        ('P1', 'エネルギー変換効率', 60),
        ('P2', 'CO2排出性', 180),
        ('P3', '海域占有面積', 300),
        ('P4', '発電単価', 420),
        ('P5', '航路閉塞率', 540),
        ('P6', '視認性', 660),
        ('P7', '耐波浪性', 780),
        ('P8', '就労機会の多さ', 900),
        ('P9', '鳥類視認性', 1020),
        ('P10', '海洋生物視認性', 1140),
    ]

    for p_key, label, x in perf_positions:
        nodes.append({
            'id': p_key,
            'layer': 1,
            'type': 'performance',
            'label': label,
            'x': x,
            'y': layer_y[1],
            'performance_id': PERF_IDS[p_key]
        })

    # === Layer 2: Attribute (属性) ===
    attributes = [
        ('A1', 'カイトの受風抗力', 100),
        ('A2', '必要推進力', 250),
        ('A3', '自己消費電力', 400),
        ('A4', '出力損失', 550),
        ('A5', '製造・維持コスト', 700),
        ('A6', '排水容積・代表サイズ', 850),
        ('A7', '輸送時移動速度', 1000),
        ('A8', '占有半径', 1100),
    ]

    for a_id, label, x in attributes:
        nodes.append({
            'id': a_id,
            'layer': 2,
            'type': 'attribute',
            'label': label,
            'x': x,
            'y': layer_y[2]
        })

    # === Layer 3: Variable (設計変数) ===
    variables = [
        ('V1', 'カイト面積', 100),
        ('V2', 'テザー長さ', 300),
        ('V3', '浮体長', 500),
        ('V4', 'スクリュー仕様', 700),
        ('V5', '発電定格出力', 900),
        ('V6', 'タンク容量', 1100),
    ]

    for v_id, label, x in variables:
        nodes.append({
            'id': v_id,
            'layer': 3,
            'type': 'variable',
            'label': label,
            'x': x,
            'y': layer_y[3]
        })

    # === Layer 4: Entity (構成要素) ===
    entities = [
        ('E1', 'カイト（受風部）', 100),
        ('E2', 'テザー（伝達索）', 350),
        ('E3', '浮体（バージ型）', 550),
        ('E4', '電気推進機', 750),
        ('E5', 'エネルギー変換・貯蔵系', 1000),
    ]

    for e_id, label, x in entities:
        nodes.append({
            'id': e_id,
            'layer': 4,
            'type': 'object',
            'label': label,
            'x': x,
            'y': layer_y[4]
        })

    # === Edges ===
    edge_id = 0

    def add_edge(source, target, edge_type, weight=None):
        nonlocal edge_id
        edge_id += 1
        edge = {
            'id': f'e{edge_id}',
            'source_id': source,
            'target_id': target,
            'type': edge_type,
        }
        if weight is not None:
            edge['weight'] = weight
        edges.append(edge)

    # V → A (type3: Variable → Attribute)
    # 離散7段階モードの重み（-5, -3, -1, 0, 1, 3, 5）
    add_edge('V1', 'A1', 'type3', 5)   # V1(カイト面積) → A1(受風抗力): +5
    add_edge('V3', 'A6', 'type3', 5)   # V3(浮体長) → A6(排水容積): +5
    add_edge('V5', 'A5', 'type3', 5)   # V5(定格出力) → A5(コスト): +5
    add_edge('V2', 'A8', 'type3', 5)   # V2(テザー長) → A8(占有半径): +5

    # A → A (type2: Attribute → Attribute)
    add_edge('A1', 'A2', 'type2', 5)   # A1(受風抗力) → A2(必要推進力): +5
    add_edge('A2', 'A3', 'type2', 5)   # A2(必要推進力) → A3(自己消費電力): +5
    add_edge('A3', 'A4', 'type2', 5)   # A3(自己消費電力) → A4(出力損失): +5
    add_edge('A3', 'A5', 'type2', 5)   # A3(自己消費電力) → A5(コスト): +5
    add_edge('A6', 'A2', 'type2', 1)   # A6(代表サイズ) → A2(必要推進力): +1

    # A → P (type1: Attribute → Performance)
    add_edge('A4', 'P1', 'type1', -5)  # A4(出力損失) → P1(変換効率): -5
    add_edge('A4', 'P4', 'type1', 5)   # A4(出力損失) → P4(発電単価): +5
    add_edge('A5', 'P4', 'type1', 5)   # A5(コスト) → P4(発電単価): +5
    add_edge('A5', 'P8', 'type1', 3)   # A5(コスト) → P8(雇用人数): +3
    add_edge('A1', 'P9', 'type1', 5)   # A1(受風抗力/面積) → P9(鳥類視認性): +5
    add_edge('A6', 'P6', 'type1', 5)   # A6(排水容積) → P6(航路視認性): +5
    add_edge('A6', 'P10', 'type1', 5)  # A6(排水容積) → P10(海洋生物視認性): +5
    add_edge('A8', 'P3', 'type1', 5)   # A8(占有半径) → P3(海域占有面積): +5
    add_edge('A7', 'P7', 'type1', -3)  # A7(移動速度) → P7(耐波浪性): -3

    # V - E (type4: Variable - Entity, 無向)
    add_edge('V1', 'E1', 'type4')      # V1(カイト面積) - E1(カイト)
    add_edge('V2', 'E2', 'type4')      # V2(テザー長) - E2(テザー)
    add_edge('V3', 'E3', 'type4')      # V3(浮体長) - E3(浮体)
    add_edge('V4', 'E4', 'type4')      # V4(スクリュー仕様) - E4(電気推進機)
    add_edge('V5', 'E5', 'type4')      # V5(発電定格出力) - E5(エネルギー系)
    add_edge('V6', 'E5', 'type4')      # V6(タンク容量) - E5(エネルギー系)

    return {
        'nodes': nodes,
        'edges': edges,
        'weight_mode': 'discrete_7'
    }


def get_performance_snapshot():
    """現在の性能ツリーのスナップショットを取得（フラットな配列）"""
    perfs = conn.execute('''
        SELECT id, name, parent_id, level, is_leaf, unit, description, utility_function_json
        FROM performances
        WHERE project_id = ?
        ORDER BY level, name
    ''', (PROJECT_ID,)).fetchall()

    # フラットな配列として返す（フロントエンドの期待する形式）
    flat_snapshot = []
    for p in perfs:
        flat_snapshot.append({
            'id': p['id'],
            'name': p['name'],
            'parent_id': p['parent_id'],
            'level': p['level'],
            'is_leaf': bool(p['is_leaf']),
            'unit': p['unit'] or '',
            'description': p['description'] or '',
            'utility_function': json.loads(p['utility_function_json']) if p['utility_function_json'] else None
        })

    return flat_snapshot


def register_design_case():
    """新設計案を登録"""

    design_case_id = str(uuid.uuid4())
    now = datetime.utcnow()

    network = create_network_structure()
    snapshot = get_performance_snapshot()

    print("=== 新設計案を登録 ===")
    print(f"  ID: {design_case_id}")
    print(f"  名前: カイト・停留・浮体が動く")
    print(f"  ノード数: {len(network['nodes'])}")
    print(f"  エッジ数: {len(network['edges'])}")

    conn.execute('''
        INSERT INTO design_cases (
            id, project_id, name, description, color,
            created_at, updated_at,
            performance_values_json, network_json, performance_snapshot_json,
            weight_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        design_case_id,
        PROJECT_ID,
        'カイト・停留・浮体が動く',
        '停留型カイト発電。風の抗力に抗って電気推進機で位置を保持し、エネルギー貯蔵後に浮体自らが港へ移動する方式。',
        '#9333EA',  # 紫色
        now,
        now,
        json.dumps(PERFORMANCE_VALUES, ensure_ascii=False),
        json.dumps(network, ensure_ascii=False),
        json.dumps(snapshot, ensure_ascii=False),
        'discrete_7'
    ))

    print("\n=== 性能値 ===")
    perf_names = {
        PERF_IDS['P1']: 'エネルギー変換効率',
        PERF_IDS['P2']: 'CO2排出性',
        PERF_IDS['P3']: '海域占有面積',
        PERF_IDS['P4']: '発電単価',
        PERF_IDS['P5']: '航路閉塞率',
        PERF_IDS['P6']: '視認性',
        PERF_IDS['P7']: '耐波浪性',
        PERF_IDS['P8']: '就労機会の多さ',
        PERF_IDS['P9']: '鳥類視認性',
        PERF_IDS['P10']: '海洋生物視認性',
    }
    for perf_id, value in PERFORMANCE_VALUES.items():
        print(f"  {perf_names[perf_id]}: {value}")

    return design_case_id


def main():
    print("=" * 50)
    print("新設計案「カイト・停留・浮体が動く」登録")
    print("=" * 50)

    try:
        design_case_id = register_design_case()
        conn.commit()
        print(f"\n✓ 登録完了: {design_case_id}")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
