"""
Batch-invoke a small allowlist of tools in one process (reduces agent round-trips).

Each item: {"id": optional key, "tool": "tool_fetch_...", "args": {...}}
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, List, Optional

_BATCH_IMPORTS = {
    "tool_metrics_snapshot": ("plugins.utils.tool_metrics", "tool_metrics_snapshot"),
    "tool_fetch_limit_up_stocks": ("plugins.data_collection.limit_up.fetch_limit_up", "tool_fetch_limit_up_stocks"),
    "tool_fetch_a_share_fund_flow": ("plugins.data_collection.a_share_fund_flow", "tool_fetch_a_share_fund_flow"),
    "tool_fetch_northbound_flow": ("plugins.data_collection.northbound", "tool_fetch_northbound_flow"),
    "tool_fetch_sector_data": ("plugins.data_collection.sector", "tool_fetch_sector_data"),
    "tool_fetch_market_data": ("plugins.merged.fetch_market_data", "tool_fetch_market_data"),
}


def tool_batch_fetch(items: Optional[List[Dict[str, Any]]] = None, **_: Any) -> Dict[str, Any]:
    items = items or []
    results: Dict[str, Any] = {}
    errors: List[str] = []

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{i}: not an object")
            continue
        tid = str(item.get("tool") or "").strip()
        args = item.get("args") if isinstance(item.get("args"), dict) else {}
        key = str(item.get("id") or tid or f"idx_{i}")
        spec = _BATCH_IMPORTS.get(tid)
        if not spec:
            errors.append(f"{key}: unsupported tool {tid!r}")
            continue
        try:
            mod = importlib.import_module(spec[0])
            fn = getattr(mod, spec[1])
            results[key] = fn(**args)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{key}: {e}")

    return {
        "success": len(errors) == 0,
        "results": results,
        "errors": errors,
        "meta": {"count": len(items), "ok_count": len(results)},
    }
