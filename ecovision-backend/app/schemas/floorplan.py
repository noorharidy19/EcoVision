from pydantic import BaseModel
from uuid import UUID
from app.models.enum import FileType


class FloorplanResponse(BaseModel):
    id: UUID
    file_path: str
    file_type: FileType
    version: int

    class Config:
        from_attributes = True
class FloorplanGenerateRequest(BaseModel):
    dxf_data: dict
    prompt: str
