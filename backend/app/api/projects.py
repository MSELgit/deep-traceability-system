# backend/app/api/projects.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import uuid
import json

from app.models.database import (
    get_db, ProjectModel, StakeholderModel, NeedModel, PerformanceModel,
    DesignCaseModel, StakeholderNeedRelationModel, NeedPerformanceRelationModel
)
from app.schemas.project import (
    Project, ProjectCreate, Stakeholder, StakeholderCreate,
    Need, NeedCreate, Performance, PerformanceCreate,
    DesignCase, DesignCaseCreate, DesignCaseUpdate, StakeholderNeedRelation, NeedPerformanceRelation,
    UtilityFunctionData, MountainPosition, NetworkStructure, NetworkNode, NetworkEdge
)

router = APIRouter()


# ========== プロジェクト ==========

@router.post("/", response_model=Project)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """新規プロジェクトを作成"""
    db_project = ProjectModel(
        id=str(uuid.uuid4()),
        name=project.name,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[Project])
def list_projects(db: Session = Depends(get_db)):
    """全プロジェクトを取得"""
    return db.query(ProjectModel).all()


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """特定のプロジェクトを取得"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 性能のis_leafを実際の子の存在に基づいて再計算
    performance_ids = {p.id for p in project.performances}
    for performance in project.performances:
        # この性能を親として持つ子が存在するか確認
        has_children = any(p.parent_id == performance.id for p in project.performances)
        performance.is_leaf = not has_children
    
    # 設計案のperformance_snapshotを明示的に設定（@propertyの値をインスタンス変数にコピー）
    for dc in project.design_cases:
        # @propertyの値を一時的なインスタンス変数として保存（Pydanticが読み取れるように）
        dc._performance_snapshot_temp = dc.performance_snapshot
    
    return project


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, project: ProjectCreate, db: Session = Depends(get_db)):
    """プロジェクトを更新"""
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_project.name = project.name
    db_project.description = project.description
    db.commit()
    db.refresh(db_project)
    return db_project


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトを削除"""
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted successfully"}


# ========== ステークホルダー ==========

@router.post("/{project_id}/stakeholders", response_model=Stakeholder)
def create_stakeholder(
    project_id: str,
    stakeholder: StakeholderCreate,
    db: Session = Depends(get_db)
):
    """ステークホルダーを追加"""
    # プロジェクト存在確認
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_stakeholder = StakeholderModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=stakeholder.name,
        category=stakeholder.category,
        votes=stakeholder.votes,
        description=stakeholder.description
    )
    db.add(db_stakeholder)
    db.commit()
    db.refresh(db_stakeholder)
    return db_stakeholder


@router.get("/{project_id}/stakeholders", response_model=List[Stakeholder])
def list_stakeholders(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトのステークホルダー一覧を取得"""
    return db.query(StakeholderModel).filter(StakeholderModel.project_id == project_id).all()


@router.put("/{project_id}/stakeholders/{stakeholder_id}", response_model=Stakeholder)
def update_stakeholder(
    project_id: str,
    stakeholder_id: str,
    stakeholder: StakeholderCreate,
    db: Session = Depends(get_db)
):
    """ステークホルダーを更新"""
    db_stakeholder = db.query(StakeholderModel).filter(
        StakeholderModel.id == stakeholder_id,
        StakeholderModel.project_id == project_id
    ).first()
    if not db_stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    
    db_stakeholder.name = stakeholder.name
    db_stakeholder.category = stakeholder.category
    db_stakeholder.votes = stakeholder.votes
    db_stakeholder.description = stakeholder.description
    db.commit()
    db.refresh(db_stakeholder)
    return db_stakeholder


@router.delete("/{project_id}/stakeholders/{stakeholder_id}")
def delete_stakeholder(project_id: str, stakeholder_id: str, db: Session = Depends(get_db)):
    """ステークホルダーを削除"""
    db_stakeholder = db.query(StakeholderModel).filter(
        StakeholderModel.id == stakeholder_id,
        StakeholderModel.project_id == project_id
    ).first()
    if not db_stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    
    # 関連するStakeholderNeedRelationを削除
    db.query(StakeholderNeedRelationModel).filter(
        StakeholderNeedRelationModel.project_id == project_id,
        StakeholderNeedRelationModel.stakeholder_id == stakeholder_id
    ).delete()
    
    db.delete(db_stakeholder)
    db.commit()
    return {"message": "Stakeholder deleted successfully"}


# ========== ニーズ ==========

@router.post("/{project_id}/needs", response_model=Need)
def create_need(
    project_id: str,
    need: NeedCreate,
    db: Session = Depends(get_db)
):
    """ニーズを追加"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_need = NeedModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=need.name,
        category=need.category,
        description=need.description
    )
    db.add(db_need)
    db.commit()
    db.refresh(db_need)
    return db_need


