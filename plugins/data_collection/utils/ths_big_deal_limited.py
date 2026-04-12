"""
同花顺数据中心「大单追踪」分页抓取（限制页数），逻辑同源 AkShare stock_fund_flow_big_deal。

环境变量 BIG_DEAL_THS_MAX_PAGES：最多请求页数（默认 30，上限 500），避免拉全市场全部页导致超时。
"""

from __future__ import annotations

import os
from io import StringIO
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    import py_mini_racer
    from akshare.stock_feature.stock_fund_flow import _get_file_content_ths
except Exception:  # noqa: BLE001
    py_mini_racer = None  # type: ignore[assignment]
    _get_file_content_ths = None  # type: ignore[assignment]


def ths_big_deal_available() -> bool:
    return py_mini_racer is not None and _get_file_content_ths is not None


def ths_big_deal_limited(max_rows: int, max_pages_cap: Optional[int] = None) -> pd.DataFrame:
    """
    返回与同花顺 ddzz 页面结构一致的 DataFrame（列含成交时间、股票代码等），最多 max_rows 行。
    """
    if not ths_big_deal_available():
        raise RuntimeError("py_mini_racer 或 AkShare ths.js 不可用，无法抓取同花顺大单")

    max_rows = max(1, int(max_rows))
    if max_pages_cap is None:
        raw = (os.environ.get("BIG_DEAL_THS_MAX_PAGES") or "30").strip()
        try:
            max_pages_cap = max(1, min(500, int(raw)))
        except ValueError:
            max_pages_cap = 30
    else:
        max_pages_cap = max(1, min(500, int(max_pages_cap)))

    js_code = py_mini_racer.MiniRacer()
    js_content = _get_file_content_ths("ths.js")
    js_code.eval(js_content)
    v_code = js_code.call("v")
    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "hexin-v": v_code,
        "Host": "data.10jqka.com.cn",
        "Pragma": "no-cache",
        "Referer": "http://data.10jqka.com.cn/funds/hyzjl/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    url_meta = "http://data.10jqka.com.cn/funds/ddzz/order/desc/ajax/1/free/1/"
    r = requests.get(url_meta, headers=headers, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, features="lxml")
    page_el = soup.find(name="span", attrs={"class": "page_info"})
    if page_el is None or not page_el.text:
        return pd.DataFrame()
    parts = page_el.text.split("/")
    if len(parts) < 2:
        return pd.DataFrame()
    total_pages = int(parts[1].strip())
    pages_to_fetch = min(total_pages, max_pages_cap)

    url_page = "http://data.10jqka.com.cn/funds/ddzz/order/asc/page/{}/ajax/1/free/1/"
    big_df = pd.DataFrame()
    for page in range(1, pages_to_fetch + 1):
        js_code = py_mini_racer.MiniRacer()
        js_code.eval(_get_file_content_ths("ths.js"))
        v_code = js_code.call("v")
        hdr = dict(headers)
        hdr["hexin-v"] = v_code
        r2 = requests.get(url_page.format(page), headers=hdr, timeout=30)
        r2.raise_for_status()
        temp_df = pd.read_html(StringIO(r2.text))[0]
        big_df = pd.concat([big_df, temp_df], ignore_index=True)
        if len(big_df) >= max_rows:
            break

    if big_df.empty:
        return big_df
    big_df.columns = [
        "成交时间",
        "股票代码",
        "股票简称",
        "成交价格",
        "成交量",
        "成交额",
        "大单性质",
        "涨跌幅",
        "涨跌额",
        "详细",
    ]
    if "详细" in big_df.columns:
        del big_df["详细"]
    return big_df.head(max_rows)
