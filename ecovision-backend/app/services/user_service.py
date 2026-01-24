from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
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
