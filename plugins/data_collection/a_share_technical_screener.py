"""
A 股技术选股排名表（同花顺数据中心 / AkShare stock_rank_*_ths）。

工具：tool_fetch_a_share_technical_screener
对应 AkShare 文档「A 股 · 技术指标」下的选股表（创新高、连续上涨、量价齐升等），
非本地 K 线计算 MACD/RSI（请用 tool_stock_data_fetcher / tool_calculate_technical_indicators）。
原始数据非投资建议；口径以同花顺为准。
"""

from __future__ import annotations

import concurrent.futures
import logging
import math
import os
import re
from contextlib import nullcontext
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import akshare as ak

    AKSHARE_AVAILABLE = True
except Exception:  # noqa: BLE001
    ak = None  # type: ignore[assignment]
    AKSHARE_AVAILABLE = False

try:
    from plugins.utils.proxy_env import without_proxy_env

    PROXY_ENV_AVAILABLE = True
except Exception:  # noqa: BLE001
    PROXY_ENV_AVAILABLE = False

    def without_proxy_env(*args: Any, **kwargs: Any):  # type: ignore[no-redef]
        return nullcontext()

LIMIT_DEFAULT = 80
LIMIT_CAP = 200
_TIMEOUT_DEFAULT_SEC = 180.0

SCREENER_KINDS = frozenset(
    {
        "new_high",
        "new_low",
        "continuous_up",
        "continuous_down",
        "volume_expansion",
        "volume_contraction",
        "breakout_up",
        "breakout_down",
        "price_volume_up",
        "price_volume_down",
        "insurance_holding_raise",
    }
)

# screener_kind -> (ak 属性名, 是否需要 variant: high_low | breakout_ma | none)
_AK_MAP: Dict[str, Tuple[str, str]] = {
    "new_high": ("stock_rank_cxg_ths", "high_low"),
    "new_low": ("stock_rank_cxd_ths", "high_low"),
    "continuous_up": ("stock_rank_lxsz_ths", "none"),
    "continuous_down": ("stock_rank_lxxd_ths", "none"),
    "volume_expansion": ("stock_rank_cxfl_ths", "none"),
    "volume_contraction": ("stock_rank_cxsl_ths", "none"),
    "breakout_up": ("stock_rank_xstp_ths", "breakout_ma"),
    "breakout_down": ("stock_rank_xxtp_ths", "breakout_ma"),
    "price_volume_up": ("stock_rank_ljqs_ths", "none"),
    "price_volume_down": ("stock_rank_ljqd_ths", "none"),
    "insurance_holding_raise": ("stock_rank_xzjp_ths", "none"),
}

_HIGH_VARIANT: Dict[str, str] = {
    "month": "创月新高",
    "half_year": "半年新高",
    "year": "一年新高",
    "all_time": "历史新高",
}

_LOW_VARIANT: Dict[str, str] = {
    "month": "创月新低",
    "half_year": "半年新低",
    "year": "一年新低",
    "all_time": "历史新低",
}

_MA_VARIANT: Dict[str, str] = {
    "ma5": "5日均线",
    "ma10": "10日均线",
    "ma20": "20日均线",
    "ma30": "30日均线",
    "ma60": "60日均线",
    "ma90": "90日均线",
    "ma250": "250日均线",
    "ma500": "500日均线",
}


def _timeout_sec() -> float:
    for key in ("AKSHARE_TECH_SCREENER_TIMEOUT_SEC", "AKSHARE_FUND_FLOW_ATTEMPT_TIMEOUT_SEC"):
        raw = (os.environ.get(key) or "").strip()
        if raw:
            try:
                return max(5.0, float(raw))
            except ValueError:
                continue
    return _TIMEOUT_DEFAULT_SEC


def _clip_limit(n: Any) -> int:
    try:
        x = int(n)
    except (TypeError, ValueError):
        x = LIMIT_DEFAULT
    return max(1, min(x, LIMIT_CAP))


_BAD_SEQ_LABELS = frozenset(
    {"序号", "股票代码", "代码", "名称", "股票简称", "nan", "none"}
)


