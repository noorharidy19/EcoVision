from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectResponse
from app.services.file_storage import save_uploaded_file

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectResponse)
def create_project(
    name: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_path = save_uploaded_file(file)

    project = Project(
        name=name,
        location=location,
        file_path=file_path
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project
