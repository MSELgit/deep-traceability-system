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
from app.services.weight_normalization import migrate_network_edges, needs_7_level_migration
from pydantic import BaseModel
from typing import Optional, Literal

# 個別操作用のスキーマ
class NetworkNodeUpdate(BaseModel):
    label: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    x3d: Optional[float] = None
    y3d: Optional[float] = None

class NetworkEdgeUpdate(BaseModel):
    weight: Optional[float] = None
    type: Optional[str] = None

class NodePositionUpdate(BaseModel):
    x3d: float
    y3d: float

# 作成用のスキーマ
class NetworkNodeCreate(BaseModel):
    label: str
    layer: Literal[1, 2, 3, 4]
    type: Literal['performance', 'property', 'attribute', 'variable', 'object', 'environment']  # 'property' deprecated, use 'attribute'
    x: Optional[float] = None
    y: Optional[float] = None
    performance_id: Optional[str] = None
    x3d: Optional[float] = None
    y3d: Optional[float] = None

class NetworkEdgeCreate(BaseModel):
    source_id: str
    target_id: str
    weight: Optional[float] = None
    type: str = 'type1'

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
    # また、utility_function_jsonをパースしてutility_functionとして設定
    performance_ids = {p.id for p in project.performances}
    for performance in project.performances:
        # この性能を親として持つ子が存在するか確認
        has_children = any(p.parent_id == performance.id for p in project.performances)
        performance.is_leaf = not has_children
        # utility_function_jsonをパース（@propertyの値をPydanticが読めるように）
        performance._utility_function_temp = performance.utility_function

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
        description=need.description,
        priority=need.priority
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
    db_need.priority = need.priority
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
        need_id=relation.need_id,
        relationship_weight=relation.relationship_weight
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


