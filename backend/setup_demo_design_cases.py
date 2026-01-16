#!/usr/bin/env python3
"""
demoプロジェクトの設計案を設定するスクリプト
5種類の設計案を作成:
1. LoopNet-3Lv: ループ構造 + 3段階離散
2. TreeNet-5Lv: ツリー構造 + 5段階離散
3. TreeNet-7Lv: TreeNet-5Lvと同じ構造 + 7段階離散（各weight_modeに適した重み値）
4. TreeNet-Cont: TreeNet-5Lvと同じ構造 + 連続値（各weight_modeに適した重み値）
5. HybridNet-5Lv: ハイブリッド構造（ループ+分岐）+ 5段階離散

重みマッピング:
同じ「意味」を持つエッジでも、weight_modeごとに適切な離散/連続値を使用
| 意味     | continuous | discrete_7 | discrete_5 | discrete_3 |
|----------|------------|------------|------------|------------|
| 強い正   | 0.86       | 5          | 3          | 1          |
| 中程度正 | 0.43       | 3          | 1          | 1          |
| 中立     | 0.0        | 0          | 0          | 0          |
| 中程度負 | -0.43      | -3         | -1         | -1         |
| 強い負   | -0.86      | -5         | -3         | -1         |
"""
import sqlite3
import json
import uuid
from datetime import datetime

DB_PATH = 'data/local.db'

# 重みマッピング: 意味レベル -> 各weight_modeの値
# continuous値は discrete_7 を正規化した値 (±6/7, ±4/7, ±2/7, 0)
WEIGHT_MAPPING = {
    'strong_positive': {'continuous': 6/7, 'discrete_7': 5, 'discrete_5': 3, 'discrete_3': 1},
    'medium_positive': {'continuous': 4/7, 'discrete_7': 3, 'discrete_5': 1, 'discrete_3': 1},
    'weak_positive':   {'continuous': 2/7, 'discrete_7': 1, 'discrete_5': 1, 'discrete_3': 0},
    'neutral':         {'continuous': 0.0, 'discrete_7': 0, 'discrete_5': 0, 'discrete_3': 0},
    'weak_negative':   {'continuous': -2/7, 'discrete_7': -1, 'discrete_5': -1, 'discrete_3': 0},
    'medium_negative': {'continuous': -4/7, 'discrete_7': -3, 'discrete_5': -1, 'discrete_3': -1},
    'strong_negative': {'continuous': -6/7, 'discrete_7': -5, 'discrete_5': -3, 'discrete_3': -1},
}

def get_weight(meaning: str, weight_mode: str) -> float:
    """意味レベルからweight_modeに応じた重み値を取得"""
    return WEIGHT_MAPPING[meaning][weight_mode]
PROJECT_ID = '02a68944-c860-4fc4-8b19-ca112808df50'

# 性能ID対応表
PERF_IDS = {
    'P1': '89527211-bab6-406f-85e9-f9c88bb1b56c',
    'P2': '76c8cd76-66e4-43aa-b29e-4e12d107717e',
    'P3': '8c6505b5-81ca-4871-91cf-b310ca3397a7',
    'P4': '62e24c8e-7c6e-4388-8c50-0024f5dcb266',
    'P5': 'c7be7c7a-b1a6-4691-a029-bc365ee53689',
    'P1_1': '14d87e18-494d-46c8-8b2c-1f73fc67c2a8',
    'P1_2': 'dc2cc1e3-e8ee-4ef7-88de-f7a3eb320701',
    'P2_1': '920e6c9a-4707-45fd-9699-5ad198375a1b',
    'P2_1_1': 'e37abefe-ac0c-49a7-88f4-da18c36bc9f2',
    'P2_2': '0a30d529-fca3-4e0f-a89d-f86751f786bd',
    'P2_1_2': '2a4429bd-1d37-4e19-b865-d4cf419018cc',
}

# 軸範囲（効用関数で設定したもの）
AXIS_RANGES = {
    'P1': (0, 200),
    'P1_1': (0, 50),
    'P1_2': (0, 100),
    'P2': (0, 1000),
    'P2_1_1': (-50, 50),
    'P2_1_2': None,  # discrete
    'P2_2': None,    # discrete
    'P3': (0, 500),
    'P4': None,      # discrete
    'P5': (0, 10),
}

