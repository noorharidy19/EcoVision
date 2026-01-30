from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.enum import FileType
from sqlalchemy.orm import relationship


class Floorplan(Base):
    __tablename__ = "floorplans"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, default=1)
    project = relationship("Project", back_populates="floorplans")
