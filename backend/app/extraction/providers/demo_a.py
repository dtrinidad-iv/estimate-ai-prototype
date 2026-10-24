import re

from .base import ProviderParser, to_decimal


class DemoProviderAParser(ProviderParser):
    """Fictional demo layout: areas in sq ft, pitch as 'x/12', lengths in ft with counts."""

    key = "demo_a"
    name = "Demo Provider A"
    fingerprints = ["DEMO PROVIDER A", "Report Summary"]
    patterns = {
        "total_area_sqft": r"^Total Roof Area\s+([\d,.]+)\s*sq\s*ft",
        "reported_squares": r"^Total Squares\s+([\d,.]+)",
        "predominant_pitch": r"^Predominant Pitch\s+(\d+(?:\.\d+)?)/12",
        "facets": r"^Total Roof Facets\s+(\d+)",
        "ridges_ft": r"^Ridges\s+([\d,.]+)\s*ft",
        "hips_ft": r"^Hips\s+([\d,.]+)\s*ft",
        "valleys_ft": r"^Valleys\s+([\d,.]+)\s*ft",
        "rakes_ft": r"^Rakes\s+([\d,.]+)\s*ft",
        "eaves_ft": r"^Eaves\s+([\d,.]+)\s*ft",
        "step_flashing_ft": r"^Step Flashing\s+([\d,.]+)\s*ft",
        "wall_flashing_ft": r"^Headwall Flashing\s+([\d,.]+)\s*ft",
        "perimeter_ft": r"^Total Perimeter:\s*([\d,.]+)\s*ft",
        "suggested_waste_pct": r"^Suggested Waste Factor:\s*([\d.]+)\s*%",
    }

    def parse_pitch_breakdown(self, text: str) -> list[dict]:
        section = text.split("Areas per Pitch", 1)[-1] if "Areas per Pitch" in text else ""
        rows = re.findall(r"^(\d+(?:\.\d+)?)/12\s+([\d,.]+)\s+[\d.]+%", section, re.MULTILINE)
        return [{"pitch": float(p), "area_sqft": float(to_decimal(a))} for p, a in rows]
