import unittest
from unittest.mock import patch

from plugins.data_collection.tools.tool_calculate_technical_indicators import (
    tool_calculate_technical_indicators,
)


def _mock_hist_rows(n: int = 80):
    rows = []
    base = 100.0
    for i in range(n):
        px = base + i * 0.2
        rows.append(
            {
                "date": f"202501{i % 28 + 1:02d}",
                "open": px - 0.3,
                "high": px + 0.6,
                "low": px - 0.8,
                "close": px,
                "volume": 100000 + i * 100,
            }
        )
    return rows


class TestTechnicalIndicatorsTool(unittest.TestCase):
    @patch("plugins.data_collection.tools.tool_calculate_technical_indicators.tool_fetch_market_data")
    def test_p0_p1_indicators_are_materialized(self, mock_fetch):
        mock_fetch.return_value = {"success": True, "data": _mock_hist_rows(120)}
        res = tool_calculate_technical_indicators(
            asset_code="510300",
            asset_type="etf",
            return_mode="append",
            engine_preference="auto",
        )
        self.assertTrue(res["success"], msg=res)
        latest = res["data"][-1]
        required_columns = [
            "sma_20",
            "ema_20",
            "macd_diff",
            "macd_dea",
            "macd_hist",
            "adx_14",
            "wma_20",
            "dema_20",
            "tema_20",
            "sar",
            "rsi_14",
            "kdj_k",
            "kdj_d",
            "kdj_j",
            "stochf_k",
            "stochf_d",
            "cci_14",
            "willr_14",
            "mom_10",
            "roc_10",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "atr_14",
            "natr_14",
            "obv",
            "mfi_14",
            "ad",
            "adosc",
            "trima_20",
            "kama_30",
            "apo_12_26",
            "ppo_12_26",
            "dx_14",
            "ht_trendline",
            "beta_hl_20",
            "correl_hl_20",
            "linearreg_14",
            "linearreg_slope_14",
            "linearreg_angle_14",
            "stddev_20",
            "trange",
            "ht_dcperiod",
            "ht_dcphase",
            "cdldoji",
            "cdldoji_label",
        ]
        for col in required_columns:
            self.assertIn(col, latest, msg=f"missing indicator column: {col}")
        self.assertEqual(len(res["meta"]["calculated_indicators"]), 58)

    @patch("plugins.data_collection.tools.tool_calculate_technical_indicators.tool_fetch_market_data")
    def test_validation_missing_columns(self, mock_fetch):
        mock_fetch.return_value = {"success": True, "data": [{"open": 1, "high": 2, "close": 1.5}]}
        res = tool_calculate_technical_indicators(asset_code="510300", asset_type="etf")
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["error_code"], "VALIDATION_ERROR")
        self.assertIn("missing_fields", res["error"])

    @patch("plugins.data_collection.tools.tool_calculate_technical_indicators.tool_fetch_market_data")
    def test_append_mode_has_series(self, mock_fetch):
        mock_fetch.return_value = {"success": True, "data": _mock_hist_rows()}
        res = tool_calculate_technical_indicators(
            asset_code="510300",
            asset_type="etf",
            return_mode="append",
            engine_preference="auto",
        )
        self.assertTrue(res["success"])
        self.assertIsInstance(res["data"], list)
        self.assertIn("macd_diff", res["data"][-1])

    @patch("plugins.data_collection.tools.tool_calculate_technical_indicators.tool_fetch_market_data")
    def test_standalone_mode_has_factor_hooks(self, mock_fetch):
        mock_fetch.return_value = {"success": True, "data": _mock_hist_rows()}
        res = tool_calculate_technical_indicators(asset_code="000300", asset_type="index")
        self.assertTrue(res["success"])
        self.assertIn("latest", res["data"])
        self.assertIn("factor_hooks", res["meta"])
        self.assertIn("rsi_regime", res["meta"]["factor_hooks"])
        self.assertIsNotNone(res["meta"]["factor_hooks"]["trend_strength_adx"])

    @patch("plugins.data_collection.tools.tool_calculate_technical_indicators.tool_fetch_market_data")
    def test_macd_alignment_factor_configurable(self, mock_fetch):
        mock_fetch.return_value = {"success": True, "data": _mock_hist_rows()}
        r1 = tool_calculate_technical_indicators(
            asset_code="000300",
            asset_type="index",
            alignment={"macd_factor": 1},
            return_mode="append",
        )
        r2 = tool_calculate_technical_indicators(
            asset_code="000300",
            asset_type="index",
            alignment={"macd_factor": 2},
            return_mode="append",
        )
        self.assertTrue(r1["success"] and r2["success"])
        self.assertEqual(r1["meta"]["alignment_applied"]["macd_factor"], 1.0)
        self.assertEqual(r2["meta"]["alignment_applied"]["macd_factor"], 2.0)

    @patch("plugins.data_collection.tools.tool_calculate_technical_indicators.tool_fetch_market_data")
    def test_upstream_empty_data_error(self, mock_fetch):
        mock_fetch.return_value = {"success": True, "data": {"klines": []}}
        res = tool_calculate_technical_indicators(asset_code="510300", asset_type="etf")
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["error_code"], "UPSTREAM_EMPTY_DATA")


if __name__ == "__main__":
    unittest.main()

