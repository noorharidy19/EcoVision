from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text ,  Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.enum import AnalysisType


class FloorplanAnalysis(Base):
    __tablename__ = "floorplan_analysis"

    id = Column(Integer, primary_key=True, index=True)
    floorplan_id = Column(Integer, ForeignKey("floorplans.id"), nullable=False)
    analysis_type = Column(Enum(AnalysisType), nullable=False)  # e.g., "MATERIAL", "THERMAL", "VISUAL"
    modelUsed= Column(String(100), nullable=False)  # e.g., "Model A", "Model B"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    floorplan = relationship("Floorplan", back_populates="analysis")