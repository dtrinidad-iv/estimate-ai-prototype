import re
import shutil
import uuid
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import services
from .db import SAMPLES_DIR, UPLOAD_DIR, get_db
from .extraction.ai import ai_available
from .extraction.providers import PROVIDERS
from .fields import FIELD_BY_KEY
from .models import Assembly, Estimate, Job, LaborRate, LineItem, Material, Report
from .schemas import (EstimateCreate, EstimateOut, EstimateUpdate, LineItemOut, LineItemUpdate, MeasurementOut,
                      MeasurementUpdate, PriceUpdate, ReportOut, Totals)
from .seed import init_db

PROVIDER_NAMES = {p.key: p.name for p in PROVIDERS} | {"unknown": "Unrecognized format"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    UPLOAD_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="EstimateAI", version="0.1.0", lifespan=lifespan)


# ---------- serializers ----------

def report_out(report: Report) -> ReportOut:
    measurements = []
    for m in report.measurements:
        f = FIELD_BY_KEY[m.key]
        measurements.append(MeasurementOut(
            key=m.key, label=f.label, unit=f.unit, required=f.required,
            value=float(m.value) if m.value is not None else None,
            original_value=float(m.original_value) if m.original_value is not None else None,
            source=m.source, confidence=m.confidence, evidence=m.evidence, confirmed=m.confirmed,
        ))
    return ReportOut(
        id=report.id, job_id=report.job_id, job_name=report.job.name, filename=report.filename,
        provider=report.provider, provider_name=PROVIDER_NAMES.get(report.provider, report.provider),
        extraction_method=report.extraction_method, uploaded_at=report.uploaded_at, notes=report.notes,
        pitch_breakdown=report.pitch_breakdown, measurements=measurements,
        verification=services.verify_report(report),
        estimate_ids=[e.id for e in report.job.estimates if e.report_id == report.id],
    )


def estimate_out(db: Session, estimate: Estimate) -> EstimateOut:
    report = db.get(Report, estimate.report_id)
    area = services.measurement_values(report).get("total_area_sqft")
    assembly = db.scalar(select(Assembly).where(Assembly.code == estimate.assembly_code))
    totals = services.estimate_totals(estimate, area)
    return EstimateOut(
        id=estimate.id, job_id=estimate.job_id, job_name=estimate.job.name, report_id=estimate.report_id,
        assembly_code=estimate.assembly_code, assembly_name=assembly.name if assembly else estimate.assembly_code,
        waste_pct=float(estimate.waste_pct), margin_pct=float(estimate.margin_pct), tax_pct=float(estimate.tax_pct),
        created_at=estimate.created_at,
        items=[LineItemOut(id=i.id, kind=i.kind, ref_code=i.ref_code, description=i.description, unit=i.unit,
                           calc_qty=float(i.calc_qty), qty=float(i.qty), unit_cost=float(i.unit_cost),
                           total=float(services.line_total(i)), formula=i.formula, overridden=i.overridden)
               for i in estimate.items],
        totals=Totals(**{k: float(v) for k, v in totals.items()}),
    )


def get_or_404(db: Session, model, id_: int):
    obj = db.get(model, id_)
    if obj is None:
        raise HTTPException(404, f"{model.__name__} {id_} not found")
    return obj


# ---------- meta ----------

@app.get("/api/health")
def health():
    return {"ok": True, "ai_enabled": ai_available(), "providers": [{"key": p.key, "name": p.name} for p in PROVIDERS]}


@app.get("/api/samples")
def list_samples():
    return [{"name": p.name, "size": p.stat().st_size} for p in sorted(SAMPLES_DIR.glob("*.pdf"))]


@app.get("/api/samples/{name}")
def get_sample(name: str):
    path = SAMPLES_DIR / Path(name).name
    if not path.is_file():
        raise HTTPException(404, "Sample not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


# ---------- jobs & reports ----------

@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).order_by(Job.created_at.desc()).limit(50)).all()
    out = []
    for job in jobs:
        report = job.reports[-1] if job.reports else None
        estimate = job.estimates[-1] if job.estimates else None
        out.append({
            "id": job.id, "name": job.name, "created_at": job.created_at,
            "report_id": report.id if report else None,
            "provider_name": PROVIDER_NAMES.get(report.provider, report.provider) if report else None,
            "status": services.verify_report(report)["status"] if report else None,
            "estimate_id": estimate.id if estimate else None,
            "selling_price": float(services.estimate_totals(
                estimate, services.measurement_values(db.get(Report, estimate.report_id)).get("total_area_sqft")
            )["selling_price"]) if estimate else None,
        })
    return out


def _job_name(filename: str, given: str | None) -> str:
    if given and given.strip():
        return given.strip()
    return re.sub(r"[_-]+", " ", Path(filename).stem).strip().title()


@app.post("/api/reports", response_model=ReportOut)
async def upload_report(file: UploadFile = File(...), job_name: str | None = Form(None), use_ai: bool = Form(True),
                        db: Session = Depends(get_db)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF measurement report.")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "PDF is larger than 25 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "That file isn't a valid PDF.")
    stored = UPLOAD_DIR / f"{uuid.uuid4().hex}.pdf"
    stored.write_bytes(data)
    report = services.create_report(db, _job_name(file.filename, job_name), Path(file.filename).name, stored, use_ai)
    return report_out(report)


