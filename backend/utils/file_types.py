"""Result and error types shared by the file extraction modules."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FileType(Enum):
    """Supported file types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    UNKNOWN = "unknown"


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""

    def __init__(self, message: str, error_code: str, details: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self):
        return {"error": self.message, "error_code": self.error_code, "details": self.details}


@dataclass
class ExtractionResult:
    """Result of text extraction from a file."""

    text: str
    file_type: FileType
    page_count: int
    encoding: Optional[str] = None
    warnings: Optional[list] = None
