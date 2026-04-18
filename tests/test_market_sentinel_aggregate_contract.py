"""Contract checks for market-sentinel aggregate JSON (docs/sentiment/api_contract.md)."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "sentiment"

FULL_TOP_LEVEL = (
    "overall_score",
    "sentiment_stage",
    "sub_scores",
    "factor_attribution",
    "data_completeness_ratio",
    "action_bias",
    "risk_counterevidence",
    "confidence_band",
    "degraded",
)
SUB_SCORE_KEYS = frozenset(
    {"limit_up_ecology", "fund_flow_attitude", "northbound_trend", "sector_structure"}
)
STAGES = frozenset({"冰点", "修复", "震荡", "混沌", "高潮", "退潮"})
ACTION_BIAS = frozenset({"进攻", "均衡", "防守"})
CONFIDENCE = frozenset({"low", "medium", "high"})

INSUFFICIENT_TOP = frozenset({"status", "reason", "data_completeness_ratio", "missing_tools"})


def map_overall_score_to_stage(score: float) -> str:
    """v1.0 table from docs/sentiment/api_contract.md (Skill aggregate section)."""
    s = int(score)
    if s <= 20:
        return "冰点"
    if s <= 35:
        return "修复"
    if s <= 50:
        return "震荡"
    if s <= 65:
        return "混沌"
    if s <= 85:
        return "高潮"
    return "退潮"


def subscore_spread(sub_scores: dict) -> float:
    vals = [float(sub_scores[k]) for k in SUB_SCORE_KEYS]
    return max(vals) - min(vals)


def _validate_full_report(obj: dict) -> None:
    for k in FULL_TOP_LEVEL:
        assert k in obj, f"missing key {k}"
    assert isinstance(obj["overall_score"], (int, float))
    assert 0 <= float(obj["overall_score"]) <= 100
    assert obj["sentiment_stage"] in STAGES
    ss = obj["sub_scores"]
    assert set(ss.keys()) == SUB_SCORE_KEYS
    for v in ss.values():
        assert isinstance(v, (int, float))
        assert 0 <= float(v) <= 100
    fa = obj["factor_attribution"]
    assert "leading" in fa and "lagging" in fa and "notes" in fa
    r = float(obj["data_completeness_ratio"])
    assert 0.0 <= r <= 1.0
    assert obj["action_bias"] in ACTION_BIAS
    assert isinstance(obj["risk_counterevidence"], list)
    assert len(obj["risk_counterevidence"]) >= 1
    assert obj["confidence_band"] in CONFIDENCE
    assert isinstance(obj["degraded"], bool)


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_full_fixture_matches_contract():
    d = _load("market_sentinel_aggregate_full.json")
    _validate_full_report(d)
    assert d["degraded"] is False
    assert d["data_completeness_ratio"] == 1.0
    assert map_overall_score_to_stage(d["overall_score"]) == d["sentiment_stage"]


def test_degraded_fixture_partial_sources():
    d = _load("market_sentinel_aggregate_degraded.json")
    _validate_full_report(d)
    assert d["degraded"] is True
    assert d["data_completeness_ratio"] == 0.75
    assert map_overall_score_to_stage(d["overall_score"]) == d["sentiment_stage"]
    assert any("northbound" in x.lower() or "Northbound" in x for x in d["risk_counterevidence"])


def test_insufficient_evidence_shape():
    d = _load("market_sentinel_aggregate_insufficient.json")
    assert set(d.keys()) == INSUFFICIENT_TOP
    assert d["status"] == "insufficient_evidence"
    assert isinstance(d["reason"], str) and len(d["reason"]) > 0
    assert d["data_completeness_ratio"] == 0.0
    assert isinstance(d["missing_tools"], list) and len(d["missing_tools"]) >= 1


def test_chaos_override_fixture_spread_rule():
    d = _load("market_sentinel_aggregate_chaos_override.json")
    _validate_full_report(d)
    assert d["sentiment_stage"] == "混沌"
    assert subscore_spread(d["sub_scores"]) >= 35


def test_stage_mapping_boundaries():
    assert map_overall_score_to_stage(0) == "冰点"
    assert map_overall_score_to_stage(20) == "冰点"
    assert map_overall_score_to_stage(21) == "修复"
    assert map_overall_score_to_stage(35) == "修复"
    assert map_overall_score_to_stage(36) == "震荡"
    assert map_overall_score_to_stage(50) == "震荡"
    assert map_overall_score_to_stage(51) == "混沌"
    assert map_overall_score_to_stage(65) == "混沌"
    assert map_overall_score_to_stage(66) == "高潮"
    assert map_overall_score_to_stage(85) == "高潮"
    assert map_overall_score_to_stage(86) == "退潮"
    assert map_overall_score_to_stage(100) == "退潮"


def test_skill_md_lists_same_top_level_keys():
    text = (ROOT / "skills" / "market-sentinel" / "SKILL.md").read_text(encoding="utf-8")
    for k in FULL_TOP_LEVEL:
        assert f"`{k}`" in text, f"SKILL.md should mention `{k}`"


def test_api_contract_documents_aggregate_section():
    text = (ROOT / "docs" / "sentiment" / "api_contract.md").read_text(encoding="utf-8")
    assert "## Skill aggregate: `market-sentinel`" in text
    assert "`overall_score`" in text and "`insufficient_evidence`" in text


def test_limit_up_empty_pool_style_report_still_valid():
    """Empty/thin limit-up pool: keep full template, flag degraded + low confidence."""
    d = _load("market_sentinel_aggregate_full.json")
    d = json.loads(json.dumps(d))
    d["sub_scores"]["limit_up_ecology"] = 25
    d["overall_score"] = 40
    d["sentiment_stage"] = map_overall_score_to_stage(d["overall_score"])
    d["risk_counterevidence"] = [
        "涨停池为空或极薄，limit_up_ecology 分项显著压低；勿将情绪结论等同于龙头战法机会。"
    ]
    d["degraded"] = True
    d["data_completeness_ratio"] = 1.0
    d["confidence_band"] = "low"
    _validate_full_report(d)


def test_aggregate_roundtrip_json_for_each_full_shape_fixture():
    for name in (
        "market_sentinel_aggregate_full.json",
        "market_sentinel_aggregate_degraded.json",
        "market_sentinel_aggregate_chaos_override.json",
    ):
        raw = (FIXTURES / name).read_text(encoding="utf-8")
        d = json.loads(raw)
        _validate_full_report(d)
        assert json.loads(json.dumps(d, ensure_ascii=False)) == d
