from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.project import ProjectResponse, ProjectWithOwner
from app.schemas.access_request import AccessRequestResponse
from app.services.auth_service import get_current_user
from app.services.project_service import (
  create_project_service,
    get_projects as get_projects_service,
    get_project_by_id as get_project_by_id_service
)
from app.services.project_service import (
    get_all_projects as get_all_projects_service,
    update_project_service,
    delete_project_service,
    request_access_service,
    approve_request_service,
    decline_request_service,
    get_project_requests_service,
    get_my_approved_projects_service,
    get_my_collaborators_service
)
from app.models.user import User
from app.models.project import Project
from app.models.floorplan import Floorplan
from app.models.activity_log import ActivityLog
from app.models.project_access import ProjectAccess  # ✅ لازم يكون عندك موديل Access Request
from app.models.project_collab import ProjectCollaborator
from pydantic import BaseModel
import os
from app.models.enum import RequestAccess
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectUpdate(BaseModel):
    name: str
    location: str


# =========================
# CREATE PROJECT
# =========================
@router.post("/")
def create_project(
    name: str = Form(...),
    location: str = Form(...),
    north_arrow_direction: str = Form(...),
    rooms_json: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # FORCE RELOAD - v2
    project = create_project_service(
        name=name,
        location=location,
        north_arrow_direction=north_arrow_direction,
        rooms_json=rooms_json,
        file=file,
        db=db,
        current_user=current_user
    )

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


# =========================
# GET MY PROJECTS
# =========================
@router.get("/", response_model=list[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_projects_service(db, current_user)


# =========================
# GET ALL PROJECTS
# =========================
@router.get("/all")
def get_all_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_all_projects_service(db, current_user)


# =========================
# GET PROJECT BY ID
# =========================
@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_project_by_id_service(project_id, db, current_user)


# =========================
# UPDATE PROJECT
# =========================
@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    update_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_project_service(project_id, update_data.name, update_data.location, db, current_user)


# =========================
# DELETE PROJECT
# =========================
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return delete_project_service(project_id, db, current_user)


# =========================
# REQUEST ACCESS
# =========================
@router.post("/{project_id}/request-access")
def request_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return request_access_service(project_id, db, current_user)


# =========================
# APPROVE ACCESS REQUEST
# =========================
@router.post("/{project_id}/requests/{request_id}/approve")
def approve_request(
    project_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return approve_request_service(project_id, request_id, db, current_user)


# =========================
# DECLINE ACCESS REQUEST
# =========================
@router.post("/{project_id}/requests/{request_id}/decline")
def decline_request(
    project_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return decline_request_service(project_id, request_id, db, current_user)


# =========================
# GET PROJECT ACCESS REQUESTS
# =========================
@router.get("/{project_id}/requests", response_model=list[AccessRequestResponse])
def get_project_requests(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_project_requests_service(project_id, db, current_user)


# =========================
# GET MY APPROVED PROJECTS (as Collaborator)
# =========================
@router.get("/collaborations/my-approved")
def get_my_approved_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_my_approved_projects_service(db, current_user)


# =========================
# GET MY COLLABORATORS & ACCESS REQUESTS
# =========================
@router.get("/access-requests/my-approvals")
def get_my_collaborators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_my_collaborators_service(db, current_user)