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
