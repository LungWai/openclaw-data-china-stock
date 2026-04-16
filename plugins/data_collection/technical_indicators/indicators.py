from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def _series(df: pd.DataFrame, key: str) -> pd.Series:
    return pd.to_numeric(df[key], errors="coerce").astype("float64")


def calculate_p0_indicators(df: pd.DataFrame, engine: str, talib_mod: object | None, pandas_ta_mod: object | None) -> pd.DataFrame:
    close = _series(df, "close")
    high = _series(df, "high")
    low = _series(df, "low")
    volume = _series(df, "volume")

    out = df.copy()
    if engine == "talib" and talib_mod is not None:
        ta = talib_mod
        out["sma_20"] = ta.SMA(close, timeperiod=20)
        out["ema_20"] = ta.EMA(close, timeperiod=20)
        macd, macd_signal, macd_hist = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        out["macd_diff"] = macd
        out["macd_dea"] = macd_signal
        out["macd_hist"] = macd_hist
        out["adx_14"] = ta.ADX(high, low, close, timeperiod=14)
        out["wma_20"] = ta.WMA(close, timeperiod=20)
        out["dema_20"] = ta.DEMA(close, timeperiod=20)
        out["tema_20"] = ta.TEMA(close, timeperiod=20)
        out["sar"] = ta.SAR(high, low, acceleration=0.02, maximum=0.2)
        out["rsi_14"] = ta.RSI(close, timeperiod=14)
        k, d = ta.STOCH(high, low, close)
        out["kdj_k"] = k
        out["kdj_d"] = d
        out["kdj_j"] = 3 * out["kdj_k"] - 2 * out["kdj_d"]
        sfk, sfd = ta.STOCHF(high, low, close)
        out["stochf_k"] = sfk
        out["stochf_d"] = sfd
        out["cci_14"] = ta.CCI(high, low, close, timeperiod=14)
        out["willr_14"] = ta.WILLR(high, low, close, timeperiod=14)
        out["mom_10"] = ta.MOM(close, timeperiod=10)
        out["roc_10"] = ta.ROC(close, timeperiod=10)
        up, mid, dn = ta.BBANDS(close, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0)
        out["bb_upper"] = up
        out["bb_middle"] = mid
        out["bb_lower"] = dn
        out["atr_14"] = ta.ATR(high, low, close, timeperiod=14)
        out["natr_14"] = ta.NATR(high, low, close, timeperiod=14)
        # P1 volume + trend extension
        out["obv"] = ta.OBV(close, volume)
        out["mfi_14"] = ta.MFI(high, low, close, volume, timeperiod=14)
        out["ad"] = ta.AD(high, low, close, volume)
        out["adosc"] = ta.ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)
        out["trima_20"] = ta.TRIMA(close, timeperiod=20)
        out["kama_30"] = ta.KAMA(close, timeperiod=30)
        out["apo_12_26"] = ta.APO(close, fastperiod=12, slowperiod=26, matype=0)
        out["ppo_12_26"] = ta.PPO(close, fastperiod=12, slowperiod=26, matype=0)
        out["dx_14"] = ta.DX(high, low, close, timeperiod=14)
        out["ht_trendline"] = ta.HT_TRENDLINE(close)
        # P2 pattern recognition (20)
        _apply_cdl_talib(out, ta, high, low, close, _series(df, "open"))
        # P2 statistics / others (6)
        out["beta_hl_20"] = ta.BETA(high, low, timeperiod=20)
        out["correl_hl_20"] = ta.CORREL(high, low, timeperiod=20)
        out["linearreg_14"] = ta.LINEARREG(close, timeperiod=14)
        out["linearreg_slope_14"] = ta.LINEARREG_SLOPE(close, timeperiod=14)
        out["linearreg_angle_14"] = ta.LINEARREG_ANGLE(close, timeperiod=14)
        out["stddev_20"] = ta.STDDEV(close, timeperiod=20, nbdev=1.0)
        # P2 volatility supplements (3)
        out["trange"] = ta.TRANGE(high, low, close)
        out["ht_dcperiod"] = ta.HT_DCPERIOD(close)
        out["ht_dcphase"] = ta.HT_DCPHASE(close)
        return out

    if engine == "pandas_ta" and pandas_ta_mod is not None:
        pta = pandas_ta_mod
        out["sma_20"] = pta.sma(close, length=20)
        out["ema_20"] = pta.ema(close, length=20)
        macd_df = pta.macd(close, fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            out["macd_diff"] = macd_df.iloc[:, 0]
            out["macd_hist"] = macd_df.iloc[:, 1]
            out["macd_dea"] = macd_df.iloc[:, 2]
        out["adx_14"] = pta.adx(high, low, close, length=14).iloc[:, 0]
        out["wma_20"] = pta.wma(close, length=20)
        out["dema_20"] = pta.dema(close, length=20)
        out["tema_20"] = pta.tema(close, length=20)
        out["sar"] = pta.psar(high, low, close).iloc[:, 0]
        out["rsi_14"] = pta.rsi(close, length=14)
        stoch_df = pta.stoch(high, low, close)
        out["kdj_k"] = stoch_df.iloc[:, 0]
        out["kdj_d"] = stoch_df.iloc[:, 1]
        out["kdj_j"] = 3 * out["kdj_k"] - 2 * out["kdj_d"]
        out["stochf_k"] = out["kdj_k"]
        out["stochf_d"] = out["kdj_d"]
        out["cci_14"] = pta.cci(high, low, close, length=14)
        out["willr_14"] = pta.willr(high, low, close, length=14)
        out["mom_10"] = pta.mom(close, length=10)
        out["roc_10"] = pta.roc(close, length=10)
        bb_df = pta.bbands(close, length=20, std=2.0)
        if bb_df is not None and not bb_df.empty:
            out["bb_lower"] = bb_df.iloc[:, 0]
            out["bb_middle"] = bb_df.iloc[:, 1]
            out["bb_upper"] = bb_df.iloc[:, 2]
        out["atr_14"] = pta.atr(high, low, close, length=14)
        out["natr_14"] = pta.natr(high, low, close, length=14)
        # P1 volume + trend extension
        out["obv"] = pta.obv(close, volume)
        out["mfi_14"] = pta.mfi(high, low, close, volume, length=14)
        out["ad"] = pta.ad(high, low, close, volume)
        out["adosc"] = pta.adosc(high, low, close, volume, fast=3, slow=10)
        out["trima_20"] = pta.trima(close, length=20)
        out["kama_30"] = pta.kama(close, length=30)
        out["apo_12_26"] = pta.apo(close, fast=12, slow=26)
        out["ppo_12_26"] = pta.ppo(close, fast=12, slow=26).iloc[:, 0]
        adx_df = pta.adx(high, low, close, length=14)
        out["dx_14"] = adx_df.iloc[:, 1] if adx_df is not None and not adx_df.empty and adx_df.shape[1] > 1 else np.nan
        out["ht_trendline"] = pta.ema(close, length=7)
        # P2 pattern recognition (20): use TA-Lib if present, otherwise placeholder NaN
        if talib_mod is not None:
            _apply_cdl_talib(out, talib_mod, high, low, close, _series(df, "open"))
        else:
            _apply_cdl_placeholder(out)
        # P2 statistics / others (6)
        out["beta_hl_20"] = high.rolling(20).cov(low) / low.rolling(20).var().replace(0, np.nan)
        out["correl_hl_20"] = high.rolling(20).corr(low)
        lin = pta.linreg(close, length=14)
        out["linearreg_14"] = lin if lin is not None else np.nan
        out["linearreg_slope_14"] = pta.slope(close, length=14)
        out["linearreg_angle_14"] = np.degrees(np.arctan(out["linearreg_slope_14"]))
        out["stddev_20"] = close.rolling(20).std()
        # P2 volatility supplements (3)
        out["trange"] = pta.true_range(high, low, close)
        out["ht_dcperiod"] = pta.ema(close, length=10)
        out["ht_dcphase"] = np.degrees(np.arctan(close.diff()))
        return out

    if engine == "builtin":
        out["sma_20"] = close.rolling(20).mean()
        out["ema_20"] = close.ewm(span=20, adjust=False).mean()
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        out["macd_diff"] = ema12 - ema26
        out["macd_dea"] = out["macd_diff"].ewm(span=9, adjust=False).mean()
        out["macd_hist"] = out["macd_diff"] - out["macd_dea"]
        out["adx_14"] = _adx_builtin(high, low, close, 14)
        out["wma_20"] = close.rolling(20).apply(lambda x: np.dot(x, np.arange(1, len(x) + 1)) / np.arange(1, len(x) + 1).sum(), raw=True)
        out["dema_20"] = 2 * out["ema_20"] - out["ema_20"].ewm(span=20, adjust=False).mean()
        out["tema_20"] = 3 * out["ema_20"] - 3 * out["ema_20"].ewm(span=20, adjust=False).mean() + out["ema_20"].ewm(span=20, adjust=False).mean().ewm(span=20, adjust=False).mean()
        out["sar"] = low.rolling(2).min()
        out["rsi_14"] = _rsi_builtin(close, 14)
        ll = low.rolling(14).min()
        hh = high.rolling(14).max()
        out["kdj_k"] = ((close - ll) / (hh - ll) * 100).ewm(alpha=1 / 3, adjust=False).mean()
        out["kdj_d"] = out["kdj_k"].ewm(alpha=1 / 3, adjust=False).mean()
        out["kdj_j"] = 3 * out["kdj_k"] - 2 * out["kdj_d"]
        out["stochf_k"] = (close - ll) / (hh - ll) * 100
        out["stochf_d"] = out["stochf_k"].rolling(3).mean()
        tp = (high + low + close) / 3
        ma_tp = tp.rolling(14).mean()
        md = (tp - ma_tp).abs().rolling(14).mean()
        out["cci_14"] = (tp - ma_tp) / (0.015 * md)
        out["willr_14"] = (hh - close) / (hh - ll) * -100
        out["mom_10"] = close - close.shift(10)
        out["roc_10"] = close.pct_change(10) * 100
        out["bb_middle"] = close.rolling(20).mean()
        std = close.rolling(20).std()
        out["bb_upper"] = out["bb_middle"] + 2 * std
        out["bb_lower"] = out["bb_middle"] - 2 * std
        tr = pd.concat([(high - low), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
        out["atr_14"] = tr.rolling(14).mean()
        out["natr_14"] = out["atr_14"] / close * 100
        # P1 volume + trend extension
        out["obv"] = _obv_builtin(close, volume)
        out["mfi_14"] = _mfi_builtin(high, low, close, volume, 14)
        out["ad"] = _ad_builtin(high, low, close, volume)
        out["adosc"] = out["ad"].ewm(span=3, adjust=False).mean() - out["ad"].ewm(span=10, adjust=False).mean()
        out["trima_20"] = close.rolling(20).mean().rolling(20).mean()
        out["kama_30"] = _kama_builtin(close, 30)
        out["apo_12_26"] = ema12 - ema26
        out["ppo_12_26"] = (ema12 - ema26) / ema26.replace(0, np.nan) * 100
        out["dx_14"] = _dx_builtin(high, low, close, 14)
        out["ht_trendline"] = close.ewm(span=7, adjust=False).mean()
        # P2 pattern recognition (20): builtin placeholder
        _apply_cdl_placeholder(out)
        # P2 statistics / others (6)
        out["beta_hl_20"] = high.rolling(20).cov(low) / low.rolling(20).var().replace(0, np.nan)
        out["correl_hl_20"] = high.rolling(20).corr(low)
        out["linearreg_14"] = close.rolling(14).apply(_linearreg_value, raw=True)
        out["linearreg_slope_14"] = close.rolling(14).apply(_linearreg_slope, raw=True)
        out["linearreg_angle_14"] = np.degrees(np.arctan(out["linearreg_slope_14"]))
        out["stddev_20"] = close.rolling(20).std()
        # P2 volatility supplements (3)
        out["trange"] = tr
        out["ht_dcperiod"] = close.rolling(10).mean()
        out["ht_dcphase"] = np.degrees(np.arctan(close.diff()))
        return out

    raise RuntimeError("未知指标引擎")


def factor_hooks(latest: Dict[str, Any]) -> Dict[str, Any]:
    adx = _safe_float(latest.get("adx_14"))
    rsi = _safe_float(latest.get("rsi_14"))
    macd_diff = _safe_float(latest.get("macd_diff"))
    macd_dea = _safe_float(latest.get("macd_dea"))
    close = _safe_float(latest.get("close"))
    bb_upper = _safe_float(latest.get("bb_upper"))
    bb_middle = _safe_float(latest.get("bb_middle"))
    bb_lower = _safe_float(latest.get("bb_lower"))

    rsi_regime = "neutral"
    if rsi is not None and rsi >= 70:
        rsi_regime = "overbought"
    elif rsi is not None and rsi <= 30:
        rsi_regime = "oversold"

    macd_cross_state = "none"
    if macd_diff is not None and macd_dea is not None:
        if macd_diff > macd_dea:
            macd_cross_state = "bullish"
        elif macd_diff < macd_dea:
            macd_cross_state = "bearish"

    boll_position = "middle_band"
    if close is not None and bb_upper is not None and close >= bb_upper:
        boll_position = "upper_band"
    elif close is not None and bb_lower is not None and close <= bb_lower:
        boll_position = "lower_band"
    elif close is not None and bb_middle is not None and close >= bb_middle:
        boll_position = "between_middle_upper"
    elif close is not None and bb_middle is not None and close < bb_middle:
        boll_position = "between_lower_middle"

    return {
        "trend_strength_adx": adx,
        "rsi_regime": rsi_regime,
        "macd_cross_state": macd_cross_state,
        "boll_position": boll_position,
    }


def _safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        x = float(v)
        if np.isnan(x):
            return None
        return x
    except Exception:
        return None


def _rsi_builtin(close: pd.Series, period: int) -> pd.Series:
    diff = close.diff()
    up = diff.clip(lower=0)
    down = -diff.clip(upper=0)
    ma_up = up.ewm(alpha=1 / period, adjust=False).mean()
    ma_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _adx_builtin(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = pd.concat([(high - low), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=high.index).rolling(period).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=high.index).rolling(period).mean() / atr.replace(0, np.nan))
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    return dx.rolling(period).mean()


def _dx_builtin(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = pd.concat([(high - low), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=high.index).rolling(period).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=high.index).rolling(period).mean() / atr.replace(0, np.nan))
    return ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100


def _obv_builtin(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0.0)
    return (direction * volume).cumsum()


def _ad_builtin(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    hl = (high - low).replace(0, np.nan)
    mfm = ((close - low) - (high - close)) / hl
    mfv = mfm.fillna(0.0) * volume
    return mfv.cumsum()


def _mfi_builtin(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int) -> pd.Series:
    tp = (high + low + close) / 3
    rmf = tp * volume
    pos = rmf.where(tp > tp.shift(1), 0.0).rolling(period).sum()
    neg = rmf.where(tp < tp.shift(1), 0.0).rolling(period).sum()
    mr = pos / neg.replace(0, np.nan)
    return 100 - (100 / (1 + mr))


def _kama_builtin(close: pd.Series, period: int) -> pd.Series:
    fast = 2 / (2 + 1)
    slow = 2 / (30 + 1)
    change = (close - close.shift(period)).abs()
    volatility = close.diff().abs().rolling(period).sum()
    er = (change / volatility.replace(0, np.nan)).fillna(0.0)
    sc = (er * (fast - slow) + slow) ** 2
    kama = close.copy()
    kama.iloc[:period] = close.iloc[:period]
    for i in range(period, len(close)):
        prev = kama.iloc[i - 1]
        curr = close.iloc[i]
        kama.iloc[i] = prev + sc.iloc[i] * (curr - prev)
    return kama


CDL_PATTERNS = [
    "CDLDOJI",
    "CDLDRAGONFLYDOJI",
    "CDLGRAVESTONEDOJI",
    "CDLHAMMER",
    "CDLHANGINGMAN",
    "CDLINVERTEDHAMMER",
    "CDLSHOOTINGSTAR",
    "CDLENGULFING",
    "CDLPIERCING",
    "CDLDARKCLOUDCOVER",
    "CDLMORNINGSTAR",
    "CDLEVENINGSTAR",
    "CDL3WHITESOLDIERS",
    "CDL3BLACKCROWS",
    "CDLHARAMI",
    "CDLHARAMICROSS",
    "CDLSPINNINGTOP",
    "CDLMARUBOZU",
    "CDLTAKURI",
    "CDLRISEFALL3METHODS",
]


def _apply_cdl_talib(out: pd.DataFrame, ta: object, high: pd.Series, low: pd.Series, close: pd.Series, open_: pd.Series) -> None:
    for p in CDL_PATTERNS:
        fn = getattr(ta, p, None)
        col = f"{p.lower()}"
        label_col = f"{col}_label"
        if fn is None:
            out[col] = np.nan
            out[label_col] = "none"
            continue
        if p in ("CDLMORNINGSTAR", "CDLEVENINGSTAR"):
            sig = fn(open_, high, low, close, penetration=0)
        else:
            sig = fn(open_, high, low, close)
        out[col] = sig
        out[label_col] = pd.Series(sig).apply(_cdl_label)


def _apply_cdl_placeholder(out: pd.DataFrame) -> None:
    for p in CDL_PATTERNS:
        col = f"{p.lower()}"
        out[col] = np.nan
        out[f"{col}_label"] = "none"


def _cdl_label(v: Any) -> str:
    x = _safe_float(v)
    if x is None:
        return "none"
    if x > 0:
        return "bullish"
    if x < 0:
        return "bearish"
    return "none"


def _linearreg_slope(arr: np.ndarray) -> float:
    if len(arr) < 2 or np.isnan(arr).all():
        return np.nan
    y = np.asarray(arr, dtype="float64")
    x = np.arange(len(y), dtype="float64")
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return np.nan
    x = x[mask]
    y = y[mask]
    x_mean = x.mean()
    y_mean = y.mean()
    denom = ((x - x_mean) ** 2).sum()
    if denom == 0:
        return np.nan
    return float(((x - x_mean) * (y - y_mean)).sum() / denom)


def _linearreg_value(arr: np.ndarray) -> float:
    slope = _linearreg_slope(arr)
    if np.isnan(slope):
        return np.nan
    y = np.asarray(arr, dtype="float64")
    x = np.arange(len(y), dtype="float64")
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return np.nan
    x = x[mask]
    y = y[mask]
    intercept = y.mean() - slope * x.mean()
    return float(intercept + slope * (len(arr) - 1))

