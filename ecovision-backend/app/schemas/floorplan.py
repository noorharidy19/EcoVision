from pydantic import BaseModel
from uuid import UUID
from app.models.enums import FileType


class FloorplanResponse(BaseModel):
    id: UUID
    file_path: str
    file_type: FileType
    version: int

    class Config:
        from_attributes = True
