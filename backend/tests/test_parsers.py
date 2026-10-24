from decimal import Decimal

from app.extraction.pipeline import run_extraction


def values(result):
    return {k: v.value for k, v in result.values.items()}


def test_demo_provider_a_template(samples):
    result, _ = run_extraction(samples / "demo_a_1428_maple_ave.pdf", use_ai=False)
    assert result.provider == "demo_a" and result.method == "template"
    v = values(result)
    assert v["total_area_sqft"] == Decimal("2846")
    assert v["predominant_pitch"] == 6
    assert (v["ridges_ft"], v["hips_ft"], v["valleys_ft"], v["rakes_ft"], v["eaves_ft"]) == (92, 48, 36, 118, 164)
    assert v["suggested_waste_pct"] == 12
    assert result.pitch_breakdown == [{"pitch": 6.0, "area_sqft": 2410.0}, {"pitch": 4.0, "area_sqft": 436.0}]


def test_demo_provider_b_converts_squares_and_colon_pitch(samples):
    result, _ = run_extraction(samples / "demo_b_77_ridgeview_dr.pdf", use_ai=False)
    assert result.provider == "demo_b"
    v = values(result)
    assert v["total_area_sqft"] == 3125
    assert v["predominant_pitch"] == 9
    assert v["reported_squares"] == Decimal("31.25")
    assert sum(r["area_sqft"] for r in result.pitch_breakdown) == 3125


def test_missing_line_is_left_missing_not_guessed(samples):
    result, _ = run_extraction(samples / "demo_a_needs_review_oak_st.pdf", use_ai=False)
    assert "eaves_ft" not in result.values


def test_unknown_format_uses_generic_parser_with_lower_confidence(samples):
    result, _ = run_extraction(samples / "field_worksheet_unknown_format.pdf", use_ai=False)
    assert result.provider == "unknown" and result.method == "generic"
    v = values(result)
    assert v["total_area_sqft"] == 1980 and v["predominant_pitch"] == 7 and v["eaves_ft"] == 140
    assert v["hips_ft"] == 0  # "No hips" is an explicit zero
    assert all(ev.confidence < 0.9 for ev in result.values.values())
