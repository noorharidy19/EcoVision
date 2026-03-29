from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    ARCHITECT = "ARCHITECT"

    
class FileType(str, Enum):
    DWG = ".dwg"
    DXF = ".dxf"
    
class AnalysisType(str, Enum):
    MATERIAL='MATERIAL'
    THERMAL='THERMAL'
    VISUAL='VISUAL'

class RequestAccess(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"

class ProjectRole(str, Enum):
    OWNER = "OWNER"
    COLLABORATOR = "COLLABORATOR"