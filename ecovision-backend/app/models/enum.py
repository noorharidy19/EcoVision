from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    ARCHITECT = "ARCHITECT"

    
class FileType(str, Enum):
    DWG = "DWG"
    DXF = "DXF"
