from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from ..fuzzy.models import PerformanceMatrix, CalculationResult
from ..fuzzy.calculations import FuzzyCalculator
from ..fuzzy.engine import FuzzyEngine 
from ..fuzzy.uncertainty_engine import UncertaintyAnalysis
import numpy as np

from datetime import datetime, timezone
import json
import uuid
from ..fuzzy.models import (
    PerformanceMatrix, CalculationResult, 
    ProjectCreateRequest, ProjectUpdateRequest, 
    ProjectData, WorkDataRequest
)

# Neo4j接続（main.pyからimport）
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

router = APIRouter(prefix="/api/fuzzy", tags=["fuzzy"])

def safe_parse_json_field(json_str: str, field_name: str):
    """JSON文字列を安全にパースする関数"""
    if not json_str:
        return None
    
    try:
        parsed_data = json.loads(json_str)
        return parsed_data
    except Exception as e:
        print(f"{field_name} JSON parse エラー: {str(e)}")
        return None

def safe_create_calculation_result(calc_data):
    """計算結果データを安全にCalculationResultに変換"""
    if not calc_data:
        return None
    
    try:
        if isinstance(calc_data, dict):
            return CalculationResult(**calc_data)
        elif hasattr(calc_data, 'energy'):
            return calc_data
        else:
            print(f"不明なcalculation_result形式: {type(calc_data)}")
            return None
    except Exception as e:
        print(f"CalculationResult作成エラー: {str(e)}")
        return None

@router.post("/calculate", response_model=Dict[str, Any])
async def calculate_fuzzy_energy(matrix: PerformanceMatrix):
    """ファジィエネルギー計算"""
    try:
        calc = FuzzyCalculator()
        energy_crisp, match_matrix_fuzzy = calc.calculate_energy(matrix)

        match_matrix_crisp = []
        for i in range(len(match_matrix_fuzzy)):
            row_crisp = []
            for j in range(len(match_matrix_fuzzy[i])):
                crisp_val = FuzzyEngine.defuzzify_centroid(match_matrix_fuzzy[i][j])
                row_crisp.append(crisp_val)
            match_matrix_crisp.append(row_crisp)

        chart_data = []
        n = matrix.n_performances
        q_squared_for_chart = 1.0 

        for i in range(n):
            for j in range(i+1, n):  # i < j の上三角部分のみ
                if i < len(match_matrix_crisp) and j < len(match_matrix_crisp[i]):
                    match_crisp_val = match_matrix_crisp[i][j]
                    
                    imp_i = matrix.importance[i] if i < len(matrix.importance) else 3
                    imp_j = matrix.importance[j] if j < len(matrix.importance) else 3
                    
                    r_ij = np.sqrt(2 * (1 - match_crisp_val))
                    
                    if r_ij > 1e-10:
                        z_val = (imp_i * imp_j * q_squared_for_chart) / r_ij
                        
                        # フロントエンド用に下三角座標系に変換
                        chart_data.append({
                            "x": j,  # 元のj（列）を行に
                            "y": i,  # 元のi（行）を列に  
                            "z": z_val
                        })

        return {
            "energy": energy_crisp,
            "match_matrix": match_matrix_crisp,
            "chart_data": chart_data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "OK", "module": "fuzzy_engine"}

