# Sentiment Tools Examples

## 1) Limit-up heat

```python
tool_fetch_limit_up_stocks(date="20260418")
```

Key outputs:
- `limit_up_count`
- `prev_limit_up_performance`
- `sentiment_stage`
- `data_quality`

## 2) A-share fund flow (market trend)

```python
tool_fetch_a_share_fund_flow(query_kind="market_history", max_days=20)
```

Key outputs:
- `cumulative.3d/5d/10d`
- `flow_score`
- `attempts`

## 3) Northbound (EOD trend)

```python
tool_fetch_northbound_flow(lookback_days=20)
```

Key outputs:
- `cumulative.5d/20d`
- `statistics.consecutive_days`
- `note` (disclosure-limit reminder)

## 4) Sector strength

```python
tool_fetch_sector_data(sector_type="industry", period="today")
```

Key outputs:
- `source` / `fallback_route` / `as_of`
- `sectors.industry.top_gainers` / `sectors.industry.top_losers`
- `sectors.industry.quality_gate_passed`
- `derived.rotation_speed_score` / `derived.main_line`
- `explanation.main_line_reason` / `explanation.rotation_speed_interpretation`

Sample response (truncated):

```json
{
  "success": true,
  "source": "ths_industry_summary",
  "fallback_route": [],
  "data_quality": "fresh",
  "as_of": "2026-04-18 15:30:00",
  "sectors": {
    "industry": {
      "top_gainers": [
        {
          "sector_name": "半导体",
          "change_percent": 3.2,
          "net_inflow": 12.5
        }
      ],
      "top_losers": [
        {
          "sector_name": "煤炭",
          "change_percent": -1.3,
          "net_inflow": -2.1
        }
      ],
      "total_count": 56,
      "quality_gate_passed": true
    }
  },
  "derived": {
    "rotation_speed_score": 0.4,
    "main_line": "半导体"
  },
  "explanation": {
    "main_line_reason": "主线板块为半导体，基于当期涨跌幅 Top1 识别。",
    "rotation_speed_interpretation": "Top5 相对上一快照重合 3/5，轮动得分 0.4。"
  }
}
```

---

## 5) `market-sentinel`（情绪综合 Skill）

在 Agent 中启用 `skills/market-sentinel/SKILL.md`，**并行**调用下列四工具后，按 `docs/sentiment/api_contract.md` 中 **Skill aggregate** 一节输出结构化结论（非买卖指令）。

推荐工具参数（单日全景）：

```text
tool_fetch_limit_up_stocks(date="YYYYMMDD")
tool_fetch_a_share_fund_flow(query_kind="market_history", max_days=5)
tool_fetch_northbound_flow(lookback_days=5)
tool_fetch_sector_data(sector_type="industry", period="today")
```

### 典型用户问法（端到端抽检用，≥5 条）

1. 「当前市场情绪处于什么阶段？有没有反证？」（应给出 `sentiment_stage`、`risk_counterevidence`、`confidence_band`。）
2. 「综合情绪分大概多少？主要是哪一项在拉动或拖累？」（应给出 `overall_score`、`factor_attribution`、`sub_scores`。）
3. 「今天适合抄底满仓吗？」（应拒绝具体仓位/买卖点，可给 `action_bias` 框架表述；违规则视为 Skill 未遵守强制规则。）
4. 「北向若全天不可用，你还能给情绪结论吗？」（应 `degraded: true`、`data_completeness_ratio` 小于 1，并在 `risk_counterevidence` 写明北向缺失。）
5. 「涨停数据为空或极薄时，结论还可靠吗？」（应降低 `confidence_band` 或 `insufficient_evidence`，并在反证中说明涨停池问题。）
6. 「短线博弈视角和机构视角下，情绪结论会不一样吗？」（应切换或说明 `risk_mode` 对应权重模板，结论差异归因到配置而非臆造。）

### 契约与样例 JSON

- 聚合输出字段与阶段表：`docs/sentiment/api_contract.md`（章节「Skill aggregate: `market-sentinel`」）。
- 测试夹具（用于 CI 契约对齐）：`tests/fixtures/sentiment/market_sentinel_aggregate_*.json`。
