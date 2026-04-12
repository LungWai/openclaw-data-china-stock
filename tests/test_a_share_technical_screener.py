"""Tests for tool_fetch_a_share_technical_screener (mocked AkShare)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from plugins.data_collection import a_share_technical_screener as mod


class TestAShareTechnicalScreener(unittest.TestCase):
    def test_sanitize_drops_html_header_junk_row(self):
        df = pd.DataFrame(
            [
                {"序号": "序号", "股票代码": "000001", "股票简称": "000703", "涨跌幅": None},
                {"序号": "2", "股票代码": "000719", "股票简称": "中原传媒", "涨跌幅": 1.97},
            ]
        )
        out = mod._sanitize_ths_rank_df(df)
        self.assertEqual(len(out), 1)
        self.assertEqual(str(out.iloc[0]["股票代码"]), "000719")

    def test_invalid_screener_kind(self):
        r = mod.tool_fetch_a_share_technical_screener(screener_kind="nope")
        self.assertFalse(r["success"])
        self.assertIn("invalid screener_kind", r.get("error", ""))

    def test_invalid_variant_new_high(self):
        r = mod.tool_fetch_a_share_technical_screener(screener_kind="new_high", variant="bad")
        self.assertFalse(r["success"])
        self.assertIn("invalid variant", r.get("error", ""))

    def test_invalid_variant_breakout(self):
        r = mod.tool_fetch_a_share_technical_screener(screener_kind="breakout_up", variant="ma99")
        self.assertFalse(r["success"])
        self.assertIn("invalid variant", r.get("error", ""))

    @patch.object(mod, "AKSHARE_AVAILABLE", False)
    def test_no_akshare(self):
        r = mod.tool_fetch_a_share_technical_screener(screener_kind="continuous_up")
        self.assertFalse(r["success"])
        self.assertIn("akshare", r.get("error", ""))

    @patch.object(mod, "ak")
    def test_continuous_up_limit(self, mock_ak: MagicMock) -> None:
        mock_ak.stock_rank_lxsz_ths.return_value = pd.DataFrame(
            [{"代码": 600000, "名称": "浦发银行"}, {"代码": 600001, "名称": "x"}]
        )
        r = mod.tool_fetch_a_share_technical_screener(screener_kind="continuous_up", limit=1)
        self.assertTrue(r["success"])
        self.assertEqual(r["screener_kind"], "continuous_up")
        self.assertEqual(r["row_count"], 1)
        self.assertEqual(r["records"][0]["代码"], "600000")
        mock_ak.stock_rank_lxsz_ths.assert_called_once_with()

    @patch.object(mod, "ak")
    def test_new_high_passes_symbol(self, mock_ak: MagicMock) -> None:
        mock_ak.stock_rank_cxg_ths.return_value = pd.DataFrame([{"代码": "1"}])
        r = mod.tool_fetch_a_share_technical_screener(screener_kind="new_high", variant="year")
        self.assertTrue(r["success"])
        self.assertEqual(r["variant_effective"], "一年新高")
        mock_ak.stock_rank_cxg_ths.assert_called_once_with(symbol="一年新高")

    @patch.object(mod, "ak")
    def test_breakout_down_default_ma20(self, mock_ak: MagicMock) -> None:
        mock_ak.stock_rank_xxtp_ths.return_value = pd.DataFrame([])
        r = mod.tool_fetch_a_share_technical_screener(screener_kind="breakout_down")
        self.assertTrue(r["success"])
        self.assertEqual(r["variant_effective"], "20日均线")
        mock_ak.stock_rank_xxtp_ths.assert_called_once_with(symbol="20日均线")


if __name__ == "__main__":
    unittest.main()
