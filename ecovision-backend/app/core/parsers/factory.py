from app.models.enum import FileType
from app.core.parsers.dwg_parser import DWGParser
from app.core.parsers.dxf_parser import DXFParser
from app.core.parsers.base import FileParser
import logging

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for creating appropriate file parser instances.
    
    Uses the factory design pattern to instantiate the correct parser
    based on the file type.
    """
    
    # Mapping of file types to parser classes
    _parsers = {
        FileType.DXF: DXFParser,
        FileType.DWG: DWGParser,
    }

    @staticmethod
    def get_parser(file_type: FileType) -> FileParser:
        """Get a parser instance for the given file type.
        
        Args:
            file_type: The type of file to parse (from FileType enum).
            
        Returns:
            An instance of the appropriate FileParser subclass.
            
        Raises:
            ValueError: If the file type is not supported.
            TypeError: If file_type is not a FileType enum value.
        """
        if not isinstance(file_type, FileType):
            raise TypeError(f"Expected FileType enum, got {type(file_type).__name__}")
        
        parser_class = ParserFactory._parsers.get(file_type)
        
        if parser_class is None:
            supported_types = ", ".join([ft.value for ft in FileType])
            raise ValueError(
                f"Unsupported file type: {file_type.value}. "
                f"Supported types: {supported_types}"
            )
        
        logger.debug(f"Creating parser for file type: {file_type.value}")
        return parser_class()
    
    @staticmethod
    def is_supported(file_type: FileType) -> bool:
        """Check if a file type is supported.
        
        Args:
            file_type: The type of file to check.
            
        Returns:
            True if the file type is supported, False otherwise.
        """
        return file_type in ParserFactory._parsers
