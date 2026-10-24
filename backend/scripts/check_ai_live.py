"""Live check of AI extraction against the real Claude API (costs one API call).

Not part of pytest: tests never touch the network. Run on demand:
    cd backend && .venv/bin/python -m scripts.check_ai_live
"""

import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND / ".env")

from app.extraction import ai, pipeline  # noqa: E402  (after .env so the key is visible)
from app.extraction.providers import GENERIC  # noqa: E402
from app.extraction.text import extract_text  # noqa: E402
from app.verification import verify  # noqa: E402

SAMPLES = BACKEND / "samples"
UNKNOWN = SAMPLES / "field_worksheet_unknown_format.pdf"
NOT_FOUND = "[number not found in PDF text]"


def check(failures: list[str], ok: bool, message: str) -> None:
    if not ok:
        failures.append(message)


def check_unknown_format(failures: list[str]) -> None:
    text = extract_text(UNKNOWN)
    generic = GENERIC.parse(text).values
    started = time.monotonic()
    result, _ = pipeline.run_extraction(UNKNOWN)
    elapsed = time.monotonic() - started

    print(f"{UNKNOWN.name}: method={result.method}, model={ai.MODEL}, {elapsed:.1f}s")
    for note in result.notes:
        print(f"  note: {note}")
    for key, v in result.values.items():
        print(f"  {key:22} {str(v.value):>10}  {v.source:8} {v.confidence:.2f}  {v.evidence[:90]!r}")
    print(f"  pitch_breakdown: {result.pitch_breakdown}")

    ai_values = {k: v for k, v in result.values.items() if v.source == "ai"}
    check(failures, result.method == "generic+ai", f"method is {result.method!r}, expected 'generic+ai'")
    check(failures, bool(ai_values), "AI filled no fields")
    check(failures, not set(ai_values) & set(generic), "AI overwrote fields the generic parser found")
    for key, v in generic.items():
        check(failures, result.values[key].value == v.value and result.values[key].source == "generic",
              f"{key}: generic value changed")
    flat_text = " ".join(text.split())
    for key, v in ai_values.items():
        found = ai.appears_in_text(v.value, text)
        quote = " ".join(v.evidence.replace(NOT_FOUND, "").split())
        check(failures, bool(quote), f"{key}: AI value has no quote")
        # Independent of appears_in_text: the quote must be verbatim and must contain the number.
        check(failures, quote in flat_text, f"{key}: quote is not verbatim in the PDF text: {quote!r}")
        check(failures, re.search(rf"(?<![\d.]){v.value.normalize():f}(?![\d])", quote.replace(",", "")) is not None,
              f"{key}: quote doesn't contain the value {v.value}")
        check(failures, v.confidence == (0.8 if found else 0.4), f"{key}: confidence {v.confidence} (in text: {found})")
        check(failures, (NOT_FOUND in v.evidence) != found, f"{key}: not-found flag doesn't match the PDF text")

    values = {k: v.value for k, v in result.values.items()}
    meta = {k: {"source": v.source, "confidence": v.confidence, "confirmed": False} for k, v in result.values.items()}
    warned = {i["field"] for i in verify(values, result.pitch_breakdown, meta)["issues"] if "read by AI" in i["message"]}
    check(failures, warned == set(ai_values), f"'read by AI' warnings {sorted(warned)} != AI fields {sorted(ai_values)}")


def check_templates_skip_ai(failures: list[str]) -> None:
    pdfs = sorted(SAMPLES.glob("demo_*.pdf"))
    check(failures, len(pdfs) == 3, f"expected 3 demo samples, found {len(pdfs)}")
    for pdf in pdfs:
        result, _ = pipeline.run_extraction(pdf)
        print(f"{pdf.name}: method={result.method}")
        check(failures, result.method == "template", f"{pdf.name}: method {result.method!r}, expected 'template'")


def main() -> int:
    if not ai.ai_available():
        print("AI is unavailable: set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN (backend/.env or the environment)"
              " and don't set AI_EXTRACTION=off.")
        return 2
    failures: list[str] = []
    check_unknown_format(failures)
    check_templates_skip_ai(failures)
    for f in failures:
        print(f"FAIL: {f}")
    print("OK" if not failures else f"{len(failures)} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
