from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .calculator import build_variables, default_waste_pct, labor_qty, material_qty
from .extraction.pipeline import run_extraction
from .fields import FIELDS
from .models import Assembly, Estimate, Job, LaborRate, LineItem, Material, Measurement, Report
from .seed import load_pricebook
from .verification import verify

CENT = Decimal("0.01")


class EstimateBlocked(Exception):
    pass


# ---------- reports & measurements ----------

def create_report(db: Session, job_name: str, filename: str, stored_path: Path, use_ai: bool) -> Report:
    result, text = run_extraction(stored_path, use_ai=use_ai)
    job = Job(name=job_name)
    report = Report(job=job, filename=filename, stored_path=str(stored_path), provider=result.provider,
                    extraction_method=result.method, raw_text=text, pitch_breakdown=result.pitch_breakdown,
                    notes=result.notes)
    for f in FIELDS:
        ev = result.values.get(f.key)
        report.measurements.append(Measurement(
            key=f.key,
            value=ev.value if ev else None,
            original_value=ev.value if ev else None,
            source=ev.source if ev else "missing",
            confidence=ev.confidence if ev else 0.0,
            evidence=ev.evidence if ev else None,
        ))
    db.add(report)
    db.commit()
    return report


def measurement_values(report: Report) -> dict[str, Decimal | None]:
    return {m.key: m.value for m in report.measurements}


def measurement_meta(report: Report) -> dict[str, dict]:
    return {m.key: {"source": m.source, "confidence": m.confidence, "confirmed": m.confirmed} for m in report.measurements}


def verify_report(report: Report) -> dict:
    return verify(measurement_values(report), report.pitch_breakdown, measurement_meta(report))


def update_measurements(db: Session, report: Report, values: dict[str, float | None],
                        confirm: list[str], pitch_breakdown: list[dict] | None) -> Report:
    by_key = {m.key: m for m in report.measurements}
    for key, raw in values.items():
        m = by_key.get(key)
        if m is None:
            continue
        new = None if raw is None else Decimal(str(raw))
        if new != m.value:
            m.value, m.source, m.confidence, m.confirmed = new, "manual", 1.0, True
    for key in confirm:
        if key in by_key:
            by_key[key].confirmed = True
    if pitch_breakdown is not None:
        report.pitch_breakdown = [{"pitch": float(r["pitch"]), "area_sqft": float(r["area_sqft"])} for r in pitch_breakdown]
    db.commit()
    return report


# ---------- estimates ----------

def generate_estimate(db: Session, report: Report, assembly_code: str, waste_pct: Decimal | None,
                      margin_pct: Decimal | None, tax_pct: Decimal | None) -> Estimate:
    check = verify_report(report)
    if not check["can_estimate"]:
        raise EstimateBlocked("Fix the measurement errors before generating an estimate.")
    assembly = db.scalar(select(Assembly).where(Assembly.code == assembly_code))
    if assembly is None:
        raise ValueError(f"Unknown assembly {assembly_code}")

    defaults = load_pricebook()["defaults"]
    values = {k: v for k, v in measurement_values(report).items() if v is not None}
    estimate = Estimate(
        job_id=report.job_id, report_id=report.id, assembly_code=assembly.code,
        waste_pct=waste_pct if waste_pct is not None else default_waste_pct(values),
        margin_pct=margin_pct if margin_pct is not None else Decimal(defaults["margin_pct"]),
        tax_pct=tax_pct if tax_pct is not None else Decimal(defaults["tax_pct"]),
    )
    variables = build_variables(values, report.pitch_breakdown, estimate.waste_pct)

    sort = 0
    materials = {m.sku: m for m in db.scalars(select(Material).where(Material.sku.in_(assembly.material_skus)))}
    for sku in assembly.material_skus:
        mat = materials[sku]
        q = material_qty(mat.basis, mat.coverage_per_unit, mat.waste, mat.unit, variables)
        if q.qty == 0:
            continue
        sort += 1
        estimate.items.append(LineItem(kind="material", ref_code=sku, description=mat.name, unit=mat.unit,
                                       calc_qty=q.qty, qty=q.qty, unit_cost=mat.unit_cost, formula=q.formula, sort=sort))
    rates = {r.code: r for r in db.scalars(select(LaborRate).where(LaborRate.code.in_(assembly.labor_codes)))}
    for code in assembly.labor_codes:
        rate = rates[code]
        q = labor_qty(rate.basis, rate.rounding, variables)
        if q.qty == 0:
            continue
        sort += 1
        estimate.items.append(LineItem(kind=rate.kind, ref_code=code, description=rate.name, unit=rate.unit,
                                       calc_qty=q.qty, qty=q.qty, unit_cost=rate.rate, formula=q.formula, sort=sort))
    db.add(estimate)
    db.commit()
    return estimate


def recalc_quantities(db: Session, estimate: Estimate, report: Report) -> None:
    """Re-run formulas (e.g. after a waste change); estimator overrides are kept."""
    values = {k: v for k, v in measurement_values(report).items() if v is not None}
    variables = build_variables(values, report.pitch_breakdown, estimate.waste_pct)
    materials = {m.sku: m for m in db.scalars(select(Material))}
    rates = {r.code: r for r in db.scalars(select(LaborRate))}
    for item in estimate.items:
        if item.kind == "material":
            mat = materials[item.ref_code]
            q = material_qty(mat.basis, mat.coverage_per_unit, mat.waste, mat.unit, variables)
        else:
            rate = rates[item.ref_code]
            q = labor_qty(rate.basis, rate.rounding, variables)
        item.calc_qty, item.formula = q.qty, q.formula
        if not item.overridden:
            item.qty = q.qty
    db.commit()


def reset_line_item(db: Session, item: LineItem) -> None:
    if item.kind == "material":
        item.unit_cost = db.scalar(select(Material.unit_cost).where(Material.sku == item.ref_code))
    else:
        item.unit_cost = db.scalar(select(LaborRate.rate).where(LaborRate.code == item.ref_code))
    item.qty, item.overridden = item.calc_qty, False
    db.commit()


def line_total(item: LineItem) -> Decimal:
    return (item.qty * item.unit_cost).quantize(CENT, ROUND_HALF_UP)


def estimate_totals(estimate: Estimate, total_area_sqft: Decimal | None) -> dict:
    by_kind = {"material": Decimal(0), "labor": Decimal(0), "other": Decimal(0)}
    for item in estimate.items:
        by_kind[item.kind] += line_total(item)
    tax = (by_kind["material"] * estimate.tax_pct / 100).quantize(CENT, ROUND_HALF_UP)
    cost = by_kind["material"] + tax + by_kind["labor"] + by_kind["other"]
    margin = estimate.margin_pct / 100
    # Margin is on the selling price (not markup on cost); round up to the next $10 for a clean quote.
    sell = (cost / (1 - margin) / 10).to_integral_value(ROUND_CEILING) * 10 if margin < 1 else cost
    profit = sell - cost
    squares = (total_area_sqft or Decimal(0)) / 100
    return {
        "materials": by_kind["material"], "material_tax": tax, "labor": by_kind["labor"], "other": by_kind["other"],
        "total_cost": cost, "selling_price": sell, "gross_profit": profit,
        "actual_margin_pct": (profit / sell * 100).quantize(CENT, ROUND_HALF_UP) if sell else Decimal(0),
        "price_per_square": (sell / squares).quantize(CENT, ROUND_HALF_UP) if squares else Decimal(0),
    }