@router.get("/{project_id}/needs", response_model=List[Need])
def list_needs(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトのニーズ一覧を取得"""
    return db.query(NeedModel).filter(NeedModel.project_id == project_id).all()


@router.put("/{project_id}/needs/{need_id}", response_model=Need)
def update_need(
    project_id: str,
    need_id: str,
    need: NeedCreate,
    db: Session = Depends(get_db)
):
    """ニーズを更新"""
    db_need = db.query(NeedModel).filter(
        NeedModel.id == need_id,
        NeedModel.project_id == project_id
    ).first()
    if not db_need:
        raise HTTPException(status_code=404, detail="Need not found")
    
    db_need.name = need.name
    db_need.category = need.category
    db_need.description = need.description
    db.commit()
    db.refresh(db_need)
    return db_need


@router.delete("/{project_id}/needs/{need_id}")
def delete_need(project_id: str, need_id: str, db: Session = Depends(get_db)):
    """ニーズを削除"""
    db_need = db.query(NeedModel).filter(
        NeedModel.id == need_id,
        NeedModel.project_id == project_id
    ).first()
    if not db_need:
        raise HTTPException(status_code=404, detail="Need not found")
    
    # 関連するStakeholderNeedRelationを削除
    db.query(StakeholderNeedRelationModel).filter(
        StakeholderNeedRelationModel.project_id == project_id,
        StakeholderNeedRelationModel.need_id == need_id
    ).delete()
    
    # 関連するNeedPerformanceRelationを削除
    db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.need_id == need_id
    ).delete()
    
    db.delete(db_need)
    db.commit()
    return {"message": "Need deleted successfully"}


# ========== ステークホルダー-ニーズ関係 ==========

@router.post("/{project_id}/stakeholder-need-relations")
def create_stakeholder_need_relation(
    project_id: str,
    relation: StakeholderNeedRelation,
    db: Session = Depends(get_db)
):
    """ステークホルダーとニーズの関係を追加"""
    # 既存の関係をチェック
    existing = db.query(StakeholderNeedRelationModel).filter(
        StakeholderNeedRelationModel.project_id == project_id,
        StakeholderNeedRelationModel.stakeholder_id == relation.stakeholder_id,
        StakeholderNeedRelationModel.need_id == relation.need_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Relation already exists")
    
    db_relation = StakeholderNeedRelationModel(
        project_id=project_id,
        stakeholder_id=relation.stakeholder_id,
        need_id=relation.need_id
    )
    db.add(db_relation)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Relation already exists")
    
    return {"message": "Relation created successfully"}


@router.get("/{project_id}/stakeholder-need-relations", response_model=List[StakeholderNeedRelation])
def list_stakeholder_need_relations(project_id: str, db: Session = Depends(get_db)):
    """ステークホルダー-ニーズ関係の一覧を取得"""
    relations = db.query(StakeholderNeedRelationModel).filter(
        StakeholderNeedRelationModel.project_id == project_id
    ).all()
    return [
        StakeholderNeedRelation(
            stakeholder_id=r.stakeholder_id,
            need_id=r.need_id
        ) for r in relations
    ]


@router.delete("/{project_id}/stakeholder-need-relations/{stakeholder_id}/{need_id}")
def delete_stakeholder_need_relation(
    project_id: str,
    stakeholder_id: str,
    need_id: str,
    db: Session = Depends(get_db)
):
    """ステークホルダー-ニーズ関係を削除"""
    relation = db.query(StakeholderNeedRelationModel).filter(
        StakeholderNeedRelationModel.project_id == project_id,
        StakeholderNeedRelationModel.stakeholder_id == stakeholder_id,
        StakeholderNeedRelationModel.need_id == need_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    db.delete(relation)
    db.commit()
    return {"message": "Relation deleted successfully"}


# ========== 性能 ==========

@router.post("/{project_id}/performances", response_model=Performance)
def create_performance(
    project_id: str,
    performance: PerformanceCreate,
    db: Session = Depends(get_db)
):
    """性能を追加"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 親性能のis_leafを先に更新
    if performance.parent_id:
        parent = db.query(PerformanceModel).filter(
            PerformanceModel.id == performance.parent_id
        ).first()
        if parent:
            parent.is_leaf = False
    
    # 新しい性能を作成（常に末端として作成）
    db_performance = PerformanceModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=performance.name,
        parent_id=performance.parent_id,
        level=performance.level,
        is_leaf=True, 
        unit=performance.unit,
        description=performance.description
    )
    db.add(db_performance)
    db.commit()
    db.refresh(db_performance)
    
    # 親もリフレッシュして最新の状態を反映
    if performance.parent_id and parent:
        db.refresh(parent)
    
    return db_performance


