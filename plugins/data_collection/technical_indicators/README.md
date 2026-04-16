# tool_calculate_technical_indicators

通用技术指标工具，面向 `index|etf|stock` 历史 OHLCV 数据计算。

## 参数

- `asset_code`：标的代码（必填）
- `asset_type`：`index|etf|stock`（必填）
- `period`：默认 `daily`
- `start_date` / `end_date`：可选，`YYYYMMDD`
- `indicators`：支持 grouped/explicit（当前实现已覆盖 P0+P1+P2）
- `return_mode`：`append|standalone`
- `use_cache`：是否复用底层数据缓存
- `engine_preference`：`auto|talib|pandas_ta`
- `output_schema_version`：默认 `v1`
- `alignment.macd_factor`：MACD 国内口径因子（默认 `2`）

## 返回结构

- `success`
- `engine`
- `data`
- `meta`
  - `asset`
  - `period`
  - `rows`
  - `calculated_indicators`
  - `alignment_applied`
  - `factor_hooks`
- `warnings`
- `error`

## P0+P1+P2 指标（58）

- 趋势：`SMA EMA MACD ADX WMA DEMA TEMA SAR`
- 动量：`RSI KDJ STOCH STOCHF CCI WILLR MOM ROC`
- 波动：`BBANDS ATR NATR`
- 成交量（P1）：`OBV MFI AD ADOSC`
- 趋势扩展（P1）：`TRIMA KAMA APO PPO DX HT_TRENDLINE`
- 形态识别（P2，20）：`CDL*`（保留原始值 `-100/0/100` 并附加 `*_label`）
- 统计/其他（P2，6）：`BETA CORREL LINEARREG LINEARREG_SLOPE LINEARREG_ANGLE STDDEV`
- 波动补充（P2，3）：`TRANGE HT_DCPERIOD HT_DCPHASE`

## 行情数据要求与可用性

- P0+P1 计算统一依赖 OHLCV：`open/high/low/close/volume`
- 该工具通过插件内 `tool_fetch_market_data(view=historical)` 获取历史数据，不直接请求外部站点
- 当上游返回空 K 线时，返回 `UPSTREAM_EMPTY_DATA`，便于上层进行重试或切换标的

## 指标字段对照表（P0/P1/P2）

| 阶段 | 分类 | 指标 | 输出列 | 默认参数 |
|---|---|---|---|---|
| P0 | 趋势 | SMA | `sma_20` | `timeperiod=20` |
| P0 | 趋势 | EMA | `ema_20` | `timeperiod=20` |
| P0 | 趋势 | MACD | `macd_diff`,`macd_dea`,`macd_hist` | `fast=12, slow=26, signal=9` |
| P0 | 趋势 | ADX | `adx_14` | `timeperiod=14` |
| P0 | 趋势 | WMA | `wma_20` | `timeperiod=20` |
| P0 | 趋势 | DEMA | `dema_20` | `timeperiod=20` |
| P0 | 趋势 | TEMA | `tema_20` | `timeperiod=20` |
| P0 | 趋势 | SAR | `sar` | `acceleration=0.02, maximum=0.2` |
| P0 | 动量 | RSI | `rsi_14` | `timeperiod=14` |
| P0 | 动量 | KDJ | `kdj_k`,`kdj_d`,`kdj_j` | `stoch(14,3,3)` |
| P0 | 动量 | STOCH | `kdj_k`,`kdj_d` | 与 KDJ 共享 |
| P0 | 动量 | STOCHF | `stochf_k`,`stochf_d` | `fastk=14, fastd=3` |
| P0 | 动量 | CCI | `cci_14` | `timeperiod=14` |
| P0 | 动量 | WILLR | `willr_14` | `timeperiod=14` |
| P0 | 动量 | MOM | `mom_10` | `timeperiod=10` |
| P0 | 动量 | ROC | `roc_10` | `timeperiod=10` |
| P0 | 波动 | BBANDS | `bb_upper`,`bb_middle`,`bb_lower` | `timeperiod=20, nbdev=2` |
| P0 | 波动 | ATR | `atr_14` | `timeperiod=14` |
| P0 | 波动 | NATR | `natr_14` | `timeperiod=14` |
| P1 | 成交量 | OBV | `obv` | 默认 |
| P1 | 成交量 | MFI | `mfi_14` | `timeperiod=14` |
| P1 | 成交量 | AD | `ad` | 默认 |
| P1 | 成交量 | ADOSC | `adosc` | `fast=3, slow=10` |
| P1 | 趋势扩展 | TRIMA | `trima_20` | `timeperiod=20` |
| P1 | 趋势扩展 | KAMA | `kama_30` | `timeperiod=30` |
| P1 | 趋势扩展 | APO | `apo_12_26` | `fast=12, slow=26` |
| P1 | 趋势扩展 | PPO | `ppo_12_26` | `fast=12, slow=26` |
| P1 | 趋势扩展 | DX | `dx_14` | `timeperiod=14` |
| P1 | 趋势扩展 | HT_TRENDLINE | `ht_trendline` | 默认 |
| P2 | 形态识别 | CDL*（20） | `cdlxxx` + `cdlxxx_label` | TA-Lib 默认，值域 `-100/0/100` |
| P2 | 统计/其他 | BETA | `beta_hl_20` | `timeperiod=20` |
| P2 | 统计/其他 | CORREL | `correl_hl_20` | `timeperiod=20` |
| P2 | 统计/其他 | LINEARREG | `linearreg_14` | `timeperiod=14` |
| P2 | 统计/其他 | LINEARREG_SLOPE | `linearreg_slope_14` | `timeperiod=14` |
| P2 | 统计/其他 | LINEARREG_ANGLE | `linearreg_angle_14` | `timeperiod=14` |
| P2 | 统计/其他 | STDDEV | `stddev_20` | `timeperiod=20` |
| P2 | 波动补充 | TRANGE | `trange` | 默认 |
| P2 | 波动补充 | HT_DCPERIOD | `ht_dcperiod` | 默认 |
| P2 | 波动补充 | HT_DCPHASE | `ht_dcphase` | 默认 |

