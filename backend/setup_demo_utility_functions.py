#!/usr/bin/env python3
"""
demoプロジェクトの効用関数を設定するスクリプト
様々なパターン（連続/離散、線形/ステップ/スムーズ補間など）を設定
"""
import sqlite3
import json

DB_PATH = 'data/local.db'
PROJECT_ID = '02a68944-c860-4fc4-8b19-ca112808df50'

def value_to_pixel(value_x, value_y, axis_min, axis_max):
    """値をピクセル座標に変換"""
    x = 50 + ((value_x - axis_min) / (axis_max - axis_min)) * 330
    y = 20 + (1 - value_y) * 260
    return x, y

def create_continuous_linear_up(axis_min=0, axis_max=100):
    """連続・線形補間・上向き（低→高が良い）"""
    points = []
    # シンプルな2点：左下から右上
    for vx, vy in [(axis_min, 0.0), (axis_max, 1.0)]:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "linear"
    }

def create_continuous_linear_down(axis_min=0, axis_max=100):
    """連続・線形補間・下向き（高→低が良い）"""
    points = []
    # 左上から右下
    for vx, vy in [(axis_min, 1.0), (axis_max, 0.0)]:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "linear"
    }

def create_continuous_step_up(axis_min=0, axis_max=100):
    """連続・ステップ補間・上向き（階段状）"""
    points = []
    # 3段階のステップ
    steps = [
        (axis_min, 0.1),
        (axis_min + (axis_max - axis_min) * 0.33, 0.1),
        (axis_min + (axis_max - axis_min) * 0.33, 0.5),
        (axis_min + (axis_max - axis_min) * 0.66, 0.5),
        (axis_min + (axis_max - axis_min) * 0.66, 0.9),
        (axis_max, 0.9),
    ]
    for vx, vy in steps:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "step"
    }

def create_continuous_step_down(axis_min=0, axis_max=100):
    """連続・ステップ補間・下向き"""
    points = []
    steps = [
        (axis_min, 0.9),
        (axis_min + (axis_max - axis_min) * 0.33, 0.9),
        (axis_min + (axis_max - axis_min) * 0.33, 0.5),
        (axis_min + (axis_max - axis_min) * 0.66, 0.5),
        (axis_min + (axis_max - axis_min) * 0.66, 0.1),
        (axis_max, 0.1),
    ]
    for vx, vy in steps:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "step"
    }

def create_continuous_smooth_up(axis_min=0, axis_max=100):
    """連続・スムーズ補間・上向き（S字カーブ）"""
    points = []
    # S字カーブ用の点
    curve_points = [
        (axis_min, 0.05),
        (axis_min + (axis_max - axis_min) * 0.25, 0.15),
        (axis_min + (axis_max - axis_min) * 0.5, 0.5),
        (axis_min + (axis_max - axis_min) * 0.75, 0.85),
        (axis_max, 0.95),
    ]
    for vx, vy in curve_points:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "smooth"
    }

def create_continuous_smooth_down(axis_min=0, axis_max=100):
    """連続・スムーズ補間・下向き"""
    points = []
    curve_points = [
        (axis_min, 0.95),
        (axis_min + (axis_max - axis_min) * 0.25, 0.85),
        (axis_min + (axis_max - axis_min) * 0.5, 0.5),
        (axis_min + (axis_max - axis_min) * 0.75, 0.15),
        (axis_max, 0.05),
    ]
    for vx, vy in curve_points:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "smooth"
    }

def create_continuous_threshold_up(axis_min=0, axis_max=100, threshold=50):
    """連続・閾値型（一定値を超えると急上昇）"""
    points = []
    curve_points = [
        (axis_min, 0.1),
        (threshold - 10, 0.15),
        (threshold, 0.5),
        (threshold + 10, 0.85),
        (axis_max, 0.9),
    ]
    for vx, vy in curve_points:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "smooth"
    }

