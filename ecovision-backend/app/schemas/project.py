from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    location: str

class ProjectResponse(ProjectCreate):
    id: int
    file_path: str

    class Config:
        from_attributes = True
