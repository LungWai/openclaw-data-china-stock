from __future__ import annotations

from typing import Dict

import pandas as pd


def apply_alignment(df: pd.DataFrame, alignment: Dict[str, float] | None = None) -> dict:
    """
    Apply local-market alignment rules.
    Current rule:
    - MACD diff/hist can be multiplied by `macd_factor` (default 2.0).
    """
    cfg = alignment or {}
    macd_factor = float(cfg.get("macd_factor", 2.0))
    applied: dict = {"macd_factor": macd_factor}

    if "macd_diff" in df.columns:
        df["macd_diff"] = df["macd_diff"] * macd_factor
    if "macd_hist" in df.columns:
        df["macd_hist"] = df["macd_hist"] * macd_factor

    return applied