def create_continuous_saturation_up(axis_min=0, axis_max=100):
    """連続・飽和型（急上昇後に飽和）"""
    points = []
    curve_points = [
        (axis_min, 0.0),
        (axis_min + (axis_max - axis_min) * 0.2, 0.6),
        (axis_min + (axis_max - axis_min) * 0.4, 0.8),
        (axis_min + (axis_max - axis_min) * 0.6, 0.9),
        (axis_max, 0.95),
    ]
    for vx, vy in curve_points:
        x, y = value_to_pixel(vx, vy, axis_min, axis_max)
        points.append({"x": x, "y": y, "valueX": vx, "valueY": vy})

    return {
        "type": "continuous",
        "axisMin": axis_min,
        "axisMax": axis_max,
        "points": points,
        "discreteRows": None,
        "saved": True,
        "warning": False,
        "archived": False,
        "interpolationType": "smooth"
    }

def create_discrete_binary_up():
    """離散・2値（良い/悪い）・上向き"""
    return {
        "type": "discrete",
        "axisMin": None,
        "axisMax": None,
        "points": [],
        "discreteRows": [
            {"label": "Low", "value": 0.2},
            {"label": "High", "value": 0.9}
        ],
        "saved": True,
        "warning": False,
        "archived": False
    }

def create_discrete_binary_down():
    """離散・2値・下向き"""
    return {
        "type": "discrete",
        "axisMin": None,
        "axisMax": None,
        "points": [],
        "discreteRows": [
            {"label": "Low", "value": 0.9},
            {"label": "High", "value": 0.2}
        ],
        "saved": True,
        "warning": False,
        "archived": False
    }

def create_discrete_three_levels_up():
    """離散・3段階（低/中/高）・上向き"""
    return {
        "type": "discrete",
        "axisMin": None,
        "axisMax": None,
        "points": [],
        "discreteRows": [
            {"label": "Low", "value": 0.1},
            {"label": "Medium", "value": 0.5},
            {"label": "High", "value": 0.9}
        ],
        "saved": True,
        "warning": False,
        "archived": False
    }

def create_discrete_three_levels_down():
    """離散・3段階・下向き"""
    return {
        "type": "discrete",
        "axisMin": None,
        "axisMax": None,
        "points": [],
        "discreteRows": [
            {"label": "Low", "value": 0.9},
            {"label": "Medium", "value": 0.5},
            {"label": "High", "value": 0.1}
        ],
        "saved": True,
        "warning": False,
        "archived": False
    }

def create_discrete_four_levels_up():
    """離散・4段階・上向き"""
    return {
        "type": "discrete",
        "axisMin": None,
        "axisMax": None,
        "points": [],
        "discreteRows": [
            {"label": "Very Low", "value": 0.1},
            {"label": "Low", "value": 0.35},
            {"label": "High", "value": 0.65},
            {"label": "Very High", "value": 0.95}
        ],
        "saved": True,
        "warning": False,
        "archived": False
    }

