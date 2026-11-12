from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_yaml_cases(relative_path: str) -> list[dict[str, Any]]:
    file_path = DATA_DIR / relative_path
    with file_path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or []

    if not isinstance(data, list):
        raise ValueError(f"Test data must be a list: {file_path}")

    for index, case in enumerate(data):
        case.setdefault("case_id", f"CASE_{index + 1:03d}")
    return data


def parametrized_cases(relative_path: str) -> list[Any]:
    params: list[Any] = []
    for case in load_yaml_cases(relative_path):
        marks = [
            getattr(pytest.mark, tag)()
            for tag in case.get("tags", [])
            if hasattr(pytest.mark, tag)
        ]
        params.append(pytest.param(case, marks=marks, id=case["case_id"]))
    return params
