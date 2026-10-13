import datetime
import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.main import create_pathway_sink


def test_sink_native_keywords_and_deletion():
    row = {"source": "regression", "data": {"event_id": "sink-contract"}, "location": {}}
    with patch("src.main.ingest_runtime_event") as ingest:
        sink = create_pathway_sink({})
        sink(key="row-1", row=row, time=2, is_addition=False)
        ingest.assert_not_called()
        sink(key="row-1", row=row, time=4, is_addition=True)
        ingest.assert_called_once_with(row, {})


def test_nonempty_subscription_stream():
    """Runs a real ConnectorSubject, anomaly UDF and production sink in isolation."""
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "tests" / "stream_regression.py")],
                            cwd=root, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "STREAM_REGRESSION_OK events=2" in result.stdout


@pytest.mark.skipif(importlib.util.find_spec("pathway") is None, reason="Native Pathway requires Linux/macOS; unavailable on this Windows host")
def test_native_pathway_0330_stream():
    import pathway
    assert pathway.__version__ == "0.33.0"
    test_nonempty_subscription_stream()
