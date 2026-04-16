from __future__ import annotations

from typing import Iterable, List, Tuple

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")


def validate_ohlcv(df: pd.DataFrame, required_cols: Iterable[str] = REQUIRED_OHLCV_COLUMNS) -> Tuple[bool, List[str]]:
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return False, missing
    return True, []


def validate_min_rows(df: pd.DataFrame, min_rows: int = 35) -> bool:
    return len(df.index) >= min_rows

