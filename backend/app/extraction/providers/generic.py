import re
from decimal import Decimal

from ..types import ExtractedValue
from .base import ProviderParser

NUM = r"([\d,]+(?:\.\d+)?)"


class GenericParser(ProviderParser):
    """Best-effort label matching for reports with no known template.

    Lower confidence: a match here is a strong hint, not a fact, so the reviewer
    is asked to confirm each value.
    """

    key = "unknown"
    name = "Unknown format"
    confidence = 0.7
    method = "generic"
    patterns = {
        "total_area_sqft": rf"(?:total\s+)?(?:roof\s+)?area[^\d\n]{{0,40}}{NUM}\s*(?:sq\.?\s*ft|sf|square feet)",
        "predominant_pitch": r"(?:predominant|primary|main)\s+(?:pitch|slope)[^\d\n]{0,20}(\d+(?:\.\d+)?)\s*[/:]\s*12",
        "facets": rf"(?:facets|planes)[^\d\n]{{0,10}}{NUM}",
        "ridges_ft": rf"ridges?(?:\s+line)?[^\d\n]{{0,25}}{NUM}\s*(?:lf|ft|')",
        "hips_ft": rf"hips?[^\d\n]{{0,25}}{NUM}\s*(?:lf|ft|')",
        "valleys_ft": rf"valleys?[^\d\n]{{0,40}}{NUM}\s*(?:lf|ft|')",
        "rakes_ft": rf"rakes?[^\d\n]{{0,25}}{NUM}\s*(?:lf|ft|')",
        "eaves_ft": rf"eaves?(?:\s+line)?[^\d\n]{{0,40}}{NUM}\s*(?:lf|ft|')",
        "step_flashing_ft": rf"(?:step|sidewall)\s+flash(?:ing)?[^\d\n]{{0,60}}{NUM}\s*(?:lf|ft|')",
        "wall_flashing_ft": rf"(?:headwall|apron|wall)\s+flash(?:ing)?[^\d\n]{{0,20}}{NUM}\s*(?:lf|ft|')",
        "suggested_waste_pct": r"waste[^\d\n]{0,20}(\d+(?:\.\d+)?)\s*%",
    }

    def matches(self, text):
        return True

    def post_process(self, result, text):
        # "No hips" / "hips: none" is an explicit zero, not a missing value.
        m = re.search(r"\bno hips\b|hips?\s*[:\-]?\s*none", text, re.IGNORECASE)
        if m and "hips_ft" not in result.values:
            result.values["hips_ft"] = ExtractedValue(Decimal(0), m.group(0), self.confidence, self.method)
