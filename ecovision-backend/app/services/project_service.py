from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.user import User
from app.models.enum import UserRole
from app.services.file_storage import save_uploaded_file, upload_and_parse_floorplan
import os
from datetime import datetime

from app.models.floorplan import Floorplan
from app.models.activity_log import ActivityLog
from app.models.project_access import ProjectAccess
from app.models.project_collab import ProjectCollaborator
from app.models.enum import RequestAccess, FileType

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_project_service(
    name: str,
    location: str,
    north_arrow_direction: str,
    rooms_json: str,
    file: UploadFile,
    db: Session,
    current_user: User
) -> Project:

    # 1️⃣ Save file
    file_path = save_uploaded_file(file)

    # 2️⃣ Detect file type
    ext = os.path.splitext(file.filename)[1].lower()

    try:
        file_type = FileType(ext)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}"
        )

    # 3️⃣ Create project FIRST (safe approach)
    new_project = Project(
        name=name,
        location=location,
        file_path=file_path,
        user_id=current_user.id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # 4️⃣ Parse rooms + floorplan (non-blocking risk)
    try:
        upload_and_parse_floorplan(
            db=db,
            project_id=new_project.id,
            file_path=file_path,
            file_type=file_type,
            city=location,  # city = location ✔
            north_arrow_direction=north_arrow_direction,
            rooms_json=rooms_json
        )

    except Exception as e:
        # ❗ don't rollback project if parsing fails
        print(f"⚠ Parsing failed: {str(e)}")

        new_project.parsing_status = "failed"
        db.commit()

    return new_project


def get_projects(db: Session, current_user: User) -> list[Project]:
    """Get all projects for admin, or only user's projects for regular users."""
    # Normalize role value to handle both Enum and plain string
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    
    if str(role_val).upper() == UserRole.ADMIN.value:
        return db.query(Project).all()
    return db.query(Project).filter(Project.user_id == current_user.id).all()


def get_project_by_id(project_id: int, db: Session, current_user: User) -> Project:
    """Get a project by id. Admin can access any project, owner/collaborators can access their projects."""
    from app.models.project_collab import ProjectCollaborator
    
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    
    if str(role_val).upper() == UserRole.ADMIN.value:
        project = db.query(Project).filter(Project.id == project_id).first()
    else:
        # Check if user is owner
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()
        
        # If not owner, check if user is a collaborator
        if not project:
            collaborator = db.query(ProjectCollaborator).filter(
                ProjectCollaborator.project_id == project_id,
                ProjectCollaborator.user_id == current_user.id
            ).first()
            
            if collaborator:
                project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


def get_all_projects(db: Session, current_user: User):
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


def update_project_service(project_id: int, name: str, location: str, db: Session, current_user: User):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    project.name = name
    project.location = location

    db.commit()
    db.refresh(project)

    log = ActivityLog(
        user_id=current_user.id,
        action="update_project",
        resource_type="project",
        resource_id=project_id,
        details=f"Updated project: {name}"
    )
    db.add(log)
    db.commit()

    return project


def delete_project_service(project_id: int, db: Session, current_user: User):
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

    # remove floorplan files
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


def request_access_service(project_id: int, db: Session, current_user: User):
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
        return {"status": existing_request.status.value if hasattr(existing_request.status, 'value') else existing_request.status}

    access_request = ProjectAccess(
        project_id=project_id,
        requester_id=current_user.id,
        status=RequestAccess.PENDING
    )
    db.add(access_request)
    db.commit()
    db.refresh(access_request)

    return {"status": "PENDING", "request_id": access_request.id}


def approve_request_service(project_id: int, request_id: int, db: Session, current_user: User):
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


def decline_request_service(project_id: int, request_id: int, db: Session, current_user: User):
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


def get_project_requests_service(project_id: int, db: Session, current_user: User):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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


def get_my_approved_projects_service(db: Session, current_user: User):
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


def get_my_collaborators_service(db: Session, current_user: User):
    my_projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    project_ids = [p.id for p in my_projects]
    if not project_ids:
        return []

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
