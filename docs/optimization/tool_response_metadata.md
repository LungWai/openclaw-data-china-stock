# Tool response metadata (cross-cutting contract)

This document applies to tools invoked via `tool_runner.py` and consumed by OpenClaw agents (including `etf-options-ai-assistant`).

## Injected by `tool_runner.py` (all dict responses)

| Field | Type | Description |
|-------|------|-------------|
| `elapsed_ms` | int | Wall time for the tool invocation in the runner process. |
| `tool` | string | Tool id (e.g. `tool_fetch_limit_up_stocks`). |

## Plugin version

| Field | Type | Description |
|-------|------|-------------|
| `plugin_version` | string | Mirrors `version` in repository `openclaw.plugin.json`. |

## Data timing and quality (tool / sentiment contract)

| Field | Type | Description |
|-------|------|-------------|
| `as_of` | string | Canonical generation timestamp for the payload. |
| `data_generated_at` | string | **Optional alias**: when present, MUST equal `as_of` exactly. |
| `quality_score` | int 0–100 | Heuristic composite; see `plugins/utils/response_quality.py`. |

Sentiment-specific fields remain documented in [../sentiment/api_contract.md](../sentiment/api_contract.md).
