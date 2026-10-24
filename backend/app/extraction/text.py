from pathlib import Path

import pdfplumber


def extract_text(pdf_path: Path) -> str:
    """Plain text of every page; digital measurement reports have a real text layer."""
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)
