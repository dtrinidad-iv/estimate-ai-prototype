"""AI-assisted extraction for report layouts we don't have a template for.

The model only *reads* the document: it returns each value exactly as printed, with
its unit and a verbatim quote. Unit conversion and every calculation happen in code,
and any number that can't be found in the PDF's own text is flagged as unverified.
"""

import base64
import logging
import os
import re
from decimal import Decimal
from pathlib import Path

import anthropic
from pydantic import BaseModel

from ..fields import FIELDS
from .types import ExtractedValue

log = logging.getLogger(__name__)

MODEL = os.getenv("EXTRACTION_MODEL", "claude-opus-5-5")


class AIField(BaseModel):
    value: float | None  # number exactly as printed; null if the document doesn't state it
    unit: str | None  # as printed, e.g. "sq ft", "squares", "LF", "/12", "%"
    quote: str | None  # verbatim text the value came from


class AIPitchArea(BaseModel):
    pitch_rise: float
    area: float
    area_unit: str


class AIExtraction(BaseModel):
    provider_name: str | None
    total_area_sqft: AIField
    predominant_pitch: AIField
    facets: AIField
    ridges_ft: AIField
    hips_ft: AIField
    valleys_ft: AIField
    rakes_ft: AIField
    eaves_ft: AIField
    step_flashing_ft: AIField
    wall_flashing_ft: AIField
    perimeter_ft: AIField
    reported_squares: AIField
    suggested_waste_pct: AIField
    pitch_breakdown: list[AIPitchArea]


PROMPT = """You are reading a roof measurement report for a roofing estimator.

For each field, copy the value exactly as the document states it, with its unit and a short verbatim quote.
Rules:
- Do not calculate, convert, sum, round or estimate anything. If a value is only derivable by math, return null.
- If the document explicitly says a feature is absent (e.g. "no hips"), return 0 with that quote.
- predominant_pitch: return the rise only (7 for "7/12" or "7:12").
- wall_flashing_ft covers headwall / apron / chimney flashing; step_flashing_ft covers step / sidewall flashing.
- If something is not stated, return null for value, unit and quote.

Field meanings:
""" + "\n".join(f"- {f.key}: {f.label} ({f.unit})" for f in FIELDS)


def ai_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")) and os.getenv("AI_EXTRACTION", "on") != "off"


def normalize(key: str, field: AIField) -> Decimal | None:
    """Unit conversion is deterministic code, not the model's job."""
    if field.value is None:
        return None
    value = Decimal(str(field.value))
    unit = (field.unit or "").lower()
    if key == "total_area_sqft" and "square" in unit and "f" not in unit.replace("square", ""):
        value *= 100  # reported in roofing squares
    return value


def appears_in_text(value: Decimal, text: str) -> bool:
    plain = re.sub(r"(?<=\d),(?=\d{3})", "", text)
    numbers = {Decimal(n) for n in re.findall(r"\d+(?:\.\d+)?", plain)}
    return value in numbers or value / 100 in numbers  # squares-vs-sq-ft conversions


def ai_extract(pdf_path: Path, text: str, wanted: list[str]) -> tuple[dict[str, ExtractedValue], list[dict], list[str]]:
    """Returns (values for the wanted keys, pitch breakdown, notes)."""
    notes: list[str] = []
    if not ai_available():
        notes.append("AI extraction skipped: no ANTHROPIC_API_KEY configured. Enter missing values manually.")
        return {}, [], notes

    client = anthropic.Anthropic()
    pdf_b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode()
    try:
        response = client.beta.messages.parse(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium"},
            output_format=AIExtraction,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )
    except anthropic.AuthenticationError:
        notes.append("AI extraction failed: the API key was rejected.")
        return {}, [], notes
    except anthropic.RateLimitError:
        notes.append("AI extraction is rate limited right now; try again in a minute or enter values manually.")
        return {}, [], notes
    except anthropic.APIStatusError as e:
        log.exception("AI extraction error")
        notes.append(f"AI extraction failed (HTTP {e.status_code}).")
        return {}, [], notes
    except anthropic.APIConnectionError:
        notes.append("AI extraction failed: could not reach the API.")
        return {}, [], notes

    if response.stop_reason == "refusal" or response.parsed_output is None:
        notes.append("AI extraction returned no usable result; enter values manually.")
        return {}, [], notes

    parsed: AIExtraction = response.parsed_output
    values: dict[str, ExtractedValue] = {}
    for key in wanted:
        field: AIField = getattr(parsed, key)
        value = normalize(key, field)
        if value is None:
            continue
        found = appears_in_text(value, text)
        values[key] = ExtractedValue(
            value=value,
            evidence=(field.quote or "")[:280] + ("" if found else "  [number not found in PDF text]"),
            confidence=0.8 if found else 0.4,
            source="ai",
        )

    breakdown = []
    for row in parsed.pitch_breakdown:
        area = Decimal(str(row.area)) * (100 if "square" in row.area_unit.lower() and "f" not in row.area_unit.lower() else 1)
        breakdown.append({"pitch": row.pitch_rise, "area_sqft": float(area)})

    notes.append(f"AI read {len(values)} value(s) the parser couldn't. Each is marked for review.")
    return values, breakdown, notes
