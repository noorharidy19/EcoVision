from app.core.parsers.dxf_normalizer import DXFNormalizer
from app.services.analysis.floorplan_processor import dxf_to_json_clustered_from_normalized
import ezdxf
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def analyze_dxf_file(dxf_path: str) -> Dict[str, Any]:
    """Analyze a DXF file with normalization and generate detailed explanation.
    
    Args:
        dxf_path: Path to the DXF file
        
    Returns:
        Dictionary containing analysis results with explanation
    """
    try:
        logger.info(f"🔍 Starting DXF analysis for: {dxf_path}")
        
        # Step 1: Extract and normalize furniture from DXF
        logger.info("📋 Extracting furniture from DXF...")
        normalized_furniture = DXFNormalizer.extract_and_normalize_furniture(dxf_path)
        logger.info(f"✅ Normalized {len(normalized_furniture)} furniture items")
        
        if not normalized_furniture:
            logger.warning("⚠️ No furniture items found in DXF file")
            return {
                "success": False,
                "rooms": [],
                "furniture": [],
                "explanation": "No furniture items found in the DXF file",
                "summary": {
                    "total_rooms": 0,
                    "total_furniture": 0,
                    "floor_area": 0,
                    "room_types": []
                }
            }
        
        # Step 2: Print normalized items for debugging
        logger.info("📝 Normalized furniture types:")
        for item in normalized_furniture[:5]:  # Show first 5
            logger.info(f"  - {item['raw_name']} → {item['type']} (semantic: {item['semantic_type']})")
        
        # Step 3: Enumerate duplicates (toilet 1, toilet 2, etc.)
        logger.info("🔢 Enumerating duplicate items...")
        enumerated_furniture = DXFNormalizer.enumerate_duplicates(normalized_furniture)
        logger.info(f"✅ Enumerated items")
        
        # Step 4: Cluster into rooms using normalized data
        logger.info("🏠 Clustering furniture into rooms...")
        clustered_data = dxf_to_json_clustered_from_normalized(dxf_path, enumerated_furniture)
        logger.info(f"✅ Found {len(clustered_data.get('rooms', []))} rooms")
        
        # Step 5: Generate detailed explanation
        logger.info("📄 Generating detailed explanation...")
        explanation = generate_detailed_analysis_explanation(clustered_data)
        
        # Step 6: Generate summary
        logger.info("📊 Generating summary...")
        summary = generate_summary(clustered_data)
        
        logger.info("✅ DXF analysis completed successfully")
        
        return {
            "success": True,
            "rooms": clustered_data.get("rooms", []),
            "furniture": clustered_data.get("furniture", []),
            "explanation": explanation,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"❌ Error analyzing DXF file: {str(e)}", exc_info=True)
        raise


