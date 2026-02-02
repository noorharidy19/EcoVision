import os
from uuid import uuid4
from typing import Tuple, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.floorplan import Floorplan
from app.models.enum import FileType
from app.core.parsers.factory import ParserFactory
from app.services.analysis.floorplan_processor import dxf_to_json_clustered
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploaded_files"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_file(file: UploadFile) -> str:
    """Save an uploaded file to disk.
    
    Args:
        file: The uploaded file object.
        
    Returns:
        The file path where the file was saved.
        
    Raises:
        IOError: If the file cannot be saved.
    """
    try:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        logger.info(f"File saved successfully: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving uploaded file {file.filename}: {str(e)}")
        raise IOError(f"Failed to save uploaded file: {str(e)}") from e


def upload_and_parse_floorplan(
    db: Session,
    project_id: str,
    file_path: str,
    file_type: FileType,
) -> Tuple[Floorplan, Dict[str, Any]]:
    """Upload and parse a floorplan file.
    
    Args:
        db: Database session.
        project_id: The ID of the project this floorplan belongs to.
        file_path: Path to the floorplan file.
        file_type: The type of the floorplan file (from FileType enum).
        
    Returns:
        A tuple of (Floorplan model instance, parsed file data dictionary).
        
    Raises:
        ValueError: If the file type is not supported or parsing fails.
        FileNotFoundError: If the file does not exist.
    """
    try:
        # Validate file type is supported
        if not ParserFactory.is_supported(file_type):
            raise ValueError(f"Unsupported file type: {file_type.value}")
        
        # Get the appropriate parser and parse the file
        logger.info(f"Parsing floorplan file: {file_path} (type: {file_type.value})")
        parser = ParserFactory.get_parser(file_type)
        parsed_data = parser.parse(file_path)
        
        # Create floorplan record in database
        floorplan = Floorplan(
            project_id=project_id,
            file_path=file_path,
            file_type=file_type,
            json_data=parsed_data,
        )

        db.add(floorplan)
        db.commit()
        db.refresh(floorplan)
        
        logger.info(f"Floorplan parsed and saved successfully: {floorplan.id}")
        return floorplan, parsed_data
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing floorplan {file_path}: {str(e)}")
        raise

