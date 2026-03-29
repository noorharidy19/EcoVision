from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AccessRequestResponse(BaseModel):
    id: int
    project_id: int
    requester_id: int
    requester_name: str
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