@router.post("/projects/", response_model=ProjectData)
async def create_project(project: ProjectCreateRequest):
    """設計案作成"""
    try:
        project_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        
        with driver.session() as session:
            session.run(
                """
                CREATE (p:DesignProject {
                    id: $id,
                    name: $name,
                    status: 'draft',
                    csv_data: null,
                    matrix_data: null,
                    fuzzy_weights: null,
                    calculation_result: null,
                    created_at: $created_at,
                    updated_at: $created_at
                })
                """,
                id=project_id,
                name=project.name,
                created_at=created_at.isoformat()
            )
        
        return ProjectData(
            id=project_id,
            name=project.name,
            status='draft',
            created_at=created_at,
            updated_at=created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/", response_model=List[ProjectData])
async def get_all_projects():
    """設計案一覧取得 - 安全なJSON処理版"""
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (p:DesignProject)
                RETURN p.id, p.name, p.status, p.csv_data, p.matrix_data, 
                       p.fuzzy_weights, p.calculation_result, p.created_at, p.updated_at
                ORDER BY p.updated_at DESC
                """
            )
            
            projects = []
            for record in result:
                try:
                    csv_data = safe_parse_json_field(record["p.csv_data"], "csv_data")
                    matrix_data = safe_parse_json_field(record["p.matrix_data"], "matrix_data")
                    fuzzy_weights = safe_parse_json_field(record["p.fuzzy_weights"], "fuzzy_weights")
                    calc_result_raw = safe_parse_json_field(record["p.calculation_result"], "calculation_result")
                    calculation_result = safe_create_calculation_result(calc_result_raw)
                    
                    project = ProjectData(
                        id=record["p.id"],
                        name=record["p.name"],
                        status=record["p.status"],
                        csv_data=csv_data,
                        matrix_data=matrix_data,
                        fuzzy_weights=fuzzy_weights,
                        calculation_result=calculation_result,
                        created_at=datetime.fromisoformat(record["p.created_at"]),
                        updated_at=datetime.fromisoformat(record["p.updated_at"])
                    )
                    
                    projects.append(project)
                    
                except Exception as record_error:
                    print(f"レコード処理エラー {record['p.name']}: {str(record_error)}")
                    continue
            return projects
            
    except Exception as e:
        print(f"プロジェクト一覧取得エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load projects: {str(e)}")

@router.get("/projects/{project_id}", response_model=ProjectData)
async def get_project(project_id: str):
    """設計案単体取得 - 安全なJSON処理版（重複削除）"""
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (p:DesignProject {id: $id})
                RETURN p.id, p.name, p.status, p.csv_data, p.matrix_data, 
                       p.fuzzy_weights, p.calculation_result, p.created_at, p.updated_at
                """,
                id=project_id
            )
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Project not found")
            
            csv_data = safe_parse_json_field(record["p.csv_data"], "csv_data")
            matrix_data = safe_parse_json_field(record["p.matrix_data"], "matrix_data")
            fuzzy_weights = safe_parse_json_field(record["p.fuzzy_weights"], "fuzzy_weights")
            
            calc_result_raw = safe_parse_json_field(record["p.calculation_result"], "calculation_result")
            calculation_result = safe_create_calculation_result(calc_result_raw)
            
            project = ProjectData(
                id=record["p.id"],
                name=record["p.name"],
                status=record["p.status"],
                csv_data=csv_data,
                matrix_data=matrix_data,
                fuzzy_weights=fuzzy_weights,
                calculation_result=calculation_result,
                created_at=datetime.fromisoformat(record["p.created_at"]),
                updated_at=datetime.fromisoformat(record["p.updated_at"])
            )
            return project
            
    except Exception as e:
        print(f"プロジェクト単体取得エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load project: {str(e)}")

@router.put("/projects/{project_id}", response_model=ProjectData)
async def update_project(project_id: str, project: ProjectUpdateRequest):
    """設計案更新（名前・ステータス）"""
    try:
        updated_at = datetime.now(timezone.utc)
        
        set_clauses = ["p.updated_at = $updated_at"]
        params = {"id": project_id, "updated_at": updated_at.isoformat()}
        
        if project.name is not None:
            set_clauses.append("p.name = $name")
            params["name"] = project.name
            
        if project.status is not None:
            set_clauses.append("p.status = $status")
            params["status"] = project.status
        
        set_query = ", ".join(set_clauses)
        
        with driver.session() as session:
            session.run(
                f"""
                MATCH (p:DesignProject {{id: $id}})
                SET {set_query}
                """,
                **params
            )
            
            return await get_project(project_id)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/save", response_model=Dict[str, str])
async def save_current_work(project_id: str, work_data: WorkDataRequest):
    """現在の作業データ保存"""
    try:
        updated_at = datetime.now(timezone.utc)

        try:
            if work_data.calculation_result:
                calc_result_dict = work_data.calculation_result.dict() if hasattr(work_data.calculation_result, 'dict') else work_data.calculation_result
                calc_result_json = json.dumps(calc_result_dict)
            else:
                calc_result_json = None
        except Exception as json_error:
            calc_result_json = None
        
        with driver.session() as session:
            session.run(
                """
                MATCH (p:DesignProject {id: $id})
                SET p.csv_data = $csv_data,
                    p.matrix_data = $matrix_data,
                    p.fuzzy_weights = $fuzzy_weights,
                    p.calculation_result = $calculation_result,
                    p.status = $status,
                    p.updated_at = $updated_at
                """,
                id=project_id,
                csv_data=json.dumps(work_data.csv_data) if work_data.csv_data else None,
                matrix_data=json.dumps(work_data.matrix_data) if work_data.matrix_data else None,
                fuzzy_weights=json.dumps(work_data.fuzzy_weights) if work_data.fuzzy_weights else None,
                calculation_result=calc_result_json,
                status=work_data.status,
                updated_at=updated_at.isoformat()
            )
        
        return {"message": "Work data saved successfully", "project_id": project_id}
        
    except Exception as e:
        print(f"保存エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")