@router.put("/{project_id}/stakeholder-need-relations/{stakeholder_id}/{need_id}")
def update_stakeholder_need_relation(
    project_id: str,
    stakeholder_id: str,
    need_id: str,
    weight_data: dict,
    db: Session = Depends(get_db)
):
    """ステークホルダー-ニーズ関係の重みを更新"""
    relation = db.query(StakeholderNeedRelationModel).filter(
        StakeholderNeedRelationModel.project_id == project_id,
        StakeholderNeedRelationModel.stakeholder_id == stakeholder_id,
        StakeholderNeedRelationModel.need_id == need_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    new_weight = weight_data.get('relationship_weight')
    if new_weight not in [0.5, 1.0]:
        raise HTTPException(status_code=400, detail="Invalid weight. Must be 0.5 or 1.0")
    
    relation.relationship_weight = new_weight
    db.commit()
    return {"message": "Relation updated successfully"}


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
            # need_idとperformance_idを追加（フロントエンドで必要）
            utility_data['need_id'] = r.need_id
            utility_data['performance_id'] = r.performance_id
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
    
    # ネットワーク構造を作成
    network = {
        'nodes': [n.dict() for n in design_case.network.nodes],
        'edges': [e.dict() for e in design_case.network.edges]
    }

    # SCC分析を実行
    scc_analysis_json = None
    try:
        from app.services.scc_analyzer import analyze_scc, scc_result_to_dict
        if network['nodes']:
            scc_result = analyze_scc(network)
            scc_analysis_json = json.dumps(scc_result_to_dict(scc_result), ensure_ascii=False)
    except Exception:
        pass  # SCC analysis error - continue without SCC data

    db_design_case = DesignCaseModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=design_case.name,
        description=design_case.description,
        color=color,
        performance_values_json=json.dumps(design_case.performance_values),
        network_json=json.dumps(network),
        performance_snapshot_json=json.dumps(design_case.performance_snapshot),
        scc_analysis_json=scc_analysis_json,
        weight_mode=design_case.weight_mode or 'discrete_7'
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
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                db_design_case.utility_vector_json = json.dumps(pos['utility_vector'])
                db_design_case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                db_design_case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                db_design_case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))
                db.commit()
                break
    except Exception as e:
        pass  # Mountain calculation error - continue
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

    # weight_mode を更新
    if hasattr(design_case, 'weight_mode') and design_case.weight_mode:
        db_design_case.weight_mode = design_case.weight_mode

    # SCC分析を実行して保存
    try:
        from app.services.scc_analyzer import analyze_scc, scc_result_to_dict
        network = {
            'nodes': [n.dict() for n in design_case.network.nodes],
            'edges': [e.dict() for e in design_case.network.edges]
        }
        if network['nodes']:
            scc_result = analyze_scc(network)
            db_design_case.scc_analysis_json = json.dumps(scc_result_to_dict(scc_result), ensure_ascii=False)
        else:
            db_design_case.scc_analysis_json = None
    except Exception:
        db_design_case.scc_analysis_json = None

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
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                db_design_case.utility_vector_json = json.dumps(pos['utility_vector'])
                db_design_case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                db_design_case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                db_design_case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))
                db.commit()
                break
    except Exception as e:
        pass  # Mountain calculation error - continue

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
                        'H': pos['H'],
                        'total_energy': pos.get('total_energy', 0),
                        'partial_energies': pos.get('partial_energies', {})
                    })
                    # utility_vectorのタプルキーを文字列に変換
                    utility_vec_str_keys = {
                        f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                    }
                    remaining_case.utility_vector_json = json.dumps(utility_vec_str_keys)
                    remaining_case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                    remaining_case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                    remaining_case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))

            db.commit()
    except Exception:
        # 削除自体は成功しているので、座標計算エラーでもロールバックしない
        pass
    
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
    
    # ソート済みの性能リスト
    sorted_performances = sort_performances_by_tree(current_performances)
    
    current_snapshot = []
    for perf in sorted_performances:
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
    
    # 性能値のマッピング
    new_performance_values = {}
    if original.performance_values_json:
        original_values = json.loads(original.performance_values_json)
        
        # 元のスナップショットがある場合は、それを使ってマッピング
        if original.performance_snapshot_json:
            original_snapshot = json.loads(original.performance_snapshot_json)
            
            # 元のスナップショットと現在の性能ツリーでマッチングを行う
            for current_perf in current_performances:
                # この性能が末端かどうかを判定
                current_is_leaf = not any(p.parent_id == current_perf.id for p in current_performances)
                if not current_is_leaf:  # 末端性能のみ対象
                    continue
                    
                # 同じ条件の性能を元のスナップショットから探す
                for orig_perf in original_snapshot:
                    if (orig_perf.get('name') == current_perf.name and 
                        orig_perf.get('parent_id') == current_perf.parent_id and
                        orig_perf.get('unit') == current_perf.unit and
                        orig_perf.get('level') == current_perf.level and
                        orig_perf.get('is_leaf', False)):
                        # マッチした場合、値をコピー
                        orig_id = orig_perf.get('id')
                        if orig_id in original_values:
                            new_performance_values[current_perf.id] = original_values[orig_id]
                        break
        else:
            # スナップショットがない場合は、IDが一致するものをそのままコピー（後方互換性）
            new_performance_values = original_values
    
    # ネットワークの更新
    updated_network = {'nodes': [], 'edges': []}
    
    if original.network_json:
        original_network = json.loads(original.network_json)
        
        # 現在の性能IDのセット
        current_perf_ids = {perf.id for perf in current_performances}
        
        # ノードの処理
        node_id_mapping = {}  # 古いノードID -> 新しいノードIDのマッピング
        
        # 末端性能のIDセットを作成
        leaf_perf_ids = {perf.id for perf in current_performances 
                         if not any(p.parent_id == perf.id for p in current_performances)}
        
        for node in original_network.get('nodes', []):
            if node.get('type') == 'performance' or node.get('layer') == 1:
                # 性能ノードの場合
                perf_id = node.get('performance_id')
                
                # 性能が現在も存在し、かつ末端性能である場合のみ保持
                if perf_id in current_perf_ids and perf_id in leaf_perf_ids:
                    updated_network['nodes'].append(node)
                    node_id_mapping[node['id']] = node['id']
                # else: 性能が削除されているか、末端でなくなった場合はノードも削除
            else:
                # 性能以外のノード（プロパティ、ニーズ）はそのまま保持
                updated_network['nodes'].append(node)
                node_id_mapping[node['id']] = node['id']
        
        # レイヤー1のノードを収集して並び替え
        layer1_nodes = [n for n in updated_network['nodes'] if n.get('layer') == 1]
        layer1_nodes.sort(key=lambda n: n.get('x', 0))  # X座標でソート
        
        # 新規追加された性能のノードを作成（末端性能のみ）
        existing_perf_ids = {node.get('performance_id') for node in original_network.get('nodes', []) 
                            if node.get('type') == 'performance' or node.get('layer') == 1}
        
        new_nodes_to_add = []
        for perf in current_performances:
            # 末端性能かどうかチェック
            is_leaf = not any(p.parent_id == perf.id for p in current_performances)
            
            if is_leaf and perf.id not in existing_perf_ids:
                # 新しい末端性能なのでノードを追加
                new_node = {
                    'id': str(uuid.uuid4()),
                    'layer': 1,
                    'type': 'performance',
                    'label': perf.name,
                    'x': 0,  # 後で計算
                    'y': 100,  # レイヤー1の固定Y座標
                    'performance_id': perf.id
                }
                new_nodes_to_add.append(new_node)
        
        # 新しいノードを追加
        updated_network['nodes'].extend(new_nodes_to_add)
        
        # レイヤー1の全ノードを再配置（均等配置）
        all_layer1_nodes = [n for n in updated_network['nodes'] if n.get('layer') == 1]
        if all_layer1_nodes:
            # 名前でソート（性能の自然な順序を保つ）
            all_layer1_nodes.sort(key=lambda n: n.get('label', ''))
            
            # 均等配置（キャンバス幅=1200）
            canvas_width = 1200
            spacing = canvas_width / (len(all_layer1_nodes) + 1)
            
            for i, node in enumerate(all_layer1_nodes):
                node['x'] = spacing * (i + 1)
                node['y'] = 100  # 確実に100に設定
        
        # エッジの処理（両端のノードが存在する場合のみ保持）
        for edge in original_network.get('edges', []):
            source_exists = edge['source_id'] in node_id_mapping
            target_exists = edge['target_id'] in node_id_mapping
            
            if source_exists and target_exists:
                updated_network['edges'].append(edge)
            # else: どちらかのノードが削除されている場合はエッジも削除
    
    # 新しい設計案を作成
    db_copy = DesignCaseModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=f"{original.name}のコピー",
        description=original.description,
        color=new_color,
        performance_values_json=json.dumps(new_performance_values),  # マッピングした値
        network_json=json.dumps(updated_network),  # 更新されたネットワーク
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
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                db_copy.utility_vector_json = json.dumps(pos['utility_vector'])
                db_copy.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                db_copy.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                db_copy.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))
                db.commit()
                break
    except Exception as e:
        pass  # Mountain calculation error - continue

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
    
    # データマイグレーションモジュールをインポート
    from app.services.data_migration import get_export_metadata, add_export_fields_to_design_case

    # エクスポートデータ構築
    export_data = {
        # メタデータ（バージョン情報）
        **get_export_metadata(),
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "two_axis_plots": project.two_axis_plots
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
                "description": n.description,
                "priority": n.priority
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
            add_export_fields_to_design_case({
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
                "performance_deltas_json": d.performance_deltas_json,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat()
            }, d) for d in design_cases
        ]
    }
    
    # JSONファイルに保存
    from pathlib import Path
    output_file = Path(__file__).parent.parent.parent / "exported_project.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    # レスポンスに保存先パスを追加
    export_data["_exported_path"] = str(output_file.resolve())

    return export_data


