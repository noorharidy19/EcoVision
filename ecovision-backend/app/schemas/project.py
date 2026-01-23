from pydantic import BaseModel
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    location: str

class ProjectResponse(ProjectCreate):
    id: int
    name: str
    file_path: str
    created_at: datetime

    class Config:
     from_attributes = True

