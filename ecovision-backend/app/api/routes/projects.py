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
from fastapi import HTTPException

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
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
     if current_user.role == "admin":
        return db.query(Project).all()
     return db.query(Project).filter(Project.user_id == current_user.id).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project