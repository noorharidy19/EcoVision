from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user, get_users, delete_user


router = APIRouter(prefix="/admin", tags=["Admin"])

# View all users
@router.get("/users", response_model=list[UserResponse])
def view_users(db: Session = Depends(get_db)):
    return get_users(db)


# Add new user
@router.post("/users", response_model=UserResponse)
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)


# Delete user
@router.delete("/users/{user_id}")
def remove_user(user_id: int, db: Session = Depends(get_db)):
    deleted = delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