@router.get("/{project_id}/performances", response_model=List[Performance])
def list_performances(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトの性能一覧を取得"""
    performances = db.query(PerformanceModel).filter(
        PerformanceModel.project_id == project_id
    ).all()
    
    # 各性能のis_leafを実際の子の存在に基づいて再計算
    performance_ids = {p.id for p in performances}
    performance_children = {}
    for perf in performances:
        has_children = any(p.parent_id == perf.id for p in performances)
        performance_children[perf.id] = has_children
    
    # utility_function_jsonをパースして結果を構築
    result = []
    for perf in performances:
        perf_dict = {
            "id": perf.id,
            "name": perf.name,
            "parent_id": perf.parent_id,
            "level": perf.level,
            "is_leaf": not performance_children[perf.id],  # 子がいなければ末端
            "unit": perf.unit,
            "description": perf.description,
            "utility_function": json.loads(perf.utility_function_json) if perf.utility_function_json else None
        }
        result.append(perf_dict)
    
    return result


@router.put("/{project_id}/performances/{performance_id}", response_model=Performance)
def update_performance(
    project_id: str,
    performance_id: str,
    performance: PerformanceCreate,
    db: Session = Depends(get_db)
):
    """性能を更新"""
    db_performance = db.query(PerformanceModel).filter(
        PerformanceModel.id == performance_id,
        PerformanceModel.project_id == project_id
    ).first()
    if not db_performance:
        raise HTTPException(status_code=404, detail="Performance not found")
    
    db_performance.name = performance.name
    db_performance.parent_id = performance.parent_id
    db_performance.level = performance.level
    db_performance.is_leaf = performance.is_leaf
    db_performance.unit = performance.unit
    db_performance.description = performance.description
    db.commit()
    db.refresh(db_performance)
    return db_performance

@router.delete("/{project_id}/performances/{performance_id}")
def delete_performance(
    project_id: str,
    performance_id: str,
    db: Session = Depends(get_db)
):
    """性能を削除（子孫も再帰的に削除）"""
    
    def delete_recursive(perf_id: str):
        # 子を取得
        children = db.query(PerformanceModel).filter(
            PerformanceModel.parent_id == perf_id
        ).all()
        
        # 再帰的に子を削除
        for child in children:
            delete_recursive(child.id)
        
        # この性能に関連するNeedPerformanceRelationを削除
        db.query(NeedPerformanceRelationModel).filter(
            NeedPerformanceRelationModel.project_id == project_id,
            NeedPerformanceRelationModel.performance_id == perf_id
        ).delete()
        
        # 自分自身を削除
        perf = db.query(PerformanceModel).filter(
            PerformanceModel.id == perf_id
        ).first()
        if perf:
            db.delete(perf)
    
    # 削除対象の性能を取得
    performance = db.query(PerformanceModel).filter(
        PerformanceModel.id == performance_id,
        PerformanceModel.project_id == project_id
    ).first()
    
    if not performance:
        raise HTTPException(status_code=404, detail="Performance not found")
    
    parent_id = performance.parent_id
    
    # 再帰的に削除
    delete_recursive(performance_id)
    
    # 親のis_leafを更新
    if parent_id:
        siblings = db.query(PerformanceModel).filter(
            PerformanceModel.parent_id == parent_id
        ).all()
        
        if len(siblings) == 0:
            parent = db.query(PerformanceModel).filter(
                PerformanceModel.id == parent_id
            ).first()
            if parent:
                parent.is_leaf = True
    
    db.commit()
    return {"message": "Performance deleted successfully"}


# ========== ニーズ-性能関係 ==========

@router.post("/{project_id}/need-performance-relations")
def create_need_performance_relation(
    project_id: str,
    relation: NeedPerformanceRelation,
    db: Session = Depends(get_db)
):
    """ニーズと性能の関係を追加"""
    # 既存の関係をチェック
    existing = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.need_id == relation.need_id,
        NeedPerformanceRelationModel.performance_id == relation.performance_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Relation already exists")
    
    db_relation = NeedPerformanceRelationModel(
        project_id=project_id,
        need_id=relation.need_id,
        performance_id=relation.performance_id,
        direction=relation.direction
    )
    db.add(db_relation)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Relation already exists")
    
    return {"message": "Relation created successfully"}


@router.get("/{project_id}/need-performance-relations", response_model=List[NeedPerformanceRelation])
def list_need_performance_relations(project_id: str, db: Session = Depends(get_db)):
    """ニーズ-性能関係の一覧を取得"""
    relations = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id
    ).all()
    return [
        NeedPerformanceRelation(
            need_id=r.need_id,
            performance_id=r.performance_id,
            direction=r.direction,
            utility_function_json=r.utility_function_json
        ) for r in relations
    ]


@router.delete("/{project_id}/need-performance-relations/{need_id}/{performance_id}")
def delete_need_performance_relation(
    project_id: str,
    need_id: str,
    performance_id: str,
    db: Session = Depends(get_db)
):
    """ニーズ-性能関係を削除"""
    relation = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.need_id == need_id,
        NeedPerformanceRelationModel.performance_id == performance_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    db.delete(relation)
    db.commit()
    return {"message": "Relation deleted successfully"}


@router.put("/{project_id}/need-performance-relations/{need_id}/{performance_id}")
def update_need_performance_relation(
    project_id: str,
    need_id: str,
    performance_id: str,
    relation: NeedPerformanceRelation,
    db: Session = Depends(get_db)
):
    """ニーズ-性能関係の方向を更新"""
    db_relation = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.need_id == need_id,
        NeedPerformanceRelationModel.performance_id == performance_id
    ).first()
    
    if not db_relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    db_relation.direction = relation.direction
    db.commit()
    return {"message": "Relation updated successfully"}


# ========== 効用関数 ==========

@router.put("/{project_id}/utility-functions/{need_id}/{performance_id}")
def save_utility_function(
    project_id: str,
    need_id: str,
    performance_id: str,
    utility_data: UtilityFunctionData,
    db: Session = Depends(get_db)
):
    """効用関数を保存"""
    # ニーズ-性能関係を取得
    db_relation = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.need_id == need_id,
        NeedPerformanceRelationModel.performance_id == performance_id
    ).first()
    
    if not db_relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    # 効用関数データをJSON文字列に変換して保存
    db_relation.utility_function_json = utility_data.model_dump_json()
    db.commit()
    return {"message": "Utility function saved successfully"}


@router.delete("/{project_id}/utility-functions/{need_id}/{performance_id}")
def delete_utility_function(
    project_id: str,
    need_id: str,
    performance_id: str,
    db: Session = Depends(get_db)
):
    """効用関数を削除（初期化）"""
    # ニーズ-性能関係を取得
    db_relation = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.need_id == need_id,
        NeedPerformanceRelationModel.performance_id == performance_id
    ).first()
    
    if not db_relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    # 効用関数をnullに設定
    db_relation.utility_function_json = None
    db.commit()
    return {"message": "Utility function deleted successfully"}


@router.get("/{project_id}/utility-functions/{need_id}/{performance_id}")
def get_utility_function(
    project_id: str,
    need_id: str,
    performance_id: str,
    db: Session = Depends(get_db)
):
    """効用関数を取得"""
    db_relation = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.need_id == need_id,
        NeedPerformanceRelationModel.performance_id == performance_id
    ).first()
    
    if not db_relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    if not db_relation.utility_function_json:
        return None
    
    return json.loads(db_relation.utility_function_json)


@router.get("/{project_id}/utility-functions")
def list_utility_functions(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトの全効用関数を取得"""
    relations = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id,
        NeedPerformanceRelationModel.utility_function_json.isnot(None)
    ).all()
    
    result = []
    for r in relations:
        if r.utility_function_json:
            utility_data = json.loads(r.utility_function_json)
            result.append(utility_data)
    
    return result

