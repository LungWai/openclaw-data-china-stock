from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EngineSelection:
    name: str
    talib: object | None
    pandas_ta: object | None


class TechnicalIndicatorEngine:
    @staticmethod
    def select(engine_preference: str = "auto") -> EngineSelection:
        pref = (engine_preference or "auto").strip().lower()
        talib_mod = None
        pta_mod = None

        try:
            import talib as _talib  # type: ignore

            talib_mod = _talib
        except Exception:
            talib_mod = None

        try:
            import pandas_ta as _pta  # type: ignore

            pta_mod = _pta
        except Exception:
            pta_mod = None

        if pref == "talib":
            if talib_mod is None:
                raise RuntimeError("TA-Lib 不可用，无法满足 engine_preference=talib")
            return EngineSelection(name="talib", talib=talib_mod, pandas_ta=pta_mod)

        if pref == "pandas_ta":
            if pta_mod is None:
                raise RuntimeError("pandas-ta 不可用，无法满足 engine_preference=pandas_ta")
            return EngineSelection(name="pandas_ta", talib=talib_mod, pandas_ta=pta_mod)

        if talib_mod is not None:
            return EngineSelection(name="talib", talib=talib_mod, pandas_ta=pta_mod)
        if pta_mod is not None:
            return EngineSelection(name="pandas_ta", talib=talib_mod, pandas_ta=pta_mod)
        return EngineSelection(name="builtin", talib=None, pandas_ta=None)

