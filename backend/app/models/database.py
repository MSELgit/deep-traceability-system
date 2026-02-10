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
    
    # 2軸プロット設定（JSON形式）
    # [{"id": "view1", "x_axis": "perf_id_or_special", "y_axis": "perf_id_or_special"}, ...]
    _two_axis_plots = Column('two_axis_plots', Text, nullable=True)
    
    @property
    def two_axis_plots(self):
        """JSON文字列をパースして返す"""
        import json
        if self._two_axis_plots:
            return json.loads(self._two_axis_plots)
        return []
    
    @two_axis_plots.setter
    def two_axis_plots(self, value):
        """辞書をJSON文字列として保存"""
        import json
        if value is None:
            self._two_axis_plots = None
        else:
            self._two_axis_plots = json.dumps(value, ensure_ascii=False)
    
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
    priority = Column(Float, default=1.0)  # 優先度（0~1、デフォルト1.0）
    
    project = relationship('ProjectModel', back_populates='needs')


class StakeholderNeedRelationModel(Base):
    __tablename__ = 'stakeholder_need_relations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    stakeholder_id = Column(String, nullable=False)
    need_id = Column(String, nullable=False)
    relationship_weight = Column(Float, default=1.0, nullable=False)  # 1.0=○, 0.5=△
    
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

    @property
    def utility_function(self):
        """utility_function_jsonをパースして返す"""
        if self.utility_function_json:
            return json.loads(self.utility_function_json)
        return None


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

    # JSON形式で保存（既存）
    performance_values_json = Column(Text, nullable=False)
    network_json = Column(Text, nullable=False)
    performance_snapshot_json = Column(Text, nullable=False, default='[]')
    mountain_position_json = Column(Text, nullable=True)
    utility_vector_json = Column(Text, nullable=True)
    partial_heights_json = Column(Text, nullable=True)  # 性能ごとの部分標高
    performance_weights_json = Column(Text, nullable=True)  # 性能ごとの合計票数
    performance_deltas_json = Column(Text, nullable=True)  # 性能ごとの正味方向票 δ_i = n_i↑ - n_i↓

    # Phase 4: 新規追加フィールド（全てOptional、既存データとの互換性維持）
    structural_analysis_json = Column(Text, nullable=True)  # 構造的トレードオフ分析結果
    paper_metrics_json = Column(Text, nullable=True)  # 論文準拠指標（H, E等）
    scc_analysis_json = Column(Text, nullable=True)  # SCC分解（ループ検出）結果
    kernel_type = Column(String(50), nullable=True, default='classic_wl')  # WLカーネルタイプ
    weight_mode = Column(String(20), nullable=True, default='discrete_7')  # エッジ重みモード

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

    @property
    def performance_deltas(self):
        """performance_deltas_jsonをパース（正味方向票 δ_i）"""
        import json
        return json.loads(self.performance_deltas_json) if self.performance_deltas_json else None

    @property
    def structural_analysis(self):
        """structural_analysis_jsonをパース"""
        import json
        return json.loads(self.structural_analysis_json) if self.structural_analysis_json else None

    @property
    def paper_metrics(self):
        """paper_metrics_jsonをパース"""
        import json
        return json.loads(self.paper_metrics_json) if self.paper_metrics_json else None

    @property
    def scc_analysis(self):
        """scc_analysis_jsonをパース"""
        import json
        return json.loads(self.scc_analysis_json) if self.scc_analysis_json else None


# テーブル作成
def init_db():
    """データベーステーブルを初期化"""
    Base.metadata.create_all(bind=engine)
    # 既存テーブルに不足カラムを追加（自動マイグレーション）
    _auto_migrate()


def _auto_migrate():
    """
    既存テーブルに不足しているカラムを自動追加するマイグレーション

    SQLiteの場合、ALTER TABLE ADD COLUMNでカラムを追加できる。
    既存データは新カラムにNULLまたはデフォルト値が設定される。
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    # design_cases テーブルのマイグレーション
    if 'design_cases' in inspector.get_table_names():
        existing_columns = {col['name'] for col in inspector.get_columns('design_cases')}

        # Phase 4で追加したカラム
        new_columns = [
            ('performance_deltas_json', 'TEXT'),
            ('structural_analysis_json', 'TEXT'),
            ('paper_metrics_json', 'TEXT'),
            ('scc_analysis_json', 'TEXT'),
            ('kernel_type', "VARCHAR(50) DEFAULT 'classic_wl'"),
            ('weight_mode', "VARCHAR(20) DEFAULT 'discrete_7'"),
        ]

        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        conn.execute(text(f'ALTER TABLE design_cases ADD COLUMN {col_name} {col_type}'))
                        conn.commit()
                        print(f'[Migration] Added column: design_cases.{col_name}')
                    except Exception as e:
                        # カラムが既に存在する場合などはスキップ
                        print(f'[Migration] Skipped {col_name}: {e}')
