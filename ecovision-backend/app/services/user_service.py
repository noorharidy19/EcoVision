from sqlalchemy.orm import Session
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.project import Project
from app.models.project_collab import ProjectCollaborator
from app.models.project_access import ProjectAccess
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


def create_user(db: Session, user: UserCreate):
    # check existing
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise ValueError("User with this email already exists")

    db_user = User(
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        password_hash=get_password_hash(user.password),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session):
    return db.query(User).all()


def update_user(db: Session, user_id: int, user_update: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None

    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.phone_number is not None:
        db_user.phone_number = user_update.phone_number
    if user_update.role is not None:
        db_user.role = user_update.role
    if user_update.password:
        db_user.password_hash = get_password_hash(user_update.password)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")

    # Delete related records to avoid foreign key constraint violations
    # 1. Delete all activity logs for this user
    db.query(ActivityLog).filter(ActivityLog.user_id == user_id).delete()
    
    # 2. Delete all collaborations where user is a collaborator
    db.query(ProjectCollaborator).filter(ProjectCollaborator.user_id == user_id).delete()
    
    # 3. Delete all access requests made by this user
    db.query(ProjectAccess).filter(ProjectAccess.requester_id == user_id).delete()
    
    # 4. Delete all projects owned by this user (cascade will handle related floorplans, etc.)
    db.query(Project).filter(Project.user_id == user_id).delete()
    
    # 5. Finally delete the user
    db.delete(db_user)
    db.commit()
    return db_user

