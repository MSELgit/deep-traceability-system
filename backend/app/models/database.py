# backend/app/models/database.py

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import os

# 環境変数からデータベースURLを取得
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/local.db')

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """データベースセッションを取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# JSONフィールド用のヘルパー
class JSONEncodedDict(str):
    """JSONとして保存される辞書型"""
    pass


class ProjectModel(Base):
    __tablename__ = 'projects'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    stakeholders = relationship('StakeholderModel', back_populates='project', cascade='all, delete-orphan')
    needs = relationship('NeedModel', back_populates='project', cascade='all, delete-orphan')
    performances = relationship('PerformanceModel', back_populates='project', cascade='all, delete-orphan')
    design_cases = relationship('DesignCaseModel', back_populates='project', cascade='all, delete-orphan')
    stakeholder_need_relations = relationship('StakeholderNeedRelationModel', back_populates='project', cascade='all, delete-orphan')
    need_performance_relations = relationship('NeedPerformanceRelationModel', back_populates='project', cascade='all, delete-orphan')


class StakeholderModel(Base):
    __tablename__ = 'stakeholders'
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    votes = Column(Integer, default=100)
    description = Column(Text, nullable=True)
    
    project = relationship('ProjectModel', back_populates='stakeholders')


class NeedModel(Base):
    __tablename__ = 'needs'
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    project = relationship('ProjectModel', back_populates='needs')


class StakeholderNeedRelationModel(Base):
    __tablename__ = 'stakeholder_need_relations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    stakeholder_id = Column(String, nullable=False)
    need_id = Column(String, nullable=False)
    
    project = relationship('ProjectModel', back_populates='stakeholder_need_relations')
    
    # ユニーク制約: 同じプロジェクト内で同じステークホルダー×ニーズの組み合わせは1つまで
    __table_args__ = (
        UniqueConstraint('project_id', 'stakeholder_id', 'need_id', name='uq_stakeholder_need'),
    )


class PerformanceModel(Base):
    __tablename__ = 'performances'
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    name = Column(String, nullable=False)
    parent_id = Column(String, nullable=True)
    level = Column(Integer, default=0)
    is_leaf = Column(Boolean, default=True)
    unit = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    utility_function_json = Column(Text, nullable=True)  # JSON文字列として保存
    
    project = relationship('ProjectModel', back_populates='performances')


class NeedPerformanceRelationModel(Base):
    __tablename__ = 'need_performance_relations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    need_id = Column(String, nullable=False)
    performance_id = Column(String, nullable=False)
    direction = Column(String, nullable=False)  # 'up' or 'down'
    utility_function_json = Column(Text, nullable=True)  # 効用関数データ（JSON形式）
    
    project = relationship('ProjectModel', back_populates='need_performance_relations')
    
    # ユニーク制約: 同じプロジェクト内で同じニーズ×性能の組み合わせは1つまで
    __table_args__ = (
        UniqueConstraint('project_id', 'need_id', 'performance_id', name='uq_need_performance'),
    )


class DesignCaseModel(Base):
    __tablename__ = 'design_cases'
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, default='#3357FF') 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # JSON形式で保存
    performance_values_json = Column(Text, nullable=False)
    network_json = Column(Text, nullable=False)
    performance_snapshot_json = Column(Text, nullable=False, default='[]')
    mountain_position_json = Column(Text, nullable=True)
    utility_vector_json = Column(Text, nullable=True)
    partial_heights_json = Column(Text, nullable=True)  # 性能ごとの部分標高
    performance_weights_json = Column(Text, nullable=True)  # 性能ごとの合計票数
    
    project = relationship('ProjectModel', back_populates='design_cases')
    
    @property
    def performance_values(self):
        """performance_values_jsonをパース"""
        import json
        return json.loads(self.performance_values_json) if self.performance_values_json else {}
    
    @property
    def network(self):
        """network_jsonをパース"""
        import json
        return json.loads(self.network_json) if self.network_json else {}
    
    @property
    def performance_snapshot(self):
        """performance_snapshot_jsonをパース"""
        import json
        return json.loads(self.performance_snapshot_json) if self.performance_snapshot_json else []
    
    @property
    def mountain_position(self):
        """mountain_position_jsonをパース"""
        import json
        return json.loads(self.mountain_position_json) if self.mountain_position_json else None
    
    @property
    def utility_vector(self):
        """utility_vector_jsonをパース"""
        import json
        return json.loads(self.utility_vector_json) if self.utility_vector_json else None
    
    @property
    def partial_heights(self):
        """partial_heights_jsonをパース"""
        import json
        return json.loads(self.partial_heights_json) if self.partial_heights_json else None
    
    @property
    def performance_weights(self):
        """performance_weights_jsonをパース"""
        import json
        return json.loads(self.performance_weights_json) if self.performance_weights_json else None


# テーブル作成
def init_db():
    """データベーステーブルを初期化"""
    Base.metadata.create_all(bind=engine)
