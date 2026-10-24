"""Template parser -> generic parser -> AI (only for what's still missing) -> human review."""

from pathlib import Path

from ..fields import FIELDS
from .ai import ai_extract
from .providers import GENERIC, detect
from .text import extract_text
from .types import ExtractionResult


def run_extraction(pdf_path: Path, use_ai: bool = True) -> tuple[ExtractionResult, str]:
    text = extract_text(pdf_path)
    if not text.strip():
        result = ExtractionResult(provider="unknown", method="manual",
                                  notes=["No text layer found (scanned PDF?). Enter values manually or enable AI extraction."])
        parser = None
    else:
        parser = detect(text)
        result = (parser or GENERIC).parse(text)
        if parser:
            result.notes.insert(0, f"Detected provider: {parser.name}. Parsed with its template.")
        else:
            result.notes.insert(0, "Unrecognized report format. Used generic label matching; please review every value.")

    missing = [f.key for f in FIELDS if f.key not in result.values]
    # Known templates are trusted as-is; AI only helps with layouts we can't parse reliably.
    if use_ai and missing and parser is None:
        values, breakdown, notes = ai_extract(pdf_path, text, missing)
        result.values.update(values)
        if not result.pitch_breakdown:
            result.pitch_breakdown = breakdown
        result.notes.extend(notes)
        if values:
            result.method = "generic+ai" if result.method == "generic" else "ai"
    return result, text
