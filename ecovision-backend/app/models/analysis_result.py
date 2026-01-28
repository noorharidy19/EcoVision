from sqlalchemy import Column, Integer, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    comfort_score = Column(Float)
    material_efficiency = Column(Float)

    details = Column(JSON)  # output بتاع AI / analysis
    version = Column(Integer, default=1)