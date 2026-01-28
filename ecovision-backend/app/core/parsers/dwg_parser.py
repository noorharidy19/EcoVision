from app.core.parsers.base import FileParser

class DWGParser(FileParser):

    def parse(self, file_path: str) -> dict:
        # simulate DWG parsing
        return {
            "type": "DWG",
            
        }