@router.post("/import/preview")
def preview_import(import_data: dict):
    """
    インポートデータのマイグレーションプレビュー

    実際のインポートは行わず、どのようなマイグレーションが適用されるかを分析して返す
    """
    from app.services.data_migration import analyze_migrations, validate_import_data

    # データ検証
    validation = validate_import_data(import_data)

    # マイグレーション分析
    migration_analysis = analyze_migrations(import_data)

    return {
        "validation": validation,
        "migration_analysis": migration_analysis,
        "project_name": import_data.get("project", {}).get("name", "Unknown"),
        "counts": {
            "stakeholders": len(import_data.get("stakeholders", [])),
            "needs": len(import_data.get("needs", [])),
            "performances": len(import_data.get("performances", [])),
            "design_cases": len(import_data.get("design_cases", []))
        }
    }


class ImportRequest(BaseModel):
    """インポートリクエストのスキーマ"""
    data: dict  # プロジェクトデータ
    user_choices: Optional[dict] = None  # ユーザー選択値（マイグレーション用）


@router.post("/import")
def import_project(
    request: ImportRequest,
    db: Session = Depends(get_db)
):
    """プロジェクトデータをインポート"""
    from app.services.data_migration import migrate_import_data, validate_import_data

    import_data = request.data
    user_choices = request.user_choices or {}

    try:
        # データ検証
        validation = validate_import_data(import_data)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={"errors": validation["errors"]})

        # バージョンマイグレーション（古いバージョンのデータを最新に変換）
        import_data = migrate_import_data(import_data, user_choices)

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
                description=need.get("description"),
                priority=need.get("priority", 1.0)  # priorityがあれば使用、なければ1.0
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
                # 効用関数JSON内のIDも更新
                utility_json = relation.get("utility_function_json")
                if utility_json:
                    utility_data = json.loads(utility_json)
                    # need_idとperformance_idを新しいIDに更新
                    utility_data["need_id"] = need_id_map[relation["need_id"]]
                    utility_data["performance_id"] = performance_id_map[relation["performance_id"]]
                    utility_json = json.dumps(utility_data)
                
                db_relation = NeedPerformanceRelationModel(
                    project_id=new_project_id,
                    need_id=need_id_map[relation["need_id"]],
                    performance_id=performance_id_map[relation["performance_id"]],
                    direction=relation["direction"],
                    utility_function_json=utility_json
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
            
            # performance_snapshotのIDも更新
            if design_case.get("performance_snapshot_json"):
                old_snapshot = json.loads(design_case["performance_snapshot_json"])
                new_snapshot = []
                for perf in old_snapshot:
                    if perf["id"] in performance_id_map:
                        new_perf = perf.copy()
                        new_perf["id"] = performance_id_map[perf["id"]]
                        # parent_idも更新
                        if perf.get("parent_id") and perf["parent_id"] in performance_id_map:
                            new_perf["parent_id"] = performance_id_map[perf["parent_id"]]
                        new_snapshot.append(new_perf)
                performance_snapshot_json = json.dumps(new_snapshot)
            else:
                performance_snapshot_json = "[]"
            
            
            db_design_case = DesignCaseModel(
                id=new_id,
                project_id=new_project_id,
                name=design_case["name"],
                description=design_case.get("description"),
                color=design_case.get("color", "#3357FF"),
                performance_values_json=performance_values_json,
                network_json=network_json,
                performance_snapshot_json=performance_snapshot_json,
                mountain_position_json=design_case.get("mountain_position_json"),
                utility_vector_json=design_case.get("utility_vector_json"),
                partial_heights_json=design_case.get("partial_heights_json"),
                performance_weights_json=design_case.get("performance_weights_json"),
                performance_deltas_json=design_case.get("performance_deltas_json"),
                # Phase 4: 新規フィールド（マイグレーション後はデフォルト値で設定済み）
                structural_analysis_json=design_case.get("structural_analysis_json"),
                paper_metrics_json=design_case.get("paper_metrics_json"),
                scc_analysis_json=design_case.get("scc_analysis_json"),
                kernel_type=design_case.get("kernel_type", "classic_wl"),
                weight_mode=design_case.get("weight_mode", "discrete")
            )
            db.add(db_design_case)
        
        # 2軸プロット設定のインポート（性能IDをマッピング）
        if "two_axis_plots" in project_data and project_data["two_axis_plots"]:
            old_plots = project_data["two_axis_plots"]
            new_plots = []
            for i, plot in enumerate(old_plots):
                new_plot = plot.copy()
                skip_plot = False
                
                # x軸の性能IDをマッピング（特殊値は除く）
                if plot.get("x_axis") and plot["x_axis"] not in ["__height", "__energy"]:
                    if plot["x_axis"] in performance_id_map:
                        new_plot["x_axis"] = performance_id_map[plot["x_axis"]]
                    else:
                        # マッピングできない場合はプロットをスキップ
                        skip_plot = True
                
                # y軸の性能IDをマッピング（特殊値は除く）
                if plot.get("y_axis") and plot["y_axis"] not in ["__height", "__energy"]:
                    if plot["y_axis"] in performance_id_map:
                        new_plot["y_axis"] = performance_id_map[plot["y_axis"]]
                    else:
                        # マッピングできない場合はプロットをスキップ
                        skip_plot = True
                
                # 両軸がマッピング可能な場合のみ追加
                if not skip_plot:
                    new_plots.append(new_plot)
            db_project.two_axis_plots = new_plots
        
        db.commit()
        
        # プロジェクトを再読み込み（リレーション含む）
        db.refresh(db_project)
        
        # 全設計案を取得（山の座標計算とエネルギー計算で共通使用）
        all_design_cases = db.query(DesignCaseModel).filter(
            DesignCaseModel.project_id == new_project_id
        ).all()
        
        
        # 作成したプロジェクトを返す
        return {
            "id": db_project.id,
            "name": db_project.name,
            "description": db_project.description,
            "created_at": db_project.created_at.isoformat(),
            "updated_at": db_project.updated_at.isoformat(),
            "needs_recalculation": True  # 山の座標とエネルギーの再計算が必要
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


# ========== ヘルパー関数 ==========

def format_design_case_response(db_design_case: DesignCaseModel) -> DesignCase:
    """DesignCaseModelをレスポンス形式に変換"""
    performance_values = json.loads(db_design_case.performance_values_json)
    network_data = json.loads(db_design_case.network_json)

    # weight_modeが設定されているか確認
    weight_mode = getattr(db_design_case, 'weight_mode', None)

    # 有効なweight_mode値のリスト
    VALID_WEIGHT_MODES = {'discrete_3', 'discrete_5', 'discrete_7', 'continuous'}

    # 古い 'discrete' や無効な値を検出
    has_valid_weight_mode = weight_mode in VALID_WEIGHT_MODES

    # 旧7段階モードからのマイグレーション
    # weight_modeが設定されていない古いデータの場合、エッジ重みをマイグレーション
    edges_data = network_data.get('edges', [])
    if not has_valid_weight_mode and needs_7_level_migration(edges_data):
        migrated_edges, _ = migrate_network_edges(edges_data, has_weight_mode=False)
        network_data['edges'] = migrated_edges
        weight_mode = 'discrete_7'  # マイグレーション後は新7段階モード
    elif not has_valid_weight_mode:
        weight_mode = 'discrete_7'  # デフォルト（'discrete'など無効値も含む）

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

    performance_deltas = None
    if hasattr(db_design_case, 'performance_deltas_json') and db_design_case.performance_deltas_json:
        performance_deltas = json.loads(db_design_case.performance_deltas_json)

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
        performance_deltas=performance_deltas,
        performance_snapshot=performance_snapshot,  # 追加！
        weight_mode=weight_mode
    )


def sort_performances_by_tree(performances):
    """深さ優先探索でツリー構造順にソート"""
    # 親子関係のマップを作成
    children_map = {}
    for perf in performances:
        parent_id = perf.parent_id
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(perf)
    
    # 各グループを名前順にソート
    for children in children_map.values():
        children.sort(key=lambda p: p.name)
    
    # 深さ優先探索で順序を構築
    result = []
    
    def traverse(parent_id):
        children = children_map.get(parent_id, [])
        for child in children:
            result.append(child)
            traverse(child.id)
    
    traverse(None)  # ルートから開始
    return result


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
    import time
    api_start = time.time()

    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if len(project.design_cases) == 0:
        return {"message": "No design cases to recalculate", "updated": 0}

    try:
        from app.services.mountain_calculator import calculate_mountain_positions

        # リクエストボディからネットワーク情報を取得
        networks = request_body.get('networks') if request_body else None

        calc_start = time.time()
        result = calculate_mountain_positions(project, db, networks=networks)
        calc_time = (time.time() - calc_start) * 1000

        positions = result['positions']
        H_max = result['H_max']
        calc_timings = result.get('timings', {})

        # 各設計案の座標を更新（calculate_mountain_positionsで既にcommit済みなのでスキップ）
        updated_count = len(positions)

        api_total = (time.time() - api_start) * 1000

        # positionsをシリアライズ可能な形式に変換
        serializable_positions = []
        for pos in positions:
            serializable_positions.append({
                'case_id': pos['case_id'],
                'x': pos['x'],
                'y': pos['y'],
                'z': pos['z'],
                'H': pos['H'],
                'total_energy': pos.get('energy', {}).get('total_energy', 0),
                'partial_heights': pos.get('partial_heights', {}),
                'partial_energies': pos.get('energy', {}).get('partial_energies', {}),
                'performance_weights': pos.get('performance_weights', {}),
                # utility_vectorはタプルキーなので文字列キーに変換
                'utility_vector': {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
            })

        return {
            "message": f"Successfully recalculated {updated_count} design cases",
            "updated": updated_count,
            "H_max": H_max,
            "positions": serializable_positions,  # 追加: 更新されたposition情報
            "timings": {
                "api_total_ms": round(api_total, 2),
                "calculation_ms": round(calc_time, 2),
                "breakdown": calc_timings
            }
        }

    except Exception as e:
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
        
        # 正規化された重みを使用するため、H_maxは1.0
        # 性能ごとの正規化された最大標高も計算
        
        # まず全体の重み合計を計算（正規化用）
        total_weight = 0.0
        performance_weights = {}  # 性能ごとの重み
        
        # 効用関数が設定されているペアを確認
        relations_with_utility = {}
        for rel in project.need_performance_relations:
            key = (rel.performance_id, rel.need_id)
            if rel.utility_function_json:
                relations_with_utility[key] = True
        
        # 重みの計算
        for key, votes in performance_need_votes.items():
            perf_id, need_id = key
            if perf_id in leaf_performance_ids and key in relations_with_utility:
                up_vote = votes['up']
                down_vote = votes['down']
                weight = up_vote + down_vote
                total_weight += weight
                
                if perf_id not in performance_weights:
                    performance_weights[perf_id] = 0.0
                performance_weights[perf_id] += weight
        
        # 正規化
        H_max = 1.0  # 正規化により常に1.0
        performance_h_max = {}
        
        if total_weight > 0:
            for perf_id, weight in performance_weights.items():
                performance_h_max[perf_id] = weight / total_weight
        
        return {
            "H_max": float(H_max),
            "performance_h_max": {k: float(v) for k, v in performance_h_max.items()}
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"H_max calculation failed: {str(e)}")


# ========== 2軸プロット ==========

@router.get("/{project_id}/two-axis-plots", response_model=List[dict])
def get_two_axis_plots(project_id: str, db: Session = Depends(get_db)):
    """プロジェクトの2軸プロット設定を取得"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.two_axis_plots


@router.put("/{project_id}/two-axis-plots")
def update_two_axis_plots(
    project_id: str, 
    plots: List[dict], 
    db: Session = Depends(get_db)
):
    """プロジェクトの2軸プロット設定を更新"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 各プロットのバリデーション
    for plot in plots:
        if 'id' not in plot or 'x_axis' not in plot or 'y_axis' not in plot:
            raise HTTPException(status_code=400, detail="Each plot must have id, x_axis, and y_axis")
    
    project.two_axis_plots = plots
    db.commit()
    
    return {"message": "Two-axis plots updated successfully", "plots": plots}


# ========== ネットワーク個別操作 (3D編集用) ==========

@router.get("/{project_id}/design-cases/{case_id}/nodes", response_model=List[NetworkNode])
def get_network_nodes(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """設計案のノード一覧を取得"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    if not design_case.network_json:
        return []
    
    network_data = json.loads(design_case.network_json)
    return [NetworkNode(**node) for node in network_data.get('nodes', [])]


@router.post("/{project_id}/design-cases/{case_id}/nodes", response_model=NetworkNode)
def create_network_node(
    project_id: str,
    case_id: str,
    node_create: NetworkNodeCreate,
    db: Session = Depends(get_db)
):
    """新しいノードを作成"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    # ネットワークデータを取得（存在しない場合は初期化）
    if design_case.network_json:
        network_data = json.loads(design_case.network_json)
    else:
        network_data = {'nodes': [], 'edges': []}
    
    # 新しいノードIDを生成
    node_id = str(uuid.uuid4())
    
    # ★ レイヤーに応じた2D座標のデフォルト値を設定
    if node_create.x is None or node_create.y is None:
        # レイヤーごとの中央Y座標（2Dキャンバス800を4分割）
        layer_center_y = {
            1: 100,   # 0-200の中央
            2: 300,   # 200-400の中央
            3: 500,   # 400-600の中央
            4: 700    # 600-800の中央
        }
        
        # 同じレイヤーの既存ノード数をカウント
        existing_nodes_in_layer = [n for n in network_data.get('nodes', []) if n.get('layer') == node_create.layer]
        node_count_in_layer = len(existing_nodes_in_layer)
        
        # X座標: レイヤー内で均等に分散（キャンバス幅1200）
        canvas_width = 1200
        spacing = canvas_width / (node_count_in_layer + 2)  # 両端に余白
        default_x = spacing * (node_count_in_layer + 1)
        
        # Y座標: レイヤーの中央に配置（少しランダムに分散）
        import random
        default_y = layer_center_y[node_create.layer] + random.randint(-30, 30)
    else:
        default_x = node_create.x
        default_y = node_create.y
    
    # 新しいノードを作成
    new_node = {
        'id': node_id,
        'label': node_create.label,
        'layer': node_create.layer,
        'type': node_create.type,
        'x': default_x,  # ← デフォルト値を使用
        'y': default_y,  # ← デフォルト値を使用
        'performance_id': node_create.performance_id,
        'x3d': node_create.x3d,
        'y3d': node_create.y3d
    }
    
    # ノードをネットワークに追加
    if 'nodes' not in network_data:
        network_data['nodes'] = []
    network_data['nodes'].append(new_node)
    
    # ネットワークデータを保存
    design_case.network_json = json.dumps(network_data)
    db.commit()
    
    # 山の座標を再計算（既存のコード）
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
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
            case = db.query(DesignCaseModel).filter(
                DesignCaseModel.id == pos['case_id']
            ).first()
            if case:
                case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                utility_vec_str_keys = {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
                case.utility_vector_json = json.dumps(utility_vec_str_keys)
                case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))

        db.commit()
    except Exception as e:
        pass  # Mountain calculation error - continue

    return NetworkNode(**new_node)

@router.put("/{project_id}/design-cases/{case_id}/nodes/{node_id}")
def update_network_node(
    project_id: str,
    case_id: str,
    node_id: str,
    node_update: NetworkNodeUpdate,
    db: Session = Depends(get_db)
):
    """ノードの情報を更新"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    if not design_case.network_json:
        raise HTTPException(status_code=404, detail="Network not found")
    
    network_data = json.loads(design_case.network_json)
    node_found = False
    
    # ノードを更新
    for node in network_data.get('nodes', []):
        if node['id'] == node_id:
            # 提供された値のみ更新
            if node_update.label is not None:
                node['label'] = node_update.label
            if node_update.x is not None:
                node['x'] = node_update.x
            if node_update.y is not None:
                node['y'] = node_update.y
            if node_update.x3d is not None:
                node['x3d'] = node_update.x3d
            if node_update.y3d is not None:
                node['y3d'] = node_update.y3d
            node_found = True
            break
    
    if not node_found:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # ネットワークデータを保存
    design_case.network_json = json.dumps(network_data)
    db.commit()
    
    # 山の座標を再計算（ネットワーク変更時）
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
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
        
        # 各設計案の座標を更新
        for pos in positions:
            case = db.query(DesignCaseModel).filter(
                DesignCaseModel.id == pos['case_id']
            ).first()
            if case:
                case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                utility_vec_str_keys = {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
                case.utility_vector_json = json.dumps(utility_vec_str_keys)
                case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))

        db.commit()
    except Exception as e:
        pass  # Mountain calculation error - continue

    return {"message": "Node updated successfully"}

@router.delete("/{project_id}/design-cases/{case_id}/nodes/{node_id}")
def delete_network_node(
    project_id: str,
    case_id: str,
    node_id: str,
    db: Session = Depends(get_db)
):
    """ノードを削除（関連するエッジも削除）"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    if not design_case.network_json:
        raise HTTPException(status_code=404, detail="Network not found")
    
    network_data = json.loads(design_case.network_json)
    
    # ノードを探す
    node_to_delete = None
    for node in network_data.get('nodes', []):
        if node['id'] == node_id:
            node_to_delete = node
            break
    
    if not node_to_delete:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # 性能ノードは削除不可
    if node_to_delete.get('type') == 'performance' and node_to_delete.get('performance_id'):
        raise HTTPException(status_code=400, detail="Performance nodes cannot be deleted")
    
    # ノードを削除
    network_data['nodes'] = [n for n in network_data.get('nodes', []) if n['id'] != node_id]
    
    # 関連するエッジも削除
    network_data['edges'] = [
        e for e in network_data.get('edges', [])
        if e['source_id'] != node_id and e['target_id'] != node_id
    ]
    
    # ネットワークデータを保存
    design_case.network_json = json.dumps(network_data)
    db.commit()
    
    # 山の座標を再計算
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
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
            case = db.query(DesignCaseModel).filter(
                DesignCaseModel.id == pos['case_id']
            ).first()
            if case:
                case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                utility_vec_str_keys = {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
                case.utility_vector_json = json.dumps(utility_vec_str_keys)
                case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))

        db.commit()
    except Exception as e:
        pass  # Mountain calculation error - continue

    return {"message": "Node deleted successfully"}


@router.delete("/{project_id}/design-cases/{case_id}/edges/{edge_id}")
def delete_network_edge(
    project_id: str,
    case_id: str,
    edge_id: str,
    db: Session = Depends(get_db)
):
    """エッジを削除"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    if not design_case.network_json:
        raise HTTPException(status_code=404, detail="Network not found")
    
    network_data = json.loads(design_case.network_json)
    
    # エッジを探す
    edge_found = any(e['id'] == edge_id for e in network_data.get('edges', []))
    
    if not edge_found:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    # エッジを削除
    network_data['edges'] = [e for e in network_data.get('edges', []) if e['id'] != edge_id]
    
    # ネットワークデータを保存
    design_case.network_json = json.dumps(network_data)
    db.commit()
    
    # 山の座標を再計算
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
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
            case = db.query(DesignCaseModel).filter(
                DesignCaseModel.id == pos['case_id']
            ).first()
            if case:
                case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                utility_vec_str_keys = {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
                case.utility_vector_json = json.dumps(utility_vec_str_keys)
                case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))

        db.commit()
    except Exception as e:
        pass  # Mountain calculation error - continue

    return {"message": "Edge deleted successfully"}

@router.put("/{project_id}/design-cases/{case_id}/nodes/{node_id}/position3d")
def update_node_3d_position(
    project_id: str,
    case_id: str,
    node_id: str,
    position_update: NodePositionUpdate,
    db: Session = Depends(get_db)
):
    """ノードの3D座標のみを更新（頻繁な位置更新用）"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    if not design_case.network_json:
        raise HTTPException(status_code=404, detail="Network not found")
    
    network_data = json.loads(design_case.network_json)
    node_found = False
    
    # ノードの3D座標を更新
    for node in network_data.get('nodes', []):
        if node['id'] == node_id:
            node['x3d'] = position_update.x3d
            node['y3d'] = position_update.y3d
            node_found = True
            break
    
    if not node_found:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # ネットワークデータを保存
    design_case.network_json = json.dumps(network_data)
    db.commit()
    
    return {"message": "Node 3D position updated successfully"}


@router.get("/{project_id}/design-cases/{case_id}/edges", response_model=List[NetworkEdge])
def get_network_edges(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db)
):
    """設計案のエッジ一覧を取得"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    if not design_case.network_json:
        return []
    
    network_data = json.loads(design_case.network_json)
    return [NetworkEdge(**edge) for edge in network_data.get('edges', [])]


@router.post("/{project_id}/design-cases/{case_id}/edges", response_model=NetworkEdge)
def create_network_edge(
    project_id: str,
    case_id: str,
    edge_create: NetworkEdgeCreate,
    db: Session = Depends(get_db)
):
    """新しいエッジを作成"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    # ネットワークデータを取得（存在しない場合は初期化）
    if design_case.network_json:
        network_data = json.loads(design_case.network_json)
    else:
        network_data = {'nodes': [], 'edges': []}
    
    # 指定されたノードが存在するか確認
    node_ids = {node['id'] for node in network_data.get('nodes', [])}
    if edge_create.source_id not in node_ids:
        raise HTTPException(status_code=400, detail="Source node not found")
    if edge_create.target_id not in node_ids:
        raise HTTPException(status_code=400, detail="Target node not found")
    
    # 新しいエッジIDを生成
    edge_id = str(uuid.uuid4())
    
    # 新しいエッジを作成
    new_edge = {
        'id': edge_id,
        'source_id': edge_create.source_id,
        'target_id': edge_create.target_id,
        'type': edge_create.type,
        'weight': edge_create.weight
    }
    
    # エッジをネットワークに追加
    if 'edges' not in network_data:
        network_data['edges'] = []
    network_data['edges'].append(new_edge)
    
    # ネットワークデータを保存
    design_case.network_json = json.dumps(network_data)
    db.commit()
    
    # 山の座標を再計算（ネットワーク変更時）
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
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
        
        # 各設計案の座標を更新
        for pos in positions:
            case = db.query(DesignCaseModel).filter(
                DesignCaseModel.id == pos['case_id']
            ).first()
            if case:
                case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                utility_vec_str_keys = {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
                case.utility_vector_json = json.dumps(utility_vec_str_keys)
                case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))

        db.commit()
    except Exception as e:
        pass  # Mountain calculation error - continue

    return NetworkEdge(**new_edge)


