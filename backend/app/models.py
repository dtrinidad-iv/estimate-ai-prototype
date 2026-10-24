from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


Money = Numeric(12, 2)
Qty = Numeric(12, 3)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    reports: Mapped[list["Report"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    estimates: Mapped[list["Estimate"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Report(Base):
    """One uploaded measurement PDF and what was extracted from it."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    filename: Mapped[str] = mapped_column(String(300))
    stored_path: Mapped[str] = mapped_column(String(500))
    provider: Mapped[str] = mapped_column(String(100))  # detected provider key or "unknown"
    extraction_method: Mapped[str] = mapped_column(String(30))  # template | generic | ai | manual
    raw_text: Mapped[str] = mapped_column(Text, default="")
    pitch_breakdown: Mapped[list] = mapped_column(JSON, default=list)  # [{"pitch": 6, "area_sqft": 1200.0}]
    notes: Mapped[list] = mapped_column(JSON, default=list)  # extraction-time messages
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[Job] = relationship(back_populates="reports")
    measurements: Mapped[list["Measurement"]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="Measurement.id"
    )


class Measurement(Base):
    """A single normalized value, with where it came from and how much we trust it."""

    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    key: Mapped[str] = mapped_column(String(50))
    value: Mapped[Decimal | None] = mapped_column(Qty)
    original_value: Mapped[Decimal | None] = mapped_column(Qty)  # as extracted, before any edit
    source: Mapped[str] = mapped_column(String(20))  # template | generic | ai | manual
    confidence: Mapped[float] = mapped_column(default=1.0)
    evidence: Mapped[str | None] = mapped_column(String(300))  # snippet of PDF text the value came from
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)  # a person checked it against the PDF

    report: Mapped[Report] = relationship(back_populates="measurements")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    unit: Mapped[str] = mapped_column(String(20))  # bundle, roll, piece, box...
    unit_cost: Mapped[Decimal] = mapped_column(Money)
    # Quantity formula: ceil(basis * (1 + waste) / coverage_per_unit)
    basis: Mapped[str] = mapped_column(String(300))  # expression over measurement keys
    coverage_per_unit: Mapped[Decimal] = mapped_column(Qty)
    coverage_note: Mapped[str] = mapped_column(String(100))  # e.g. "33.3 sq ft per bundle"
    waste: Mapped[str] = mapped_column(String(20), default="job")  # "job" = job waste %, else fixed pct
    manufacturer_spec: Mapped[str | None] = mapped_column(String(300))


class LaborRate(Base):
    __tablename__ = "labor_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    kind: Mapped[str] = mapped_column(String(20), default="labor")  # labor | other (dumpster, permit...)
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(20))
    rate: Mapped[Decimal] = mapped_column(Money)
    basis: Mapped[str] = mapped_column(String(300))  # expression; 0 means the line is skipped
    rounding: Mapped[str] = mapped_column(String(10), default="none")  # none | ceil


class Assembly(Base):
    """A reusable bundle of materials + labor, e.g. 'Architectural shingle re-roof'."""

    __tablename__ = "assemblies"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    material_skus: Mapped[list] = mapped_column(JSON)
    labor_codes: Mapped[list] = mapped_column(JSON)


class Estimate(Base):
    __tablename__ = "estimates"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    assembly_code: Mapped[str] = mapped_column(String(50))
    waste_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    margin_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    tax_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[Job] = relationship(back_populates="estimates")
    items: Mapped[list["LineItem"]] = relationship(
        back_populates="estimate", cascade="all, delete-orphan", order_by="LineItem.sort"
    )


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_id: Mapped[int] = mapped_column(ForeignKey("estimates.id"))
    kind: Mapped[str] = mapped_column(String(20))  # material | labor | other
    ref_code: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(20))
    calc_qty: Mapped[Decimal] = mapped_column(Qty)  # what the formula produced
    qty: Mapped[Decimal] = mapped_column(Qty)  # what the estimator is using
    unit_cost: Mapped[Decimal] = mapped_column(Money)
    formula: Mapped[str] = mapped_column(String(400))  # human-readable working
    overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    estimate: Mapped[Estimate] = relationship(back_populates="items")
