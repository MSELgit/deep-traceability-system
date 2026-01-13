# backend/tests/test_scc_shapley.py
"""
SCC分解とShapley値計算のテスト
"""

import pytest
import numpy as np
from app.services.scc_analyzer import (
    TarjanSCC,
    analyze_scc,
    build_attribute_graph,
    compute_local_spectral_radius,
    scc_result_to_dict
)
from app.services.shapley_calculator import (
    compute_partial_tradeoff,
    compute_shapley_values_exact,
    compute_shapley_values_monte_carlo,
    compute_shapley_for_performance_pair,
    shapley_result_to_dict,
    estimate_computation_cost,
    compute_all_pairwise_shapley
)


class TestTarjanSCC:
    """TarjanアルゴリズムのテストI"""

    def test_no_cycles(self):
        """サイクルなしのグラフ"""
        graph = {
            'a': ['b'],
            'b': ['c'],
            'c': []
        }
        tarjan = TarjanSCC(graph)
        sccs = tarjan.find_sccs()

        # 各ノードが独立したSCC
        assert len(sccs) == 3
        for scc in sccs:
            assert len(scc) == 1

    def test_simple_cycle(self):
        """単純なサイクル"""
        graph = {
            'a': ['b'],
            'b': ['c'],
            'c': ['a']
        }
        tarjan = TarjanSCC(graph)
        sccs = tarjan.find_sccs()

        # 1つのSCCに全ノード
        assert len(sccs) == 1
        assert set(sccs[0]) == {'a', 'b', 'c'}

    def test_two_cycles(self):
        """2つの独立したサイクル"""
        graph = {
            'a': ['b'],
            'b': ['a'],
            'c': ['d'],
            'd': ['c'],
            'e': []
        }
        tarjan = TarjanSCC(graph)
        sccs = tarjan.find_sccs()

        # 2つのサイクル + 1つの孤立ノード
        cycle_sccs = [scc for scc in sccs if len(scc) >= 2]
        assert len(cycle_sccs) == 2


class TestSCCAnalysis:
    """SCC分解のテスト"""

    def test_empty_network(self):
        """空のネットワーク"""
        network = {'nodes': [], 'edges': []}
        result = analyze_scc(network)

        assert result.has_loops == False
        assert len(result.components) == 0

    def test_dag_network(self):
        """DAG（ループなし）"""
        network = {
            'nodes': [
                {'id': 'p1', 'layer': 1, 'type': 'performance', 'label': 'P1'},
                {'id': 'a1', 'layer': 2, 'type': 'property', 'label': 'A1'},
                {'id': 'a2', 'layer': 2, 'type': 'property', 'label': 'A2'},
                {'id': 'v1', 'layer': 3, 'type': 'variable', 'label': 'V1'},
            ],
            'edges': [
                {'source_id': 'a1', 'target_id': 'p1', 'weight': 1},
                {'source_id': 'a2', 'target_id': 'a1', 'weight': 1},
                {'source_id': 'v1', 'target_id': 'a2', 'weight': 1},
            ]
        }
        result = analyze_scc(network)

        assert result.has_loops == False
        assert len(result.components) == 0

    def test_loop_network(self):
        """ループありのネットワーク"""
        network = {
            'nodes': [
                {'id': 'p1', 'layer': 1, 'type': 'performance', 'label': 'P1'},
                {'id': 'a1', 'layer': 2, 'type': 'property', 'label': 'A1'},
                {'id': 'a2', 'layer': 2, 'type': 'property', 'label': 'A2'},
                {'id': 'v1', 'layer': 3, 'type': 'variable', 'label': 'V1'},
            ],
            'edges': [
                {'source_id': 'a1', 'target_id': 'p1', 'weight': 1},
                {'source_id': 'a1', 'target_id': 'a2', 'weight': 0.5},  # A1 → A2
                {'source_id': 'a2', 'target_id': 'a1', 'weight': 0.3},  # A2 → A1 (ループ)
                {'source_id': 'v1', 'target_id': 'a2', 'weight': 1},
            ]
        }
        result = analyze_scc(network)

        assert result.has_loops == True
        assert len(result.components) == 1
        assert set(result.components[0].nodes) == {'a1', 'a2'}

    def test_convergent_loop(self):
        """収束するループ（ρ < 1）"""
        network = {
            'nodes': [
                {'id': 'a1', 'layer': 2, 'type': 'property', 'label': 'A1'},
                {'id': 'a2', 'layer': 2, 'type': 'property', 'label': 'A2'},
            ],
            'edges': [
                {'source_id': 'a1', 'target_id': 'a2', 'weight': 0.3},
                {'source_id': 'a2', 'target_id': 'a1', 'weight': 0.3},
            ]
        }
        result = analyze_scc(network)

        assert result.has_loops == True
        assert len(result.components) == 1
        # 小さい重みなので収束するはず
        assert result.components[0].converges == True
        assert result.components[0].spectral_radius < 1.0


