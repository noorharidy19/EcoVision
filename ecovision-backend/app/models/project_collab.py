from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enum import ProjectRole


class ProjectCollaborator(Base):
    __tablename__ = "project_collaborators"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    role = Column(Enum(ProjectRole), default=ProjectRole.COLLABORATOR)

    added_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="collaborators")

    user = relationship("User", back_populates="collaborations")
    __table_args__ = (
        UniqueConstraint("project_id", "user_id"),
    )