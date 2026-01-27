from pydantic import BaseModel
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    location: str
    
    
class UserMini(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True   

class ProjectResponse(ProjectCreate):
    id: int
    name: str
    location: str
    file_path: str
    created_at: datetime
    user_id: int

    class Config:
     from_attributes = True

