import io
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Extracts text from PDF, DOCX, TXT, and Markdown files.

    Always returns human-readable text. Never returns raw PDF operators,
    binary dumps, or embedding vectors — those leak into claim verification
    questions and job-fit evidence if passed through.
    """

    # Substrings that only appear in raw PDF binary / operator dumps.
    _PDF_ARTIFACT_MARKERS = (
        "%pdf", "endobj", "xref", "trailer", "/type", "/font",
        "/pages", "/page ", "obj <<", ">>", "/filter", "/length",
    )

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        ext = filename.lower().split(".")[-1] if "." in filename else "txt"

        if ext == "pdf":
            raw = DocumentParser._parse_pdf(file_bytes)
        elif ext in ["docx", "doc"]:
            raw = DocumentParser._parse_docx(file_bytes)
        else:
            # Fallback to UTF-8 text decoding
            try:
                raw = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raw = file_bytes.decode("utf-8", errors="ignore")
        return DocumentParser.clean_extracted_text(raw)

    @staticmethod
    def clean_extracted_text(text: str) -> str:
        """Normalize extracted text to a human-readable form."""
        if not text:
            return ""
        # Drop non-printable / control characters (keep \n and \t).
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
        # Collapse whitespace but preserve paragraph breaks.
        lines = []
        for line in text.split("\n"):
            stripped = re.sub(r"[ \t\xa0]+", " ", line).strip()
            if not stripped:
                continue
            # Skip lines that are clearly binary / PDF operator dumps.
            if DocumentParser._looks_like_binary_dump(stripped):
                continue
            lines.append(stripped)
        cleaned = "\n".join(lines)
        # Collapse 3+ consecutive newlines.
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def _looks_like_binary_dump(line: str) -> bool:
        lowered = line.lower()
        # Raw PDF header / cross-reference table.
        if any(m in lowered for m in DocumentParser._PDF_ARTIFACT_MARKERS) and len(line.split()) <= 12:
            # Allow legitimate resume lines that merely mention e.g. "trailer"
            # only when they are full sentences.
            alpha_ratio = sum(c.isalpha() for c in line) / max(len(line), 1)
            if alpha_ratio < 0.5:
                return True
            if lowered.startswith("%pdf") or "endobj" in lowered or "xref" in lowered:
                return True
        # Long base64 / embed blobs with no spaces (vectors, images, fonts).
        tokens = line.split()
        if tokens and len(max(tokens, key=len)) > 80:
            return True
        # Very low alpha content (mostly symbols / numbers) and short.
        if len(line) < 120:
            alpha = sum(c.isalpha() or c.isspace() for c in line) / max(len(line), 1)
            if alpha < 0.35:
                return True
        return False

    @staticmethod
    def is_readable_text(text: str, min_chars: int = 20) -> bool:
        """True when text is worth indexing / quoting as a resume claim."""
        if not text or len(text.strip()) < min_chars:
            return False
        sample = text.strip()[:2000]
        alpha = sum(c.isalpha() or c.isspace() for c in sample) / max(len(sample), 1)
        return alpha >= 0.45

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
            joined = "\n\n".join(text_parts)
            if DocumentParser.is_readable_text(joined):
                return joined
            logger.warning("PDF parsed but produced no readable text; rejecting binary dump.")
            return ""
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            # Do NOT return raw byte decoding here — that leaks "%PDF ...
            # endobj xref ..." binary into claims, chunks, and interview
            # questions. Return empty so callers fall back to a clean error.
            return ""

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            try:
                fallback = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                return ""
            # Only accept the fallback if it actually looks like text.
            if DocumentParser.is_readable_text(fallback):
                return fallback
            return ""


document_parser = DocumentParser()
