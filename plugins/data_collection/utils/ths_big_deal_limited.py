"""
同花顺「大单追踪」受限拉取。

安全说明：
- 旧实现通过执行 ths.js 计算请求签名，触发安全扫描对“动态代码执行”的高风险告警。
- 现改为直接复用 AkShare 的公开接口并在本地截断行数，不在本仓库内执行任何动态 JS 代码。
"""

from __future__ import annotations

import os
from typing import Optional

import akshare as ak
import pandas as pd
import numpy as np


def ths_big_deal_limited(max_rows: int, max_pages_cap: Optional[int] = None) -> pd.DataFrame:
    """
    返回与同花顺 ddzz 页面结构一致的 DataFrame（列含成交时间、股票代码等），最多 max_rows 行。
    """
    max_rows = max(1, int(max_rows))
    # 保留环境变量兼容（不再用于分页抓取，只作为最终行数保护上限）
    if max_pages_cap is None:
        raw = (os.environ.get("BIG_DEAL_THS_MAX_PAGES") or "30").strip()
        try:
            max_pages_cap = max(1, min(500, int(raw)))
        except ValueError:
            max_pages_cap = 30
    else:
        max_pages_cap = max(1, min(500, int(max_pages_cap)))

    hard_cap = max_rows if max_pages_cap is None else min(max_rows, max_pages_cap * 100)
    try:
        big_df = ak.stock_fund_flow_big_deal()
    except Exception as exc:  # pragma: no cover - network dependent
        raise RuntimeError(f"AkShare stock_fund_flow_big_deal failed: {exc}") from exc

    if big_df.empty:
        return big_df

    # 与历史下游保持兼容：确保常见列存在，缺失则补空值。
    expected_cols = [
        "成交时间",
        "股票代码",
        "股票简称",
        "成交价格",
        "成交量",
        "成交额",
        "大单性质",
        "涨跌幅",
        "涨跌额",
    ]
    for col in expected_cols:
        if col not in big_df.columns:
            big_df[col] = np.nan
    return big_df[expected_cols].head(hard_cap)
