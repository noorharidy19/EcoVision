from app.core.parsers.base import FileParser

class DXFParser(FileParser):

    def parse(self, file_path: str) -> dict:
        # simulate DXF parsing
        return {
            "type": "DXF",
           
        }
