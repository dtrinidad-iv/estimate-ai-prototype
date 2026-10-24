import os
import tempfile
from pathlib import Path

# Point the app at a throwaway database before anything imports app.db.
_tmp = tempfile.mkdtemp(prefix="estimateai-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ.pop("ANTHROPIC_API_KEY", None)

import pytest  # noqa: E402

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture
def samples() -> Path:
    return SAMPLES
