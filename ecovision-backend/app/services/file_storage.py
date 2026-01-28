import os
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.floorplan import Floorplan
from app.models.enum import FileType
from app.core.parsers.factory import ParserFactory
UPLOAD_DIR = "uploaded_files"

os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path



def upload_and_parse_floorplan(
    db: Session,
    project_id,
    file_path: str,
    file_type: FileType
):
    # save floorplan
    floorplan = Floorplan(
        project_id=project_id,
        file_path=file_path,
        file_type=file_type
    )
    db.add(floorplan)
    db.commit()
    db.refresh(floorplan)

    # parse file
    parser = ParserFactory.get_parser(file_type)
    parsed_data = parser.parse(file_path)

    return floorplan, parsed_data

