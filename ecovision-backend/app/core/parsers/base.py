from abc import ABC, abstractmethod
from typing import Dict, Any


class FileParser(ABC):
    """Abstract base class for file parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a file and return its data as a dictionary.
        
        Args:
            file_path: Path to the file to parse.
            
        Returns:
            Dictionary containing the parsed file data.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed.
        """
        pass
