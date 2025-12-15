# backend/app/schemas/project.py

from typing import Optional, List, Dict, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field


class StakeholderBase(BaseModel):
    name: str
    category: Optional[str] = None
    votes: int = 100
    description: Optional[str] = None


class StakeholderCreate(StakeholderBase):
    pass


class Stakeholder(StakeholderBase):
    id: str
    
    class Config:
        from_attributes = True


class NeedBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: float = 1.0  # 優先度（0~1、デフォルト1.0）


class NeedCreate(NeedBase):
    pass


class Need(NeedBase):
    id: str
    
    class Config:
        from_attributes = True


class StakeholderNeedRelation(BaseModel):
    stakeholder_id: str
    need_id: str
    relationship_weight: float = 1.0  # 1.0=○, 0.5=△


class PerformanceBase(BaseModel):
    name: str
    parent_id: Optional[str] = None
    level: int = 0
    is_leaf: bool = True
    unit: Optional[str] = None
    description: Optional[str] = None


class PerformanceCreate(PerformanceBase):
    pass


class UtilityPoint(BaseModel):
    x: float
    y: float = Field(ge=0, le=1)  # 0~1の範囲


class UtilityFunction(BaseModel):
    type: Literal['continuous', 'discrete']
    points: List[UtilityPoint]


class Performance(PerformanceBase):
    id: str
    utility_function: Optional[UtilityFunction] = None
    
    class Config:
        from_attributes = True


class DiscreteRow(BaseModel):
    label: str
    value: float = Field(ge=0, le=1)


class UtilityFunctionData(BaseModel):
    need_id: str
    performance_id: str
    direction: Literal['up', 'down']
    type: Literal['continuous', 'discrete']
    axisMin: Optional[float] = None
    axisMax: Optional[float] = None
    points: Optional[List[Dict[str, float]]] = None
    discreteRows: Optional[List[DiscreteRow]] = None
    saved: bool = False
    warning: bool = False
    archived: bool = False


class NeedPerformanceRelation(BaseModel):
    need_id: str
    performance_id: str
    direction: Literal['up', 'down']
    utility_function_json: Optional[str] = None


class NetworkNode(BaseModel):
    id: str
    layer: Literal[1, 2, 3, 4]
    type: Literal['performance', 'property', 'variable', 'object', 'environment']
    label: str
    x: float
    y: float
    performance_id: Optional[str] = None
    x3d: Optional[float] = None
    y3d: Optional[float] = None


class NetworkEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    type: Literal['type1', 'type2', 'type3', 'type4']
    weight: Optional[float] = None  # 3, 1, 0.33, 0, -0.33, -1, -3


class NetworkStructure(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]


class MountainPosition(BaseModel):
    x: float
    y: float
    z: float
    H: float


class DesignCaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = '#3357FF'
    performance_values: Dict[str, Union[float, str]]  # 離散値の場合は文字列
    network: NetworkStructure


class DesignCaseCreate(DesignCaseBase):
    performance_snapshot: List[Dict]  # 作成時のみ必須


class DesignCaseUpdate(DesignCaseBase):
    pass  # 更新時はperformance_snapshotを含めない


class DesignCase(DesignCaseBase):
    id: str
    created_at: datetime
    updated_at: datetime
    performance_snapshot: Optional[List[Dict]] = None  # オプショナル（既存データ対応）
    mountain_position: Optional[MountainPosition] = None
    utility_vector: Optional[Dict[str, float]] = None
    partial_heights: Optional[Dict[str, float]] = None  # 性能ごとの部分標高
    performance_weights: Optional[Dict[str, float]] = None  # 性能ごとの合成票数
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """ORM モデルから Pydantic モデルへの変換"""
        # _performance_snapshot_temp があればそれを使用、なければ @property を使用
        if hasattr(obj, '_performance_snapshot_temp'):
            snapshot = obj._performance_snapshot_temp
        elif hasattr(obj, 'performance_snapshot'):
            snapshot = obj.performance_snapshot
        else:
            snapshot = None
            
        data = {
            'id': obj.id,
            'name': obj.name,
            'description': obj.description,
            'color': obj.color,
            'performance_values': obj.performance_values,
            'network': obj.network,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'performance_snapshot': snapshot,
            'mountain_position': obj.mountain_position,
            'utility_vector': obj.utility_vector,
            'partial_heights': obj.partial_heights,
            'performance_weights': obj.performance_weights,
        }
        return super().model_validate(data, **kwargs)


class TwoAxisPlot(BaseModel):
    id: str
    x_axis: str  # performance_id or "__height" or "__energy"
    y_axis: str  # performance_id or "__height" or "__energy"


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    stakeholders: List[Stakeholder] = []
    needs: List[Need] = []
    performances: List[Performance] = []
    design_cases: List[DesignCase] = []
    stakeholder_need_relations: List[StakeholderNeedRelation] = []
    need_performance_relations: List[NeedPerformanceRelation] = []
    two_axis_plots: List[TwoAxisPlot] = []
    
    class Config:
        from_attributes = True


# class HHIResult(BaseModel):  # HHI分析削除
#     performance_id: str
#     hhi: float
#     p_squared: float
#     weight: float
#     children_count: int


class VoteDistribution(BaseModel):
    need_id: str
    effective_votes: float
    up_votes: float
    down_votes: float
