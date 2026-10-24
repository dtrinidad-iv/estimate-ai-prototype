import re
from decimal import Decimal

from ..types import ExtractedValue
from .base import ProviderParser, to_decimal


class AeroRoofParser(ProviderParser):
    """AeroRoof reports areas in squares and slopes as 'x:12'; we normalize to sq ft and x/12."""

    key = "aeroroof"
    name = "AeroRoof Analytics"
    fingerprints = ["AEROROOF ANALYTICS", "Roof Geometry Summary"]
    patterns = {
        "eaves_ft": r"^Eave Length\s+([\d,.]+)\s*LF",
        "rakes_ft": r"^Rake Length\s+([\d,.]+)\s*LF",
        "ridges_ft": r"^Ridge Length\s+([\d,.]+)\s*LF",
        "hips_ft": r"^Hip Length\s+([\d,.]+)\s*LF",
        "valleys_ft": r"^Valley Length\s+([\d,.]+)\s*LF",
        "step_flashing_ft": r"^Step Flash\s+([\d,.]+)\s*LF",
        "wall_flashing_ft": r"^Headwall\s+([\d,.]+)\s*LF",
        "perimeter_ft": r"^Drip Edge \(Eave \+ Rake\)\s+([\d,.]+)\s*LF",
        "suggested_waste_pct": r"^Recommended Waste:\s*([\d.]+)\s*%",
    }

    def post_process(self, result, text):
        # Summary is a one-row table: "ROOF SQUARES AREA PRIMARY SLOPE PLANES" then the values line.
        m = re.search(r"ROOF SQUARES\s+AREA\s+PRIMARY SLOPE\s+PLANES\s*\n\s*([\d.,]+)\s+([\d,]+)\s*SF\s+(\d+(?:\.\d+)?):12\s+(\d+)", text)
        if not m:
            result.notes.append("AeroRoof summary table not found; area/pitch need manual entry.")
            return
        evidence = m.group(0).replace("\n", " | ")
        for key, raw in [("reported_squares", m.group(1)), ("total_area_sqft", m.group(2)),
                         ("predominant_pitch", m.group(3)), ("facets", m.group(4))]:
            result.values[key] = ExtractedValue(to_decimal(raw), evidence, self.confidence, self.method)

    def parse_pitch_breakdown(self, text):
        section = text.split("Slope Breakdown", 1)[-1] if "Slope Breakdown" in text else ""
        rows = re.findall(r"^(\d+(?:\.\d+)?):12\s+([\d.]+)\s*$", section, re.MULTILINE)
        # squares -> sq ft
        return [{"pitch": float(p), "area_sqft": float(to_decimal(sq) * Decimal(100))} for p, sq in rows]
