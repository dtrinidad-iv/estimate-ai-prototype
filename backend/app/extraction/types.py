from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ExtractedValue:
    value: Decimal
    evidence: str  # the text the value was read from, shown to the reviewer
    confidence: float
    source: str  # template | generic | ai


@dataclass
class ExtractionResult:
    provider: str
    method: str
    values: dict[str, ExtractedValue] = field(default_factory=dict)
    pitch_breakdown: list[dict] = field(default_factory=list)  # [{"pitch": 6.0, "area_sqft": 2410.0}]
    notes: list[str] = field(default_factory=list)
