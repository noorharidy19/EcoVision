from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = Path("uploaded_files")


@router.get("/protected/{file_path:path}")
def get_protected_file(file_path: str, current_user=Depends(get_current_user)):
    target = UPLOAD_DIR.joinpath(file_path)
    if not target.exists() or not target.resolve().is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(target), filename=target.name)
