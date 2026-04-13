from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
from app.models.user import User
from typing import List, Optional
from datetime import datetime


def create_activity_log(
    db: Session,
    user_id: int,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    log = ActivityLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_activity_logs_service(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
):
    query = db.query(ActivityLog).join(User)

    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if action:
        query = query.filter(ActivityLog.action == action)

    logs = query.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()

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
            "timestamp": log.timestamp,
        })

    return result


def track_activity_service(
    db: Session,
    user_id: int,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    log = create_activity_log(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    return {"message": "Activity logged", "log_id": log.id}


def test_logs_service(db: Session):
    count = db.query(ActivityLog).count()
    recent = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(5).all()
    return {
        "total_logs": count,
        "recent_actions": [
            {"id": log.id, "action": log.action, "user_id": log.user_id, "timestamp": str(log.timestamp)}
            for log in recent
        ],
    }
