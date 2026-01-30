from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.user import User
from app.models.enum import UserRole
from app.services.file_storage import save_uploaded_file, upload_and_parse_floorplan
import os

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def create_project(name: str, location: str, file: UploadFile, db: Session, current_user: User) -> Project:
    """Create a new project with uploaded file."""
    file_path = save_uploaded_file(file)

    # determine file type enum from extension
    ext = os.path.splitext(file.filename)[1].lower()
    try:
        from app.models.enum import FileType
        file_type = FileType(ext)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    new_project = Project(
        name=name,
        location=location,
        file_path=file_path,
        user_id=current_user.id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # create floorplan record and parse file
    try:
        upload_and_parse_floorplan(db, new_project.id, file_path, file_type)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save or parse floorplan")

    return new_project


def get_projects(db: Session, current_user: User) -> list[Project]:
    """Get all projects for admin, or only user's projects for regular users."""
    # Normalize role value to handle both Enum and plain string
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    
    if str(role_val).upper() == UserRole.ADMIN.value:
        return db.query(Project).all()
    return db.query(Project).filter(Project.user_id == current_user.id).all()


def get_project_by_id(project_id: int, db: Session, current_user: User) -> Project:
    """Get a project by id. Admin can access any project, others can only access their own."""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    
    if str(role_val).upper() == UserRole.ADMIN.value:
        project = db.query(Project).filter(Project.id == project_id).first()
    else:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project