@router.delete("/projects/{project_id}", response_model=Dict[str, str])
async def delete_project(project_id: str):
    """設計案削除"""
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (p:DesignProject {id: $id})
                DELETE p
                RETURN count(p) as deleted_count
                """,
                id=project_id
            )
            
            record = result.single()
            if record["deleted_count"] == 0:
                raise HTTPException(status_code=404, detail="Project not found")
        
        return {"message": "Project deleted successfully", "project_id": project_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# back/app/routers/fuzzy_api.py の uncertainty-analysis エンドポイントを修正
@router.post("/projects/{project_id}/uncertainty-analysis")
async def run_uncertainty_analysis(
    project_id: str, 
    max_scenarios: int = 1000,
    debug: bool = True
):
    """不確実性分析API（軽量版）"""
    try:
        project_data = await get_project(project_id)
        if isinstance(project_data, dict):
            calculation_result = project_data.get('calculation_result')
            csv_data = project_data.get('csv_data')
            fuzzy_weights = project_data.get('fuzzy_weights')
            project_name = project_data.get('name', 'Unknown')
        else:
            # オブジェクト形式でアクセス
            calculation_result = getattr(project_data, 'calculation_result', None)
            csv_data = getattr(project_data, 'csv_data', None)
            fuzzy_weights = getattr(project_data, 'fuzzy_weights', None)
            project_name = getattr(project_data, 'name', 'Unknown')
        
        # 必要データの確認
        if not calculation_result:
            raise HTTPException(status_code=400, detail="計算結果が必要です")
        
        if not csv_data:
            raise HTTPException(status_code=400, detail="CSVデータが必要です")
        
        if not fuzzy_weights:
            raise HTTPException(status_code=400, detail="ファジィ重みが必要です")
        
        # CSV_dataの詳細構造確認
        if isinstance(csv_data, dict):
            # integrated内にデータがある場合
            if 'integrated' in csv_data:
                actual_csv_data = csv_data['integrated']
            else:
                actual_csv_data = csv_data
        else:
            actual_csv_data = csv_data
        
        current_energy = calculation_result.get('energy') if isinstance(calculation_result, dict) else calculation_result.energy
        importance = actual_csv_data.get('importance') if isinstance(actual_csv_data, dict) else actual_csv_data.importance
        features = actual_csv_data.get('features') if isinstance(actual_csv_data, dict) else actual_csv_data.features
        performances = actual_csv_data.get('performances') if isinstance(actual_csv_data, dict) else actual_csv_data.performances
        
        analyzer = UncertaintyAnalysis(
            current_energy=current_energy,
            importance=importance,
            features=features,
            performances=performances,
            existing_weights=fuzzy_weights,
            debug=debug
        )
        
        result = analyzer.run_lightweight_analysis(max_scenarios)
        
        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project_name,
            "analysis_result": result
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Exception詳細: {type(e).__name__}: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"分析エラー: {type(e).__name__}: {str(e)}")
    
@router.get("/debug/project-structure/{project_id}")
async def debug_project_structure(project_id: str):
    """プロジェクトデータ構造の詳細確認"""
    try:
        project_data = await get_project(project_id)
        
        def analyze_structure(obj, path="root"):
            """オブジェクト構造を再帰的に分析"""
            if isinstance(obj, dict):
                return {
                    "type": "dict",
                    "keys": list(obj.keys()),
                    "sample_values": {k: analyze_structure(v, f"{path}.{k}") 
                                    for k, v in list(obj.items())[:3]}  # 最初の3個のみ
                }
            elif isinstance(obj, list):
                return {
                    "type": "list",
                    "length": len(obj),
                    "sample_items": [analyze_structure(item, f"{path}[{i}]") 
                                   for i, item in enumerate(obj[:3])]  # 最初の3個のみ
                }
            else:
                return {
                    "type": type(obj).__name__,
                    "value": str(obj)[:100] + ("..." if len(str(obj)) > 100 else "")
                }
        
        structure = analyze_structure(project_data)
        
        return {
            "project_id": project_id,
            "data_structure": structure
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "project_id": project_id
        }