"""Deterministic checks run on extracted (or edited) measurements before estimating.

Errors block estimate generation; warnings are shown to the reviewer but allowed.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal

from .fields import FIELD_BY_KEY, REQUIRED_KEYS

LENGTH_KEYS = ["ridges_ft", "hips_ft", "valleys_ft", "rakes_ft", "eaves_ft", "step_flashing_ft", "wall_flashing_ft", "perimeter_ft"]


@dataclass
class Issue:
    level: str  # error | warning
    field: str | None
    message: str


def pct_diff(a: Decimal, b: Decimal) -> Decimal:
    return abs(a - b) / b * 100 if b else Decimal(0)


def verify(values: dict[str, Decimal | None], breakdown: list[dict], meta: dict[str, dict] | None = None) -> dict:
    """values: key -> Decimal (None = missing); meta: key -> {"source", "confidence", "confirmed"}."""
    meta = meta or {}
    issues: list[Issue] = []
    v = {k: val for k, val in values.items() if val is not None}

    for key in REQUIRED_KEYS:
        if key not in v:
            issues.append(Issue("error", key, f"{FIELD_BY_KEY[key].label} is missing. Enter it from the report."))

    for key, val in v.items():
        if val < 0:
            issues.append(Issue("error", key, f"{FIELD_BY_KEY[key].label} can't be negative."))

    area = v.get("total_area_sqft")
    if area is not None and area <= 0:
        issues.append(Issue("error", "total_area_sqft", "Total roof area must be greater than zero."))

    pitch = v.get("predominant_pitch")
    if pitch is not None:
        if pitch > 24:
            issues.append(Issue("error", "predominant_pitch", f"Pitch {pitch}/12 is outside the expected 0-24/12 range."))
        elif pitch < 2:
            issues.append(Issue("warning", "predominant_pitch", f"{pitch}/12 is low slope: asphalt shingles are not rated below 2/12."))
        elif pitch < 4:
            issues.append(Issue("warning", "predominant_pitch", f"{pitch}/12 is low slope: manufacturer specs require double underlayment."))

    if area and "reported_squares" in v and pct_diff(v["reported_squares"] * 100, area) > Decimal("0.5"):
        issues.append(Issue("warning", "reported_squares",
                            f"Reported squares ({v['reported_squares']}) don't match total area / 100 ({area / 100:.2f})."))

    if area and breakdown:
        total = sum(Decimal(str(r["area_sqft"])) for r in breakdown)
        diff = pct_diff(total, area)
        if diff > 5:
            issues.append(Issue("error", "pitch_breakdown",
                                f"Areas per pitch add up to {total:,.0f} sq ft but total area is {area:,.0f} sq ft ({diff:.1f}% off)."))
        elif diff > 1:
            issues.append(Issue("warning", "pitch_breakdown",
                                f"Areas per pitch add up to {total:,.0f} sq ft vs. total {area:,.0f} sq ft ({diff:.1f}% off)."))
        largest = max(breakdown, key=lambda r: r["area_sqft"])
        if pitch is not None and Decimal(str(largest["pitch"])) != pitch:
            issues.append(Issue("warning", "predominant_pitch",
                                f"Predominant pitch is {pitch}/12 but the largest area is at {largest['pitch']:g}/12."))

    eaves, rakes = v.get("eaves_ft"), v.get("rakes_ft")
    if "perimeter_ft" in v and eaves is not None and rakes is not None and pct_diff(eaves + rakes, v["perimeter_ft"]) > 2:
        issues.append(Issue("warning", "perimeter_ft",
                            f"Eaves + rakes = {eaves + rakes} ft, but the reported perimeter is {v['perimeter_ft']} ft."))

    if area and eaves == 0:
        issues.append(Issue("error", "eaves_ft", "Eaves can't be 0 on a pitched roof."))
    if area and eaves is not None and rakes is not None and (eaves + rakes) > 0:
        # A footprint of A sq ft has a perimeter of at least ~3.5 x sqrt(A) (circle bound).
        min_perimeter = Decimal("3.5") * area.sqrt() * Decimal("0.8")
        if eaves + rakes < min_perimeter:
            issues.append(Issue("warning", "eaves_ft",
                                f"Eaves + rakes ({eaves + rakes} ft) look short for a {area:,.0f} sq ft roof. Check the lengths."))
    if "ridges_ft" in v and "hips_ft" in v and v["ridges_ft"] + v["hips_ft"] == 0 and area:
        issues.append(Issue("warning", "ridges_ft", "No ridges or hips: confirm this is a shed or flat roof."))

    waste = v.get("suggested_waste_pct")
    if waste is not None and not (0 <= waste <= 30):
        issues.append(Issue("warning", "suggested_waste_pct", f"Waste factor {waste}% is outside the usual 0-30% range."))

    for key, m in meta.items():
        if key in v and not m.get("confirmed") and m.get("source") != "manual" and m.get("confidence", 1) < 0.9:
            reason = "read by AI" if m.get("source") == "ai" else "matched by the generic parser"
            issues.append(Issue("warning", key, f"{FIELD_BY_KEY[key].label} was {reason}. Confirm it against the PDF."))

    errors = sum(i.level == "error" for i in issues)
    return {
        "status": "fail" if errors else ("warn" if issues else "pass"),
        "can_estimate": errors == 0,
        "issues": [asdict(i) for i in issues],
    }