def generate_summary(clustered_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics from clustered data.
    
    Args:
        clustered_data: Dictionary with rooms and furniture
        
    Returns:
        Summary dictionary with key metrics
    """
    rooms = clustered_data.get("rooms", [])
    furniture = clustered_data.get("furniture", [])
    
    # Get unique room types
    room_types = list(set([room.get("type", "unknown") for room in rooms]))
    
    # Calculate total floor area
    total_area = sum([room.get("area", 0) for room in rooms])
    
    return {
        "total_rooms": len(rooms),
        "total_furniture": len(furniture),
        "floor_area": round(total_area, 2),
        "room_types": room_types
    }


def generate_detailed_analysis_explanation(clustered_data: Dict[str, Any]) -> str:
    """Generate a detailed markdown explanation of the floorplan analysis.
    
    Args:
        clustered_data: Dictionary with rooms and furniture data
        
    Returns:
        Markdown-formatted explanation string
    """
    rooms = clustered_data.get("rooms", [])
    furniture = clustered_data.get("furniture", [])
    
    # Calculate metrics
    total_area = sum([room.get("area", 0) for room in rooms])
    avg_room_size = total_area / len(rooms) if rooms else 0
    
    # Sort rooms by area (largest first)
    rooms_by_area = sorted(rooms, key=lambda r: r.get("area", 0), reverse=True)
    
    # Count furniture by type
    furniture_by_type = {}
    for item in furniture:
        ftype = item.get("type", "unknown")
        if ftype not in furniture_by_type:
            furniture_by_type[ftype] = []
        furniture_by_type[ftype].append(item)
    
    # Build markdown explanation
    md_lines = []
    
    # Header
    md_lines.append("# 📐 Floorplan Analysis Report\n")
    
    # Overview Section
    md_lines.append("## 📊 Overview\n")
    md_lines.append(f"- **Total Rooms:** {len(rooms)}")
    md_lines.append(f"- **Total Furniture Items:** {len(furniture)}")
    md_lines.append(f"- **Total Floor Area:** {round(total_area, 2)} sq units")
    md_lines.append(f"- **Average Room Size:** {round(avg_room_size, 2)} sq units\n")
    
    # Rooms Analysis Section
    md_lines.append("## 🏠 Rooms Analysis\n")
    
    # Group rooms by type
    rooms_by_type = {}
    for room in rooms:
        rtype = room.get("type", "unknown").replace("_", " ").title()
        if rtype not in rooms_by_type:
            rooms_by_type[rtype] = []
        rooms_by_type[rtype].append(room)
    
    for room_type in sorted(rooms_by_type.keys()):
        rooms_of_type = rooms_by_type[room_type]
        md_lines.append(f"### {room_type} ({len(rooms_of_type)})\n")
        
        for i, room in enumerate(rooms_of_type, 1):
            md_lines.append(f"**{room_type} {i}:**")
            md_lines.append(f"- Area: {room.get('area', 0)} sq units")
            md_lines.append(f"- Dimensions: {room.get('width', 0)} × {room.get('height', 0)} units")
            md_lines.append(f"- Perimeter: {room.get('perimeter', 0)} units")
            md_lines.append(f"- Location: ({room.get('centroid', [0, 0])[0]}, {room.get('centroid', [0, 0])[1]})\n")
    
    # Furniture Inventory Section
    md_lines.append("## 🪑 Furniture Inventory\n")
    
    md_lines.append("### Summary by Type\n")
    for ftype in sorted(furniture_by_type.keys()):
        count = len(furniture_by_type[ftype])
        md_lines.append(f"- **{ftype.replace('_', ' ').title()}:** {count}")
    md_lines.append("")
    
    # Detailed furniture listing
    md_lines.append("### Detailed Listing\n")
    for ftype in sorted(furniture_by_type.keys()):
        items = furniture_by_type[ftype]
        md_lines.append(f"#### {ftype.replace('_', ' ').title()}\n")
        
        for item in items:
            enum_id = item.get("enumerated_id", "unknown")
            centroid = item.get("centroid", [0, 0])
            semantic = item.get("semantic_type", "unknown")
            room_id = item.get("room_id", "unassigned")
            
            md_lines.append(f"- **{enum_id}** (Semantic: {semantic})")
            md_lines.append(f"  - Position: ({centroid[0]}, {centroid[1]})")
            md_lines.append(f"  - Room: {room_id}\n")
    
    # Space Utilization Section
    md_lines.append("## 📈 Space Utilization Analysis\n")
    
    for room in sorted(rooms, key=lambda r: r.get("area", 0), reverse=True):
        room_type = room.get("type", "unknown")
        room_id = room.get("id", "unknown")
        room_area = room.get("area", 0)
        
        # Count furniture in this room
        items_in_room = [f for f in furniture if f.get("room_id") == room_id]
        occupancy = (len(items_in_room) / len(furniture) * 100) if furniture else 0
        
        md_lines.append(f"**{room_type.replace('_', ' ').title()}:**")
        md_lines.append(f"- Area: {room_area} sq units")
        md_lines.append(f"- Items: {len(items_in_room)}")
        md_lines.append(f"- Occupancy: {round(occupancy, 1)}%\n")
    
    # Key Metrics Section
    md_lines.append("## 🔑 Key Metrics\n")
    
    if rooms_by_area:
        largest = rooms_by_area[0]
        smallest = rooms_by_area[-1]
        md_lines.append(f"- **Largest Room:** {largest.get('type', 'unknown').replace('_', ' ').title()} ({largest.get('area', 0)} sq units)")
        md_lines.append(f"- **Smallest Room:** {smallest.get('type', 'unknown').replace('_', ' ').title()} ({smallest.get('area', 0)} sq units)")
    
    if furniture_by_type:
        most_common_type = max(furniture_by_type.keys(), key=lambda k: len(furniture_by_type[k]))
        most_common_count = len(furniture_by_type[most_common_type])
        md_lines.append(f"- **Most Common Furniture:** {most_common_type.replace('_', ' ').title()} ({most_common_count} items)")
    
    return "\n".join(md_lines)
