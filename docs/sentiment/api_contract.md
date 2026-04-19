# Sentiment Tools API Contract

Applies to:
- `tool_fetch_limit_up_stocks`
- `tool_fetch_a_share_fund_flow`
- `tool_fetch_northbound_flow`
- `tool_fetch_sector_data`

## Unified top-level fields

- `success`: bool
- `source`: winner data source
- `fallback_route`: attempted sources in order
- `used_fallback`: whether winner is not first source
- `attempts`: source-level attempt records
- `as_of`: generation timestamp
- `data_quality`: `fresh | cached | partial`
- `cache_hit`: bool
- `error_code`: nullable, e.g. `UPSTREAM_FETCH_FAILED`
- `error_message`: nullable
- `explanation`: short human-readable explanation
- `quality_score`: int in \[0, 100\] — heuristic composite (freshness, fallback, completeness); see `plugins/utils/response_quality.py`
- `data_generated_at`: optional string — when present, **must equal** `as_of` (alias for consumers that expect an `*_at` suffix)

## Global fields injected by `tool_runner.py`

These apply to **all** tools invoked via `tool_runner.py` (not only sentiment):

- `elapsed_ms`: int — wall-clock duration of the invocation in the runner process
- `tool`: string — tool id (e.g. `tool_fetch_limit_up_stocks`)
- `plugin_version`: string — mirrors `version` in `openclaw.plugin.json`

See also [../optimization/tool_response_metadata.md](../optimization/tool_response_metadata.md).

## Backward compatibility

Existing business fields are preserved (e.g. `data`, `records`, `leaders`, `signal`).

## Example (abbreviated)

```json
{
  "success": true,
  "source": "akshare.stock_zt_pool_em",
  "fallback_route": ["akshare.stock_zt_pool_em"],
  "used_fallback": false,
  "attempts": [{"source":"akshare.stock_zt_pool_em","ok":true,"message":"20260418"}],
  "as_of": "2026-04-18 11:00:00",
  "data_quality": "fresh",
  "cache_hit": false,
  "error_code": null,
  "error_message": null,
  "explanation": "...",
  "quality_score": 88,
  "data_generated_at": "2026-04-18 11:00:00",
  "elapsed_ms": 120,
  "tool": "tool_fetch_limit_up_stocks",
  "plugin_version": "0.5.3"
}
```

---

## Skill aggregate: `market-sentinel`

Applies to the **structured narrative output** produced when the agent follows `skills/market-sentinel/SKILL.md` (not a single `tool_runner` tool). Numeric bands and weights are defined in `skills/market-sentinel/config/market-sentinel_config.yaml` (`sentiment_stage_thresholds`, `risk_modes`, `dynamic_weight_adjustment`).

### Top-level fields (full report)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `overall_score` | number | yes | Composite 0–100 after re-normalization when tools are missing. |
| `sentiment_stage` | string | yes | One of: `冰点`, `修复`, `震荡`, `混沌`, `高潮`, `退潮`. |
| `sub_scores` | object | yes | Four keys, each 0–100: `limit_up_ecology`, `fund_flow_attitude`, `northbound_trend`, `sector_structure`. |
| `factor_attribution` | object | yes | At least `leading`, `lagging` (sub-score dimension keys) and `notes` (string). |
| `data_completeness_ratio` | number | yes | In \[0,1\], e.g. successful tools / 4. |
| `action_bias` | string | yes | One of: `进攻`, `均衡`, `防守`. |
| `risk_counterevidence` | array | yes | List of strings (or objects with `text`), non-empty when any tool failed or signals conflict. |
| `confidence_band` | string | yes | `low` \| `medium` \| `high` (document agent may mirror Chinese labels if consistent). |
| `degraded` | boolean | yes | `true` if any dependency tool failed or was skipped after partial success. |

### `overall_score` → `sentiment_stage` (v1.0 default bands)

Bands below are normative for contract tests; deploy may override via config only.

| `overall_score` (inclusive range) | `sentiment_stage` |
|-----------------------------------|-------------------|
| 0–20 | `冰点` |
| 21–35 | `修复` |
| 36–50 | `震荡` |
| 51–65 | `混沌` |
| 66–85 | `高潮` |
| 86–100 | `退潮` |

**`混沌` override:** if max(`sub_scores`) − min(`sub_scores`) ≥ `chaos_subscore_spread_min` from config, `sentiment_stage` SHOULD be `混沌` even when `overall_score` maps elsewhere; record the override in `factor_attribution.notes`.

### Degraded report (fixed template)

When `degraded` is `true`, the same top-level keys MUST still be present. Use these conventions:

- `risk_counterevidence`: MUST include one entry per failed tool, e.g. `northbound: upstream unavailable`.
- `data_completeness_ratio`: MUST reflect successful tools only.
- `confidence_band`: SHOULD be `low` or `medium` unless remaining evidence is exceptionally strong.
- `overall_score`: MUST be recomputed from available sub-scores only (re-normalized weights per config).

### Insufficient evidence shape

When the skill cannot justify a composite view:

| Field | Type | Required |
|-------|------|----------|
| `status` | string | yes, literal `insufficient_evidence` |
| `reason` | string | yes |
| `data_completeness_ratio` | number | yes |
| `missing_tools` | array of strings | yes (tool ids or short names) |

No requirement to populate `overall_score` / `sentiment_stage` in this shape.

### Minimal JSON example (full report, abbreviated)

```json
{
  "overall_score": 45,
  "sentiment_stage": "震荡",
  "sub_scores": {
    "limit_up_ecology": 62,
    "fund_flow_attitude": 55,
    "northbound_trend": 60,
    "sector_structure": 52
  },
  "factor_attribution": {
    "leading": "limit_up_ecology",
    "lagging": "sector_structure",
    "notes": "涨停分项略高于其他三项。"
  },
  "data_completeness_ratio": 1.0,
  "action_bias": "均衡",
  "risk_counterevidence": ["北向与内资单日方向不一致，降低进攻置信度。"],
  "confidence_band": "medium",
  "degraded": false
}
```
