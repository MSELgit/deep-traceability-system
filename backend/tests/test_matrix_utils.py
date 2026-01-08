# backend/tests/test_matrix_utils.py
"""
matrix_utils.py のユニットテスト
"""

import pytest
import numpy as np
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.matrix_utils import (
    normalize_weight,
    build_adjacency_matrices,
    compute_total_effect_matrix,
    compute_structural_tradeoff,
    analyze_network_structure,
)


class TestNormalizeWeight:
    """normalize_weight のテスト"""

    def test_discrete_values(self):
        """離散値の変換"""
        assert normalize_weight(-3) == -0.8
        assert normalize_weight(-1) == -0.4
        assert normalize_weight(0) == 0.0
        assert normalize_weight(1) == 0.4
        assert normalize_weight(3) == 0.8

    def test_continuous_values(self):
        """連続値のパススルー"""
        assert normalize_weight(0.5) == 0.5
        assert normalize_weight(-0.5) == -0.5

    def test_clipping(self):
        """範囲外の値のクリッピング"""
        assert normalize_weight(5) == pytest.approx(1.0, abs=0.1)
        assert normalize_weight(-5) == pytest.approx(-1.0, abs=0.1)


class TestBuildAdjacencyMatrices:
    """build_adjacency_matrices のテスト"""

    def test_empty_network(self):
        """空のネットワーク"""
        network = {'nodes': [], 'edges': []}
        result = build_adjacency_matrices(network)

        assert result['dimensions']['n_perf'] == 0
        assert result['dimensions']['n_attr'] == 0
        assert result['dimensions']['n_var'] == 0

    def test_simple_network(self):
        """シンプルなネットワーク: P1 ← A1 ← V1"""
        network = {
            'nodes': [
                {'id': 'p1', 'layer': 1, 'label': 'Perf1', 'performance_id': 'perf-001'},
                {'id': 'a1', 'layer': 2, 'label': 'Attr1'},
                {'id': 'v1', 'layer': 3, 'label': 'Var1'},
            ],
            'edges': [
                {'source_id': 'a1', 'target_id': 'p1', 'weight': 3},  # A→P
                {'source_id': 'v1', 'target_id': 'a1', 'weight': 1},  # V→A
            ]
        }
        result = build_adjacency_matrices(network)

        assert result['dimensions']['n_perf'] == 1
        assert result['dimensions']['n_attr'] == 1
        assert result['dimensions']['n_var'] == 1

        # B_PA: Attr → Perf (1×1)
        assert result['B_PA'].shape == (1, 1)
        assert result['B_PA'][0, 0] == pytest.approx(0.8)  # weight 3 → 0.8

        # B_AV: Var → Attr (1×1)
        assert result['B_AV'].shape == (1, 1)
        assert result['B_AV'][0, 0] == pytest.approx(0.4)  # weight 1 → 0.4

        # B_AA: Attr → Attr (1×1)
        assert result['B_AA'].shape == (1, 1)
        assert result['B_AA'][0, 0] == 0.0  # 自己ループなし

    def test_tradeoff_network(self):
        """トレードオフを含むネットワーク: P1 ←(+)A1(-)→ P2"""
        network = {
            'nodes': [
                {'id': 'p1', 'layer': 1, 'label': 'Perf1'},
                {'id': 'p2', 'layer': 1, 'label': 'Perf2'},
                {'id': 'a1', 'layer': 2, 'label': 'Attr1'},
                {'id': 'v1', 'layer': 3, 'label': 'Var1'},
            ],
            'edges': [
                {'source_id': 'a1', 'target_id': 'p1', 'weight': 3},   # A→P1 (+)
                {'source_id': 'a1', 'target_id': 'p2', 'weight': -3},  # A→P2 (-)
                {'source_id': 'v1', 'target_id': 'a1', 'weight': 3},   # V→A
            ]
        }
        result = build_adjacency_matrices(network)

        assert result['dimensions']['n_perf'] == 2
        assert result['B_PA'].shape == (2, 1)

        # P1への効果は正、P2への効果は負
        assert result['B_PA'][0, 0] > 0  # P1
        assert result['B_PA'][1, 0] < 0  # P2


class TestComputeTotalEffectMatrix:
    """compute_total_effect_matrix のテスト"""

    def test_no_attribute_interaction(self):
        """属性間相互作用なし: T = B_PA × B_AV"""
        B_PA = np.array([[0.8]])
        B_AA = np.array([[0.0]])
        B_AV = np.array([[0.4]])

        result = compute_total_effect_matrix(B_PA, B_AA, B_AV)

        # T = 0.8 × 1 × 0.4 = 0.32
        assert result['T'].shape == (1, 1)
        assert result['T'][0, 0] == pytest.approx(0.32)
        assert result['convergence'] is True

    def test_with_attribute_interaction(self):
        """属性間相互作用あり"""
        B_PA = np.array([[1.0, 0.5]])  # 2属性→1性能
        B_AA = np.array([
            [0.0, 0.3],  # A1→A2
            [0.0, 0.0],  # なし
        ])
        B_AV = np.array([
            [1.0],  # V1→A1
            [0.0],  # V1→A2 なし
        ])

        result = compute_total_effect_matrix(B_PA, B_AA, B_AV)

        assert result['T'].shape == (1, 1)
        assert result['convergence'] is True
        # V1→A1→P1 の直接効果 + V1→A1→A2→P1 の間接効果
        # T = B_PA × (I - B_AA)^(-1) × B_AV
        # (I - B_AA)^(-1) = [[1, 0.3], [0, 1]] の逆行列 = [[1, -0.3], [0, 1]]... 計算が複雑なので近似
        assert result['T'][0, 0] > 1.0  # 間接効果で増幅

    def test_empty_matrices(self):
        """空行列の処理"""
        B_PA = np.array([])
        B_AA = np.array([])
        B_AV = np.array([])

        result = compute_total_effect_matrix(B_PA, B_AA, B_AV)

        assert result['method'] == 'empty'