def create_discrete_nonlinear_up():
    """離散・非線形（中間値が偏っている）・上向き"""
    return {
        "type": "discrete",
        "axisMin": None,
        "axisMax": None,
        "points": [],
        "discreteRows": [
            {"label": "Poor", "value": 0.05},
            {"label": "Fair", "value": 0.3},
            {"label": "Good", "value": 0.8},
            {"label": "Excellent", "value": 0.95}
        ],
        "saved": True,
        "warning": False,
        "archived": False
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Need-Performance関係を取得
    cursor.execute('''
        SELECT npr.id, npr.need_id, npr.performance_id, npr.direction,
               n.name as need_name, p.name as perf_name
        FROM need_performance_relations npr
        JOIN needs n ON npr.need_id = n.id
        JOIN performances p ON npr.performance_id = p.id
        WHERE npr.project_id = ?
        ORDER BY n.name, p.name
    ''', (PROJECT_ID,))

    relations = cursor.fetchall()

    # 性能ごとの軸設定（連続/離散の種類も統一、軸幅もバリエーション）
    # 各関係に多様な効用関数を割り当て（同じ列は同じ軸・タイプ）
    utility_assignments = {
        # N1: P3↑, P5↑, P2_2↑, P2_1_1↓
        ('N1', 'P3', 'up'): create_continuous_step_up(0, 500),           # P3: 0-500, ステップ
        ('N1', 'P5', 'up'): create_continuous_smooth_up(0, 10),          # P5: 0-10, スムーズ
        ('N1', 'P2_2', 'up'): create_discrete_three_levels_up(),         # P2_2: 3段階離散
        ('N1', 'P2_1_1', 'down'): create_continuous_smooth_down(-50, 50), # P2_1_1: -50〜50, スムーズ

        # N2: P2↑, P4↑, P1_2↑
        ('N2', 'P2', 'up'): create_continuous_saturation_up(0, 1000),    # P2: 0-1000, 飽和型
        ('N2', 'P4', 'up'): create_discrete_binary_up(),                 # P4: 2値離散
        ('N2', 'P1_2', 'up'): create_continuous_threshold_up(0, 100, 50), # P1_2: 0-100, 閾値型

        # N3: P1↓, P2_1_2↑
        ('N3', 'P1', 'down'): create_continuous_linear_down(0, 200),     # P1: 0-200, 線形
        ('N3', 'P2_1_2', 'up'): create_discrete_four_levels_up(),        # P2_1_2: 4段階離散

        # N4: P3↑, P1_1↓
        ('N4', 'P3', 'up'): create_continuous_step_up(0, 500),           # P3: 0-500（N1と同じ）
        ('N4', 'P1_1', 'down'): create_continuous_linear_down(0, 50),    # P1_1: 0-50, 線形

        # N5: P2↑, P4↑, P5↑, P2_1_1↑
        ('N5', 'P2', 'up'): create_continuous_saturation_up(0, 1000),    # P2: 0-1000（N2と同じ）
        ('N5', 'P4', 'up'): create_discrete_binary_up(),                 # P4: 2値（N2と同じ）
        ('N5', 'P5', 'up'): create_continuous_smooth_up(0, 10),          # P5: 0-10（N1と同じ）
        ('N5', 'P2_1_1', 'up'): create_continuous_smooth_up(-50, 50),    # P2_1_1: -50〜50

        # N6: P1↓, P5↓, P1_1↑, P2_2↓
        ('N6', 'P1', 'down'): create_continuous_linear_down(0, 200),     # P1: 0-200（N3と同じ）
        ('N6', 'P5', 'down'): create_continuous_smooth_down(0, 10),      # P5: 0-10（下向き）
        ('N6', 'P1_1', 'up'): create_continuous_linear_up(0, 50),        # P1_1: 0-50（上向き）
        ('N6', 'P2_2', 'down'): create_discrete_three_levels_down(),     # P2_2: 3段階（下向き）
    }

    print("=== Demo Project Utility Function Setup ===\n")

    for row in relations:
        rel_id, need_id, perf_id, direction, need_name, perf_name = row

        key = (need_name, perf_name, direction)
        if key in utility_assignments:
            utility_func = utility_assignments[key].copy()
            # need_id と performance_id を追加
            utility_func["need_id"] = need_id
            utility_func["performance_id"] = perf_id
            utility_json = json.dumps(utility_func, ensure_ascii=False)

            cursor.execute('''
                UPDATE need_performance_relations
                SET utility_function_json = ?
                WHERE id = ?
            ''', (utility_json, rel_id))

            func_type = utility_func['type']
            if func_type == 'continuous':
                interp = utility_func.get('interpolationType', 'linear')
                print(f"{need_name} -> {perf_name} ({direction}): {func_type}/{interp}")
            else:
                num_rows = len(utility_func.get('discreteRows', []))
                print(f"{need_name} -> {perf_name} ({direction}): {func_type}/{num_rows}levels")
        else:
            print(f"WARNING: No assignment for {need_name} -> {perf_name} ({direction})")

    conn.commit()
    conn.close()

    print("\n=== Setup Complete ===")
    print(f"Updated {len(utility_assignments)} utility functions")


if __name__ == '__main__':
    main()
