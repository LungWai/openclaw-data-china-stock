# Changelog

## 2026-04-16

### Major Upgrade: Technical Indicators Expansion

- 新增并完成 `tool_calculate_technical_indicators` 的 P0/P1/P2 全量实现。
- 指标总数扩展至 **58**：
  - P0: 19
  - P1: 10
  - P2: 29（CDL 形态识别 20 + 统计 6 + 波动补充 3）
- 引擎策略完善：`TA-Lib` 优先，`pandas-ta` 自动降级，`builtin` 最后兜底。
- 新增结构化错误码：`UPSTREAM_EMPTY_DATA`。
- 完善解释器解析策略（支持环境变量优先 + 本地 `.venv` 自动发现）。
- 文档体系升级：
  - `README.md`（产品化入口）
  - `INSTALL.md`（安装部署指南）
  - 指标文档增加字段对照表与 P2 说明

### Validation

- 指标工具、manifest/tool_runner 对齐测试全部通过。
- 真实行情 smoke 验证通过（含 P2 字段）。