def _sanitize_ths_rank_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    AkShare read_html 偶发把表头或错列拼进首行（如 序号=「序号」、股票简称=六位数字）。
    在 limit 截取前剔除明显无效行。
    """
    if df is None or getattr(df, "empty", True):
        return df
    out = df.copy()
    mask = pd.Series(True, index=out.index)

    if "序号" in out.columns:
        seq = out["序号"].map(lambda x: str(x).strip().lower() if pd.notna(x) else "")
        mask &= ~seq.isin({s.lower() for s in _BAD_SEQ_LABELS})
        mask &= ~seq.eq("")

    if "股票简称" in out.columns:
        name = out["股票简称"].map(lambda x: str(x).strip() if pd.notna(x) else "")
        mask &= ~name.str.fullmatch(r"\d{6}", na=False)

    if "股票代码" in out.columns:

        def _code_looks_valid(v: Any) -> bool:
            if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                return False
            t = str(v).strip()
            if t in ("股票代码", "代码"):
                return False
            if t.endswith(".0") and t[:-2].isdigit():
                t = t[:-2]
            return bool(re.fullmatch(r"\d{1,6}", t))

        mask &= out["股票代码"].map(_code_looks_valid)

    out = out.loc[mask].reset_index(drop=True)
    dropped = len(df) - len(out)
    if dropped:
        logger.info("technical_screener: dropped %s invalid html row(s)", dropped)
    return out


def _df_to_records(df: Optional[pd.DataFrame], limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    if df is None or getattr(df, "empty", True):
        return [], []
    df = df.head(_clip_limit(limit)).copy()
    df = df.where(pd.notnull(df), None)
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
    records = df.to_dict(orient="records")
    for row in records:
        for k, v in list(row.items()):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                row[k] = None
    return records, [str(c) for c in df.columns]


def _normalize_stock_codes(records: List[Dict[str, Any]], columns: List[str]) -> None:
    code_cols = [c for c in columns if "代码" in c]
    for row in records:
        for c in code_cols:
            v = row.get(c)
            if v is None:
                continue
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)) and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                row[c] = str(int(v)).zfill(6)
            elif isinstance(v, str) and v.isdigit() and len(v) <= 6:
                row[c] = v.zfill(6)


def _resolve_variant(kind: str, vkind: str, variant: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Returns (chinese_for_ak, error_message)."""
    raw = (variant or "").strip().lower().replace("-", "_")
    if vkind == "none":
        return None, None
    if vkind == "high_low":
        key = raw or "month"
        table = _HIGH_VARIANT if kind == "new_high" else _LOW_VARIANT
        if key not in table:
            return None, f"invalid variant for {kind!r}: {variant!r}; expected one of {sorted(table)}"
        return table[key], None
    if vkind == "breakout_ma":
        key = raw or "ma20"
        if key not in _MA_VARIANT:
            return None, f"invalid variant for {kind!r}: {variant!r}; expected one of {sorted(_MA_VARIANT)}"
        return _MA_VARIANT[key], None
    return None, "internal: unknown vkind"


def _call_df_with_timeout(fn: Callable[[], pd.DataFrame], timeout_sec: float) -> pd.DataFrame:
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        fut = ex.submit(fn)
        return fut.result(timeout=timeout_sec)
    finally:
        ex.shutdown(wait=False, cancel_futures=False)


def _build_caller(kind: str) -> Tuple[Callable[[], pd.DataFrame], str]:
    ak_name, vkind = _AK_MAP[kind]
    if not AKSHARE_AVAILABLE or ak is None:
        raise RuntimeError("akshare not available")
    fn = getattr(ak, ak_name, None)
    if fn is None or not callable(fn):
        raise RuntimeError(f"akshare missing callable {ak_name!r}")
    return fn, vkind


