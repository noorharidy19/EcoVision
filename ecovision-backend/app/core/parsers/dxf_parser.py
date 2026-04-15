from app.core.parsers.base import FileParser
from app.core.parsers.dxf_normalizer import DXFNormalizer
from app.services.analysis.floorplan_processor import extract_features
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DXFParser(FileParser):
    """Parser for DXF (Drawing Exchange Format) files."""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a DXF file with normalization and return its data.
        
        Args:
            file_path: Path to the DXF file.
            
        Returns:
            Dictionary containing the parsed and normalized DXF data.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as DXF.
        """
        try:
            logger.info(f"Parsing DXF file: {file_path}")
            
            # Step 1: Extract and normalize furniture from DXF
            normalized_furniture = DXFNormalizer.extract_and_normalize_furniture(file_path)
            logger.info(f"Normalized {len(normalized_furniture)} furniture items")
            
            # Step 2: Enumerate duplicates
            enumerated_furniture = DXFNormalizer.enumerate_duplicates(normalized_furniture)
            logger.info("Enumerated duplicate items")
            
            # Step 3: Cluster into rooms using normalized data
            result = dxf_to_json_clustered_from_normalized(file_path, enumerated_furniture)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing DXF file {file_path}: {str(e)}")
            raise ValueError(f"Failed to parse DXF file: {str(e)}") from e