# 離散値ラベル
DISCRETE_LABELS = {
    'P4': ['Low', 'High'],
    'P2_2': ['Low', 'Medium', 'High'],
    'P2_1_2': ['Very Low', 'Low', 'High', 'Very High'],
}

def create_performance_nodes(leaf_perfs):
    """性能ノードを生成"""
    nodes = []
    x_spacing = 1200 / (len(leaf_perfs) + 1)
    for i, perf_name in enumerate(leaf_perfs):
        perf_id = PERF_IDS[perf_name]
        nodes.append({
            "id": f"perf-{perf_id}",
            "layer": 1,
            "type": "performance",
            "label": perf_name,
            "x": x_spacing * (i + 1),
            "y": 100.0,
            "performance_id": perf_id,
            "x3d": None,
            "y3d": None
        })
    return nodes

def create_loop_network(weight_mode: str = 'discrete_3'):
    """
    ループ構造を持つ複雑なネットワーク（複数のループ）

    Args:
        weight_mode: 'discrete_3', 'discrete_5', 'discrete_7', 'continuous'
    """
    leaf_perfs = ['P1_1', 'P1_2', 'P2_1_1', 'P2_1_2', 'P2_2', 'P3', 'P4', 'P5']
    nodes = create_performance_nodes(leaf_perfs)

    # Attribute nodes (複数ループ: A1↔A2, A2↔A3, A4→A5→A4)
    attr_nodes = [
        {"id": "attr-1", "layer": 2, "type": "attribute", "label": "Power", "x": 200, "y": 260},
        {"id": "attr-2", "layer": 2, "type": "attribute", "label": "Efficiency", "x": 400, "y": 320},
        {"id": "attr-3", "layer": 2, "type": "attribute", "label": "Cost", "x": 600, "y": 260},
        {"id": "attr-4", "layer": 2, "type": "attribute", "label": "Weight", "x": 800, "y": 320},
        {"id": "attr-5", "layer": 2, "type": "attribute", "label": "Size", "x": 1000, "y": 260},
    ]
    for n in attr_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(attr_nodes)

    # Variable nodes
    var_nodes = [
        {"id": "var-1", "layer": 3, "type": "variable", "label": "Material", "x": 250, "y": 500},
        {"id": "var-2", "layer": 3, "type": "variable", "label": "Structure", "x": 500, "y": 480},
        {"id": "var-3", "layer": 3, "type": "variable", "label": "Process", "x": 750, "y": 500},
        {"id": "var-4", "layer": 3, "type": "variable", "label": "Config", "x": 1000, "y": 480},
    ]
    for n in var_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(var_nodes)

    # Entity nodes
    entity_nodes = [
        {"id": "obj-1", "layer": 4, "type": "object", "label": "Core", "x": 200, "y": 700},
        {"id": "obj-2", "layer": 4, "type": "object", "label": "Frame", "x": 450, "y": 700},
        {"id": "obj-3", "layer": 4, "type": "object", "label": "Cover", "x": 700, "y": 700},
        {"id": "env-1", "layer": 4, "type": "environment", "label": "Thermal", "x": 950, "y": 700},
    ]
    for n in entity_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(entity_nodes)

    # weight_modeに応じた重み値を取得
    w = lambda meaning: get_weight(meaning, weight_mode)

    edges = [
        # Loops in A layer
        {"id": "e-loop1a", "source_id": "attr-1", "target_id": "attr-2", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-loop1b", "source_id": "attr-2", "target_id": "attr-1", "type": "type1", "weight": w('medium_negative')},  # Loop 1
        {"id": "e-loop2a", "source_id": "attr-2", "target_id": "attr-3", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-loop2b", "source_id": "attr-3", "target_id": "attr-2", "type": "type1", "weight": w('medium_positive')},   # Loop 2
        {"id": "e-loop3a", "source_id": "attr-4", "target_id": "attr-5", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-loop3b", "source_id": "attr-5", "target_id": "attr-4", "type": "type1", "weight": w('strong_negative')},  # Loop 3
        {"id": "e-bridge", "source_id": "attr-3", "target_id": "attr-4", "type": "type1", "weight": w('strong_positive')},   # Bridge
        # V -> A
        {"id": "e-va1", "source_id": "var-1", "target_id": "attr-1", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va2", "source_id": "var-1", "target_id": "attr-2", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-va3", "source_id": "var-2", "target_id": "attr-2", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va4", "source_id": "var-2", "target_id": "attr-3", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-va5", "source_id": "var-3", "target_id": "attr-3", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-va6", "source_id": "var-3", "target_id": "attr-4", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va7", "source_id": "var-4", "target_id": "attr-4", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-va8", "source_id": "var-4", "target_id": "attr-5", "type": "type1", "weight": w('strong_positive')},
        # E -> V
        {"id": "e-ev1", "source_id": "obj-1", "target_id": "var-1", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev2", "source_id": "obj-2", "target_id": "var-2", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev3", "source_id": "obj-3", "target_id": "var-3", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev4", "source_id": "env-1", "target_id": "var-4", "type": "type1", "weight": w('neutral')},
        # A -> P (multiple connections)
        {"id": "e-ap1", "source_id": "attr-1", "target_id": f"perf-{PERF_IDS['P1_1']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap2", "source_id": "attr-1", "target_id": f"perf-{PERF_IDS['P3']}", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-ap3", "source_id": "attr-2", "target_id": f"perf-{PERF_IDS['P1_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap4", "source_id": "attr-2", "target_id": f"perf-{PERF_IDS['P2_1_1']}", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-ap5", "source_id": "attr-3", "target_id": f"perf-{PERF_IDS['P2_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap6", "source_id": "attr-3", "target_id": f"perf-{PERF_IDS['P4']}", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-ap7", "source_id": "attr-4", "target_id": f"perf-{PERF_IDS['P2_1_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap8", "source_id": "attr-4", "target_id": f"perf-{PERF_IDS['P5']}", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-ap9", "source_id": "attr-5", "target_id": f"perf-{PERF_IDS['P3']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap10", "source_id": "attr-5", "target_id": f"perf-{PERF_IDS['P4']}", "type": "type1", "weight": w('strong_positive')},
    ]

    return {"nodes": nodes, "edges": edges}

def create_tree_network(weight_mode: str = 'discrete_5'):
    """
    ツリー構造（ループなし）の複雑なネットワーク

    Args:
        weight_mode: 'discrete_3', 'discrete_5', 'discrete_7', 'continuous'
    """
    leaf_perfs = ['P1_1', 'P1_2', 'P2_1_1', 'P2_1_2', 'P2_2', 'P3', 'P4', 'P5']
    nodes = create_performance_nodes(leaf_perfs)

    # Attribute nodes (階層的ツリー構造)
    attr_nodes = [
        {"id": "attr-1", "layer": 2, "type": "attribute", "label": "Strength", "x": 180, "y": 250},
        {"id": "attr-2", "layer": 2, "type": "attribute", "label": "Durability", "x": 360, "y": 300},
        {"id": "attr-3", "layer": 2, "type": "attribute", "label": "Flexibility", "x": 540, "y": 250},
        {"id": "attr-4", "layer": 2, "type": "attribute", "label": "Precision", "x": 720, "y": 300},
        {"id": "attr-5", "layer": 2, "type": "attribute", "label": "Stability", "x": 900, "y": 250},
        {"id": "attr-6", "layer": 2, "type": "attribute", "label": "Response", "x": 1080, "y": 300},
    ]
    for n in attr_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(attr_nodes)

    # Variable nodes
    var_nodes = [
        {"id": "var-1", "layer": 3, "type": "variable", "label": "Thickness", "x": 200, "y": 480},
        {"id": "var-2", "layer": 3, "type": "variable", "label": "Density", "x": 400, "y": 500},
        {"id": "var-3", "layer": 3, "type": "variable", "label": "Geometry", "x": 600, "y": 480},
        {"id": "var-4", "layer": 3, "type": "variable", "label": "Tolerance", "x": 800, "y": 500},
        {"id": "var-5", "layer": 3, "type": "variable", "label": "Frequency", "x": 1000, "y": 480},
    ]
    for n in var_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(var_nodes)

    # Entity nodes
    entity_nodes = [
        {"id": "obj-1", "layer": 4, "type": "object", "label": "Chassis", "x": 200, "y": 700},
        {"id": "obj-2", "layer": 4, "type": "object", "label": "Motor", "x": 400, "y": 700},
        {"id": "obj-3", "layer": 4, "type": "object", "label": "Sensor", "x": 600, "y": 700},
        {"id": "env-1", "layer": 4, "type": "environment", "label": "Load", "x": 800, "y": 700},
        {"id": "env-2", "layer": 4, "type": "environment", "label": "Vibration", "x": 1000, "y": 700},
    ]
    for n in entity_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(entity_nodes)

    # weight_modeに応じた重み値を取得
    w = lambda meaning: get_weight(meaning, weight_mode)

    edges = [
        # Tree structure: A1,A2 <- V1; A2,A3 <- V2; A3,A4 <- V3; A4,A5 <- V4; A5,A6 <- V5
        # V -> A (fan-out, cascading)
        {"id": "e-va1", "source_id": "var-1", "target_id": "attr-1", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va2", "source_id": "var-1", "target_id": "attr-2", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-va3", "source_id": "var-2", "target_id": "attr-2", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va4", "source_id": "var-2", "target_id": "attr-3", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-va5", "source_id": "var-3", "target_id": "attr-3", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va6", "source_id": "var-3", "target_id": "attr-4", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-va7", "source_id": "var-4", "target_id": "attr-4", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-va8", "source_id": "var-4", "target_id": "attr-5", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va9", "source_id": "var-5", "target_id": "attr-5", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-va10", "source_id": "var-5", "target_id": "attr-6", "type": "type1", "weight": w('strong_positive')},
        # E -> V
        {"id": "e-ev1", "source_id": "obj-1", "target_id": "var-1", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev2", "source_id": "obj-2", "target_id": "var-2", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev3", "source_id": "obj-3", "target_id": "var-3", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev4", "source_id": "env-1", "target_id": "var-4", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev5", "source_id": "env-2", "target_id": "var-5", "type": "type1", "weight": w('neutral')},
        # A -> P (distributed)
        {"id": "e-ap1", "source_id": "attr-1", "target_id": f"perf-{PERF_IDS['P1_1']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap2", "source_id": "attr-2", "target_id": f"perf-{PERF_IDS['P1_1']}", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-ap3", "source_id": "attr-2", "target_id": f"perf-{PERF_IDS['P1_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap4", "source_id": "attr-3", "target_id": f"perf-{PERF_IDS['P2_1_1']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap5", "source_id": "attr-3", "target_id": f"perf-{PERF_IDS['P2_1_2']}", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-ap6", "source_id": "attr-4", "target_id": f"perf-{PERF_IDS['P2_1_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap7", "source_id": "attr-4", "target_id": f"perf-{PERF_IDS['P2_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap8", "source_id": "attr-5", "target_id": f"perf-{PERF_IDS['P3']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap9", "source_id": "attr-5", "target_id": f"perf-{PERF_IDS['P4']}", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-ap10", "source_id": "attr-6", "target_id": f"perf-{PERF_IDS['P4']}", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-ap11", "source_id": "attr-6", "target_id": f"perf-{PERF_IDS['P5']}", "type": "type1", "weight": w('strong_positive')},
    ]

    return {"nodes": nodes, "edges": edges}

def create_hybrid_network(weight_mode: str = 'discrete_5'):
    """
    ハイブリッド構造（複数ループ+多分岐+収束）の複雑なネットワーク

    Args:
        weight_mode: 'discrete_3', 'discrete_5', 'discrete_7', 'continuous'
    """
    leaf_perfs = ['P1_1', 'P1_2', 'P2_1_1', 'P2_1_2', 'P2_2', 'P3', 'P4', 'P5']
    nodes = create_performance_nodes(leaf_perfs)

    # Complex attribute structure with multiple loops and convergence
    attr_nodes = [
        {"id": "attr-1", "layer": 2, "type": "attribute", "label": "Input", "x": 150, "y": 240},
        {"id": "attr-2", "layer": 2, "type": "attribute", "label": "Process1", "x": 350, "y": 280},
        {"id": "attr-3", "layer": 2, "type": "attribute", "label": "Process2", "x": 550, "y": 240},
        {"id": "attr-4", "layer": 2, "type": "attribute", "label": "Buffer", "x": 450, "y": 360},  # Convergence point
        {"id": "attr-5", "layer": 2, "type": "attribute", "label": "Output1", "x": 750, "y": 280},
        {"id": "attr-6", "layer": 2, "type": "attribute", "label": "Output2", "x": 950, "y": 240},
        {"id": "attr-7", "layer": 2, "type": "attribute", "label": "Feedback", "x": 850, "y": 360},  # Feedback loop
    ]
    for n in attr_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(attr_nodes)

    # Variable nodes
    var_nodes = [
        {"id": "var-1", "layer": 3, "type": "variable", "label": "Rate", "x": 200, "y": 500},
        {"id": "var-2", "layer": 3, "type": "variable", "label": "Capacity", "x": 400, "y": 520},
        {"id": "var-3", "layer": 3, "type": "variable", "label": "Mode", "x": 600, "y": 500},
        {"id": "var-4", "layer": 3, "type": "variable", "label": "Threshold", "x": 800, "y": 520},
        {"id": "var-5", "layer": 3, "type": "variable", "label": "Gain", "x": 1000, "y": 500},
    ]
    for n in var_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(var_nodes)

    # Entity nodes
    entity_nodes = [
        {"id": "obj-1", "layer": 4, "type": "object", "label": "Processor", "x": 200, "y": 700},
        {"id": "obj-2", "layer": 4, "type": "object", "label": "Memory", "x": 400, "y": 700},
        {"id": "obj-3", "layer": 4, "type": "object", "label": "Interface", "x": 600, "y": 700},
        {"id": "env-1", "layer": 4, "type": "environment", "label": "Network", "x": 800, "y": 700},
        {"id": "env-2", "layer": 4, "type": "environment", "label": "Power", "x": 1000, "y": 700},
    ]
    for n in entity_nodes:
        n.update({"performance_id": None, "x3d": None, "y3d": None})
    nodes.extend(entity_nodes)

    # weight_modeに応じた重み値を取得
    w = lambda meaning: get_weight(meaning, weight_mode)

    edges = [
        # Complex topology with loops
        # Forward path: A1 -> A2 -> A4 -> A5
        {"id": "e-fwd1", "source_id": "attr-1", "target_id": "attr-2", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-fwd2", "source_id": "attr-2", "target_id": "attr-4", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-fwd3", "source_id": "attr-4", "target_id": "attr-5", "type": "type1", "weight": w('strong_positive')},
        # Parallel path: A1 -> A3 -> A4
        {"id": "e-par1", "source_id": "attr-1", "target_id": "attr-3", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-par2", "source_id": "attr-3", "target_id": "attr-4", "type": "type1", "weight": w('strong_positive')},
        # Loop 1: A2 <-> A3
        {"id": "e-loop1a", "source_id": "attr-2", "target_id": "attr-3", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-loop1b", "source_id": "attr-3", "target_id": "attr-2", "type": "type1", "weight": w('medium_positive')},
        # Output branch: A5 -> A6, A5 -> A7
        {"id": "e-out1", "source_id": "attr-5", "target_id": "attr-6", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-out2", "source_id": "attr-5", "target_id": "attr-7", "type": "type1", "weight": w('strong_negative')},
        # Feedback loop: A7 -> A4
        {"id": "e-fb", "source_id": "attr-7", "target_id": "attr-4", "type": "type1", "weight": w('medium_negative')},
        # Loop 2: A6 <-> A7
        {"id": "e-loop2a", "source_id": "attr-6", "target_id": "attr-7", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-loop2b", "source_id": "attr-7", "target_id": "attr-6", "type": "type1", "weight": w('strong_negative')},
        # V -> A
        {"id": "e-va1", "source_id": "var-1", "target_id": "attr-1", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va2", "source_id": "var-2", "target_id": "attr-2", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va3", "source_id": "var-2", "target_id": "attr-3", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-va4", "source_id": "var-3", "target_id": "attr-4", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va5", "source_id": "var-4", "target_id": "attr-5", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-va6", "source_id": "var-4", "target_id": "attr-7", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-va7", "source_id": "var-5", "target_id": "attr-6", "type": "type1", "weight": w('strong_positive')},
        # E -> V
        {"id": "e-ev1", "source_id": "obj-1", "target_id": "var-1", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev2", "source_id": "obj-2", "target_id": "var-2", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev3", "source_id": "obj-3", "target_id": "var-3", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev4", "source_id": "env-1", "target_id": "var-4", "type": "type1", "weight": w('neutral')},
        {"id": "e-ev5", "source_id": "env-2", "target_id": "var-5", "type": "type1", "weight": w('neutral')},
        # A -> P (complex mapping)
        {"id": "e-ap1", "source_id": "attr-1", "target_id": f"perf-{PERF_IDS['P1_1']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap2", "source_id": "attr-2", "target_id": f"perf-{PERF_IDS['P1_1']}", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-ap3", "source_id": "attr-2", "target_id": f"perf-{PERF_IDS['P1_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap4", "source_id": "attr-3", "target_id": f"perf-{PERF_IDS['P2_1_1']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap5", "source_id": "attr-4", "target_id": f"perf-{PERF_IDS['P2_1_1']}", "type": "type1", "weight": w('medium_positive')},
        {"id": "e-ap6", "source_id": "attr-4", "target_id": f"perf-{PERF_IDS['P2_1_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap7", "source_id": "attr-5", "target_id": f"perf-{PERF_IDS['P2_2']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap8", "source_id": "attr-5", "target_id": f"perf-{PERF_IDS['P3']}", "type": "type1", "weight": w('strong_negative')},
        {"id": "e-ap9", "source_id": "attr-6", "target_id": f"perf-{PERF_IDS['P3']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap10", "source_id": "attr-6", "target_id": f"perf-{PERF_IDS['P4']}", "type": "type1", "weight": w('strong_positive')},
        {"id": "e-ap11", "source_id": "attr-7", "target_id": f"perf-{PERF_IDS['P4']}", "type": "type1", "weight": w('medium_negative')},
        {"id": "e-ap12", "source_id": "attr-7", "target_id": f"perf-{PERF_IDS['P5']}", "type": "type1", "weight": w('strong_positive')},
    ]

    return {"nodes": nodes, "edges": edges}

def create_performance_values_set1():
    """性能値セット1（LoopNet用）"""
    return {
        PERF_IDS['P1_1']: 35,       # 0-50
        PERF_IDS['P1_2']: 72,       # 0-100
        PERF_IDS['P2_1_1']: -15,    # -50 to 50
        PERF_IDS['P2_1_2']: "High", # discrete 4
        PERF_IDS['P2_2']: "Medium", # discrete 3
        PERF_IDS['P3']: 320,        # 0-500
        PERF_IDS['P4']: "High",     # discrete 2
        PERF_IDS['P5']: 7.5,        # 0-10
    }

def create_performance_values_set2():
    """性能値セット2（TreeNet用 - 基準となる5段階設計案）"""
    return {
        PERF_IDS['P1_1']: 28,       # 0-50
        PERF_IDS['P1_2']: 55,       # 0-100
        PERF_IDS['P2_1_1']: 20,     # -50 to 50
        PERF_IDS['P2_1_2']: "Low",  # discrete 4
        PERF_IDS['P2_2']: "High",   # discrete 3
        PERF_IDS['P3']: 180,        # 0-500
        PERF_IDS['P4']: "Low",      # discrete 2
        PERF_IDS['P5']: 4.2,        # 0-10
    }

def create_performance_values_set3():
    """性能値セット3（HybridNet用）"""
    return {
        PERF_IDS['P1_1']: 42,       # 0-50
        PERF_IDS['P1_2']: 88,       # 0-100
        PERF_IDS['P2_1_1']: 35,     # -50 to 50
        PERF_IDS['P2_1_2']: "Very High",  # discrete 4
        PERF_IDS['P2_2']: "Low",    # discrete 3
        PERF_IDS['P3']: 420,        # 0-500
        PERF_IDS['P4']: "High",     # discrete 2
        PERF_IDS['P5']: 2.8,        # 0-10
    }

def get_performance_snapshot():
    """性能スナップショット（全性能ツリー）"""
    # DBの構造と完全に一致させる必要がある
    return [
        # Level 0 (root)
        {"id": PERF_IDS['P1'], "name": "P1", "parent_id": None, "level": 0, "is_leaf": False, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P2'], "name": "P2", "parent_id": None, "level": 0, "is_leaf": False, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P3'], "name": "P3", "parent_id": None, "level": 0, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P4'], "name": "P4", "parent_id": None, "level": 0, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P5'], "name": "P5", "parent_id": None, "level": 0, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
        # Level 1
        {"id": PERF_IDS['P1_1'], "name": "P1_1", "parent_id": PERF_IDS['P1'], "level": 1, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P1_2'], "name": "P1_2", "parent_id": PERF_IDS['P1'], "level": 1, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P2_1'], "name": "P2_1", "parent_id": PERF_IDS['P2'], "level": 1, "is_leaf": False, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P2_2'], "name": "P2_2", "parent_id": PERF_IDS['P2'], "level": 1, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
        # Level 2
        {"id": PERF_IDS['P2_1_1'], "name": "P2_1_1", "parent_id": PERF_IDS['P2_1'], "level": 2, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
        {"id": PERF_IDS['P2_1_2'], "name": "P2_1_2", "parent_id": PERF_IDS['P2_1'], "level": 2, "is_leaf": True, "unit": "", "description": "", "utility_function": None},
    ]

COLORS = ['#3357FF', '#FF5733', '#33FF57', '#FF33F5', '#F5FF33']

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 既存の設計案を削除
    cursor.execute('DELETE FROM design_cases WHERE project_id = ?', (PROJECT_ID,))

    now = datetime.now().isoformat()
    perf_snapshot_json = json.dumps(get_performance_snapshot())

    # 設計案の定義（各weight_modeに適した重み値を使用）
    design_cases = [
        {
            "name": "LoopNet-3Lv",
            "description": "ループ構造（A1→A2→A3→A1）を持つネットワーク、3段階離散重み",
            "weight_mode": "discrete_3",
            "network": create_loop_network(weight_mode='discrete_3'),
            "perf_values": create_performance_values_set1(),
            "color": COLORS[0],
        },
        {
            "name": "TreeNet-5Lv",
            "description": "ツリー構造（ループなし）のネットワーク、5段階離散重み（基準設計）",
            "weight_mode": "discrete_5",
            "network": create_tree_network(weight_mode='discrete_5'),
            "perf_values": create_performance_values_set2(),
            "color": COLORS[1],
        },
        {
            "name": "TreeNet-7Lv",
            "description": "TreeNet-5Lvと同構造、7段階離散重み（より細かい表現力）",
            "weight_mode": "discrete_7",
            "network": create_tree_network(weight_mode='discrete_7'),
            "perf_values": create_performance_values_set2(),  # Same as 5Lv
            "color": COLORS[2],
        },
        {
            "name": "TreeNet-Cont",
            "description": "TreeNet-5Lvと同構造、連続値重み（最も細かい表現力）",
            "weight_mode": "continuous",
            "network": create_tree_network(weight_mode='continuous'),
            "perf_values": create_performance_values_set2(),  # Same as 5Lv
            "color": COLORS[3],
        },
        {
            "name": "HybridNet-5Lv",
            "description": "ハイブリッド構造（ループ+多分岐）のネットワーク、5段階離散重み",
            "weight_mode": "discrete_5",
            "network": create_hybrid_network(weight_mode='discrete_5'),
            "perf_values": create_performance_values_set3(),
            "color": COLORS[4],
        },
    ]

    print("=== Demo Project Design Cases Setup ===\n")

    for dc in design_cases:
        case_id = str(uuid.uuid4())

        cursor.execute('''
            INSERT INTO design_cases (
                id, project_id, name, description, color,
                created_at, updated_at,
                performance_values_json, network_json,
                performance_snapshot_json, weight_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_id, PROJECT_ID, dc["name"], dc["description"], dc["color"],
            now, now,
            json.dumps(dc["perf_values"]),
            json.dumps(dc["network"]),
            perf_snapshot_json,
            dc["weight_mode"]
        ))

        # ネットワーク構造の特徴を表示
        n_nodes = len(dc["network"]["nodes"])
        n_edges = len(dc["network"]["edges"])
        n_attr = len([n for n in dc["network"]["nodes"] if n["type"] == "attribute"])

        print(f"✓ {dc['name']}")
        print(f"  - Weight mode: {dc['weight_mode']}")
        print(f"  - Network: {n_nodes} nodes, {n_edges} edges, {n_attr} attributes")
        print(f"  - Description: {dc['description'][:50]}...")
        print()

    conn.commit()
    conn.close()

    print("=== Setup Complete ===")
    print(f"Created {len(design_cases)} design cases")

if __name__ == '__main__':
    main()
