from app.models.enum import FileType
from app.core.parsers.dwg_parser import DWGParser
from app.core.parsers.dxf_parser import DXFParser
from app.core.parsers.base import FileParser


class ParserFactory:

    @staticmethod
    def get_parser(file_type: FileType) -> FileParser:
        if file_type == FileType.DWG:
            return DWGParser()
        elif file_type == FileType.DXF:
            return DXFParser()
        else:
            raise ValueError("Unsupported file type")
