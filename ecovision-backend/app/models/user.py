from sqlalchemy import Column, Integer, String
from app.core.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="Architect")
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    projects = relationship("Project", back_populates="user")


   
