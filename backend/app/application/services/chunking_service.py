import re
from typing import List, Dict, Any


class ChunkingService:
    """
    Splits text into semantic, overlapping chunks with metadata for vector embeddings.
    """

    @staticmethod
    def chunk_resume(text: str, chunk_size: int = 500, overlap: int = 80) -> List[Dict[str, Any]]:
        # Identify section boundaries
        section_headers = [
            (r'(?i)\b(technical\s+skills|skills|technologies|tools)\b', "skills"),
            (r'(?i)\b(experience|work\s+history|employment)\b', "experience"),
            (r'(?i)\b(projects|personal\s+projects|academic\s+projects)\b', "projects"),
            (r'(?i)\b(education|academics|qualifications)\b', "education"),
            (r'(?i)\b(summary|objective|profile|about\s+me)\b', "summary"),
        ]

        lines = text.split("\n")
        chunks: List[Dict[str, Any]] = []
        current_section = "general"
        current_buffer = []
        current_length = 0
        chunk_idx = 0

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            # Check if this line is a section header
            for pattern, sec in section_headers:
                if re.search(pattern, trimmed) and len(trimmed) < 40:
                    current_section = sec
                    break

            current_buffer.append(trimmed)
            current_length += len(trimmed)

            if current_length >= chunk_size:
                chunk_text = " ".join(current_buffer)
                chunks.append({
                    "chunk_index": chunk_idx,
                    "section": current_section,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "token_estimate": len(chunk_text.split())
                })
                chunk_idx += 1
                
                # Keep overlap from the end of the buffer
                overlap_chars = 0
                overlap_buffer = []
                for b_line in reversed(current_buffer):
                    overlap_buffer.insert(0, b_line)
                    overlap_chars += len(b_line)
                    if overlap_chars >= overlap:
                        break
                current_buffer = overlap_buffer
                current_length = overlap_chars

        # Remaining buffer
        if current_buffer:
            chunk_text = " ".join(current_buffer)
            if len(chunk_text) > 30:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "section": current_section,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "token_estimate": len(chunk_text.split())
                })

        return chunks


chunking_service = ChunkingService()
