import io
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Extracts text from PDF, DOCX, TXT, and Markdown files.
    """

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        ext = filename.lower().split(".")[-1] if "." in filename else "txt"
        
        if ext == "pdf":
            return DocumentParser._parse_pdf(file_bytes)
        elif ext in ["docx", "doc"]:
            return DocumentParser._parse_docx(file_bytes)
        else:
            # Fallback to UTF-8 text decoding
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="ignore")

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            # Fallback byte string extraction
            clean_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', ' ', file_bytes.decode('latin-1', errors='ignore'))
            return clean_str

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            return file_bytes.decode("utf-8", errors="ignore")


document_parser = DocumentParser()
