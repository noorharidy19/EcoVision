from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
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
        password_hash=get_password_hash(user.password)
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
        raise ValueError("User not found")

    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.phone_number is not None:
        db_user.phone_number = user_update.phone_number
    if user_update.password:
        db_user.password_hash = get_password_hash(user_update.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
