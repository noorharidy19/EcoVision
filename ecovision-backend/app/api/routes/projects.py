from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.project import ProjectResponse
from app.services.auth_service import get_current_user
from app.services.project_service import create_project as create_project_service, get_projects as get_projects_service, get_project_by_id as get_project_by_id_service
from app.models.user import User
from app.models.project import Project
from app.models.floorplan import Floorplan
from app.models.activity_log import ActivityLog
from pydantic import BaseModel
import os

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectUpdate(BaseModel):
    name: str
    location: str

@router.post("/", response_model=ProjectResponse)
def create_project(
    name: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = create_project_service(name, location, file, db, current_user)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="create_project",
        resource_type="project",
        resource_id=project.id,
        details=f"Created project: {name}"
    )
    db.add(log)
    db.commit()
    
    return project

@router.get("/", response_model=list[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_projects_service(db, current_user)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_project_by_id_service(project_id, db, current_user)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    update_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project name and location"""
    # Get the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check authorization
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")
    
    # Update fields
    project.name = update_data.name
    project.location = update_data.location
    
    db.commit()
    db.refresh(project)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="update_project",
        resource_type="project",
        resource_id=project_id,
        details=f"Updated project: {update_data.name}"
    )
    db.add(log)
    db.commit()
    
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project and its associated files"""
    # Get the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check authorization
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    # Log activity before deletion
    log = ActivityLog(
        user_id=current_user.id,
        action="delete_project",
        resource_type="project",
        resource_id=project_id,
        details=f"Deleted project: {project.name}"
    )
    db.add(log)
    db.commit()
    
    # Delete associated floorplan files
    floorplans = db.query(Floorplan).filter(Floorplan.project_id == project_id).all()
    for floorplan in floorplans:
        if floorplan.file_path and os.path.exists(floorplan.file_path):
            try:
                os.remove(floorplan.file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {floorplan.file_path}: {e}")
    
    # Delete floorplans from database
    db.query(Floorplan).filter(Floorplan.project_id == project_id).delete()
    
    # Delete the project
    db.delete(project)
    db.commit()
    
    return {"message": f"Project {project_id} deleted successfully"}