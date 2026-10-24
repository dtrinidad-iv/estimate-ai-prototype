"""Creates tables and loads the price book from config/pricebook.json (idempotent)."""

import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .models import Assembly, LaborRate, Material

PRICEBOOK = Path(__file__).parent / "config" / "pricebook.json"


def load_pricebook() -> dict:
    return json.loads(PRICEBOOK.read_text())


def init_db() -> None:
    Base.metadata.create_all(engine)
    data = load_pricebook()
    with SessionLocal() as db:
        for m in data["materials"]:
            if not db.scalar(select(Material).where(Material.sku == m["sku"])):
                db.add(Material(**{**m, "unit_cost": Decimal(m["unit_cost"]),
                                   "coverage_per_unit": Decimal(m["coverage_per_unit"])}))
        for l in data["labor"]:
            if not db.scalar(select(LaborRate).where(LaborRate.code == l["code"])):
                db.add(LaborRate(**{**l, "rate": Decimal(l["rate"])}))
        for a in data["assemblies"]:
            if not db.scalar(select(Assembly).where(Assembly.code == a["code"])):
                db.add(Assembly(**a))
        db.commit()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