@app.post("/api/samples/{name}/load", response_model=ReportOut)
def load_sample(name: str, db: Session = Depends(get_db)):
    """Demo shortcut: run a bundled sample through the same pipeline as an upload."""
    src = SAMPLES_DIR / Path(name).name
    if not src.is_file():
        raise HTTPException(404, "Sample not found")
    stored = UPLOAD_DIR / f"{uuid.uuid4().hex}.pdf"
    shutil.copy(src, stored)
    return report_out(services.create_report(db, _job_name(src.name, None), src.name, stored, use_ai=True))


@app.get("/api/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    return report_out(get_or_404(db, Report, report_id))


@app.get("/api/reports/{report_id}/pdf")
def get_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = get_or_404(db, Report, report_id)
    return FileResponse(report.stored_path, media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="{report.filename}"'})


@app.patch("/api/reports/{report_id}/measurements", response_model=ReportOut)
def patch_measurements(report_id: int, body: MeasurementUpdate, db: Session = Depends(get_db)):
    report = get_or_404(db, Report, report_id)
    unknown = [k for k in body.values if k not in FIELD_BY_KEY]
    if unknown:
        raise HTTPException(400, f"Unknown measurement keys: {', '.join(unknown)}")
    breakdown = [r.model_dump() for r in body.pitch_breakdown] if body.pitch_breakdown is not None else None
    services.update_measurements(db, report, body.values, body.confirm, breakdown)
    return report_out(report)


# ---------- estimates ----------

@app.post("/api/reports/{report_id}/estimates", response_model=EstimateOut)
def create_estimate(report_id: int, body: EstimateCreate, db: Session = Depends(get_db)):
    report = get_or_404(db, Report, report_id)
    try:
        estimate = services.generate_estimate(db, report, body.assembly_code, body.waste_pct, body.margin_pct, body.tax_pct)
    except services.EstimateBlocked as e:
        raise HTTPException(409, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return estimate_out(db, estimate)


@app.get("/api/estimates/{estimate_id}", response_model=EstimateOut)
def get_estimate(estimate_id: int, db: Session = Depends(get_db)):
    return estimate_out(db, get_or_404(db, Estimate, estimate_id))


@app.patch("/api/estimates/{estimate_id}", response_model=EstimateOut)
def patch_estimate(estimate_id: int, body: EstimateUpdate, db: Session = Depends(get_db)):
    estimate = get_or_404(db, Estimate, estimate_id)
    if body.margin_pct is not None:
        if not (Decimal(0) <= body.margin_pct < Decimal(90)):
            raise HTTPException(400, "Margin must be between 0 and 90%.")
        estimate.margin_pct = body.margin_pct
    if body.tax_pct is not None:
        estimate.tax_pct = body.tax_pct
    if body.waste_pct is not None:
        estimate.waste_pct = body.waste_pct
        services.recalc_quantities(db, estimate, db.get(Report, estimate.report_id))
    db.commit()
    return estimate_out(db, estimate)


@app.patch("/api/line-items/{item_id}", response_model=EstimateOut)
def patch_line_item(item_id: int, body: LineItemUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, LineItem, item_id)
    if body.reset:
        services.reset_line_item(db, item)
    else:
        if body.qty is not None:
            if body.qty < 0:
                raise HTTPException(400, "Quantity can't be negative.")
            item.qty = body.qty
        if body.unit_cost is not None:
            if body.unit_cost < 0:
                raise HTTPException(400, "Unit cost can't be negative.")
            item.unit_cost = body.unit_cost
        item.overridden = True
        db.commit()
    return estimate_out(db, item.estimate)


# ---------- price book ----------

@app.get("/api/pricebook")
def pricebook(db: Session = Depends(get_db)):
    return {
        "materials": [{"sku": m.sku, "name": m.name, "category": m.category, "unit": m.unit, "price": float(m.unit_cost),
                       "basis": m.basis, "coverage": m.coverage_note, "waste": m.waste, "spec": m.manufacturer_spec}
                      for m in db.scalars(select(Material).order_by(Material.id))],
        "labor": [{"code": r.code, "kind": r.kind, "name": r.name, "unit": r.unit, "price": float(r.rate), "basis": r.basis}
                  for r in db.scalars(select(LaborRate).order_by(LaborRate.kind, LaborRate.id))],
        "assemblies": [{"code": a.code, "name": a.name, "description": a.description,
                        "material_skus": a.material_skus, "labor_codes": a.labor_codes}
                       for a in db.scalars(select(Assembly))],
    }


@app.patch("/api/pricebook/materials/{sku}")
def update_material_price(sku: str, body: PriceUpdate, db: Session = Depends(get_db)):
    mat = db.scalar(select(Material).where(Material.sku == sku))
    if mat is None:
        raise HTTPException(404, "Material not found")
    mat.unit_cost = body.price
    db.commit()
    return {"sku": sku, "price": float(mat.unit_cost)}


@app.patch("/api/pricebook/labor/{code}")
def update_labor_rate(code: str, body: PriceUpdate, db: Session = Depends(get_db)):
    rate = db.scalar(select(LaborRate).where(LaborRate.code == code))
    if rate is None:
        raise HTTPException(404, "Labor rate not found")
    rate.rate = body.price
    db.commit()
    return {"code": code, "price": float(rate.rate)}


# Serve the built React app (npm run build) so the demo runs from one process.
DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
