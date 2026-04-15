import os
import json
import logging
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.floorplan import Floorplan
from app.models.enum import FileType
from app.services.analysis.floorplan_processor import extract_features

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_file(file: UploadFile) -> str:
    """
    Save uploaded file to disk and return its path.
    """
    try:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # الأفضل استخدام read async-safe pattern (لكن حسب setup عندك sync ok)
        content = file.file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        logger.info(f"File saved successfully: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error saving uploaded file {file.filename}: {str(e)}")
        raise IOError(f"Failed to save uploaded file: {str(e)}") from e


def upload_and_parse_floorplan(
    db: Session,
    project_id: int,
    file_path: str,
    file_type: FileType,
    city: str,
    north_arrow_direction: str,
    rooms_json: str
):
    """
    Save parsed floorplan into DB after extracting features from uploaded file.
    """
    try:
        # validate JSON input
        try:
            rooms_list = json.loads(rooms_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid rooms_json format: {str(e)}")

        # extract features from file
        parsed_data = extract_features(
            dxf_path=file_path,
            city=city,
            north_arrow_direction=north_arrow_direction,
            form_rooms=rooms_list
        )

        if not parsed_data or "error" in parsed_data:
            raise ValueError(parsed_data.get("error", "Unknown parsing error"))

        # save to DB
        floorplan = Floorplan(
            project_id=project_id,
            file_path=file_path,
            file_type=file_type,
            json_data=parsed_data
        )

        db.add(floorplan)
        db.commit()
        db.refresh(floorplan)

        return floorplan, parsed_data

    except Exception as e:
        db.rollback()
        logger.error(f"Floorplan upload/parse failed: {str(e)}")
        raise Exception(f"Failed to save or parse floorplan: {str(e)}") from e