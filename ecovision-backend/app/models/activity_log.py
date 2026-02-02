from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "login", "create_project", "delete_project"
    resource_type = Column(String(50))  # e.g., "project", "floorplan", "user"
    resource_id = Column(Integer)  # ID of the resource affected
    details = Column(Text)  # JSON string or additional info
    ip_address = Column(String(45))  # IPv4 or IPv6
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="activity_logs")
