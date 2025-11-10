# backend/app/api/calculations.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.database import get_db, ProjectModel
from app.schemas.project import MountainPosition
# from app.services.hhi_calculator import calculate_hhi_for_project  # HHI分析削除
from app.services.mountain_calculator import calculate_mountain_positions
from app.services.energy_calculator import calculate_energy_for_project, calculate_energy_for_case

router = APIRouter()


# @router.post("/hhi/{project_id}", response_model=List[HHIResult])
# def calculate_project_hhi(project_id: str, db: Session = Depends(get_db)):
#     """
#     プロジェクトの全性能についてHHI値とp²値を計算
#     
#     Args:
#         project_id: プロジェクトID
#     
#     Returns:
#         各性能のHHI値、p²値、重み、子要素数
#     """
#     project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
#     
#     try:
#         results = calculate_hhi_for_project(project, db)
#         return results
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


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
        return positions
    except Exception as e:
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
        result = calculate_energy_for_case(design_case, project.performances, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