@router.put("/{project_id}/design-cases/{case_id}/edges/{edge_id}")
def update_network_edge(
    project_id: str,
    case_id: str,
    edge_id: str,
    edge_update: NetworkEdgeUpdate,
    db: Session = Depends(get_db)
):
    """エッジの情報を更新"""
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == case_id,
        DesignCaseModel.project_id == project_id
    ).first()
    
    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")
    
    if not design_case.network_json:
        raise HTTPException(status_code=404, detail="Network not found")
    
    network_data = json.loads(design_case.network_json)
    edge_found = False
    
    # エッジを更新
    for edge in network_data.get('edges', []):
        if edge['id'] == edge_id:
            if edge_update.weight is not None:
                edge['weight'] = edge_update.weight
            if edge_update.type is not None:
                edge['type'] = edge_update.type
            edge_found = True
            break
    
    if not edge_found:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    # ネットワークデータを保存
    design_case.network_json = json.dumps(network_data)
    db.commit()
    
    # 山の座標を再計算（エッジの重み変更時）
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
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
        
        # 各設計案の座標を更新
        for pos in positions:
            case = db.query(DesignCaseModel).filter(
                DesignCaseModel.id == pos['case_id']
            ).first()
            if case:
                case.mountain_position_json = json.dumps({
                    'x': pos['x'],
                    'y': pos['y'],
                    'z': pos['z'],
                    'H': pos['H'],
                    'total_energy': pos.get('total_energy', 0),
                    'partial_energies': pos.get('partial_energies', {})
                })
                utility_vec_str_keys = {
                    f"{k[0]}_{k[1]}": v for k, v in pos['utility_vector'].items()
                }
                case.utility_vector_json = json.dumps(utility_vec_str_keys)
                case.partial_heights_json = json.dumps(pos.get('partial_heights', {}))
                case.performance_weights_json = json.dumps(pos.get('performance_weights', {}))
                case.performance_deltas_json = json.dumps(pos.get('performance_deltas', {}))

        db.commit()
    except Exception as e:
        pass  # Mountain calculation error - continue
    
    return {"message": "Edge updated successfully"}


