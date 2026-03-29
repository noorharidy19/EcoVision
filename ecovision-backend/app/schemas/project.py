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


class ProjectWithOwner(ProjectResponse):
    owner: str = None
    
    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "name": obj.name,
            "location": obj.location,
            "file_path": obj.file_path,
            "created_at": obj.created_at,
            "user_id": obj.user_id,
            "owner": obj.user.full_name if obj.user else "Unknown"
        }
        return cls(**data)

    class Config:
        from_attributes = True
