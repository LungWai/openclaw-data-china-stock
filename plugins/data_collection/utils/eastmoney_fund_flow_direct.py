"""
东方财富资金流向：HTTP 直连 + AkShare request_with_retry（与行情工具一致配合 without_proxy_env 使用）。

当前提供：
- 大盘 / 个股日 K 资金流（push2his）
- push2 clist 分页截断（主力排名、**大单语义代理**：按 f72 大单净流入排序的全 A 快照等）
- 个股/板块「排名」类复杂列仍以 AkShare 为准；本模块只做可安全截断的 clist 场景。
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List

import pandas as pd

try:
    from akshare.utils.request import request_with_retry
except Exception:  # noqa: BLE001
    request_with_retry = None  # type: ignore[assignment]

_PUSH2 = "https://push2.eastmoney.com/api/qt/clist/get"
_PUSH2HIS = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
_UT = "b2884a393a59ad64002292a3e90d46a5"


def em_http_available() -> bool:
    return request_with_retry is not None


def _get_json(url: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    if request_with_retry is None:
        raise RuntimeError("akshare.utils.request.request_with_retry 不可用")
    r = request_with_retry(url, params=params, timeout=timeout)
    return r.json()


def clist_fetch_pages_limited(
    base_params: Dict[str, Any],
    max_rows: int,
    timeout: int = 20,
) -> pd.DataFrame:
    """东财 push2/clist：只拉取前 ceil(max_rows/100) 页。"""
    max_rows = max(1, int(max_rows))
    params = dict(base_params)
    params["pz"] = "100"
    params["pn"] = "1"
    j = _get_json(_PUSH2, params, timeout=timeout)
    data = j.get("data") or {}
    diff = data.get("diff") or []
    if not diff:
        return pd.DataFrame()
    total = int(data.get("total") or 0)
    per = len(diff)
    total_page = max(1, math.ceil(total / per)) if total else 1
    max_page = max(1, min(total_page, math.ceil(max_rows / per)))
    frames: List[pd.DataFrame] = [pd.DataFrame(diff)]
    for page in range(2, max_page + 1):
        params["pn"] = str(page)
        j2 = _get_json(_PUSH2, params, timeout=timeout)
        d2 = (j2.get("data") or {}).get("diff") or []
        if not d2:
            break
        frames.append(pd.DataFrame(d2))
    out = pd.concat(frames, ignore_index=True)
    return out.head(max_rows)


def stock_market_fund_flow_direct(timeout: int = 20) -> pd.DataFrame:
    """沪深两市大盘资金流日 K（同源 AkShare stock_market_fund_flow）。"""
    params = {
        "lmt": "0",
        "klt": "101",
        "secid": "1.000001",
        "secid2": "0.399001",
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
        "ut": _UT,
        "_": int(time.time() * 1000),
    }
    j = _get_json(_PUSH2HIS, params, timeout=timeout)
    content_list = (j.get("data") or {}).get("klines") or []
    if not content_list:
        return pd.DataFrame()
    temp_df = pd.DataFrame([item.split(",") for item in content_list])
    temp_df.columns = [
        "日期",
        "主力净流入-净额",
        "小单净流入-净额",
        "中单净流入-净额",
        "大单净流入-净额",
        "超大单净流入-净额",
        "主力净流入-净占比",
        "小单净流入-净占比",
        "中单净流入-净占比",
        "大单净流入-净占比",
        "超大单净流入-净占比",
        "上证-收盘价",
        "上证-涨跌幅",
        "深证-收盘价",
        "深证-涨跌幅",
    ]
    temp_df = temp_df[
        [
            "日期",
            "上证-收盘价",
            "上证-涨跌幅",
            "深证-收盘价",
            "深证-涨跌幅",
            "主力净流入-净额",
            "主力净流入-净占比",
            "超大单净流入-净额",
            "超大单净流入-净占比",
            "大单净流入-净额",
            "大单净流入-净占比",
            "中单净流入-净额",
            "中单净流入-净占比",
            "小单净流入-净额",
            "小单净流入-净占比",
        ]
    ]
    for c in temp_df.columns:
        if c != "日期":
            temp_df[c] = pd.to_numeric(temp_df[c], errors="coerce")
    temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.date
    return temp_df


def stock_individual_fund_flow_direct(stock: str, market: str, timeout: int = 20) -> pd.DataFrame:
    """个股日 K 资金流（同源 AkShare stock_individual_fund_flow）。"""
    market_map = {"sh": 1, "sz": 0, "bj": 0}
    m = (market or "sh").lower()
    if m not in market_map:
        m = "sh"
    params = {
        "lmt": "0",
        "klt": "101",
        "secid": f"{market_map[m]}.{stock}",
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
        "ut": _UT,
        "_": int(time.time() * 1000),
    }
    j = _get_json(_PUSH2HIS, params, timeout=timeout)
    content_list = (j.get("data") or {}).get("klines") or []
    if not content_list:
        return pd.DataFrame()
    temp_df = pd.DataFrame([item.split(",") for item in content_list])
    temp_df.columns = [
        "日期",
        "主力净流入-净额",
        "小单净流入-净额",
        "中单净流入-净额",
        "大单净流入-净额",
        "超大单净流入-净额",
        "主力净流入-净占比",
        "小单净流入-净占比",
        "中单净流入-净占比",
        "大单净流入-净占比",
        "超大单净流入-净占比",
        "收盘价",
        "涨跌幅",
        "-",
        "-",
    ]
    temp_df = temp_df[
        [
            "日期",
            "收盘价",
            "涨跌幅",
            "主力净流入-净额",
            "主力净流入-净占比",
            "超大单净流入-净额",
            "超大单净流入-净占比",
            "大单净流入-净额",
            "大单净流入-净占比",
            "中单净流入-净额",
            "中单净流入-净占比",
            "小单净流入-净额",
            "小单净流入-净占比",
        ]
    ]
    temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.date
    for c in temp_df.columns:
        if c != "日期":
            temp_df[c] = pd.to_numeric(temp_df[c], errors="coerce")
    return temp_df


def stock_main_fund_flow_limited(symbol: str, max_rows: int, timeout: int = 20) -> pd.DataFrame:
    """
    主力净流入排名（东财 push2），限制行数；列名与 AkShare stock_main_fund_flow 对齐。
    """
    symbol_map = {
        "全部股票": "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2",
        "沪深A股": "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2",
        "沪市A股": "m:1+t:2+f:!2,m:1+t:23+f:!2",
        "科创板": "m:1+t:23+f:!2",
        "深市A股": "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2",
        "创业板": "m:0+t:80+f:!2",
        "沪市B股": "m:1+t:3+f:!2",
        "深市B股": "m:0+t:7+f:!2",
    }
    if symbol not in symbol_map:
        raise ValueError(f"unsupported main_force symbol {symbol!r}")
    params = {
        "fid": "f184",
        "po": "1",
        "pz": "100",
        "pn": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fields": "f2,f3,f12,f13,f14,f62,f184,f225,f165,f263,f109,f175,f264,f160,f100,f124,f265,f1",
        "ut": _UT,
        "fs": symbol_map[symbol],
    }
    raw = clist_fetch_pages_limited(params, max_rows, timeout=timeout)
    if raw.empty:
        return raw
    raw.rename(
        columns={
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f184": "今日排行榜-主力净占比",
            "f225": "今日排行榜-今日排名",
            "f3": "今日排行榜-今日涨跌",
            "f165": "5日排行榜-主力净占比",
            "f263": "5日排行榜-5日排名",
            "f109": "5日排行榜-5日涨跌",
            "f175": "10日排行榜-主力净占比",
            "f264": "10日排行榜-10日排名",
            "f160": "10日排行榜-10日涨跌",
            "f100": "所属板块",
        },
        inplace=True,
    )
    cols = [
        "代码",
        "名称",
        "最新价",
        "今日排行榜-主力净占比",
        "今日排行榜-今日排名",
        "今日排行榜-今日涨跌",
        "5日排行榜-主力净占比",
        "5日排行榜-5日排名",
        "5日排行榜-5日涨跌",
        "10日排行榜-主力净占比",
        "10日排行榜-10日排名",
        "10日排行榜-10日涨跌",
        "所属板块",
    ]
    keep = [c for c in cols if c in raw.columns]
    out = raw[keep].copy()
    out.insert(0, "序号", range(1, len(out) + 1))
    for c in out.columns:
        if c not in ("代码", "名称", "所属板块", "序号"):
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def eastmoney_big_deal_proxy_limited(max_rows: int, timeout: int = 20) -> pd.DataFrame:
    """
    东财侧「大单」语义替代（非同花顺逐笔大单明细）：

    使用 push2/clist 全 A 股列表，按 **今日大单净流入-净额 (f72)** 排序，只拉取前若干页。
    与 `stock_fund_flow_big_deal` 的「成交时间/单笔成交额」字段不同，适合作为公开分发时的稳定兜底。
    """
    max_rows = max(1, int(max_rows))
    fields = "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124"
    params: Dict[str, Any] = {
        "fid": "f72",
        "po": "1",
        "pz": "100",
        "pn": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "ut": _UT,
        "fs": "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2",
        "fields": fields,
    }
    raw = clist_fetch_pages_limited(params, max_rows, timeout=timeout)
    if raw.empty:
        return raw
    mapping = {
        "f12": "代码",
        "f14": "名称",
        "f2": "最新价",
        "f3": "今日涨跌幅",
        "f62": "今日主力净流入-净额",
        "f184": "今日主力净流入-净占比",
        "f66": "今日超大单净流入-净额",
        "f69": "今日超大单净流入-净占比",
        "f72": "今日大单净流入-净额",
        "f75": "今日大单净流入-净占比",
        "f78": "今日中单净流入-净额",
        "f81": "今日中单净流入-净占比",
        "f84": "今日小单净流入-净额",
        "f87": "今日小单净流入-净占比",
    }
    out = raw.rename(columns={k: v for k, v in mapping.items() if k in raw.columns})
    for c in out.columns:
        if c not in ("代码", "名称"):
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.head(max_rows)
