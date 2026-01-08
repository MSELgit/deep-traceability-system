from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

from app.models.database import get_db, ProjectModel
from app.schemas.project import MountainPosition
from app.services.mountain_calculator import calculate_mountain_positions
from app.services.energy_calculator import calculate_energy_for_project, calculate_energy_for_case
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
    プロジェクトの全設計案についてエネルギーを計算
    
    Args:
        project_id: プロジェクトID
    
    Returns:
        各設計案のエネルギー {case_id, case_name, total_energy, partial_energies, match_matrix}
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        results = calculate_energy_for_project(project, db)
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
    特定の設計案のエネルギーを計算
    
    Args:
        project_id: プロジェクトID
        case_id: 設計案ID
    
    Returns:
        {total_energy, partial_energies, match_matrix}
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    design_case = next((dc for dc in project.design_cases if dc.id == case_id), None)
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    try:
        if design_case.performance_snapshot:
            from app.schemas.project import Performance
            case_performances = [Performance(**perf_data) for perf_data in design_case.performance_snapshot]
            result = calculate_energy_for_case(design_case, case_performances, db)
        else:
            result = calculate_energy_for_case(design_case, project.performances, db)
        
        return result
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

        result = calculate_structural_tradeoff_for_case(
            design_case.network,
            performances_data
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
            # 構造的分析
            calculator = StructuralTradeoffCalculator(
                design_case.network,
                performances_data
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

        result = calculate_with_both_methods(
            design_case.network,
            performances_data
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
