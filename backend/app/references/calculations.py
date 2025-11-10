# back/fuzzy_system/calculations.py
import numpy as np
from typing import Dict, List, Tuple
from .engine import FuzzyEngine
from .models import PerformanceMatrix, FuzzyWeight

class FuzzyCalculator:
    """ファジィ計算の実行"""

    @staticmethod
    def calculate_match(matrix: PerformanceMatrix, i: int, j: int) -> Dict[float, float]:
        """Match_i,j の計算"""
        engine = FuzzyEngine()
        sum_terms = []

        for k in range(matrix.m_features):
            key_i = f"{k}_{i}"
            key_j = f"{k}_{j}"

            if key_i in matrix.fuzzy_weights and key_j in matrix.fuzzy_weights:
                product = engine.fuzzy_multiply(
                    matrix.fuzzy_weights[key_i],
                    matrix.fuzzy_weights[key_j]
                )
                sign_sqrt = engine.fuzzy_sign_sqrt(product)
                sum_terms.append(sign_sqrt)

        if sum_terms:
            fuzzy_sum_result = engine.fuzzy_sum(sum_terms)
        else:
            fuzzy_sum_result = {0: 1.0}

        log_factor = np.log(3/2)
        match_fuzzy = {}

        for sum_val, membership in fuzzy_sum_result.items():
            match_val = -np.tanh(log_factor * sum_val)
            if match_val in match_fuzzy:
                match_fuzzy[match_val] = max(match_fuzzy[match_val], membership)
            else:
                match_fuzzy[match_val] = membership

        return match_fuzzy 

    @staticmethod
    def calculate_energy(matrix: PerformanceMatrix) -> Tuple[float, List[List[Dict[float, float]]]]: 
        """エネルギーU の計算"""
        n = matrix.n_performances

        match_matrix_fuzzy = []
        total_energy_crisp = 0.0

        for i in range(n):
            match_row_fuzzy_temp = []
            for j in range(n):
                if i == j:
                    match_ij_fuzzy = {0.0: 1.0}
                elif i < j: 
                    match_ij_fuzzy = FuzzyCalculator.calculate_match(matrix, i, j)
                    match_crisp_for_energy = FuzzyEngine.defuzzify_centroid(match_ij_fuzzy)

                    if i < len(matrix.importance):
                        imp_i = matrix.importance[i]
                    else:
                        imp_i = 3
                    if j < len(matrix.importance):
                        imp_j = matrix.importance[j]
                    else:
                        imp_j = 3

                    q_squared = 1.0

                    r_ij = np.sqrt(2 * (1 - match_crisp_for_energy))

                    if r_ij > 1e-10:
                        energy_contribution = (imp_i * imp_j * q_squared) / r_ij
                        total_energy_crisp += energy_contribution

                else:
                    match_ij_fuzzy = {0.0: 1.0} 
                
                match_row_fuzzy_temp.append(match_ij_fuzzy) 

            match_matrix_fuzzy.append(match_row_fuzzy_temp) 
        return total_energy_crisp, match_matrix_fuzzy
