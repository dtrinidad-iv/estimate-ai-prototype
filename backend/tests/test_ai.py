"""AI extraction is tested against a fake client: no network, no API key."""

from decimal import Decimal
from types import SimpleNamespace

from app.extraction import ai, pipeline
from app.extraction.ai import AIExtraction, AIField


def empty():
    return AIField(value=None, unit=None, quote=None)


def fake_response(**fields):
    data = {k: empty() for k in AIExtraction.model_fields if k not in ("provider_name", "pitch_breakdown")}
    data.update(fields)
    parsed = AIExtraction(provider_name=None, pitch_breakdown=[], **data)
    return SimpleNamespace(stop_reason="end_turn", parsed_output=parsed)


class FakeClient:
    def __init__(self, response):
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=self._parse))
        self._response = response

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


def test_ai_fills_only_missing_fields_and_flags_unverified_numbers(samples, monkeypatch):
    response = fake_response(
        wall_flashing_ft=AIField(value=6, unit="LF", quote="Chimney has 6 LF of apron flashing"),
        facets=AIField(value=11, unit="count", quote="eleven facets"),  # number not in the PDF text
    )
    client = FakeClient(response)
    monkeypatch.setattr(ai, "ai_available", lambda: True)
    monkeypatch.setattr(ai.anthropic, "Anthropic", lambda: client)

    result, _ = pipeline.run_extraction(samples / "field_worksheet_unknown_format.pdf")

    assert result.method == "generic+ai"
    assert result.values["wall_flashing_ft"].value == 6
    assert result.values["wall_flashing_ft"].source == "ai"
    assert result.values["wall_flashing_ft"].confidence == 0.8
    assert result.values["facets"].confidence == 0.4
    assert "not found in PDF text" in result.values["facets"].evidence
    # Generic-parser values are not overwritten by AI.
    assert result.values["total_area_sqft"].source == "generic"
    assert client.calls[0]["model"] == "claude-opus-5-5"


def test_area_reported_in_squares_is_converted_in_code():
    assert ai.normalize("total_area_sqft", AIField(value=31.25, unit="squares", quote="")) == Decimal("3125.00")
    assert ai.normalize("total_area_sqft", AIField(value=3125, unit="sq ft", quote="")) == 3125


def test_known_templates_never_call_ai(samples, monkeypatch):
    monkeypatch.setattr(ai, "ai_available", lambda: True)
    monkeypatch.setattr(ai.anthropic, "Anthropic", lambda: (_ for _ in ()).throw(AssertionError("AI called")))
    result, _ = pipeline.run_extraction(samples / "demo_a_needs_review_oak_st.pdf")
    assert result.method == "template"


def test_without_api_key_ai_is_skipped_with_a_note(samples):
    result, _ = pipeline.run_extraction(samples / "field_worksheet_unknown_format.pdf")
    assert any("AI extraction skipped" in n for n in result.notes)
