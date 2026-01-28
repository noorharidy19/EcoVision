from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database.base import Base
from app.models.enum import FileType


class Floorplan(Base):
    __tablename__ = "floorplans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String, nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, default=1)