# ========== 設計案 ==========

@router.post("/{project_id}/design-cases", response_model=DesignCase)
def create_design_case(
    project_id: str,
    design_case: DesignCaseCreate,
    db: Session = Depends(get_db)
):
    """設計案を作成"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 色の自動割り当て（指定がない場合）
    if not hasattr(design_case, 'color') or not design_case.color:
        existing_colors = [dc.color for dc in project.design_cases if hasattr(dc, 'color') and dc.color]
        color = get_next_available_color(existing_colors)
    else:
        color = design_case.color
    
    db_design_case = DesignCaseModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=design_case.name,
        description=design_case.description,
        color=color,
        performance_values_json=json.dumps(design_case.performance_values),
        network_json=json.dumps({
            'nodes': [n.dict() for n in design_case.network.nodes],
            'edges': [e.dict() for e in design_case.network.edges]
        }),
        performance_snapshot_json=json.dumps(design_case.performance_snapshot)
    )
    db.add(db_design_case)
    db.commit()
    db.refresh(db_design_case)
    
    # 山の座標を計算（非同期ではなく同期的に実行）
    try:
        # 全ての設計案のネットワーク情報を取得
        all_design_cases = db.query(DesignCaseModel).filter(
            DesignCaseModel.project_id == project_id
        ).all()
        
        networks = []
        for case in all_design_cases:
            if case.network_json:
                network = json.loads(case.network_json)
                networks.append(network)
            else:
                networks.append({'nodes': [], 'edges': []})
        
        from app.services.mountain_calculator import calculate_mountain_positions
        result = calculate_mountain_positions(project, db, networks=networks)
        positions = result['positions']
        
        # 新しい設計案の座標を更新
        for pos in positions:
            if pos['case_id'] == db_design_case.id:
                db_design_case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H']
                })
                db_design_case.utility_vector_json = json.dumps(pos['utility_vector'])
                db_design_case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                db_design_case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                db.commit()
                break
    except Exception as e:
        print(f"Mountain calculation error: {e}")
        # 計算エラーでも設計案は作成する
    
    db.refresh(db_design_case)
    return format_design_case_response(db_design_case)


@router.get("/{project_id}/design-cases", response_model=List[DesignCase])
def list_design_cases(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトの設計案一覧を取得"""
    design_cases = db.query(DesignCaseModel).filter(
        DesignCaseModel.project_id == project_id
    ).all()
    
    return [format_design_case_response(dc) for dc in design_cases]


