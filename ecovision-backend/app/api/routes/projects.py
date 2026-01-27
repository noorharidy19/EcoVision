from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import shutil
from app.core.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectResponse
from app.services.file_storage import save_uploaded_file
from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=ProjectResponse)
def create_project(
    name: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    file_path = save_uploaded_file(file)

    new_project = Project(
        name=name,
        location=location,
        file_path=file_path,
        user_id=current_user.id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project

@router.get("/", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()
