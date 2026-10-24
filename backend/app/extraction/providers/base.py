import re
from decimal import Decimal, InvalidOperation

from ..types import ExtractedValue, ExtractionResult


def to_decimal(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace(",", "").strip())
    except InvalidOperation:
        return None


class ProviderParser:
    """A template parser for one provider's report layout.

    Subclasses set `key`, `name`, `fingerprints` (strings that identify the layout)
    and `patterns`: {field_key: regex with one capture group for the number}.
    Template parsers are trusted more than the generic parser or AI because the
    layout is known.
    """

    key = ""
    name = ""
    fingerprints: list[str] = []
    patterns: dict[str, str] = {}
    confidence = 0.98
    method = "template"

    def matches(self, text: str) -> bool:
        return all(f.lower() in text.lower() for f in self.fingerprints)

    def parse(self, text: str) -> ExtractionResult:
        result = ExtractionResult(provider=self.key, method=self.method)
        for field_key, pattern in self.patterns.items():
            self.capture(result, text, field_key, pattern)
        result.pitch_breakdown = self.parse_pitch_breakdown(text)
        self.post_process(result, text)
        return result

    def capture(self, result: ExtractionResult, text: str, field_key: str, pattern: str, scale: Decimal = Decimal(1)):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if not match:
            return
        value = to_decimal(match.group(1))
        if value is None:
            return
        result.values[field_key] = ExtractedValue(
            value=value * scale, evidence=match.group(0).strip()[:300],
            confidence=self.confidence, source=self.method,
        )

    def parse_pitch_breakdown(self, text: str) -> list[dict]:
        return []

    def post_process(self, result: ExtractionResult, text: str) -> None:
        pass
