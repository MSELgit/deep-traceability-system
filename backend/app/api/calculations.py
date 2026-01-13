from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

from app.models.database import get_db, ProjectModel, DesignCaseModel
from app.schemas.project import MountainPosition
from app.services.mountain_calculator import calculate_mountain_positions
from app.services.structural_energy import compute_structural_energy
from app.services.tradeoff_calculator import TradeoffCalculator
from app.services.tradeoff_debug import debug_tradeoff_calculation
from app.services.structural_tradeoff import (
    StructuralTradeoffCalculator,
    calculate_structural_tradeoff_for_case,
    calculate_with_both_methods,
)

router = APIRouter()


@router.post("/mountain/{project_id}", response_model=List[Dict])
def calculate_project_mountain(project_id: str, db: Session = Depends(get_db)):
    """
    プロジェクトの全設計案について山の座標を計算
    
    Args:
        project_id: プロジェクトID
    
    Returns:
        各設計案の座標 {case_id, x, y, z, H, utility_vector}
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        positions = calculate_mountain_positions(project, db)
        
        # 計算結果をデータベースにコミット
        db.commit()
        
        return positions
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/utility/{project_id}/{case_id}", response_model=Dict[str, float])
def calculate_case_utility(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    特定の設計案の効用ベクトルを計算
    
    Args:
        project_id: プロジェクトID
        case_id: 設計案ID
    
    Returns:
        {performance_id: utility_value}
    """
    # TODO: 実装予定
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/energy/{project_id}", response_model=List[Dict])
def calculate_project_energy(project_id: str, db: Session = Depends(get_db)):
    """
    プロジェクトの全設計案についてエネルギーを計算（論文準拠式）

    論文式: E = Σ(i<j) W_i × W_j × L(C_ij) / (Σ W_i)²

    Args:
        project_id: プロジェクトID

    Returns:
        各設計案のエネルギー {case_id, case_name, total_energy, partial_energies, inner_product_matrix}
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        results = []
        for case in project.design_cases:
            network = case.network
            perf_weights = case.performance_weights or {}
            weight_mode = getattr(case, 'weight_mode', 'discrete_7') or 'discrete_7'

            if network and 'nodes' in network and 'edges' in network:
                energy_result = compute_structural_energy(
                    network=network,
                    performance_weights=perf_weights,
                    weight_mode=weight_mode
                )

                # 性能ごとの部分エネルギーを集計（正規化済み）
                partial_energies = {}
                normalization_factor = energy_result.get('normalization_factor', 1.0)
                for contrib in energy_result.get('energy_contributions', []):
                    perf_i_id = contrib['perf_i_id']
                    perf_j_id = contrib['perf_j_id']
                    contribution = contrib['contribution']
                    # 正規化して各性能に半分ずつ配分
                    normalized_half = (contribution / 2) / normalization_factor if normalization_factor > 0 else 0
                    partial_energies[perf_i_id] = partial_energies.get(perf_i_id, 0) + normalized_half
                    partial_energies[perf_j_id] = partial_energies.get(perf_j_id, 0) + normalized_half

                results.append({
                    'case_id': case.id,
                    'case_name': case.name,
                    'total_energy': energy_result['E'],
                    'partial_energies': partial_energies,
                    'inner_product_matrix': energy_result.get('inner_product_matrix', []),
                    'cos_theta_matrix': energy_result.get('cos_theta_matrix', []),
                    'energy_contributions': energy_result.get('energy_contributions', []),
                })
            else:
                results.append({
                    'case_id': case.id,
                    'case_name': case.name,
                    'total_energy': 0.0,
                    'partial_energies': {},
                    'inner_product_matrix': [],
                    'cos_theta_matrix': [],
                    'energy_contributions': [],
                })

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/energy/{project_id}/{case_id}", response_model=Dict)
def calculate_case_energy(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    特定の設計案のエネルギーを計算（論文準拠式）

    論文式: E = Σ(i<j) W_i × W_j × L(C_ij) / (Σ W_i)²

    Args:
        project_id: プロジェクトID
        case_id: 設計案ID

    Returns:
        {total_energy, partial_energies, inner_product_matrix, cos_theta_matrix, energy_contributions}
    """
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()

    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        network = design_case.network
        perf_weights = design_case.performance_weights or {}
        weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

        if network and 'nodes' in network and 'edges' in network:
            energy_result = compute_structural_energy(
                network=network,
                performance_weights=perf_weights,
                weight_mode=weight_mode
            )

            # 性能ごとの部分エネルギーを集計（正規化済み）
            partial_energies = {}
            normalization_factor = energy_result.get('normalization_factor', 1.0)
            for contrib in energy_result.get('energy_contributions', []):
                perf_i_id = contrib['perf_i_id']
                perf_j_id = contrib['perf_j_id']
                contribution = contrib['contribution']
                # 正規化して各性能に半分ずつ配分
                normalized_half = (contribution / 2) / normalization_factor if normalization_factor > 0 else 0
                partial_energies[perf_i_id] = partial_energies.get(perf_i_id, 0) + normalized_half
                partial_energies[perf_j_id] = partial_energies.get(perf_j_id, 0) + normalized_half

            return {
                'total_energy': energy_result['E'],
                'partial_energies': partial_energies,
                'inner_product_matrix': energy_result.get('inner_product_matrix', []),
                'cos_theta_matrix': energy_result.get('cos_theta_matrix', []),
                'energy_contributions': energy_result.get('energy_contributions', []),
                'performance_ids': energy_result.get('performance_ids', []),
                'performance_labels': energy_result.get('performance_labels', []),
                'norms': energy_result.get('norms', []),
                'metadata': energy_result.get('metadata', {}),
            }
        else:
            return {
                'total_energy': 0.0,
                'partial_energies': {},
                'inner_product_matrix': [],
                'cos_theta_matrix': [],
                'energy_contributions': [],
                'performance_ids': [],
                'performance_labels': [],
                'norms': [],
                'metadata': {},
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/tradeoff/{project_id}", response_model=Dict[str, Dict])
def calculate_performance_tradeoff(project_id: str, db: Session = Depends(get_db)):
    """
    プロジェクトの全設計案について性能間背反割合を計算
    
    Args:
        project_id: プロジェクトID
    
    Returns:
        各設計案の性能間背反割合 {case_id: ratio}
    """
    
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # 設計ケースとネットワーク情報を準備
        design_cases_data = []
        for dc in project.design_cases:
            design_cases_data.append({
                'id': dc.id,
                'network': dc.network
            })
        
        # 性能データを準備
        performances_data = [
            {
                'id': p.id,
                'is_leaf': p.is_leaf
            }
            for p in project.performances
        ]
        
        
        # 背反割合を計算
        results = TradeoffCalculator.calculate_performance_tradeoff_ratio(
            design_cases_data,
            performances_data
        )
        
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/tradeoff-debug/{project_id}/{case_id}")
def debug_case_tradeoff(
    project_id: str, 
    case_id: str, 
    db: Session = Depends(get_db)
):
    """
    特定の設計案の性能間背反割合の計算をデバッグ
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    design_case = next((dc for dc in project.design_cases if dc.id == case_id), None)
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    performances_data = [
        {
            'id': p.id,
            'is_leaf': p.is_leaf,
            'name': p.name
        }
        for p in project.performances
    ]
    
    # デバッグ情報を取得
    debug_info = debug_tradeoff_calculation(
        design_case.network,
        performances_data,
        design_case.name
    )

    return debug_info


# =============================================================================
# 構造的トレードオフ分析 API（論文理論に基づく新機能）
# =============================================================================

@router.get("/structural-tradeoff/{project_id}/{case_id}")
def get_structural_tradeoff(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    設計案の構造的トレードオフ分析を取得

    論文(design.tex)の理論に基づく分析:
    - 総効果行列 T = B_PA × (I - B_AA)^(-1) × B_AV
    - 構造的トレードオフ指標 cos θ

    既存の tradeoff（競合パス比率）と併用可能

    Args:
        project_id: プロジェクトID
        case_id: 設計案ID

    Returns:
        {
            'total_effect_matrix': List[List[float]],
            'cos_theta_matrix': List[List[float]],
            'performance_ids': List[str],
            'performance_labels': List[str],
            'tradeoff_pairs': List[Dict],
            'synergy_pairs': List[Dict],
            'metadata': {...}
        }
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    design_case = next((dc for dc in project.design_cases if dc.id == case_id), None)
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        performances_data = [
            {'id': p.id, 'name': p.name, 'is_leaf': p.is_leaf}
            for p in project.performances
        ]

        # 設計案のweight_modeを取得（デフォルトは'discrete_7'）
        weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

        # 性能の重みを取得（E_ij計算用）
        performance_weights = design_case.performance_weights or {}

        result = calculate_structural_tradeoff_for_case(
            design_case.network,
            performances_data,
            weight_mode,
            performance_weights
        )

        return result
    except Exception as e:
        logger.error(f"Structural tradeoff calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/structural-tradeoff-summary/{project_id}")
def get_project_structural_tradeoff_summary(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    プロジェクト全体の構造的トレードオフサマリー

    全設計案の構造的トレードオフを一覧で取得

    Returns:
        {
            'cases': [
                {
                    'case_id': str,
                    'case_name': str,
                    'n_tradeoff_pairs': int,
                    'strongest_tradeoff': Dict or None,
                    'classic_ratio': float  # 既存指標も併記
                }
            ],
            'common_tradeoffs': [...]  # 全設計案で共通のトレードオフ
        }
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        performances_data = [
            {'id': p.id, 'name': p.name, 'is_leaf': p.is_leaf}
            for p in project.performances
        ]

        cases_results = []
        all_tradeoff_pairs = []  # 全ケースのトレードオフペアを収集

        for design_case in project.design_cases:
            # 設計案のweight_modeを取得
            weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

            # 構造的分析
            calculator = StructuralTradeoffCalculator(
                design_case.network,
                performances_data,
                weight_mode
            )
            analysis = calculator.analyze()
            summary = calculator.get_tradeoff_summary()

            # 既存のトレードオフ比率も計算
            classic_result = TradeoffCalculator.calculate_single_case_tradeoff_ratio(
                design_case.network,
                performances_data
            )

            cases_results.append({
                'case_id': design_case.id,
                'case_name': design_case.name,
                'n_tradeoff_pairs': summary['n_tradeoff_pairs'],
                'n_synergy_pairs': summary['n_synergy_pairs'],
                'strongest_tradeoff': summary['strongest_tradeoff'],
                'classic_ratio': classic_result.get('ratio', 0.0),
                'classic_is_valid': classic_result.get('is_valid', False),
            })

            # トレードオフペアを収集（共通分析用）
            for pair in analysis['tradeoff_pairs']:
                all_tradeoff_pairs.append({
                    'case_id': design_case.id,
                    'perf_i': pair.get('perf_i_performance_id') or pair.get('perf_i_id'),
                    'perf_j': pair.get('perf_j_performance_id') or pair.get('perf_j_id'),
                    'cos_theta': pair['cos_theta'],
                })

        # 共通のトレードオフを抽出（全設計案で cos θ < 0 のペア）
        common_tradeoffs = _find_common_tradeoffs(all_tradeoff_pairs, len(project.design_cases))

        return {
            'cases': cases_results,
            'common_tradeoffs': common_tradeoffs,
            'project_summary': {
                'n_design_cases': len(project.design_cases),
                'n_performances': len(performances_data),
            }
        }
    except Exception as e:
        logger.error(f"Project structural tradeoff summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/tradeoff-comparison/{project_id}/{case_id}")
def compare_tradeoff_methods(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    既存手法と構造的手法のトレードオフ分析を比較

    両方の手法の結果を並べて表示し、違いを明確化

    Returns:
        {
            'classic': {...},  # 既存のTradeoffCalculatorの結果
            'structural': {...},  # 構造的分析の結果
            'comparison': {...},  # 比較結果
        }
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    design_case = next((dc for dc in project.design_cases if dc.id == case_id), None)
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        performances_data = [
            {'id': p.id, 'name': p.name, 'is_leaf': p.is_leaf}
            for p in project.performances
        ]

        # 設計案のweight_modeを取得
        weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

        result = calculate_with_both_methods(
            design_case.network,
            performances_data,
            weight_mode
        )

        return result
    except Exception as e:
        logger.error(f"Tradeoff comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


def _find_common_tradeoffs(all_pairs: List[Dict], n_cases: int) -> List[Dict]:
    """
    全設計案で共通のトレードオフペアを抽出

    Args:
        all_pairs: 全ケースのトレードオフペア
        n_cases: 設計案数

    Returns:
        共通トレードオフのリスト
    """
    if n_cases == 0:
        return []

    # ペアごとに出現回数をカウント
    pair_counts = {}
    pair_cos_thetas = {}

    for pair in all_pairs:
        # ペアのキーを正規化（順序を統一）
        key = tuple(sorted([pair['perf_i'], pair['perf_j']]))

        if key not in pair_counts:
            pair_counts[key] = 0
            pair_cos_thetas[key] = []

        pair_counts[key] += 1
        pair_cos_thetas[key].append(pair['cos_theta'])

    # 全設計案で共通のペア（出現回数 == n_cases）
    common = []
    for key, count in pair_counts.items():
        if count == n_cases:
            cos_thetas = pair_cos_thetas[key]
            common.append({
                'perf_i': key[0],
                'perf_j': key[1],
                'avg_cos_theta': sum(cos_thetas) / len(cos_thetas),
                'min_cos_theta': min(cos_thetas),
                'max_cos_theta': max(cos_thetas),
            })

    # 平均cos θが小さい順（強いトレードオフ順）
    common.sort(key=lambda x: x['avg_cos_theta'])

    return common


# =============================================================================
# 論文準拠指標 API（Chapter 7の定義に基づく）
# =============================================================================

@router.get("/paper-metrics/{project_id}/{case_id}")
def get_paper_metrics(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    論文準拠の指標を一括取得（Chapter 7）

    - 標高 H = Σ(W_i × U_i) / Σ(W_i)
    - エネルギー E = Σ(i<j) W_i × W_j × L(C_ij) / (Σ W_i)²
    - 構造的トレードオフ（cos θ と 内積 C_ij）

    既存の指標（classic_energy, tradeoff_ratio）も併記して比較可能

    Returns:
        {
            'height': {...},
            'energy': {...},  # 論文定義のエネルギー
            'classic_energy': float,  # 従来のエネルギー
            'structural_tradeoff': {...},
            'comparison': {...}  # 新旧指標の比較
        }
    """
    from app.services.structural_energy import (
        compute_structural_energy,
        compute_structural_height,
    )
    from app.services.energy_calculator import calculate_energy_for_case

    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    design_case = next((dc for dc in project.design_cases if dc.id == case_id), None)
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        # 性能の重みを取得
        performance_weights = design_case.performance_weights or {}

        # ネットワーク
        network = design_case.network
        if not network:
            raise HTTPException(status_code=400, detail="Design case has no network")

        # 設計案のweight_modeを取得
        weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

        # 1. 論文準拠エネルギー計算
        structural_energy_result = compute_structural_energy(
            network,
            performance_weights,
            weight_mode
        )

        # 2. 従来のエネルギー計算（比較用）
        classic_energy_result = None
        try:
            if design_case.performance_snapshot:
                from app.schemas.project import Performance
                case_performances = [Performance(**perf_data) for perf_data in design_case.performance_snapshot]
                classic_energy_result = calculate_energy_for_case(design_case, case_performances, db)
            else:
                classic_energy_result = calculate_energy_for_case(design_case, project.performances, db)
        except Exception as e:
            logger.warning(f"Classic energy calculation failed: {e}")

        classic_energy = classic_energy_result.get('total_energy', 0.0) if classic_energy_result else 0.0

        # 3. 効用ベクトルから標高を計算（既存の値を使用）
        utility_vector = design_case.utility_vector or {}
        height_result = compute_structural_height(utility_vector, performance_weights)

        # 既存の標高値との比較
        existing_H = None
        if design_case.mountain_position:
            existing_H = design_case.mountain_position.get('H')

        # 4. 構造的トレードオフ情報を整理
        structural_tradeoff = {
            'cos_theta_matrix': structural_energy_result['cos_theta_matrix'],
            'inner_product_matrix': structural_energy_result['inner_product_matrix'],
            'norms': structural_energy_result['norms'],
            'performance_ids': structural_energy_result['performance_ids'],
            'performance_labels': structural_energy_result['performance_labels'],
            'tradeoff_contributions': structural_energy_result['energy_contributions'],
        }

        # 5. 比較情報
        comparison = {
            'paper_energy': structural_energy_result['E'],
            'classic_energy': classic_energy,
            'energy_difference': structural_energy_result['E'] - classic_energy if classic_energy else None,
            'paper_height': height_result['H'],
            'existing_height': existing_H,
            'height_match': abs(height_result['H'] - existing_H) < 0.001 if existing_H is not None else None,
        }

        return {
            'height': height_result,
            'energy': {
                'E': structural_energy_result['E'],
                'total_energy_unnormalized': structural_energy_result['total_energy_unnormalized'],
                'normalization_factor': structural_energy_result['normalization_factor'],
                'n_tradeoff_pairs': structural_energy_result['metadata']['n_tradeoff_pairs'],
            },
            'classic_energy': classic_energy,
            'structural_tradeoff': structural_tradeoff,
            'metadata': structural_energy_result['metadata'],
            'comparison': comparison,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Paper metrics calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# =============================================================================
# 離散化信頼度 API（design.tex Chapter 6 準拠）
# =============================================================================

@router.get("/discretization-confidence/{project_id}/{case_id}")
def get_discretization_confidence_for_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    特定の設計案の離散化信頼度を計算

    論文(design.tex) Chapter 6 の理論に基づく符号保存確率・順序保存確率:
    - P_sign = Φ(|C̃_ij| / σ_δC)
    - P_order = Φ(|Δ̃| / σ_δΔ)
    """
    from app.services.discretization_confidence import analyze_discretization_confidence
    from app.services.weight_normalization import get_discretization_error
    from app.models.database import DesignCaseModel

    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        VALID_WEIGHT_MODES = {'discrete_3', 'discrete_5', 'discrete_7', 'continuous'}
        raw_mode = getattr(design_case, 'weight_mode', None) or 'discrete_7'
        weight_mode = raw_mode if raw_mode in VALID_WEIGHT_MODES else 'discrete_7'

        network = design_case.network
        if not network:
            return {
                'case_id': case_id,
                'case_name': design_case.name,
                'weight_mode': weight_mode,
                'is_discrete': weight_mode != 'continuous',
                'n_discrete_levels': None,
                'sign_preservation_probability': None,
                'order_preservation_probability': None,
                'sigma_eff': 0,
                'interpretation': 'No network data',
            }

        result = analyze_discretization_confidence(network, weight_mode)

        return {
            'case_id': case_id,
            'case_name': design_case.name,
            'weight_mode': weight_mode,
            'is_discrete': result['is_discrete'],
            'n_discrete_levels': result['n_discrete_levels'],
            'sign_preservation_probability': result['sign_preservation']['average'],
            'min_sign_preservation': result['sign_preservation']['min'],
            'order_preservation_probability': result['order_preservation']['average'],
            'sigma_eff': result['sigma_eff'],
            'connection_density': result.get('connection_density'),
            'B_AA_frobenius_norm': result.get('B_AA_frobenius_norm'),
            'interpretation': result['interpretation'],
        }

    except Exception as e:
        logger.error(f"Discretization confidence calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# ========== SCC分解（ループ検出）API ==========

@router.get("/scc/{project_id}/{case_id}")
def analyze_scc_for_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    設計案のネットワークに対してSCC分解を実行し、ループ構造を検出

    論文 design.tex 2398-2469行に基づく実装:
    - Tarjanアルゴリズムによる強連結成分（SCC）の検出
    - ループ内のスペクトル半径による収束判定
    - ループ解消方法の提案

    Returns:
        {
            'has_loops': bool,              # ループが存在するか
            'n_components_with_loops': int, # ループを含むSCCの数
            'components': [
                {
                    'nodes': List[str],          # SCC内のノードID
                    'edges': List,               # SCC内のエッジ
                    'spectral_radius': float,    # ρ(B_AA^(C_k))
                    'converges': bool,           # ρ < 1 なら True
                    'suggestions': List[Dict]    # 解消方法の提案
                }
            ],
            'all_attribute_nodes': List[str],
            'dag_after_condensation': List[Dict]
        }
    """
    from app.services.scc_analyzer import analyze_scc, scc_result_to_dict
    from app.models.database import DesignCaseModel

    # 設計案を取得
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()

    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        network = design_case.network
        if not network or not network.get('nodes'):
            return {
                "has_loops": False,
                "n_components_with_loops": 0,
                "components": [],
                "all_attribute_nodes": [],
                "dag_after_condensation": [],
                "message": "No network data available"
            }

        # SCC分解を実行
        result = analyze_scc(network)
        return scc_result_to_dict(result)

    except Exception as e:
        logger.error(f"SCC analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"SCC analysis error: {str(e)}")


@router.post("/scc-analyze")
def analyze_scc_direct(
    network: Dict,
):
    """
    ネットワーク構造を直接受け取ってSCC分解を実行（保存前のプレビュー用）

    Request Body:
        {
            "nodes": [...],
            "edges": [...]
        }

    Returns:
        SCCAnalysisResult (same as GET /scc/{project_id}/{case_id})
    """
    from app.services.scc_analyzer import analyze_scc, scc_result_to_dict

    try:
        if not network or not network.get('nodes'):
            return {
                "has_loops": False,
                "n_components_with_loops": 0,
                "components": [],
                "all_attribute_nodes": [],
                "dag_after_condensation": [],
                "message": "No network data provided"
            }

        # SCC分解を実行
        result = analyze_scc(network)
        return scc_result_to_dict(result)

    except Exception as e:
        logger.error(f"SCC analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"SCC analysis error: {str(e)}")


@router.get("/scc-summary/{project_id}")
def analyze_scc_summary(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    プロジェクト内の全設計案に対するSCC分解のサマリー

    Returns:
        {
            'project_id': str,
            'n_cases': int,
            'cases_with_loops': int,
            'total_loop_components': int,
            'summary': [
                {
                    'case_id': str,
                    'case_name': str,
                    'has_loops': bool,
                    'n_components': int,
                    'all_converge': bool
                }
            ]
        }
    """
    from app.services.scc_analyzer import analyze_scc

    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        summary = []
        cases_with_loops = 0
        total_loop_components = 0

        for design_case in project.design_cases:
            network = design_case.network
            if not network or not network.get('nodes'):
                summary.append({
                    'case_id': design_case.id,
                    'case_name': design_case.name,
                    'has_loops': False,
                    'n_components': 0,
                    'all_converge': True
                })
                continue

            result = analyze_scc(network)

            if result.has_loops:
                cases_with_loops += 1
                total_loop_components += len(result.components)

            all_converge = all(comp.converges for comp in result.components) if result.components else True

            summary.append({
                'case_id': design_case.id,
                'case_name': design_case.name,
                'has_loops': result.has_loops,
                'n_components': len(result.components),
                'all_converge': all_converge
            })

        return {
            'project_id': project_id,
            'n_cases': len(project.design_cases),
            'cases_with_loops': cases_with_loops,
            'total_loop_components': total_loop_components,
            'summary': summary
        }

    except Exception as e:
        logger.error(f"SCC summary error: {e}")
        raise HTTPException(status_code=500, detail=f"SCC summary error: {str(e)}")


# ========== Shapley値（寄与度分解）API ==========

@router.get("/shapley/{project_id}/{case_id}/{perf_i_id}/{perf_j_id}")
def compute_shapley_for_pair(
    project_id: str,
    case_id: str,
    perf_i_id: str,
    perf_j_id: str,
    method: str = "auto",
    db: Session = Depends(get_db)
):
    """
    指定した性能ペアに対するShapley値を計算

    論文 design.tex 2849-2913行に基づく実装:
    - トレードオフ C_ij を各属性（Property）の寄与に分解
    - Shapley値の加法性: Σφ_k = C_ij

    Args:
        project_id: プロジェクトID
        case_id: 設計案ID
        perf_i_id: 性能iのID
        perf_j_id: 性能jのID
        method: 'exact', 'monte_carlo', 'auto'

    Returns:
        {
            'perf_i': {'idx': int, 'name': str},
            'perf_j': {'idx': int, 'name': str},
            'C_ij': float,
            'cos_theta': float,
            'relationship': 'tradeoff' | 'synergy' | 'neutral',
            'shapley_values': [
                {'property_idx': int, 'property_name': str, 'phi': float, 'percentage': float}
            ],
            'sum_check': float,
            'additivity_error': float,
            'computation': {'method': str, 'n_properties': int, 'time_ms': float}
        }
    """
    from app.models.database import DesignCaseModel, PerformanceModel
    from app.services.matrix_utils import build_adjacency_matrices, compute_total_effect_matrix
    from app.services.shapley_calculator import (
        compute_shapley_for_performance_pair,
        shapley_result_to_dict,
        estimate_computation_cost
    )

    # 設計案を取得
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()

    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        network = design_case.network
        if not network or not network.get('nodes'):
            raise HTTPException(status_code=400, detail="No network data available")

        # 隣接行列を構築（ネットワークノードIDベース）
        matrices = build_adjacency_matrices(network)
        if matrices is None or 'B_PA' not in matrices:
            raise HTTPException(status_code=400, detail="Failed to build adjacency matrices")

        B_PA = matrices['B_PA']
        B_AA = matrices['B_AA']
        B_AV = matrices['B_AV']
        perf_node_ids = matrices['node_ids']['P']  # ネットワークノードID (perf-xxx)
        perf_labels = matrices['node_labels']['P']
        var_ids = matrices['node_ids']['V']
        var_labels = matrices['node_labels']['V']
        perf_id_map = matrices.get('performance_id_map', {})  # node_id -> db_perf_id

        # IDマッピング: ネットワークノードID または データベースIDを受け付ける
        perf_i_idx = None
        perf_j_idx = None

        for idx, node_id in enumerate(perf_node_ids):
            # ネットワークノードIDで一致チェック
            if node_id == perf_i_id:
                perf_i_idx = idx
            if node_id == perf_j_id:
                perf_j_idx = idx
            # データベースIDで一致チェック (performance_id_mapを逆引き)
            db_id = perf_id_map.get(node_id)
            if db_id == perf_i_id:
                perf_i_idx = idx
            if db_id == perf_j_id:
                perf_j_idx = idx

        if perf_i_idx is None or perf_j_idx is None:
            raise HTTPException(status_code=404, detail=f"Performance not found: i={perf_i_id}, j={perf_j_id}")

        T_result = compute_total_effect_matrix(B_PA, B_AA, B_AV)
        T = T_result['T']

        # 計算コスト見積もり
        cost = estimate_computation_cost(T.shape[1])
        if cost['warning'] == 'high' and method == 'auto':
            logger.warning(f"High computation cost for Shapley: {cost['message']}")

        # Shapley値を計算
        result = compute_shapley_for_performance_pair(
            T, perf_i_idx, perf_j_idx,
            method=method
        )

        return shapley_result_to_dict(result, perf_labels, var_labels)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shapley calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Shapley calculation error: {str(e)}")


@router.get("/shapley-all/{project_id}/{case_id}")
def compute_all_shapley(
    project_id: str,
    case_id: str,
    method: str = "auto",
    only_tradeoffs: bool = True,
    db: Session = Depends(get_db)
):
    """
    設計案の全性能ペアに対するShapley値を計算

    Args:
        project_id: プロジェクトID
        case_id: 設計案ID
        method: 'exact', 'monte_carlo', 'auto'
        only_tradeoffs: Trueの場合、トレードオフ関係のみ

    Returns:
        {
            'case_id': str,
            'case_name': str,
            'n_pairs': int,
            'pairs': [...]
        }
    """
    from app.models.database import DesignCaseModel, PerformanceModel
    from app.services.matrix_utils import build_adjacency_matrices, compute_total_effect_matrix
    from app.services.shapley_calculator import compute_all_pairwise_shapley

    # 設計案を取得
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()

    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    # 性能情報を取得
    performances = db.query(PerformanceModel).filter(
        PerformanceModel.project_id == project_id,
        PerformanceModel.is_leaf == True
    ).all()

    perf_id_to_idx = {p.id: idx for idx, p in enumerate(performances)}
    perf_names = [p.name for p in performances]

    try:
        network = design_case.network
        if not network or not network.get('nodes'):
            return {
                "case_id": case_id,
                "case_name": design_case.name,
                "n_pairs": 0,
                "pairs": [],
                "message": "No network data available"
            }

        # 総効果行列を計算
        matrices = build_adjacency_matrices(network, perf_id_to_idx)
        if matrices is None:
            return {
                "case_id": case_id,
                "case_name": design_case.name,
                "n_pairs": 0,
                "pairs": [],
                "message": "Failed to build adjacency matrices"
            }

        B_PA, B_AA, B_AV, var_ids, attr_ids = matrices
        T_result = compute_total_effect_matrix(B_PA, B_AA, B_AV)
        T = T_result['T']

        # 属性名を取得
        nodes = network.get('nodes', [])
        property_names = []
        for var_id in var_ids:
            node = next((n for n in nodes if n['id'] == var_id), None)
            if node:
                property_names.append(node.get('label', var_id))
            else:
                property_names.append(var_id)

        # 全ペアのShapley値を計算
        pairs = compute_all_pairwise_shapley(
            T, perf_names, property_names,
            method=method,
            only_tradeoffs=only_tradeoffs
        )

        return {
            "case_id": case_id,
            "case_name": design_case.name,
            "n_pairs": len(pairs),
            "pairs": pairs
        }

    except Exception as e:
        logger.error(f"Shapley all calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Shapley calculation error: {str(e)}")


@router.get("/shapley-cost/{n_properties}")
def estimate_shapley_cost(n_properties: int):
    """
    Shapley値計算のコスト見積もり

    Args:
        n_properties: 属性（変数）の数

    Returns:
        {
            'n_properties': int,
            'n_subsets': int,
            'estimated_time_ms': float,
            'warning': 'low' | 'medium' | 'high',
            'recommendation': 'exact' | 'monte_carlo',
            'message': str
        }
    """
    from app.services.shapley_calculator import estimate_computation_cost

    if n_properties < 0 or n_properties > 30:
        raise HTTPException(status_code=400, detail="n_properties must be between 0 and 30")

    return estimate_computation_cost(n_properties)


# ========== ノードShapley値API（V ∪ A がプレイヤー） ==========

@router.get("/node-shapley/{project_id}/{case_id}/{perf_i_id}/{perf_j_id}")
def compute_node_shapley_for_pair(
    project_id: str,
    case_id: str,
    perf_i_id: str,
    perf_j_id: str,
    method: str = "auto",
    db: Session = Depends(get_db)
):
    """
    指定した性能ペアに対するノードShapley値を計算（V ∪ A がプレイヤー）

    トレードオフ C_ij を Variable と Attribute の寄与に分解:
    - プレイヤー = V ∪ A = {V_1, ..., V_m, A_1, ..., A_l}
    - Shapley値の加法性: Σφ_k = C_ij

    Args:
        project_id: プロジェクトID
        case_id: 設計案ID
        perf_i_id: 性能iのID
        perf_j_id: 性能jのID
        method: 'exact', 'monte_carlo', 'auto'

    Returns:
        {
            'perf_i': {'idx': int, 'name': str},
            'perf_j': {'idx': int, 'name': str},
            'C_ij': float,
            'cos_theta': float,
            'relationship': 'tradeoff' | 'synergy' | 'neutral',
            'node_shapley_values': [
                {
                    'node_id': str, 'node_label': str, 'node_type': 'V' | 'A',
                    'layer': int, 'phi': float, 'percentage': float
                }
            ],
            'sum_check': float,
            'additivity_error': float,
            'computation': {'method': str, 'n_nodes': int, 'n_variables': int, 'n_attributes': int, 'time_ms': float}
        }
    """
    from app.models.database import DesignCaseModel
    from app.services.matrix_utils import build_adjacency_matrices
    from app.services.shapley_calculator import (
        compute_node_shapley_for_performance_pair,
        node_shapley_result_to_dict,
        extract_node_info
    )

    # 設計案を取得
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()

    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        network = design_case.network
        if not network or not network.get('nodes'):
            raise HTTPException(status_code=400, detail="No network data available")

        # 設計案のweight_modeを取得（デフォルトは'discrete_7'）
        weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

        # 隣接行列を構築（weight_modeを渡す）
        matrices = build_adjacency_matrices(network, weight_mode)
        if matrices is None or 'B_PA' not in matrices:
            raise HTTPException(status_code=400, detail="Failed to build adjacency matrices")

        perf_node_ids = matrices['node_ids']['P']
        perf_labels = matrices['node_labels']['P']
        perf_id_map = matrices.get('performance_id_map', {})

        # IDマッピング
        perf_i_idx = None
        perf_j_idx = None

        for idx, node_id in enumerate(perf_node_ids):
            if node_id == perf_i_id:
                perf_i_idx = idx
            if node_id == perf_j_id:
                perf_j_idx = idx
            db_id = perf_id_map.get(node_id)
            if db_id == perf_i_id:
                perf_i_idx = idx
            if db_id == perf_j_id:
                perf_j_idx = idx

        if perf_i_idx is None or perf_j_idx is None:
            raise HTTPException(status_code=404, detail=f"Performance not found: i={perf_i_id}, j={perf_j_id}")

        # ノードShapley値を計算
        result = compute_node_shapley_for_performance_pair(
            network=network,
            matrices=matrices,
            perf_i=perf_i_idx,
            perf_j=perf_j_idx,
            method=method
        )

        # ノード情報を取得（レスポンス変換用）
        node_infos = extract_node_info(network, matrices)

        return node_shapley_result_to_dict(result, node_infos, perf_labels)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Node Shapley calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Node Shapley calculation error: {str(e)}")


# ========== エッジShapley値API ==========

@router.get("/edge-shapley/{project_id}/{case_id}/{perf_i_id}/{perf_j_id}")
def compute_edge_shapley_for_pair(
    project_id: str,
    case_id: str,
    perf_i_id: str,
    perf_j_id: str,
    method: str = "auto",
    db: Session = Depends(get_db)
):
    """
    指定した性能ペアに対するエッジShapley値を計算

    論文に基づくエッジShapley分解:
    - トレードオフ C_ij を各エッジの寄与に分解
    - Shapley値の加法性: Σφ_e = C_ij

    Args:
        project_id: プロジェクトID
        case_id: 設計案ID
        perf_i_id: 性能iのID
        perf_j_id: 性能jのID
        method: 'exact', 'monte_carlo', 'auto'

    Returns:
        {
            'perf_i': {'idx': int, 'name': str},
            'perf_j': {'idx': int, 'name': str},
            'C_ij': float,
            'cos_theta': float,
            'relationship': 'tradeoff' | 'synergy' | 'neutral',
            'edge_shapley_values': [
                {
                    'edge_id': str, 'source_id': str, 'target_id': str,
                    'source_label': str, 'target_label': str,
                    'edge_type': str, 'phi': float, 'percentage': float
                }
            ],
            'sum_check': float,
            'additivity_error': float,
            'computation': {'method': str, 'n_edges': int, 'time_ms': float}
        }
    """
    from app.models.database import DesignCaseModel
    from app.services.matrix_utils import build_adjacency_matrices
    from app.services.shapley_calculator import (
        compute_edge_shapley_for_performance_pair,
        edge_shapley_result_to_dict,
        extract_edge_info
    )

    # 設計案を取得
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()

    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    try:
        network = design_case.network
        if not network or not network.get('nodes'):
            raise HTTPException(status_code=400, detail="No network data available")

        # 設計案のweight_modeを取得（デフォルトは'discrete_7'）
        weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

        # 隣接行列を構築（weight_modeを渡す）
        matrices = build_adjacency_matrices(network, weight_mode)
        if matrices is None or 'B_PA' not in matrices:
            raise HTTPException(status_code=400, detail="Failed to build adjacency matrices")

        perf_node_ids = matrices['node_ids']['P']
        perf_labels = matrices['node_labels']['P']
        perf_id_map = matrices.get('performance_id_map', {})

        # IDマッピング
        perf_i_idx = None
        perf_j_idx = None

        for idx, node_id in enumerate(perf_node_ids):
            if node_id == perf_i_id:
                perf_i_idx = idx
            if node_id == perf_j_id:
                perf_j_idx = idx
            db_id = perf_id_map.get(node_id)
            if db_id == perf_i_id:
                perf_i_idx = idx
            if db_id == perf_j_id:
                perf_j_idx = idx

        if perf_i_idx is None or perf_j_idx is None:
            raise HTTPException(status_code=404, detail=f"Performance not found: i={perf_i_id}, j={perf_j_id}")

        # weight_mode を取得
        weight_mode = getattr(design_case, 'weight_mode', 'discrete_7') or 'discrete_7'

        # エッジShapley値を計算
        result = compute_edge_shapley_for_performance_pair(
            network=network,
            matrices=matrices,
            perf_i=perf_i_idx,
            perf_j=perf_j_idx,
            weight_mode=weight_mode,
            method=method
        )

        # エッジ情報を取得（レスポンス変換用）
        edge_infos = extract_edge_info(network, matrices, weight_mode)

        return edge_shapley_result_to_dict(result, edge_infos, perf_labels)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Edge Shapley calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Edge Shapley calculation error: {str(e)}")
