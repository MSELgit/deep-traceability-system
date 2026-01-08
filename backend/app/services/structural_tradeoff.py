# backend/app/services/structural_tradeoff.py
"""
構造的トレードオフ分析サービス

論文(design.tex)の理論に基づく構造的トレードオフ分析
- 総効果行列による統合的なトレードオフ判定
- 既存のTradeoffCalculatorとの併用が可能
"""

from typing import Dict, List, Optional
import numpy as np

from .matrix_utils import (
    build_adjacency_matrices,
    compute_total_effect_matrix,
    compute_structural_tradeoff,
    analyze_network_structure,
)


class StructuralTradeoffCalculator:
    """
    論文の構造的トレードオフ分析を実装

    既存のTradeoffCalculator（競合パス比率）と併用可能
    より理論的に厳密なトレードオフ指標を提供
    """

    def __init__(self, network: Dict, performances: List[Dict] = None):
        """
        Args:
            network: ネットワーク構造 {'nodes': [...], 'edges': [...]}
            performances: 性能リスト（オプション、ラベル情報の補完用）
        """
        self.network = network
        self.performances = performances or []
        self._analysis_result = None

    def analyze(self) -> Dict:
        """
        構造分析を実行

        Returns:
            {
                'total_effect_matrix': List[List[float]],
                'cos_theta_matrix': List[List[float]],
                'performance_ids': List[str],
                'performance_labels': List[str],
                'variable_ids': List[str],
                'variable_labels': List[str],
                'tradeoff_pairs': [
                    {
                        'perf_i_id': str,
                        'perf_i_label': str,
                        'perf_i_performance_id': str,
                        'perf_j_id': str,
                        'perf_j_label': str,
                        'perf_j_performance_id': str,
                        'cos_theta': float,
                        'interpretation': str
                    }
                ],
                'synergy_pairs': [...],  # cos θ > 0 のペア
                'metadata': {
                    'spectral_radius': float,
                    'convergence': bool,
                    'method': str,
                    'n_performances': int,
                    'n_attributes': int,
                    'n_variables': int,
                }
            }
        """
        if self._analysis_result is not None:
            return self._analysis_result

        # 基本分析を実行
        raw_result = analyze_network_structure(self.network)

        # 結果を整形
        matrices = raw_result['matrices']
        total_effect = raw_result['total_effect']
        tradeoff = raw_result['tradeoff']

        # シナジーペアも抽出
        synergy_pairs = []
        cos_theta = tradeoff['cos_theta']
        n_perf = cos_theta.shape[0] if cos_theta.size > 0 else 0

        for i in range(n_perf):
            for j in range(i + 1, n_perf):
                if cos_theta[i, j] > 0.3:  # 弱いシナジー以上
                    synergy_pairs.append({
                        'i': i,
                        'j': j,
                        'perf_i_id': matrices['node_ids']['P'][i],
                        'perf_i_label': matrices['node_labels']['P'][i],
                        'perf_i_performance_id': matrices['performance_id_map'].get(
                            matrices['node_ids']['P'][i]
                        ),
                        'perf_j_id': matrices['node_ids']['P'][j],
                        'perf_j_label': matrices['node_labels']['P'][j],
                        'perf_j_performance_id': matrices['performance_id_map'].get(
                            matrices['node_ids']['P'][j]
                        ),
                        'cos_theta': float(cos_theta[i, j]),
                        'interpretation': tradeoff['interpretations'][i][j],
                    })

        # シナジーの強い順にソート
        synergy_pairs.sort(key=lambda x: -x['cos_theta'])

        self._analysis_result = {
            'total_effect_matrix': total_effect['T'].tolist() if total_effect['T'].size > 0 else [],
            'cos_theta_matrix': tradeoff['cos_theta'].tolist() if tradeoff['cos_theta'].size > 0 else [],
            'performance_ids': matrices['node_ids']['P'],
            'performance_labels': matrices['node_labels']['P'],
            'variable_ids': matrices['node_ids']['V'],
            'variable_labels': matrices['node_labels']['V'],
            'attribute_ids': matrices['node_ids']['A'],
            'attribute_labels': matrices['node_labels']['A'],
            'tradeoff_pairs': tradeoff['tradeoff_pairs'],
            'synergy_pairs': synergy_pairs,
            'metadata': {
                'spectral_radius': total_effect['spectral_radius'],
                'convergence': total_effect['convergence'],
                'method': total_effect['method'],
                'n_performances': matrices['dimensions']['n_perf'],
                'n_attributes': matrices['dimensions']['n_attr'],
                'n_variables': matrices['dimensions']['n_var'],
            }
        }

        return self._analysis_result

    def get_tradeoff_summary(self) -> Dict:
        """
        トレードオフのサマリーを取得

        Returns:
            {
                'n_tradeoff_pairs': int,
                'n_synergy_pairs': int,
                'strongest_tradeoff': Dict or None,
                'strongest_synergy': Dict or None,
                'all_pairs_summary': List[Dict],  # 全ペアの要約
            }
        """
        analysis = self.analyze()

        all_pairs = []
        cos_theta = np.array(analysis['cos_theta_matrix'])
        n = len(analysis['performance_ids'])

        for i in range(n):
            for j in range(i + 1, n):
                all_pairs.append({
                    'perf_i': analysis['performance_labels'][i],
                    'perf_j': analysis['performance_labels'][j],
                    'cos_theta': float(cos_theta[i, j]),
                    'relationship': self._classify_relationship(cos_theta[i, j]),
                })

        return {
            'n_tradeoff_pairs': len(analysis['tradeoff_pairs']),
            'n_synergy_pairs': len(analysis['synergy_pairs']),
            'strongest_tradeoff': analysis['tradeoff_pairs'][0] if analysis['tradeoff_pairs'] else None,
            'strongest_synergy': analysis['synergy_pairs'][0] if analysis['synergy_pairs'] else None,
            'all_pairs_summary': all_pairs,
        }

    def compare_with_classic(self, classic_result: Dict) -> Dict:
        """
        既存のトレードオフ計算結果と比較

        Args:
            classic_result: TradeoffCalculator.calculate_single_case_tradeoff_ratio() の結果

        Returns:
            {
                'classic_ratio': float,
                'structural_n_tradeoffs': int,
                'agreement': float,  # 一致度
                'differences': List[Dict],  # 判定が異なるペア
            }
        """
        analysis = self.analyze()

        classic_ratio = classic_result.get('ratio', 0.0)
        n_structural = len(analysis['tradeoff_pairs'])

        # 総ペア数
        n = len(analysis['performance_ids'])
        total_pairs = n * (n - 1) // 2

        # 構造的分析のトレードオフ比率
        structural_ratio = n_structural / total_pairs if total_pairs > 0 else 0.0

        return {
            'classic': {
                'ratio': classic_ratio,
                'total_paths': classic_result.get('total_paths', 0),
                'tradeoff_paths': classic_result.get('tradeoff_paths', 0),
            },
            'structural': {
                'ratio': structural_ratio,
                'n_tradeoff_pairs': n_structural,
                'total_pairs': total_pairs,
            },
            'comparison': {
                'ratio_difference': abs(structural_ratio - classic_ratio),
                'both_valid': classic_result.get('is_valid', False) and n > 0,
            }
        }

    @staticmethod
    def _classify_relationship(cos_theta: float) -> str:
        """cos θ の値から関係性を分類"""
        if cos_theta < -0.5:
            return 'strong_tradeoff'
        elif cos_theta < 0:
            return 'weak_tradeoff'
        elif cos_theta < 0.5:
            return 'independent'
        else:
            return 'synergy'


