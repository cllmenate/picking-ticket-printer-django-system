import os

from .file_processors import (
    DocxProcessor,
    ExcelProcessor,
    FileProcessor,
    PDFProcessor,
    ProcessingError,
)


class ProcessorFactory:
    @staticmethod
    def get_processor(file_path: str) -> FileProcessor:
        _, ext = os.path.splitext(file_path.lower())
        if ext in [".xls", ".xlsx"]:
            return ExcelProcessor()
        elif ext == ".pdf":
            return PDFProcessor()
        elif ext in [".doc", ".docx"]:
            return DocxProcessor()
        else:
            raise ProcessingError(f"Unsupported file format: {ext}")
