"""Material and labor quantities from verified measurements. Pure Decimal math, no AI."""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from .fields import FIELDS
from .formula import evaluate

TWO = Decimal("0.01")


def default_waste_pct(values: dict[str, Decimal]) -> Decimal:
    """Use the report's suggestion; otherwise scale with roof complexity (hip + valley lf per square)."""
    if values.get("suggested_waste_pct"):
        return values["suggested_waste_pct"]
    squares = values.get("total_area_sqft", Decimal(0)) / 100
    if not squares:
        return Decimal(10)
    complexity = (values.get("hips_ft", Decimal(0)) + values.get("valleys_ft", Decimal(0))) / squares
    return Decimal(10) if complexity < 2 else Decimal(12) if complexity < 4 else Decimal(15)


def steep_squares(values: dict[str, Decimal], breakdown: list[dict]) -> dict[str, Decimal]:
    """Squares in each steep-charge band, from the pitch breakdown (or predominant pitch if none)."""
    rows = [(Decimal(str(r["pitch"])), Decimal(str(r["area_sqft"]))) for r in breakdown] or \
           [(values.get("predominant_pitch", Decimal(0)), values.get("total_area_sqft", Decimal(0)))]
    bands = {"steep_8_9_sq": Decimal(0), "steep_10_12_sq": Decimal(0), "steep_13_plus_sq": Decimal(0)}
    for pitch, area in rows:
        if 8 <= pitch < 10:
            bands["steep_8_9_sq"] += area / 100
        elif 10 <= pitch <= 12:
            bands["steep_10_12_sq"] += area / 100
        elif pitch > 12:
            bands["steep_13_plus_sq"] += area / 100
    return bands


def build_variables(values: dict[str, Decimal], breakdown: list[dict], waste_pct: Decimal) -> dict[str, Decimal]:
    variables = {f.key: values.get(f.key) or Decimal(0) for f in FIELDS}
    variables["squares"] = variables["total_area_sqft"] / 100
    variables["pitch"] = variables["predominant_pitch"]
    variables["waste_pct"] = waste_pct
    variables.update(steep_squares(values, breakdown))
    return variables


@dataclass
class QtyResult:
    qty: Decimal
    formula: str


def fmt(d: Decimal, places: int = 2) -> str:
    d = d.quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP)
    return f"{d:,.{places}f}".rstrip("0").rstrip(".")


def material_qty(basis: str, coverage: Decimal, waste: str, unit: str, variables: dict[str, Decimal]) -> QtyResult:
    raw = evaluate(basis, variables)
    if raw <= 0:
        return QtyResult(Decimal(0), f"{basis} = 0")
    waste_pct = variables["waste_pct"] if waste == "job" else Decimal(waste)
    exact = raw * (1 + waste_pct / 100) / coverage
    qty = exact.to_integral_value(ROUND_CEILING)
    return QtyResult(qty, f"({basis}) {fmt(raw)} x {1 + waste_pct / 100:.2f} waste / {fmt(coverage)} per {unit} = {fmt(exact, 3)} -> {qty}")


def labor_qty(basis: str, rounding: str, variables: dict[str, Decimal]) -> QtyResult:
    raw = evaluate(basis, variables)
    if raw <= 0:
        return QtyResult(Decimal(0), f"{basis} = 0")
    qty = raw.to_integral_value(ROUND_CEILING) if rounding == "ceil" else raw.quantize(TWO, ROUND_HALF_UP)
    note = f" -> {qty}" if rounding == "ceil" else ""
    return QtyResult(qty, f"({basis}) = {fmt(raw)}{note}")
