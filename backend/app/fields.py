"""Canonical measurement fields every provider parser normalizes into."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    unit: str
    required: bool = False


FIELDS: list[Field] = [
    Field("total_area_sqft", "Total roof area", "sq ft", required=True),
    Field("predominant_pitch", "Predominant pitch", "/12", required=True),
    Field("facets", "Facets", "count"),
    Field("ridges_ft", "Ridges", "ft", required=True),
    Field("hips_ft", "Hips", "ft"),
    Field("valleys_ft", "Valleys", "ft"),
    Field("rakes_ft", "Rakes", "ft", required=True),
    Field("eaves_ft", "Eaves", "ft", required=True),
    Field("step_flashing_ft", "Step flashing", "ft"),
    Field("wall_flashing_ft", "Wall / headwall flashing", "ft"),
    Field("perimeter_ft", "Perimeter (reported)", "ft"),
    Field("reported_squares", "Squares (reported)", "sq"),
    Field("suggested_waste_pct", "Suggested waste", "%"),
]

FIELD_BY_KEY = {f.key: f for f in FIELDS}
REQUIRED_KEYS = [f.key for f in FIELDS if f.required]
