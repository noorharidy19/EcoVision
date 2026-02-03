from app.core.parsers.base import FileParser
from app.services.analysis.floorplan_processor import dxf_to_json_clustered
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DXFParser(FileParser):
    """Parser for DXF (Drawing Exchange Format) files."""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a DXF file and return its data.
        
        Args:
            file_path: Path to the DXF file.
            
        Returns:
            Dictionary containing the parsed DXF data.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as DXF.
        """
        try:
            logger.info(f"Parsing DXF file: {file_path}")
            return dxf_to_json_clustered(file_path)
        except Exception as e:
            logger.error(f"Error parsing DXF file {file_path}: {str(e)}")
            raise ValueError(f"Failed to parse DXF file: {str(e)}") from e