class TestShapleyPartialTradeoff:
    """部分トレードオフ計算のテスト"""

    def test_empty_subset(self):
        """空の部分集合"""
        T = np.array([[1, 2, 3], [4, 5, 6]])
        result = compute_partial_tradeoff(T, 0, 1, set())
        assert result == 0.0

    def test_single_element(self):
        """単一要素"""
        T = np.array([[1, 0, 0], [2, 0, 0]])
        result = compute_partial_tradeoff(T, 0, 1, {0})
        assert result == 1 * 2  # T[0,0] * T[1,0]

    def test_full_subset(self):
        """全要素"""
        T = np.array([[1, 2], [3, 4]])
        result = compute_partial_tradeoff(T, 0, 1, {0, 1})
        expected = 1*3 + 2*4  # 内積
        assert result == expected


class TestShapleyExact:
    """Shapley値厳密計算のテスト"""

    def test_single_variable(self):
        """1変数の場合"""
        T = np.array([[2], [3]])
        shapley = compute_shapley_values_exact(T, 0, 1)

        # 1変数なので、その変数が全ての寄与
        assert len(shapley) == 1
        assert abs(shapley[0] - 6) < 1e-10  # 2 * 3 = 6

    def test_two_variables(self):
        """2変数の場合"""
        T = np.array([[1, 2], [3, 4]])
        shapley = compute_shapley_values_exact(T, 0, 1)

        # C_ij = 1*3 + 2*4 = 11
        C_ij = 11
        sum_shapley = sum(shapley.values())

        # 加法性のテスト: Σφ_k = C_ij
        assert abs(sum_shapley - C_ij) < 1e-10

    def test_additivity(self):
        """加法性のテスト（Σφ_k = C_ij）"""
        np.random.seed(42)
        T = np.random.randn(3, 5)

        for i in range(3):
            for j in range(i+1, 3):
                shapley = compute_shapley_values_exact(T, i, j)
                C_ij = np.dot(T[i, :], T[j, :])
                sum_shapley = sum(shapley.values())

                assert abs(sum_shapley - C_ij) < 1e-10


class TestShapleyMonteCarlo:
    """Shapley値Monte Carlo近似のテスト"""

    def test_approximate_additivity(self):
        """近似的な加法性"""
        np.random.seed(42)
        T = np.random.randn(2, 8)

        shapley = compute_shapley_values_monte_carlo(T, 0, 1, n_samples=5000, seed=42)
        C_ij = np.dot(T[0, :], T[1, :])
        sum_shapley = sum(shapley.values())

        # Monte Carloなので少し誤差を許容
        assert abs(sum_shapley - C_ij) < 0.5


class TestShapleyResult:
    """ShapleyResult生成のテスト"""

    def test_result_structure(self):
        """結果構造のテスト"""
        T = np.array([[1, 2], [3, 4]])
        result = compute_shapley_for_performance_pair(T, 0, 1)

        assert result.perf_i_idx == 0
        assert result.perf_j_idx == 1
        assert result.n_properties == 2
        assert result.computation_method in ['exact', 'monte_carlo']

    def test_result_to_dict(self):
        """辞書変換のテスト"""
        T = np.array([[1, 2], [3, 4]])
        result = compute_shapley_for_performance_pair(T, 0, 1)
        result_dict = shapley_result_to_dict(
            result,
            performance_names=['P1', 'P2'],
            property_names=['A1', 'A2']
        )

        assert 'perf_i' in result_dict
        assert 'perf_j' in result_dict
        assert 'shapley_values' in result_dict
        assert result_dict['perf_i']['name'] == 'P1'
        assert result_dict['perf_j']['name'] == 'P2'


class TestComputationCost:
    """計算コスト見積もりのテスト"""

    def test_small_cost(self):
        """小規模"""
        cost = estimate_computation_cost(5)
        assert cost['warning'] == 'low'
        assert cost['recommendation'] == 'exact'

    def test_medium_cost(self):
        """中規模"""
        cost = estimate_computation_cost(12)
        assert cost['warning'] == 'medium'

    def test_large_cost(self):
        """大規模"""
        cost = estimate_computation_cost(20)
        assert cost['warning'] == 'high'
        assert cost['recommendation'] == 'monte_carlo'


class TestAllPairwiseShapley:
    """全ペア計算のテスト"""

    def test_all_pairs(self):
        """全ペア計算"""
        T = np.array([
            [1, 0.5],
            [0.5, 1],
            [-0.5, 0.5]
        ])

        results = compute_all_pairwise_shapley(
            T,
            performance_names=['P1', 'P2', 'P3'],
            property_names=['A1', 'A2'],
            only_tradeoffs=False
        )

        # 3C2 = 3ペア
        assert len(results) == 3

    def test_only_tradeoffs(self):
        """トレードオフのみ"""
        # P1とP2は相乗、P1とP3はトレードオフ
        T = np.array([
            [1, 0],
            [1, 0],    # P1と同じ方向
            [-1, 0]    # P1と逆方向
        ])

        results = compute_all_pairwise_shapley(
            T,
            performance_names=['P1', 'P2', 'P3'],
            property_names=['A1', 'A2'],
            only_tradeoffs=True
        )

        # トレードオフ関係のみ
        for r in results:
            assert r['cos_theta'] < 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
