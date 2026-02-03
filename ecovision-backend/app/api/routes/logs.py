from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.activity_log import ActivityLog
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

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
def create_activity_log(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    details: str = None,
    ip_address: str = None
):
    log = ActivityLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

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
    
    query = db.query(ActivityLog).join(User)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if action:
        query = query.filter(ActivityLog.action == action)
    
    logs = query.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    # Format response with user info
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.full_name or "Unknown",
            "user_email": log.user.email,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp
        })
    
    return result

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
    
    log = create_activity_log(
        db=db,
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    
    return {"message": "Activity logged", "log_id": log.id}

@router.get("/test")
def test_logs(db: Session = Depends(get_db)):
    """Test endpoint to check if logs exist - for debugging"""
    count = db.query(ActivityLog).count()
    recent = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(5).all()
    return {
        "total_logs": count,
        "recent_actions": [{"id": log.id, "action": log.action, "user_id": log.user_id, "timestamp": str(log.timestamp)} for log in recent]
    }
