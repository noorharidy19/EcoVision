from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enum import RequestAccess


class ProjectAccess(Base):
    __tablename__ = "project_access_requests"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(Enum(RequestAccess, native_enum=False), default="PENDING")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    responded_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="access_requests")

    requester = relationship("User", back_populates="access_requests")
