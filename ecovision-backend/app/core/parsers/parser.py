import sys
from pathlib import Path
from app.core.parsers.base import FileParser
from app.core.parsers.dxf_normalizer import DXFNormalizer
from app.services.analysis.floorplan_processor import dxf_to_json_clustered_from_normalized
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Import extract_features from edit_recommendation package
_edit_rec_path = Path(__file__).parent.parent.parent.parent / "edit_recommendation"
if str(_edit_rec_path) not in sys.path:
    sys.path.insert(0, str(_edit_rec_path))
try:
    from dxf_parser import extract_features
    HAS_EXTRACT_FEATURES = True
except Exception as e:
    logger.warning(f"Could not import extract_features: {e}")
    HAS_EXTRACT_FEATURES = False


class DXFParser(FileParser):
    """Parser for DXF (Drawing Exchange Format) files."""
    
    def parse(
        self, 
        file_path: str,
        city: Optional[str] = None,
        north_arrow_direction: Optional[str] = None,
        rooms: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Parse a DXF file and return its data.
        
        When city, north_arrow_direction, and rooms are provided, uses advanced
        feature extraction with window analysis and solar ratings.
        Otherwise, uses simple furniture clustering.
        
        Args:
            file_path: Path to the DXF file.
            city: City location for climate data (optional).
            north_arrow_direction: Building orientation (N, NE, E, etc.) (optional).
            rooms: List of room data [{"name": str, "area": float}, ...] (optional).
            
        Returns:
            Dictionary containing the parsed DXF data with rooms and analysis.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as DXF.
        """
        try:
            logger.info(f"Parsing DXF file: {file_path}")
            logger.info(f"HAS_EXTRACT_FEATURES: {HAS_EXTRACT_FEATURES}, city: {city}, north_arrow_direction: {north_arrow_direction}, rooms: {len(rooms) if rooms else 0}")
            
            # Use extract_features if available and all parameters provided
            if (HAS_EXTRACT_FEATURES and city and north_arrow_direction and rooms 
                and len(rooms) > 0):
                logger.info("🎯 Using advanced feature extraction with window analysis")
                print(f"🎯 Using advanced feature extraction with window analysis")
                result = extract_features(
                    file_path,
                    city,
                    north_arrow_direction,
                    rooms
                )
                logger.info(f"✅ Extract features result: {type(result)} with {len(result.keys()) if isinstance(result, dict) else 'N/A'} keys")
                print(f"✅ Extract features result: {type(result)} with {len(result.keys()) if isinstance(result, dict) else 'N/A'} keys")
                return result
            else:
                msg = f"Conditions not met - HAS_EXTRACT_FEATURES: {HAS_EXTRACT_FEATURES}, city: {bool(city)}, north_arrow_direction: {bool(north_arrow_direction)}, rooms: {bool(rooms and len(rooms) > 0)}"
                logger.info(f"⚠️  {msg}")
                print(f"⚠️  {msg}")
            
            # Fall back to simple clustering approach
            logger.info("Using furniture clustering approach")
            print(f"Using furniture clustering approach")
            
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
