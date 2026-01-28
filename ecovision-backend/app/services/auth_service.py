from fastapi import HTTPException, status, Request, Response, Depends
from sqlalchemy.orm import Session
from datetime import timedelta

from app.models.user import User
from app.core.security import verify_password, create_access_token, decode_access_token
from app.core.config import settings
from app.core.database import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract and validate current user from JWT token or cookie."""
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


def login_user(response: Response, email: str, password: str, db: Session):
    """Authenticate user and set session cookie."""
    user: User = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Extract role value (handle Enum or string)
    role_val = user.role.value if hasattr(user.role, "value") else user.role

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": str(role_val)}, 
        expires_delta=access_token_expires
    )

    # Set HttpOnly cookie for session-based auth
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="lax",
        secure=False,
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": str(role_val)},
    }


def logout_user(response: Response):
    """Clear session cookie."""
    response.delete_cookie("access_token", path="/")
    return {"msg": "logged out"}
