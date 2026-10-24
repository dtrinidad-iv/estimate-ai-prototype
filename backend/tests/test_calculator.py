from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from app.calculator import build_variables, default_waste_pct, labor_qty, material_qty, steep_squares
from app.formula import FormulaError, evaluate
from app.services import estimate_totals


def test_formula_arithmetic_and_conditionals():
    v = {"a": D(10), "b": D(4), "pitch": D(9)}
    assert evaluate("a * 2 + b / 4", v) == D(21)
    assert evaluate("a if 8 <= pitch < 10 else 0", v) == D(10)
    assert evaluate("max(a, b) - min(a, b)", v) == D(6)
    assert evaluate("a / 0", v) == 0


@pytest.mark.parametrize("expr", ["__import__('os')", "a.real", "open('x')", "[1, 2]", "unknown_var"])
def test_formula_rejects_anything_but_math(expr):
    with pytest.raises(FormulaError):
        evaluate(expr, {"a": D(1)})


def test_shingle_bundles_round_up_after_waste():
    v = build_variables({"total_area_sqft": D(2846)}, [], D(12))
    q = material_qty("total_area_sqft", D("33.333"), "job", "bundle", v)
    assert q.qty == 96  # 2846 * 1.12 / 33.333 = 95.63 -> 96


def test_fixed_waste_overrides_job_waste():
    v = build_variables({"eaves_ft": D(100), "rakes_ft": D(100)}, [], D(15))
    assert material_qty("eaves_ft + rakes_ft", D(10), "0", "piece", v).qty == 20


def test_zero_basis_gives_zero_quantity():
    v = build_variables({}, [], D(10))
    assert material_qty("valleys_ft", D(10), "5", "piece", v).qty == 0


def test_steep_bands_use_pitch_breakdown():
    bands = steep_squares({}, [{"pitch": 9, "area_sqft": 2140}, {"pitch": 12, "area_sqft": 785}, {"pitch": 4, "area_sqft": 200}])
    assert bands == {"steep_8_9_sq": D("21.4"), "steep_10_12_sq": D("7.85"), "steep_13_plus_sq": D(0)}


def test_steep_bands_fall_back_to_predominant_pitch():
    bands = steep_squares({"predominant_pitch": D(14), "total_area_sqft": D(1500)}, [])
    assert bands["steep_13_plus_sq"] == 15


def test_default_waste_prefers_report_then_complexity():
    assert default_waste_pct({"suggested_waste_pct": D(14)}) == 14
    assert default_waste_pct({"total_area_sqft": D(2000), "hips_ft": D(10), "valleys_ft": D(10)}) == 10
    assert default_waste_pct({"total_area_sqft": D(2000), "hips_ft": D(60), "valleys_ft": D(40)}) == 15


def test_labor_ceil_rounding():
    v = build_variables({"total_area_sqft": D(2846)}, [], D(10))
    assert labor_qty("squares / 25", "ceil", v).qty == 2
    assert labor_qty("squares", "none", v).qty == D("28.46")


def test_margin_is_on_selling_price():
    items = [SimpleNamespace(kind="material", qty=D(1), unit_cost=D(1000)),
             SimpleNamespace(kind="labor", qty=D(1), unit_cost=D(500))]
    est = SimpleNamespace(items=items, tax_pct=D(10), margin_pct=D(40))
    t = estimate_totals(est, D(1000))
    assert t["total_cost"] == D(1600)  # 1000 + 100 tax + 500
    assert t["selling_price"] == D(2670)  # 1600 / 0.6 = 2666.67 -> next $10
    assert t["actual_margin_pct"] >= 40
