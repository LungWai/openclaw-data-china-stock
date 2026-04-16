# 安装与部署指南（openclaw-data-china-stock）

本指南面向“首次使用者 / 团队部署者”，目标是让用户快速找到、安装、验证插件。

## 1. 获取插件

推荐两种方式：

- **源码方式**：直接克隆仓库（适合开发与可定制部署）
- **打包方式**：使用发布包（例如仓库内 `.tgz` 产物，适合标准化分发）

## 2. 环境准备

- Python 3.10+
- 建议 Linux/macOS 使用 `python3`
- 建议每个部署实例使用独立 `.venv`

## 3. 源码安装（推荐）

```bash
cd /path/to/openclaw-data-china-stock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## 4. 关键依赖验证

```bash
python - <<'PY'
import talib, pandas_ta
print("talib ok")
print("pandas_ta ok")
PY
```

## 5. 解释器固定（强烈建议）

为避免多 Python 环境导致口径不一致：

```bash
export OPENCLAW_DATA_CHINA_STOCK_PYTHON="/abs/path/to/.venv/bin/python"
```

## 6. 最小验收

```bash
python -m pytest -q tests/test_manifest_tool_map_parity.py tests/test_tool_runner_dispatch.py tests/test_technical_indicators_tool.py
```

并执行一次真实数据 smoke（index/etf 任一标的）验证工具可用。

## 7. 常见问题

- **出现 `TA-Lib 与 pandas-ta 均不可用`**
  - 当前解释器未装好依赖；按本指南第 3-5 步重装并固定解释器。
- **同机测试通过，服务运行失败**
  - 常见原因是运行时解释器不是你测试使用的 `.venv`。
