from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.project import ProjectResponse, ProjectWithOwner
from app.schemas.access_request import AccessRequestResponse
from app.services.auth_service import get_current_user
from app.services.project_service import (
    create_project as create_project_service,
    get_projects as get_projects_service,
    get_project_by_id as get_project_by_id_service
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
@router.post("/", response_model=ProjectResponse)
def create_project(
    name: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = create_project_service(name, location, file, db, current_user)

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
    projects = db.query(Project).all()
    
    result = []
    for project in projects:
        result.append({
            "id": project.id,
            "name": project.name,
            "location": project.location,
            "file_path": project.file_path,
            "created_at": project.created_at,
            "user_id": project.user_id,
            "owner": project.user.full_name if project.user else "Unknown"
        })
    
    return result


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
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role

    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    project.name = update_data.name
    project.location = update_data.location

    db.commit()
    db.refresh(project)

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


# =========================
# DELETE PROJECT
# =========================
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role

    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    log = ActivityLog(
        user_id=current_user.id,
        action="delete_project",
        resource_type="project",
        resource_id=project_id,
        details=f"Deleted project: {project.name}"
    )

    db.add(log)
    db.commit()

    floorplans = db.query(Floorplan).filter(Floorplan.project_id == project_id).all()

    for floorplan in floorplans:
        if floorplan.file_path and os.path.exists(floorplan.file_path):
            try:
                os.remove(floorplan.file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {floorplan.file_path}: {e}")

    db.query(Floorplan).filter(Floorplan.project_id == project_id).delete()

    db.delete(project)
    db.commit()

    return {"message": f"Project {project_id} deleted successfully"}


# =========================
# REQUEST ACCESS
# =========================
@router.post("/{project_id}/request-access")
def request_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You are the owner")

    existing_request = db.query(ProjectAccess).filter(
        ProjectAccess.project_id == project_id,
        ProjectAccess.requester_id == current_user.id
    ).first()

    if existing_request:
        return {"status": existing_request.status.value if hasattr(existing_request.status, 'value') else existing_request.status}  # Already requested

    access_request = ProjectAccess(
        project_id=project_id,
        requester_id=current_user.id,
        status=RequestAccess.PENDING
    )
    db.add(access_request)
    db.commit()
    db.refresh(access_request)

    return {"status": "PENDING", "request_id": access_request.id}


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
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You are not the project owner")

        access_request = db.query(ProjectAccess).filter(
            ProjectAccess.id == request_id,
            ProjectAccess.project_id == project_id
        ).first()

        if not access_request:
            raise HTTPException(status_code=404, detail="Access request not found")

        access_request.status = RequestAccess.ACCEPTED
        access_request.responded_at = datetime.utcnow()

        db.commit()

        # Create collaborator record for approved user
        collaborator = ProjectCollaborator(
            project_id=project_id,
            user_id=access_request.requester_id,
            role="COLLABORATOR"
        )
        db.add(collaborator)
        db.commit()

        log = ActivityLog(
            user_id=current_user.id,
            action="approve_access",
            resource_type="project",
            resource_id=project_id,
            details=f"Approved access request {request_id} from user {access_request.requester_id}"
        )
        db.add(log)
        db.commit()

        return {"status": "ACCEPTED", "message": "Request approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error approving request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You are not the project owner")

        access_request = db.query(ProjectAccess).filter(
            ProjectAccess.id == request_id,
            ProjectAccess.project_id == project_id
        ).first()

        if not access_request:
            raise HTTPException(status_code=404, detail="Access request not found")

        access_request.status = RequestAccess.DECLINED
        access_request.responded_at = datetime.utcnow()

        db.commit()

        log = ActivityLog(
            user_id=current_user.id,
            action="decline_access",
            resource_type="project",
            resource_id=project_id,
            details=f"Declined access request {request_id} from user {access_request.requester_id}"
        )
        db.add(log)
        db.commit()

        return {"status": "DECLINED", "message": "Request declined successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error declining request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# =========================
# GET PROJECT ACCESS REQUESTS
# =========================
@router.get("/{project_id}/requests", response_model=list[AccessRequestResponse])
def get_project_requests(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only project owner can view requests
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    requests = db.query(ProjectAccess).filter(
        ProjectAccess.project_id == project_id
    ).all()

    result = []
    for req in requests:
        result.append({
            "id": req.id,
            "project_id": req.project_id,
            "requester_id": req.requester_id,
            "requester_name": req.requester.full_name,
            "status": req.status.value,
            "created_at": req.created_at,
            "responded_at": req.responded_at
        })

    return result


# =========================
# GET MY APPROVED PROJECTS (as Collaborator)
# =========================
@router.get("/collaborations/my-approved")
def get_my_approved_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all projects where user is a collaborator
    collaborations = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.user_id == current_user.id
    ).all()

    result = []
    for collab in collaborations:
        project = collab.project
        if project:
            result.append({
                "id": project.id,
                "name": project.name,
                "location": project.location,
                "file_path": project.file_path,
                "owner": project.user.full_name if project.user else "Unknown",
                "user_id": project.user_id,
                "access_status": "ACCEPTED",
                "role": collab.role
            })

    return result


# =========================
# GET MY COLLABORATORS & ACCESS REQUESTS
# =========================
@router.get("/access-requests/my-approvals")
def get_my_collaborators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all projects owned by current user
    my_projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    project_ids = [p.id for p in my_projects]

    if not project_ids:
        return []

    # Get all access requests for those projects
    requests = db.query(ProjectAccess).filter(
        ProjectAccess.project_id.in_(project_ids)
    ).all()

    result = []
    for req in requests:
        result.append({
            "id": req.id,
            "project_id": req.project_id,
            "project_name": req.project.name,
            "requester_id": req.requester_id,
            "requester_name": req.requester.full_name,
            "status": req.status.value,
            "created_at": req.created_at,
            "responded_at": req.responded_at
        })

    return result