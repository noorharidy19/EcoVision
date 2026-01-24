from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user
from app.schemas.user import UserUpdate
from app.services.user_service import update_user
from app.core.security import verify_password, create_access_token, decode_access_token
from app.models.user import User
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return new_user


@router.post("/login")
def login(response: Response, form_data: UserCreate, db: Session = Depends(get_db)):
    # using UserCreate for simplicity (email + password)
    user: User = db.query(User).filter(User.email == form_data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, expires_delta=access_token_expires
    )

    # Set HttpOnly cookie for session-based auth; frontend should use credentials: 'include'
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="lax",
        secure=False,  # set True in production with HTTPS
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = None
    # First try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    else:
        # Fallback to cookie
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


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
    # Clear cookie
    response.delete_cookie("access_token", path="/")
    return {"msg": "logged out"}

