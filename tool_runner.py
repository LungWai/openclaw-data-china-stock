#!/usr/bin/env python3
from __future__ import annotations

import importlib
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).parent
PLUGINS_DIR = PROJECT_ROOT / "plugins"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PLUGINS_DIR))


class ToolSpec:
    def __init__(self, module_path: str, function_name: str) -> None:
        self.module_path = module_path
        self.function_name = function_name


ALIASES: Dict[str, tuple[str, Dict[str, Any]]] = {
    "tool_read_index_daily": ("tool_read_market_data", {"data_type": "index_daily"}),
    "tool_read_index_minute": ("tool_read_market_data", {"data_type": "index_minute"}),
    "tool_read_etf_daily": ("tool_read_market_data", {"data_type": "etf_daily"}),
    "tool_read_etf_minute": ("tool_read_market_data", {"data_type": "etf_minute"}),
    "tool_read_option_minute": ("tool_read_market_data", {"data_type": "option_minute"}),
    "tool_read_option_greeks": ("tool_read_market_data", {"data_type": "option_greeks"}),
}


TOOL_MAP: Dict[str, ToolSpec] = {
    "tool_fetch_market_data": ToolSpec(
        module_path="data.fetch_market_data",
        function_name="tool_fetch_market_data",
    ),
    "tool_read_market_data": ToolSpec(
        module_path="data.read_market_data",
        function_name="tool_read_market_data",
    ),
    "tool_calculate_technical_indicators": ToolSpec(
        module_path="plugins.data_collection.tools.tool_calculate_technical_indicators",
        function_name="tool_calculate_technical_indicators",
    ),
}


def _json_error(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    out = {"success": False, "error_code": code, "message": message}
    out.update(extra)
    return out


def run_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name in ALIASES:
        new_name, injected = ALIASES[tool_name]
        merged = dict(injected)
        merged.update(params)
        tool_name = new_name
        params = merged

    if tool_name not in TOOL_MAP:
        return _json_error("UNKNOWN_TOOL", f"未知工具: {tool_name}", available_tools=list(TOOL_MAP.keys()))

    spec = TOOL_MAP[tool_name]
    try:
        mod = importlib.import_module(spec.module_path)
        fn = getattr(mod, spec.function_name)
    except Exception as e:
        return _json_error("IMPORT_ERROR", f"导入失败: {e}", tool_name=tool_name, module=spec.module_path)

    try:
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            result = fn(**params)
        if isinstance(result, dict):
            return result
        return {"success": True, "data": result}
    except TypeError as e:
        return _json_error("VALIDATION_ERROR", f"参数校验失败: {e}")
    except Exception as e:
        return _json_error("RUNTIME_ERROR", f"执行异常: {e}")


def main() -> int:
    if len(sys.argv) < 3:
        print(
            json.dumps(
                _json_error("VALIDATION_ERROR", "用法: tool_runner.py <tool_name> <json_params>"),
                ensure_ascii=False,
            )
        )
        return 1

    tool_name = sys.argv[1]
    try:
        params = json.loads(sys.argv[2] or "{}")
        if not isinstance(params, dict):
            raise ValueError("params must be object")
    except Exception as e:
        print(json.dumps(_json_error("VALIDATION_ERROR", f"参数 JSON 解析失败: {e}"), ensure_ascii=False))
        return 1

    result = run_tool(tool_name, params)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

