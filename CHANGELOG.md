# Changelog

All notable changes to this project are documented here. The format is loosely based on Keep a Changelog; versions match `package.json` / ClawHub releases.

## [0.2.3] - 2026-04-12

### Added

- **`tool_fetch_a_share_fund_flow`**: Unified onshore A-share money flow (`query_kind`: market/sector/stock history and ranks, big deals, main-force rank, sector drill-down). Multi-source chain: Eastmoney HTTP direct (push2/push2his/clist) + Tonghuashun HTML (limited pages for big deals) + AkShare fallbacks. Env: `AKSHARE_FUND_FLOW_ATTEMPT_TIMEOUT_SEC`, `BIG_DEAL_THS_MAX_PAGES`.
- **`tool_fetch_a_share_technical_screener`**: Tonghuashun technical stock screeners via AkShare `stock_rank_*_ths` (new highs/lows, consecutive up/down, volume patterns, MA breakouts, price–volume sync, insurance holdings). HTML row sanitization for bad header rows. Env: `AKSHARE_TECH_SCREENER_TIMEOUT_SEC` (falls back to fund-flow timeout).

### Changed

- **`scripts/test_all_tools.py`**: Heuristics for `query_kind` / `screener_kind` so batch smoke tests pass schema validation.
- **Docs**: `AkShare_fund_flow_probe_notes.md`, manifest descriptions, `ROADMAP.md` appendices H–I, `SKILL.md`, `plugins/data_collection/README.md`.

### Tests

- `tests/test_a_share_fund_flow.py`, `tests/test_a_share_technical_screener.py` (mocked; no live network required).

## [0.2.2] - earlier

Prior ClawHub release baseline (manifest/tool_runner alignment). See git history for details.