def calculate_structural_tradeoff_for_case(
    network: Dict,
    performances: List[Dict] = None
) -> Dict:
    """
    設計案の構造的トレードオフを計算する便利関数

    Args:
        network: ネットワーク構造
        performances: 性能リスト（オプション）

    Returns:
        StructuralTradeoffCalculator.analyze() の結果
    """
    calculator = StructuralTradeoffCalculator(network, performances)
    return calculator.analyze()


def calculate_with_both_methods(
    network: Dict,
    performances: List[Dict]
) -> Dict:
    """
    既存の手法と構造的手法の両方でトレードオフを計算

    既存システムとの互換性を保ちつつ、新しい指標を追加

    Args:
        network: ネットワーク構造
        performances: 性能リスト

    Returns:
        {
            'classic': {...},  # 既存のTradeoffCalculatorの結果
            'structural': {...},  # 構造的分析の結果
            'comparison': {...},  # 比較結果
        }
    """
    from .tradeoff_calculator import TradeoffCalculator

    # 既存の計算
    classic_result = TradeoffCalculator.calculate_single_case_tradeoff_ratio(
        network, performances
    )

    # 構造的分析
    structural_calculator = StructuralTradeoffCalculator(network, performances)
    structural_result = structural_calculator.analyze()

    # 比較
    comparison = structural_calculator.compare_with_classic(classic_result)

    return {
        'classic': classic_result,
        'structural': structural_result,
        'comparison': comparison,
    }
