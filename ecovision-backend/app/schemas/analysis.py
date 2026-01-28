from pydantic import BaseModel
from uuid import UUID


class AnalysisResultResponse(BaseModel):
    id: UUID
    comfort_score: float
    material_efficiency: float
    details: dict
    version: int

    class Config:
        from_attributes = True
