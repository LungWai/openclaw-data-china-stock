# AkShare 资金流向接口探测备忘（开发基线）

在实现 `tool_fetch_a_share_fund_flow` 前于本环境 `python3 -c "import akshare as ak; import inspect; ..."` 打印的签名（随 AkShare 版本可能变化）：

| 函数 | 签名摘要 |
|------|-----------|
| `stock_market_fund_flow` | `() -> DataFrame` |
| `stock_sector_fund_flow_rank` | `(indicator='今日', sector_type='行业资金流')` |
| `stock_fund_flow_individual` | `(symbol='即时')` |
| `stock_individual_fund_flow_rank` | `(indicator='5日')` |
| `stock_individual_fund_flow` | `(stock='600094', market='sh')` |
| `stock_fund_flow_industry` / `stock_fund_flow_concept` | `(symbol='即时')` |
| `stock_fund_flow_big_deal` | `() -> DataFrame` |
| `stock_main_fund_flow` | `(symbol='全部股票')` |
| `stock_sector_fund_flow_summary` | `(symbol='电源设备', indicator='今日')` |
| `stock_sector_fund_flow_hist` / `stock_concept_fund_flow_hist` | 单参数 `symbol` 行业名/概念名 |

联网烟测需在可访问东财/同花顺 API 的环境执行；CI 或无外网时以 mock 单测为准。

## 手工原始接口 vs `tool_fetch_a_share_fund_flow` 对照（调试记录）

条件：与线上一致使用 `plugins.utils.proxy_env.without_proxy_env()` 包裹调用；AkShare 1.18.x；单接口线程超时 120s 用于观察（工具内链式调用默认单次尝试 **180s**，可用环境变量 `AKSHARE_FUND_FLOW_ATTEMPT_TIMEOUT_SEC` 调整）。

| 原始接口 | 典型现象 | 与工具失败是否一致 |
|----------|----------|-------------------|
| `stock_market_fund_flow()` | 多数时候 **成功**（约百行） | 与 `market_history` 成功一致 |
| `stock_sector_fund_flow_rank(…地域…)` | 东财偶发 `RemoteDisconnected` / 空表；**无同花顺备源** | 与 `sector_rank`+`region` 易失败一致（非封装 bug） |
| `stock_sector_fund_flow_rank(…行业…)` | 东财可能断连；`stock_fund_flow_industry` 可走同花顺 | 与 `sector_rank`+`industry` 可走 THS 备源一致 |
| `stock_fund_flow_individual(symbol="即时")` | **极慢**（分页 tqdm 常 100+ 步），易 **>120s** | 工具默认**先东财个股排名**；THS 为备源，超时后切换 |
| `stock_individual_fund_flow_rank(indicator="今日")` | 东财可能 `RemoteDisconnected` | 与 `stock_rank` 东财备源失败一致 |
| `stock_fund_flow_big_deal()` | 同花顺分页慢，接近 120s 边界 | 工具已加东财 clist 代理首源 + THS 限页；仍慢时可调 `BIG_DEAL_THS_MAX_PAGES` 或依赖末级 AkShare |
| `stock_main_fund_flow` / `stock_sector_fund_flow_summary` | 东财偶发断连 | 与 `main_force_rank` / `sector_drill` 报错一致 |
| `stock_individual_fund_flow(stock, market)` | 多数 **成功** | 与 `stock_history` 成功一致 |

结论：**失败主要来自数据源网络与同花顺全量分页耗时**，与封装逻辑一致。工具侧已对 `_run_chain` 内**每次尝试**加线程超时（默认 180s，环境变量 `AKSHARE_FUND_FLOW_ATTEMPT_TIMEOUT_SEC`），超时后尝试下一源；实现上使用 `ThreadPoolExecutor.shutdown(wait=False)`，避免 CPython 在线程仍跑同花顺分页时阻塞整条链。

**勿**用 `with ThreadPoolExecutor(...) as ex` 包裹单次超时调用：`__exit__` 会 `shutdown(wait=True)`，在子线程 HTTP 未结束时仍会长时间阻塞。

## 与全仓库行情工具对齐的多层策略（2026-04）

参考 `stock/fetch_realtime.py`（mootdx→东财五档→腾讯→AkShare 新浪快照）、`stock/fetch_minute.py`（新浪→东财→**efinance**）等：

| 层次 | 资金流向工具中的对应 |
|------|---------------------|
| 绕过代理 | `without_proxy_env()`（与 northbound、分钟线等一致） |
| AkShare 内多路由 | 东财 `stock_individual_fund_flow_rank` ↔ 同花顺 `stock_fund_flow_individual` 等 |
| **东财 HTTP 直连** | `utils/eastmoney_fund_flow_direct.py`：`request_with_retry` + push2his / push2 **clist 分页截断**（大盘、个股 K 线、主力排名限制行数），减轻 AkShare 全量分页导致的超时 |
| 板块窗口 | 东财板块/行业下钻 **仅支持** 今日/5日/10日；`rank_window` 的 d3/d20 在 `SECTOR_RANK_*` 中映射为 5日/10日（见 `params_echo`） |

**公开分发说明**：任何依赖免费行情接口的工具都无法承诺「100% 成功」；本插件通过多源链 + 直连 + 超时切换 **提高可用性**。

`big_deal` 链（2026-04）：① 东财 `push2/clist` 限页、按 **今日大单净流入** 排序的全 A 快照（**非**同花顺逐笔「大单追踪」，字段不同，见返回 `params_echo`）；② 同花顺 HTML 分页 + `hexin-v`，页数上限 `BIG_DEAL_THS_MAX_PAGES`（默认 30）；③ AkShare `stock_fund_flow_big_deal` 全量末级。
