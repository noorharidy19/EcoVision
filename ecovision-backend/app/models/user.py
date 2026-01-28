from sqlalchemy import Column, Enum, Integer, String
from app.core.database import Base
from sqlalchemy.orm import relationship
from app.models.enum import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.ARCHITECT.value)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    projects = relationship("Project", back_populates="user")


   