def tool_fetch_a_share_technical_screener(
    screener_kind: str,
    variant: str = "",
    limit: int = LIMIT_DEFAULT,
) -> Dict[str, Any]:
    """
    拉取同花顺技术选股排名表（AkShare stock_rank_*_ths）。

    screener_kind：new_high | new_low | continuous_up | continuous_down |
        volume_expansion | volume_contraction | breakout_up | breakout_down |
        price_volume_up | price_volume_down | insurance_holding_raise

    variant：new_high/new_low 用 month|half_year|year|all_time；
             breakout_up/breakout_down 用 ma5…ma500；其余忽略。

    环境变量：AKSHARE_TECH_SCREENER_TIMEOUT_SEC（优先），否则 AKSHARE_FUND_FLOW_ATTEMPT_TIMEOUT_SEC，默认 180。
    """
    sk = (screener_kind or "").strip().lower()
    params_echo: Dict[str, Any] = {
        "screener_kind": sk,
        "variant": (variant or "").strip(),
        "limit": _clip_limit(limit),
    }

    if sk not in SCREENER_KINDS:
        return {
            "success": False,
            "error": f"invalid screener_kind: {screener_kind!r}",
            "params_echo": params_echo,
            "hint": f"expected one of {sorted(SCREENER_KINDS)}",
        }

    if not AKSHARE_AVAILABLE:
        return {
            "success": False,
            "error": "akshare not installed",
            "params_echo": params_echo,
        }

    try:
        fn_base, vkind = _build_caller(sk)
    except RuntimeError as e:
        return {"success": False, "error": str(e), "params_echo": params_echo}

    var_cn, verr = _resolve_variant(sk, vkind, variant)
    if verr:
        return {"success": False, "error": verr, "params_echo": params_echo}

    def invoke() -> pd.DataFrame:
        if var_cn is None:
            return fn_base()
        return fn_base(symbol=var_cn)

    ak_attr = _AK_MAP[sk][0]
    source = f"akshare.{ak_attr}"
    timeout_sec = _timeout_sec()
    ctx = without_proxy_env() if PROXY_ENV_AVAILABLE else nullcontext()
    try:
        with ctx:
            df = _call_df_with_timeout(invoke, timeout_sec)
    except concurrent.futures.TimeoutError:
        return {
            "success": False,
            "error": f"timeout after {timeout_sec:.0f}s",
            "params_echo": params_echo,
            "source": source,
            "variant_effective": var_cn,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning("technical_screener %s failed: %s", sk, e)
        return {
            "success": False,
            "error": str(e)[:500],
            "params_echo": params_echo,
            "source": source,
            "variant_effective": var_cn,
        }

    lim = _clip_limit(limit)
    if df is None or getattr(df, "empty", True):
        return {
            "success": True,
            "screener_kind": sk,
            "variant_effective": var_cn,
            "provider_preference": "ths",
            "params_echo": params_echo,
            "source": source,
            "row_count": 0,
            "columns": [],
            "records": [],
            "disclaimer_cn": "原始数据非投资建议；口径以同花顺页面为准。",
        }

    raw_row_count = len(df)
    df = _sanitize_ths_rank_df(df)
    sanitized_drop_count = raw_row_count - len(df)

    if getattr(df, "empty", True):
        return {
            "success": True,
            "screener_kind": sk,
            "variant_effective": var_cn,
            "provider_preference": "ths",
            "params_echo": params_echo,
            "source": source,
            "row_count": 0,
            "total_rows_raw": raw_row_count,
            "sanitized_row_drop_count": sanitized_drop_count,
            "columns": [],
            "records": [],
            "disclaimer_cn": "原始数据非投资建议；口径以同花顺页面为准。",
        }

    full_rows = len(df)
    records, columns = _df_to_records(df, lim)
    _normalize_stock_codes(records, columns)

    out: Dict[str, Any] = {
        "success": True,
        "screener_kind": sk,
        "variant_effective": var_cn,
        "provider_preference": "ths",
        "params_echo": params_echo,
        "source": source,
        "row_count": len(records),
        "total_rows_raw": raw_row_count,
        "total_rows_before_limit": full_rows,
        "columns": columns,
        "records": records,
        "disclaimer_cn": "原始数据非投资建议；口径以同花顺页面为准。",
    }
    if sanitized_drop_count:
        out["sanitized_row_drop_count"] = sanitized_drop_count
    return out
