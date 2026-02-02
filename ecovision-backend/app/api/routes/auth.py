from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_user, update_user
from app.services.auth_service import get_current_user, login_user, logout_user
from app.models.user import User
from app.models.activity_log import ActivityLog


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = create_user(db, user)
        # Log activity
        log = ActivityLog(
            user_id=new_user.id,
            action="signup",
            details=f"New user registered: {user.email}"
        )
        db.add(log)
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return new_user


@router.post("/login")
def login(response: Response, form_data: UserCreate, db: Session = Depends(get_db)):
    return login_user(response, form_data.email, form_data.password, db)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        updated = update_user(db, current_user.id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated


@router.post("/logout")
def logout(response: Response):
    return logout_user(response)

