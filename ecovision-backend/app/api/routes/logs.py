from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.services.logs_service import (
    create_activity_log,
    get_activity_logs_service,
    track_activity_service,
    test_logs_service,
)

router = APIRouter(prefix="/logs", tags=["logs"])

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

# Create activity log utility function
# service functions live in app.services.logs_service

@router.get("/", response_model=List[ActivityLogResponse])
def get_activity_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity logs (admin only)"""
    # Handle both Enum and string role values
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if str(role_val).upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_activity_logs_service(db, skip=skip, limit=limit, user_id=user_id, action=action)

@router.post("/track")
def track_activity(
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    details: str = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track user activity"""
    ip_address = request.client.host if request else None
    return track_activity_service(db=db, user_id=current_user.id, action=action, resource_type=resource_type, resource_id=resource_id, details=details, ip_address=ip_address)

@router.get("/test")
def test_logs(db: Session = Depends(get_db)):
    """Test endpoint to check if logs exist - for debugging"""
    return test_logs_service(db)
