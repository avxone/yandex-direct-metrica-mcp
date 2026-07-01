from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_wordstat_access.py"
    spec = importlib.util.spec_from_file_location("check_wordstat_access", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_monthly_windows_tries_recent_then_buffered_month() -> None:
    module = _load_module()
    windows = module._monthly_windows(dt.date(2026, 7, 1))
    assert windows == [("2026-06", "2026-06-30"), ("2026-05", "2026-05-31")]


def test_monthly_windows_crosses_year_boundary() -> None:
    module = _load_module()
    windows = module._monthly_windows(dt.date(2026, 1, 3))
    assert windows == [("2025-12", "2025-12-31"), ("2025-11", "2025-11-30")]