@router.get("/{project_id}/design-cases/{case_id}", response_model=DesignCase)
def get_design_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """特定の設計案を取得"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    return format_design_case_response(design_case)


@router.put("/{project_id}/design-cases/{case_id}", response_model=DesignCase)
def update_design_case(
    project_id: str,
    case_id: str,
    design_case: DesignCaseUpdate,
    db: Session = Depends(get_db)
):
    """設計案を更新"""
    db_design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not db_design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    # 更新（performance_snapshotは更新しない）
    db_design_case.name = design_case.name
    db_design_case.description = design_case.description
    db_design_case.performance_values_json = json.dumps(design_case.performance_values)
    db_design_case.network_json = json.dumps({
        'nodes': [n.dict() for n in design_case.network.nodes],
        'edges': [e.dict() for e in design_case.network.edges]
    })
    
    if hasattr(design_case, 'color') and design_case.color:
        db_design_case.color = design_case.color
    
    db.commit()
    
    # 山の座標を再計算
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        
        # ★ 全ての設計案のネットワーク情報を取得
        all_design_cases = db.query(DesignCaseModel).filter(
            DesignCaseModel.project_id == project_id
        ).all()
        
        networks = []
        for case in all_design_cases:
            if case.network_json:
                network = json.loads(case.network_json)
                networks.append(network)
            else:
                # ネットワークがない場合は空のネットワーク
                networks.append({'nodes': [], 'edges': []})

        from app.services.mountain_calculator import calculate_mountain_positions
        result = calculate_mountain_positions(project, db, networks=networks)
        positions = result['positions']
        
        for pos in positions:
            if pos['case_id'] == case_id:
                db_design_case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H']
                })
                db_design_case.utility_vector_json = json.dumps(pos['utility_vector'])
                db_design_case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                db_design_case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                db.commit()
                break
    except Exception as e:
        print(f"Mountain calculation error: {e}")
    
    db.refresh(db_design_case)
    return format_design_case_response(db_design_case)


@router.delete("/{project_id}/design-cases/{case_id}")
def delete_design_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """設計案を削除"""
    db_design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not db_design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    db.delete(db_design_case)
    db.commit()
    
    # 削除後、残りの設計案の座標を再計算
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        
        # 残りの設計案のネットワーク情報を取得
        remaining_design_cases = db.query(DesignCaseModel).filter(
            DesignCaseModel.project_id == project_id
        ).all()
        
        if len(remaining_design_cases) > 0:
            networks = []
            for case in remaining_design_cases:
                if case.network_json:
                    network = json.loads(case.network_json)
                    networks.append(network)
                else:
                    networks.append({'nodes': [], 'edges': []})
            
            from app.services.mountain_calculator import calculate_mountain_positions
            result = calculate_mountain_positions(project, db, networks=networks)
            positions = result['positions']
            
            # 残りの全設計案の座標を更新
            for pos in positions:
                remaining_case = db.query(DesignCaseModel).filter(
                    DesignCaseModel.id == pos['case_id']
                ).first()
                
                if remaining_case:
                    remaining_case.mountain_position_json = json.dumps({
                        'x': pos['x'],
                        'y': pos['y'],
                        'z': pos['z'],
                        'H': pos['H']
                    })
                    # utility_vectorのタプルキーを文字列に変換
                    utility_vec_str_keys = {
                        f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                    }
                    remaining_case.utility_vector_json = json.dumps(utility_vec_str_keys)
                    remaining_case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                    remaining_case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
            
            db.commit()
            print(f"✓ Updated coordinates for {len(positions)} remaining design cases\n")
    except Exception as e:
        import traceback
        print(f"❌ Mountain calculation error after delete: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        # 削除自体は成功しているので、座標計算エラーでもロールバックしない
    
    return {"message": "Design case deleted successfully"}


@router.post("/{project_id}/design-cases/{case_id}/copy", response_model=DesignCase)
def copy_design_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """設計案をコピー"""
    original = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not original:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    # 色の自動割り当て
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    existing_colors = [dc.color for dc in project.design_cases if hasattr(dc, 'color') and dc.color]
    new_color = get_next_available_color(existing_colors)
    
    # 現在の性能ツリーからスナップショットを作成
    current_performances = project.performances
    current_snapshot = []
    
    for perf in current_performances:
        # この性能が末端かどうかを判定（子がいなければ末端）
        is_leaf = not any(p.parent_id == perf.id for p in current_performances)
        
        current_snapshot.append({
            'id': perf.id,
            'name': perf.name,
            'parent_id': perf.parent_id,
            'level': perf.level,
            'is_leaf': is_leaf,
            'unit': perf.unit,
            'description': perf.description,
            'order': getattr(perf, 'order', 0)
        })
    
    # 新しい設計案を作成
    db_copy = DesignCaseModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=f"{original.name}のコピー",
        description=original.description,
        color=new_color,
        performance_values_json=original.performance_values_json,  # そのままコピー
        network_json=original.network_json,  # そのままコピー
        performance_snapshot_json=json.dumps(current_snapshot),  # 現在の性能ツリーをスナップショット
        # mountain_position_jsonとutility_vector_jsonはnull（後で再計算）
    )
    db.add(db_copy)
    db.commit()
    db.refresh(db_copy)
    
    try:
        # 全ての設計案のネットワーク情報を取得
        all_design_cases = db.query(DesignCaseModel).filter(
            DesignCaseModel.project_id == project_id
        ).all()
        
        networks = []
        for case in all_design_cases:
            if case.network_json:
                network = json.loads(case.network_json)
                networks.append(network)
            else:
                networks.append({'nodes': [], 'edges': []})
        
        from app.services.mountain_calculator import calculate_mountain_positions
        result = calculate_mountain_positions(project, db, networks=networks)
        positions = result['positions']
        
        for pos in positions:
            if pos['case_id'] == db_copy.id:
                db_copy.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H']
                })
                db_copy.utility_vector_json = json.dumps(pos['utility_vector'])
                db.commit()
                break
    except Exception as e:
        print(f"Mountain calculation error: {e}")
    
    db.refresh(db_copy)
    return format_design_case_response(db_copy)


@router.patch("/{project_id}/design-cases/{case_id}/color")
def update_design_case_color(
    project_id: str,
    case_id: str,
    color_data: dict,
    db: Session = Depends(get_db)
):
    """設計案の色を変更"""
    db_design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not db_design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    db_design_case.color = color_data.get('color', '#3357FF')
    db.commit()
    
    return {"message": "Color updated successfully", "color": db_design_case.color}


# ========== エクスポート/インポート機能 ==========

@router.get("/{project_id}/export")
def export_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """プロジェクトの全データをエクスポート"""
    # プロジェクト取得
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # ステークホルダー取得
    stakeholders = db.query(StakeholderModel).filter(
        StakeholderModel.project_id == project_id
    ).all()
    
    # ニーズ取得
    needs = db.query(NeedModel).filter(
        NeedModel.project_id == project_id
    ).all()
    
    # ステークホルダー・ニーズ関係取得
    stakeholder_need_relations = db.query(StakeholderNeedRelationModel).filter(
        StakeholderNeedRelationModel.project_id == project_id
    ).all()
    
    # 性能取得
    performances = db.query(PerformanceModel).filter(
        PerformanceModel.project_id == project_id
    ).all()
    
    # ニーズ・性能関係取得
    need_performance_relations = db.query(NeedPerformanceRelationModel).filter(
        NeedPerformanceRelationModel.project_id == project_id
    ).all()
    
    # 設計案取得
    design_cases = db.query(DesignCaseModel).filter(
        DesignCaseModel.project_id == project_id
    ).all()
    
    # エクスポートデータ構築
    export_data = {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        },
        "stakeholders": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "votes": s.votes,
                "description": s.description
            } for s in stakeholders
        ],
        "needs": [
            {
                "id": n.id,
                "name": n.name,
                "category": n.category,
                "description": n.description
            } for n in needs
        ],
        "stakeholder_need_relations": [
            {
                "stakeholder_id": r.stakeholder_id,
                "need_id": r.need_id
            } for r in stakeholder_need_relations
        ],
        "performances": [
            {
                "id": p.id,
                "name": p.name,
                "parent_id": p.parent_id,
                "level": p.level,
                "is_leaf": p.is_leaf,
                "unit": p.unit,
                "description": p.description,
                "utility_function_json": p.utility_function_json
            } for p in performances
        ],
        "need_performance_relations": [
            {
                "need_id": r.need_id,
                "performance_id": r.performance_id,
                "direction": r.direction,
                "utility_function_json": r.utility_function_json
            } for r in need_performance_relations
        ],
        "design_cases": [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "color": d.color,
                "performance_values_json": d.performance_values_json,
                "network_json": d.network_json,
                "performance_snapshot_json": d.performance_snapshot_json,
                "mountain_position_json": d.mountain_position_json,
                "utility_vector_json": d.utility_vector_json,
                "partial_heights_json": d.partial_heights_json,
                "performance_weights_json": d.performance_weights_json,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat()
            } for d in design_cases
        ]
    }
    
    return export_data


@router.post("/import")
def import_project(
    import_data: dict,
    db: Session = Depends(get_db)
):
    """プロジェクトデータをインポート"""
    try:
        # 新しいプロジェクトIDを生成
        new_project_id = str(uuid.uuid4())
        
        # プロジェクト作成
        project_data = import_data["project"]
        db_project = ProjectModel(
            id=new_project_id,
            name=project_data["name"] + " (imported)",
            description=project_data.get("description", "")
        )
        db.add(db_project)
        
        # IDマッピング辞書（旧ID→新ID）
        stakeholder_id_map = {}
        need_id_map = {}
        performance_id_map = {}
        design_case_id_map = {}
        
        # ステークホルダーインポート
        for stakeholder in import_data.get("stakeholders", []):
            new_id = str(uuid.uuid4())
            stakeholder_id_map[stakeholder["id"]] = new_id
            db_stakeholder = StakeholderModel(
                id=new_id,
                project_id=new_project_id,
                name=stakeholder["name"],
                category=stakeholder.get("category"),
                votes=stakeholder.get("votes", 100),
                description=stakeholder.get("description")
            )
            db.add(db_stakeholder)
        
        # ニーズインポート
        for need in import_data.get("needs", []):
            new_id = str(uuid.uuid4())
            need_id_map[need["id"]] = new_id
            db_need = NeedModel(
                id=new_id,
                project_id=new_project_id,
                name=need["name"],
                category=need.get("category"),
                description=need.get("description")
            )
            db.add(db_need)
        
        # ステークホルダー・ニーズ関係インポート
        for relation in import_data.get("stakeholder_need_relations", []):
            if relation["stakeholder_id"] in stakeholder_id_map and relation["need_id"] in need_id_map:
                db_relation = StakeholderNeedRelationModel(
                    project_id=new_project_id,
                    stakeholder_id=stakeholder_id_map[relation["stakeholder_id"]],
                    need_id=need_id_map[relation["need_id"]]
                )
                db.add(db_relation)
        
        # 性能インポート（親子関係を考慮）
        performance_parent_map = {}  # 旧ID→旧parent_ID
        for performance in import_data.get("performances", []):
            new_id = str(uuid.uuid4())
            performance_id_map[performance["id"]] = new_id
            if performance.get("parent_id"):
                performance_parent_map[performance["id"]] = performance["parent_id"]
        
        # 性能を作成
        for performance in import_data.get("performances", []):
            new_parent_id = None
            if performance["id"] in performance_parent_map:
                old_parent_id = performance_parent_map[performance["id"]]
                if old_parent_id in performance_id_map:
                    new_parent_id = performance_id_map[old_parent_id]
            
            db_performance = PerformanceModel(
                id=performance_id_map[performance["id"]],
                project_id=new_project_id,
                name=performance["name"],
                parent_id=new_parent_id,
                level=performance["level"],
                is_leaf=performance["is_leaf"],
                unit=performance.get("unit"),
                description=performance.get("description"),
                utility_function_json=performance.get("utility_function_json")
            )
            db.add(db_performance)
        
        # ニーズ・性能関係インポート
        for relation in import_data.get("need_performance_relations", []):
            if relation["need_id"] in need_id_map and relation["performance_id"] in performance_id_map:
                db_relation = NeedPerformanceRelationModel(
                    project_id=new_project_id,
                    need_id=need_id_map[relation["need_id"]],
                    performance_id=performance_id_map[relation["performance_id"]],
                    direction=relation["direction"],
                    utility_function_json=relation.get("utility_function_json")
                )
                db.add(db_relation)
        
        # 設計案インポート
        for design_case in import_data.get("design_cases", []):
            new_id = str(uuid.uuid4())
            design_case_id_map[design_case["id"]] = new_id
            
            # performance_values_jsonのキーを新しいIDに更新
            if design_case.get("performance_values_json"):
                old_values = json.loads(design_case["performance_values_json"])
                new_values = {}
                for old_perf_id, value in old_values.items():
                    if old_perf_id in performance_id_map:
                        new_values[performance_id_map[old_perf_id]] = value
                performance_values_json = json.dumps(new_values)
            else:
                performance_values_json = "{}"
            
            # networkのノードIDを更新（性能ノードのみ）
            if design_case.get("network_json"):
                old_network = json.loads(design_case["network_json"])
                new_nodes = []
                node_id_map = {}
                
                for node in old_network.get("nodes", []):
                    if node.get("layer") == 1 and node.get("performance_id") in performance_id_map:
                        # 性能ノードの場合はIDを更新
                        new_node = node.copy()
                        new_node["performance_id"] = performance_id_map[node["performance_id"]]
                        new_nodes.append(new_node)
                        node_id_map[node["id"]] = new_node["id"]
                    else:
                        # その他のノードはそのまま
                        new_nodes.append(node)
                        node_id_map[node["id"]] = node["id"]
                
                # エッジもコピー
                new_edges = []
                for edge in old_network.get("edges", []):
                    if edge["source_id"] in node_id_map and edge["target_id"] in node_id_map:
                        new_edge = edge.copy()
                        new_edges.append(new_edge)
                
                network_json = json.dumps({"nodes": new_nodes, "edges": new_edges})
            else:
                network_json = '{"nodes": [], "edges": []}'
            
            db_design_case = DesignCaseModel(
                id=new_id,
                project_id=new_project_id,
                name=design_case["name"],
                description=design_case.get("description"),
                color=design_case.get("color", "#3357FF"),
                performance_values_json=performance_values_json,
                network_json=network_json,
                performance_snapshot_json=design_case.get("performance_snapshot_json", "[]"),
                mountain_position_json=design_case.get("mountain_position_json"),
                utility_vector_json=design_case.get("utility_vector_json"),
                partial_heights_json=design_case.get("partial_heights_json"),
                performance_weights_json=design_case.get("performance_weights_json")
            )
            db.add(db_design_case)
        
        db.commit()
        
        # 作成したプロジェクトを返す
        return {
            "id": db_project.id,
            "name": db_project.name,
            "description": db_project.description,
            "created_at": db_project.created_at.isoformat(),
            "updated_at": db_project.updated_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


# ========== ヘルパー関数 ==========

def format_design_case_response(db_design_case: DesignCaseModel) -> DesignCase:
    """DesignCaseModelをレスポンス形式に変換"""
    performance_values = json.loads(db_design_case.performance_values_json)
    network_data = json.loads(db_design_case.network_json)
    
    mountain_position = None
    if db_design_case.mountain_position_json:
        mountain_position = MountainPosition(**json.loads(db_design_case.mountain_position_json))
    
    utility_vector = None
    if db_design_case.utility_vector_json:
        utility_vector = json.loads(db_design_case.utility_vector_json)
    
    partial_heights = None
    if hasattr(db_design_case, 'partial_heights_json') and db_design_case.partial_heights_json:
        partial_heights = json.loads(db_design_case.partial_heights_json)
    
    performance_weights = None
    if hasattr(db_design_case, 'performance_weights_json') and db_design_case.performance_weights_json:
        performance_weights = json.loads(db_design_case.performance_weights_json)
    
    # performance_snapshotを@propertyから取得
    performance_snapshot = db_design_case.performance_snapshot if hasattr(db_design_case, 'performance_snapshot') else None
    
    return DesignCase(
        id=db_design_case.id,
        name=db_design_case.name,
        description=db_design_case.description,
        color=getattr(db_design_case, 'color', '#3357FF'),
        created_at=db_design_case.created_at,
        updated_at=db_design_case.updated_at,
        performance_values=performance_values,
        network=NetworkStructure(
            nodes=[NetworkNode(**n) for n in network_data['nodes']],
            edges=[NetworkEdge(**e) for e in network_data['edges']]
        ),
        mountain_position=mountain_position,
        utility_vector=utility_vector,
        partial_heights=partial_heights,
        performance_weights=performance_weights,
        performance_snapshot=performance_snapshot  # 追加！
    )


def get_next_available_color(existing_colors: List[str]) -> str:
    """使用されていない色を返す"""
    COLOR_PALETTE = [
        '#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#F5FF33',
        '#33F5FF', '#FF8C33', '#8C33FF', '#33FF8C', '#FF338C',
        '#5733FF', '#FF5733', '#33FFFF', '#FFFF33', '#FF3333',
    ]
    
    for color in COLOR_PALETTE:
        if color not in existing_colors:
            return color
    
    # 全色使用済みの場合はランダム
    import random
    return f"#{random.randint(0, 0xFFFFFF):06x}"


@router.post("/{project_id}/recalculate-mountains")
def recalculate_mountains(
    project_id: str,
    request_body: dict = {},
    db: Session = Depends(get_db)
):
    """
    全設計案の山の座標を再計算
    性能、ニーズ、効用関数、投票などが変更された場合に使用
    
    Request body:
        networks: 各設計案のネットワーク情報（オプション）
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if len(project.design_cases) == 0:
        return {"message": "No design cases to recalculate", "updated": 0}
    
    try:
        from app.services.mountain_calculator import calculate_mountain_positions
        
        # リクエストボディからネットワーク情報を取得
        networks = request_body.get('networks') if request_body else None
        
        result = calculate_mountain_positions(project, db, networks=networks)
        positions = result['positions']
        H_max = result['H_max']
        
        # 各設計案の座標を更新
        updated_count = 0
        for pos in positions:
            design_case = db.query(DesignCaseModel).filter(
                DesignCaseModel.id == pos['case_id']
            ).first()
            
            if design_case:
                design_case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H']
                })
                # utility_vectorのタプルキーを文字列に変換
                utility_vec_str_keys = {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
                design_case.utility_vector_json = json.dumps(utility_vec_str_keys)
                design_case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                design_case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                updated_count += 1
        
        db.commit()
        return {
            "message": f"Successfully recalculated {updated_count} design cases", 
            "updated": updated_count,
            "H_max": H_max
        }
    
    except Exception as e:
        import traceback
        print(f"❌ Recalculation error: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")


@router.get("/{project_id}/h-max")
def get_h_max(project_id: str, db: Session = Depends(get_db)):
    """
    プロジェクトの頂点標高H_maxを取得
    H_max = 全末端性能×ニーズペアの重みの合計
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # 末端性能のIDを取得（実際の子の存在に基づいて再計算）
        leaf_performance_ids = set()
        for perf in project.performances:
            has_children = any(p.parent_id == perf.id for p in project.performances)
            if not has_children:
                leaf_performance_ids.add(perf.id)
        
        # ニーズ×性能の関係から重みを計算
        from app.services.mountain_calculator import (
            distribute_votes_to_needs, 
            distribute_votes_to_performances
        )
        need_votes = distribute_votes_to_needs(project)
        performance_need_votes = distribute_votes_to_performances(project, need_votes)
        
        # 全末端性能×ニーズペアの重み（票数）を合計
        # H_max = Σ weight （全効用が1.0の場合、効用関数が設定されているペアのみ）
        H_max = 0.0
        performance_h_max = {}  # 性能ごとの部分標高最大値
        count = 0
        count_with_utility = 0
        
        # 効用関数が設定されているペアを確認
        relations_with_utility = {}
        for rel in project.need_performance_relations:
            key = (rel.performance_id, rel.need_id)
            if rel.utility_function_json:
                relations_with_utility[key] = True
        
        for key, votes in performance_need_votes.items():
            perf_id, need_id = key
            if perf_id in leaf_performance_ids:
                count += 1
                # 効用関数が設定されている場合のみカウント
                if key in relations_with_utility:
                    up_vote = votes['up']
                    down_vote = votes['down']
                    weight = up_vote + down_vote  # この性能×ニーズペアの重み（票数）
                    H_max += weight
                    
                    # 性能ごとの部分標高最大値を集計
                    if perf_id not in performance_h_max:
                        performance_h_max[perf_id] = 0.0
                    performance_h_max[perf_id] += weight
                    
                    count_with_utility += 1
        
        return {
            "H_max": float(H_max),
            "performance_h_max": {k: float(v) for k, v in performance_h_max.items()}
        }
    
    except Exception as e:
        import traceback
        print(f"❌ H_max calculation error: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"H_max calculation failed: {str(e)}")