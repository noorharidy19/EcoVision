from enum import Enum
from sqlalchemy import Column, String
from database.base import Base

class FileType(str, Enum):
    DWG = "DWG"
    DXF = "DXF"