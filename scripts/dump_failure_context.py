#!/usr/bin/env python3
"""打印最近一次 pytest 失败上下文，供 Cursor/大模型排查。"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILURE_FILE = ROOT / "reports" / "last_failure.json"
SESSION_PATTERN = re.compile(r'"sessionId"\s*:\s*"[^"]+"')


def _redact(text: str) -> str:
    return SESSION_PATTERN.sub('"sessionId": "***"', text)


def main() -> int:
    if not FAILURE_FILE.exists():
        print("未找到 reports/last_failure.json，请先运行 pytest 并产生失败用例。")
        return 1

    data = json.loads(FAILURE_FILE.read_text(encoding="utf-8"))
    print("# 最近失败上下文\n")
    print(f"- test: {data.get('test_name')}")
    print(f"- case_id: {data.get('case_id') or '(无)'}")
    print(f"- time: {data.get('timestamp')}\n")
    print("## traceback\n")
    print(data.get("longrepr", ""))
    print("\n## api_test.log (tail)\n")
    for line in data.get("last_log_lines", []):
        print(_redact(line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
