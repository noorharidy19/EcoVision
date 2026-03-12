import ezdxf
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DXFNormalizer:
    """Normalizes DXF furniture and room data before clustering."""
    
    # Furniture name mapping dictionary
    FURNITURE_MAPPING = {
        # --- Seating & Living ---
        "cay03_mb": "chairmodern",
        "sofa-46": "sofasmall",
        "sofa-50": "sofalarge",
        "s2": "sofaloveseat",
        "st": "sidetable",
        "arm-ch": "armchair",

        # --- Kitchen & Dining ---
        "12pplt12": "diningplate",
        "ps sin 12": "sinkkitchen",
        "k-sink": "sinkkitchen",
        "ref-1": "refrigerator",
        "ovn-01": "ovenrange",
        "dsadas": "diningtableset",

        # --- Bathroom & Plumbing ---
        "toilet": "toilet",
        "lav-01": "sinkbathroom",
        "shw-sq": "showerstall",
        "btub": "bathtub",
        "f": "fixtureplumbing",

        # --- Structural & Architectural ---
        "s-cols": "structuralcolumn",
        "a-furn": "furniturelayergeneric",
        "dr-s": "doorsingle",
        "dr-d": "doordouble",
        "win-std": "windowstandard",

        # --- Decorative & Utility ---
        "a$c2cc23d6e": "decoritem",
        "fsfsf": "miscellaneous_item",
        "p-pot": "indoor_plant",
        "tv-unit": "media_console"
    }

    @staticmethod
    def normalize_furniture_name(raw_name: str) -> str:
        """Normalize raw DXF furniture name to standardized type.
        
        Args:
            raw_name: Raw furniture name from DXF file
            
        Returns:
            Normalized furniture type name
        """
        raw_name = (raw_name or "").lower().strip()
        
        # 1. Check for exact match in mapping
        if raw_name in DXFNormalizer.FURNITURE_MAPPING:
            return DXFNormalizer.FURNITURE_MAPPING[raw_name]
        
        # 2. Check for partial matches (minimal fallback)
        if "toilet" in raw_name:
            return "toilet"
        if "bed" in raw_name:
            return "bed"
        if "sink" in raw_name:
            return "sink"
        if "table" in raw_name:
            return "table"
        
        # 3. Fallback to original
        return raw_name

    @staticmethod
    def normalize_for_semantics(furniture_type: str) -> str:
        """Convert normalized type to semantic category for room detection.
        
        Args:
            furniture_type: Normalized furniture type
            
        Returns:
            Semantic category (e.g., 'sink', 'toilet', 'sofa')
        """
        t = (furniture_type or "").lower().strip()
        
        if "sink" in t:
            return "sink"
        if "refrigerator" in t or "fridge" in t or "ref" in t:
            return "refrigerator"
        if "oven" in t or "stove" in t or "range" in t:
            return "stove"
        if "toilet" in t or "wc" in t:
            return "toilet"
        if "sofa" in t:
            return "sofa"
        if "chair" in t:
            return "chair"
        if "plate" in t or "dining" in t:
            return "plate"
        if "bed" in t:
            return "bed"
        if "shower" in t:
            return "shower"
        if "bathtub" in t:
            return "bathtub"
        
        return t

    @staticmethod
    def extract_and_normalize_furniture(dxf_path: str) -> List[Dict[str, Any]]:
        """Extract and normalize all furniture from DXF file.
        
        Args:
            dxf_path: Path to DXF file
            
        Returns:
            List of normalized furniture dictionaries
        """
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            
            furniture_data = []
            
            for f_ent in msp.query("INSERT"):
                try:
                    x = float(f_ent.dxf.insert.x)
                    y = float(f_ent.dxf.insert.y)
                except (ValueError, AttributeError):
                    continue
                
                raw_name = getattr(f_ent.dxf, "name", "") or ""
                
                # Skip internal DXF blocks (those starting with *)
                if raw_name.startswith("*"):
                    logger.debug(f"Skipping internal block: {raw_name}")
                    continue
                
                # Apply normalization
                normalized_type = DXFNormalizer.normalize_furniture_name(raw_name)
                semantic_type = DXFNormalizer.normalize_for_semantics(normalized_type)
                
                furniture_data.append({
                    "id": f"furn_{f_ent.dxf.handle}",  # DXF handle for file operations
                    "dxf_handle": f_ent.dxf.handle,
                    "raw_name": raw_name,
                    "type": normalized_type,
                    "semantic_type": semantic_type,
                    "centroid": [x, y],
                    "enumerated_id": None  # Will be set by enumerate_duplicates
                })
            
            logger.info(f"Extracted and normalized {len(furniture_data)} furniture items from {dxf_path}")
            return furniture_data
            
        except Exception as e:
            logger.error(f"Error normalizing DXF file {dxf_path}: {str(e)}")
            raise

    @staticmethod
    def enumerate_duplicates(furniture_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enumerate furniture items with IDs. Single items get type name only.
        Multiple items of same type get enumerated IDs (e.g., chairmodern1, chairmodern2).
        
        Args:
            furniture_list: List of furniture dictionaries
            
        Returns:
            Furniture list with IDs set appropriately
        """
        # First pass: count each type
        type_counts = {}
        for item in furniture_list:
            furn_type = item["type"]
            type_counts[furn_type] = type_counts.get(furn_type, 0) + 1
        
        # Second pass: assign IDs
        type_counters = {}
        for item in furniture_list:
            furn_type = item["type"]
            
            if type_counters.get(furn_type) is None:
                type_counters[furn_type] = 0
            
            type_counters[furn_type] += 1
            count = type_counters[furn_type]
            
            # Only add number if there are multiple items of this type
            if type_counts[furn_type] > 1:
                item["enumerated_id"] = f"{furn_type}{count}"
            else:
                item["enumerated_id"] = furn_type  # No number for single items
            
            item["enum_count"] = count
        
        logger.info(f"Enumerated {len(furniture_list)} furniture items")
        
        # Log some examples
        examples = {}
        for item in furniture_list[:15]:
            ftype = item["type"]
            if ftype not in examples:
                examples[ftype] = item["enumerated_id"]
        
        logger.info(f"Enumeration examples: {examples}")
        return furniture_list