### P2 形态识别首批 20 项清单

- `CDLDOJI`
- `CDLDRAGONFLYDOJI`
- `CDLGRAVESTONEDOJI`
- `CDLHAMMER`
- `CDLHANGINGMAN`
- `CDLINVERTEDHAMMER`
- `CDLSHOOTINGSTAR`
- `CDLENGULFING`
- `CDLPIERCING`
- `CDLDARKCLOUDCOVER`
- `CDLMORNINGSTAR`
- `CDLEVENINGSTAR`
- `CDL3WHITESOLDIERS`
- `CDL3BLACKCROWS`
- `CDLHARAMI`
- `CDLHARAMICROSS`
- `CDLSPINNINGTOP`
- `CDLMARUBOZU`
- `CDLTAKURI`
- `CDLRISEFALL3METHODS`

## 错误约定

- `VALIDATION_ERROR`：参数或数据字段校验失败（例如缺少 `open/high/low/close/volume`）
- `UPSTREAM_EMPTY_DATA`：上游成功返回但无可计算 K 线数据
- `UPSTREAM_FETCH_FAILED`：历史行情获取失败
- `RUNTIME_ERROR`：执行异常

## 示例

```json
{
  "asset_code": "510300",
  "asset_type": "etf",
  "period": "daily",
  "return_mode": "standalone",
  "engine_preference": "auto",
  "alignment": {
    "macd_factor": 2
  }
}
```

## 注册链路

- `index.ts` 通过 `config/tools_manifest.json` 动态注册工具
- `tool_runner.py` 通过 `TOOL_MAP` 分发：
  - `tool_calculate_technical_indicators` -> `plugins.data_collection.tools.tool_calculate_technical_indicators`
- Python 解释器优先级与环境变量配置见项目根文档：`README.md`

## 非 Mock Smoke Test（示例）

下面是一次真实数据 smoke（`asset_type=index`, `asset_code=000300`）的样例关键信息：

```json
{
  "success": true,
  "engine": "builtin",
  "warnings": [
    "TA-Lib 与 pandas-ta 均不可用，已使用内置计算实现（精度可能与 TA-Lib 存在差异）"
  ],
  "rows": 64,
  "macd_factor": 2.0,
  "sample": {
    "close": 4736.608,
    "macd_diff": 33.54667796456124,
    "macd_dea": -15.479356279313876,
    "macd_hist": 64.50539052318899,
    "rsi_14": 61.98176589307365,
    "adx_14": 35.92420449062315
  }
}
```

