"""
In-process tool / cache metrics for observability (tool_metrics_snapshot).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, DefaultDict, Dict, List

_lock = threading.RLock()
_window_start = time.perf_counter()
_since_iso: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

_cache_hits = 0
_cache_misses = 0
_tool_calls: DefaultDict[str, int] = defaultdict(int)
_tool_errors: DefaultDict[str, int] = defaultdict(int)
_elapsed_sum_ms: DefaultDict[str, float] = defaultdict(float)


def reset_window() -> None:
    global _window_start, _since_iso, _cache_hits, _cache_misses, _tool_calls, _tool_errors, _elapsed_sum_ms
    with _lock:
        _window_start = time.perf_counter()
        _since_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _cache_hits = 0
        _cache_misses = 0
        _tool_calls = defaultdict(int)
        _tool_errors = defaultdict(int)
        _elapsed_sum_ms = defaultdict(float)


def record_cache_hit() -> None:
    global _cache_hits
    with _lock:
        _cache_hits += 1


def record_cache_miss() -> None:
    global _cache_misses
    with _lock:
        _cache_misses += 1


def record_tool_call(tool: str, elapsed_ms: int, *, ok: bool) -> None:
    with _lock:
        _tool_calls[tool] += 1
        _elapsed_sum_ms[tool] += float(max(0, elapsed_ms))
        if not ok:
            _tool_errors[tool] += 1


def build_snapshot() -> Dict[str, Any]:
    with _lock:
        total = max(1, _cache_hits + _cache_misses)
        hit_rate = round(_cache_hits / total, 4)
        avg_elapsed: Dict[str, int] = {}
        err_rate: Dict[str, float] = {}
        for t, n in _tool_calls.items():
            if n <= 0:
                continue
            avg_elapsed[t] = int(round(_elapsed_sum_ms[t] / n))
            err_rate[t] = round(_tool_errors.get(t, 0) / n, 4)
        return {
            "cache_hit_rate": hit_rate,
            "avg_elapsed_ms_by_tool": avg_elapsed,
            "error_rate_by_tool": err_rate,
            "since": _since_iso,
            "cache_hits": _cache_hits,
            "cache_misses": _cache_misses,
        }


def tool_metrics_snapshot(reset: bool = False) -> Dict[str, Any]:
    """MCP tool: return in-process cache/tool counters (see docs/optimization/tool_response_metadata.md)."""
    if reset:
        reset_window()
    snap = build_snapshot()
    return {"success": True, **snap}