# ========== 論文用：ネットワークフィルタリング（一時的） ==========

@router.get("/{project_id}/design-cases/{design_case_id}/network/filtered")
def get_filtered_network_for_paper(
    project_id: str,
    design_case_id: str,
    db: Session = Depends(get_db)
):
    """
    論文用に特定のノードとエッジのみを抽出したネットワークを返す（一時的エンドポイント）

    抽出対象：
    - 浮体、浮体サイズ、流体抵抗、センターボード、センターボード面積、
      浮体速度(横)、発電出力、P7_耐波性、P1_エネルギー変換効率
    - 発電出力→P1への直接エッジを追加（元は発電出力→ネット発電量→P1）
    """
    # 設計案を取得
    design_case = db.query(DesignCaseModel).filter(
        DesignCaseModel.id == design_case_id,
        DesignCaseModel.project_id == project_id
    ).first()

    if not design_case:
        raise HTTPException(status_code=404, detail="Design case not found")

    # ネットワークデータを取得
    network = json.loads(design_case.network_json) if design_case.network_json else {'nodes': [], 'edges': []}

    # 抜き出したいノードのラベル
    target_labels = [
        "浮体",
        "浮体サイズ",
        "流体抵抗",
        "センターボード",
        "センターボード面積",
        "浮体速度(横)",
        "発電出力",
        "P7_耐波性",
        "P1_エネルギー変換効率"
    ]

    # ノードをフィルタリング
    all_nodes = network.get('nodes', [])
    filtered_nodes = [node for node in all_nodes if node.get('label') in target_labels]
    filtered_node_ids = {node['id'] for node in filtered_nodes}

    # エッジをフィルタリング（sourceもtargetも対象ノードに含まれる）
    all_edges = network.get('edges', [])
    filtered_edges = [
        edge for edge in all_edges
        if edge.get('source_id') in filtered_node_ids and edge.get('target_id') in filtered_node_ids
    ]

    # 発電出力 → P1 への直接エッジを追加
    output_node = next((n for n in filtered_nodes if n.get('label') == '発電出力'), None)
    p1_node = next((n for n in filtered_nodes if n.get('label') == 'P1_エネルギー変換効率'), None)

    if output_node and p1_node:
        # ネット発電量を経由するパスのエッジを確認
        net_output_node = next((n for n in all_nodes if n.get('label') == 'ネット発電量'), None)

        # 発電出力 → ネット発電量 のエッジからweightを取得
        edge_to_net = next(
            (e for e in all_edges
             if e.get('source_id') == output_node['id'] and e.get('target_id') == net_output_node['id']),
            None
        ) if net_output_node else None

        # 重みを決定（デフォルトは5.0）
        weight = edge_to_net.get('weight', 5.0) if edge_to_net else 5.0

        # 直接エッジを追加
        new_edge = {
            'id': f"edge-paper-output-to-p1",
            'source_id': output_node['id'],
            'target_id': p1_node['id'],
            'type': 'type4',
            'weight': weight
        }
        filtered_edges.append(new_edge)

    # ノード位置を調整（論文用レイアウト）
    # 浮体とセンターボードのx座標を取得
    float_node = next((n for n in filtered_nodes if n.get('label') == '浮体'), None)
    center_board_node = next((n for n in filtered_nodes if n.get('label') == 'センターボード'), None)

    if float_node and center_board_node:
        x1 = float_node.get('x', 120.0)
        x2 = center_board_node.get('x', 360.0)
        x_mid = (x1 + x2) / 2

        # x1に配置: 浮体サイズ、発電出力、P1
        x1_nodes = ['浮体サイズ', '発電出力', 'P1_エネルギー変換効率']
        for node in filtered_nodes:
            if node.get('label') in x1_nodes:
                node['x'] = x1

        # x2に配置: センターボード面積、流体抵抗、P7
        x2_nodes = ['センターボード面積', '流体抵抗', 'P7_耐波性']
        for node in filtered_nodes:
            if node.get('label') in x2_nodes:
                node['x'] = x2

        # x_midに配置: 浮体速度(横)
        for node in filtered_nodes:
            if node.get('label') == '浮体速度(横)':
                node['x'] = x_mid

    # フィルタリングされたネットワークを返す
    return {
        'nodes': filtered_nodes,
        'edges': filtered_edges
    }