class TestComputeStructuralTradeoff:
    """compute_structural_tradeoff のテスト"""

    def test_perfect_tradeoff(self):
        """完全なトレードオフ: cos θ = -1"""
        # 2つの性能が逆方向の効果を受ける
        T = np.array([
            [1.0, 0.0],   # P1: V1に正の効果
            [-1.0, 0.0],  # P2: V1に負の効果
        ])

        result = compute_structural_tradeoff(T)

        assert result['cos_theta'].shape == (2, 2)
        assert result['cos_theta'][0, 1] == pytest.approx(-1.0)
        assert result['cos_theta'][1, 0] == pytest.approx(-1.0)
        assert len(result['tradeoff_pairs']) == 1
        assert result['tradeoff_pairs'][0]['interpretation'] == 'strong_tradeoff'

    def test_perfect_synergy(self):
        """完全なシナジー: cos θ = 1"""
        T = np.array([
            [1.0, 0.0],
            [1.0, 0.0],
        ])

        result = compute_structural_tradeoff(T)

        assert result['cos_theta'][0, 1] == pytest.approx(1.0)
        assert len(result['tradeoff_pairs']) == 0  # トレードオフなし

    def test_independent(self):
        """独立: cos θ ≈ 0"""
        T = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
        ])

        result = compute_structural_tradeoff(T)

        assert result['cos_theta'][0, 1] == pytest.approx(0.0)
        assert result['interpretations'][0][1] == 'independent'


class TestAnalyzeNetworkStructure:
    """analyze_network_structure の統合テスト"""

    def test_full_analysis(self):
        """完全な分析フロー"""
        network = {
            'nodes': [
                {'id': 'p1', 'layer': 1, 'label': 'Performance1', 'performance_id': 'perf-001'},
                {'id': 'p2', 'layer': 1, 'label': 'Performance2', 'performance_id': 'perf-002'},
                {'id': 'a1', 'layer': 2, 'label': 'Attribute1'},
                {'id': 'v1', 'layer': 3, 'label': 'Variable1'},
            ],
            'edges': [
                {'source_id': 'a1', 'target_id': 'p1', 'weight': 3},
                {'source_id': 'a1', 'target_id': 'p2', 'weight': -3},
                {'source_id': 'v1', 'target_id': 'a1', 'weight': 3},
            ]
        }

        result = analyze_network_structure(network)

        assert result['summary']['n_performances'] == 2
        assert result['summary']['n_tradeoff_pairs'] >= 1

        # トレードオフペアにラベル情報が含まれている
        if result['tradeoff']['tradeoff_pairs']:
            pair = result['tradeoff']['tradeoff_pairs'][0]
            assert 'perf_i_label' in pair
            assert 'perf_j_label' in pair
            assert 'perf_i_performance_id' in pair

    def test_real_world_like_network(self):
        """実際のネットワークに近い構造"""
        network = {
            'nodes': [
                {'id': 'p1', 'layer': 1, 'label': '燃費', 'performance_id': 'fuel'},
                {'id': 'p2', 'layer': 1, 'label': '加速性能', 'performance_id': 'accel'},
                {'id': 'p3', 'layer': 1, 'label': '安全性', 'performance_id': 'safety'},
                {'id': 'a1', 'layer': 2, 'label': '車両重量'},
                {'id': 'a2', 'layer': 2, 'label': 'エンジン出力'},
                {'id': 'v1', 'layer': 3, 'label': '素材選択'},
                {'id': 'v2', 'layer': 3, 'label': 'エンジン設計'},
            ],
            'edges': [
                # 車両重量 → 性能
                {'source_id': 'a1', 'target_id': 'p1', 'weight': -3},  # 重い→燃費悪い
                {'source_id': 'a1', 'target_id': 'p2', 'weight': -1},  # 重い→加速悪い
                {'source_id': 'a1', 'target_id': 'p3', 'weight': 3},   # 重い→安全性良い
                # エンジン出力 → 性能
                {'source_id': 'a2', 'target_id': 'p1', 'weight': -3},  # 出力高→燃費悪い
                {'source_id': 'a2', 'target_id': 'p2', 'weight': 3},   # 出力高→加速良い
                # 変数 → 属性
                {'source_id': 'v1', 'target_id': 'a1', 'weight': 3},   # 素材→重量
                {'source_id': 'v2', 'target_id': 'a2', 'weight': 3},   # 設計→出力
            ]
        }

        result = analyze_network_structure(network)

        print("\n=== 分析結果 ===")
        print(f"性能数: {result['summary']['n_performances']}")
        print(f"トレードオフペア数: {result['summary']['n_tradeoff_pairs']}")
        print(f"総効果行列:\n{result['total_effect']['T']}")
        print(f"cos θ 行列:\n{result['tradeoff']['cos_theta']}")

        for pair in result['tradeoff']['tradeoff_pairs']:
            print(f"トレードオフ: {pair['perf_i_label']} vs {pair['perf_j_label']} "
                  f"(cos θ = {pair['cos_theta']:.3f}, {pair['interpretation']})")

        # 燃費と加速性能、燃費と安全性などにトレードオフがあるはず
        assert result['summary']['n_tradeoff_pairs'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
