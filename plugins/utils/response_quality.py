"""
Numeric data quality score (0–100) and optional metadata for tool responses.

See docs/optimization/tool_response_metadata.md for contract.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def _count_primary_records(payload: Dict[str, Any]) -> int:
    """Best-effort row count for scoring."""
    data = payload.get("data")
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for k in ("records", "rows", "items", "bars", "history"):
            v = data.get(k)
            if isinstance(v, list):
                return len(v)
    for k in ("records", "leaders", "signals", "history", "all_data"):
        v = payload.get(k)
        if isinstance(v, list):
            return len(v)
    return 0


def _parse_as_of(as_of: Any) -> Optional[datetime]:
    if as_of is None:
        return None
    s = str(as_of).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d", "%Y%m%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:26], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    except ValueError:
        return None


def compute_quality_score(
    payload: Dict[str, Any],
    *,
    min_records: int = 1,
    intraday_stale_minutes: Optional[int] = None,
    tool_ttl_seconds: Optional[int] = None,
) -> int:
    """
    Weighted deduction from 100. Used for sentiment tools and generic dict responses.
    """
    stale_min = int(
        intraday_stale_minutes
        if intraday_stale_minutes is not None
        else int(os.getenv("OPENCLAW_QUALITY_STALE_MINUTES", "15") or "15")
    )
    score = 100
    success = bool(payload.get("success", True))
    if not success:
        return max(0, 30)

    used_fallback = bool(payload.get("used_fallback"))
    data_quality = str(payload.get("data_quality") or "fresh")

    n = _count_primary_records(payload)

    has_structured_success = bool(
        n > 0
        or (isinstance(payload.get("data"), dict) and payload["data"])
        or (payload.get("cumulative") is not None)
        or (payload.get("signal") is not None and payload.get("signal") != "")
    )
    if not has_structured_success and n == 0:
        score -= 40

    if n > 0 and n < max(1, min_records):
        score -= 20

    if data_quality == "partial":
        score -= 20
    if used_fallback:
        score -= 15

    as_of_dt = _parse_as_of(payload.get("as_of"))
    if as_of_dt is not None:
        age_sec = (datetime.now() - as_of_dt).total_seconds()
        if age_sec > stale_min * 60:
            score -= 25
        elif data_quality == "cached" and tool_ttl_seconds and age_sec > float(tool_ttl_seconds):
            score -= 25

    gate = payload.get("quality_gate")
    if isinstance(gate, dict) and gate.get("ok") is False:
        score -= 10

    return max(0, min(100, int(score)))


def enrich_response_dict(
    payload: Dict[str, Any],
    *,
    min_records: int = 1,
    tool_ttl_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Mutates and returns payload: quality_score, data_generated_at alias."""
    qs = compute_quality_score(payload, min_records=min_records, tool_ttl_seconds=tool_ttl_seconds)
    payload["quality_score"] = qs
    ao = payload.get("as_of")
    if ao is not None and str(ao).strip():
        payload["data_generated_at"] = str(ao).strip()
    return payload
