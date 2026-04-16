"""
Technical indicators package.

This package provides a generic, reusable indicator engine for stock/ETF/index OHLCV
data, with TA-Lib priority and pandas-ta fallback.
"""

from .engine import TechnicalIndicatorEngine

__all__ = ["TechnicalIndicatorEngine"]

