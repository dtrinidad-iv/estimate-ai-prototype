from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    unit: str
    required: bool
    value: float | None
    original_value: float | None
    source: str
    confidence: float
    evidence: str | None
    confirmed: bool


class Issue(BaseModel):
    level: str
    field: str | None
    message: str


class Verification(BaseModel):
    status: str
    can_estimate: bool
    issues: list[Issue]


class PitchArea(BaseModel):
    pitch: float
    area_sqft: float


class ReportOut(BaseModel):
    id: int
    job_id: int
    job_name: str
    filename: str
    provider: str
    provider_name: str
    extraction_method: str
    uploaded_at: datetime
    notes: list[str]
    pitch_breakdown: list[PitchArea]
    measurements: list[MeasurementOut]
    verification: Verification
    estimate_ids: list[int]


class MeasurementUpdate(BaseModel):
    values: dict[str, float | None] = {}
    confirm: list[str] = []
    pitch_breakdown: list[PitchArea] | None = None


class EstimateCreate(BaseModel):
    assembly_code: str = "ARCH-STD"
    waste_pct: Decimal | None = None
    margin_pct: Decimal | None = None
    tax_pct: Decimal | None = None


class EstimateUpdate(BaseModel):
    waste_pct: Decimal | None = None
    margin_pct: Decimal | None = None
    tax_pct: Decimal | None = None


class LineItemUpdate(BaseModel):
    qty: Decimal | None = None
    unit_cost: Decimal | None = None
    reset: bool = False


class LineItemOut(BaseModel):
    id: int
    kind: str
    ref_code: str
    description: str
    unit: str
    calc_qty: float
    qty: float
    unit_cost: float
    total: float
    formula: str
    overridden: bool


class Totals(BaseModel):
    materials: float
    material_tax: float
    labor: float
    other: float
    total_cost: float
    selling_price: float
    gross_profit: float
    actual_margin_pct: float
    price_per_square: float


class EstimateOut(BaseModel):
    id: int
    job_id: int
    job_name: str
    report_id: int
    assembly_code: str
    assembly_name: str
    waste_pct: float
    margin_pct: float
    tax_pct: float
    created_at: datetime
    items: list[LineItemOut]
    totals: Totals


class PriceUpdate(BaseModel):
    price: Decimal
