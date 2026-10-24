from decimal import Decimal as D

from app.verification import verify

GOOD = {"total_area_sqft": D(2846), "predominant_pitch": D(6), "ridges_ft": D(92), "hips_ft": D(48),
        "valleys_ft": D(36), "rakes_ft": D(118), "eaves_ft": D(164), "perimeter_ft": D(282), "reported_squares": D("28.46")}
BREAKDOWN = [{"pitch": 6, "area_sqft": 2410}, {"pitch": 4, "area_sqft": 436}]


def messages(result, level=None):
    return [i["message"] for i in result["issues"] if level in (None, i["level"])]


def test_clean_report_passes():
    r = verify(GOOD, BREAKDOWN)
    assert r["status"] == "pass" and r["can_estimate"]


def test_missing_required_field_blocks():
    r = verify({**GOOD, "eaves_ft": None}, BREAKDOWN)
    assert not r["can_estimate"]
    assert any("Eaves is missing" in m for m in messages(r, "error"))


def test_pitch_breakdown_must_add_up():
    r = verify(GOOD, [{"pitch": 6, "area_sqft": 2000}, {"pitch": 4, "area_sqft": 436}])
    assert not r["can_estimate"]
    small = verify(GOOD, [{"pitch": 6, "area_sqft": 2360}, {"pitch": 4, "area_sqft": 436}])  # ~1.8% off
    assert small["can_estimate"] and small["status"] == "warn"


def test_perimeter_and_squares_cross_checks():
    r = verify({**GOOD, "perimeter_ft": D(320), "reported_squares": D(30)}, BREAKDOWN)
    fields = {i["field"] for i in r["issues"]}
    assert {"perimeter_ft", "reported_squares"} <= fields
    assert r["can_estimate"]


def test_low_slope_and_out_of_range_pitch():
    assert any("double underlayment" in m for m in messages(verify({**GOOD, "predominant_pitch": D(3)}, [])))
    assert not verify({**GOOD, "predominant_pitch": D(30)}, [])["can_estimate"]


def test_low_confidence_values_need_confirmation():
    meta = {"eaves_ft": {"source": "ai", "confidence": 0.8, "confirmed": False}}
    assert any("read by AI" in m for m in messages(verify(GOOD, BREAKDOWN, meta)))
    meta["eaves_ft"]["confirmed"] = True
    assert verify(GOOD, BREAKDOWN, meta)["status"] == "pass"
