from __future__ import annotations

import json
from typing import Any

import allure

DATA_TYPES = {"int": int, "dict": dict, "bool": bool}
BUSY_EXPECTED = {"code": 500, "msg": "服务繁忙"}
_SECRET_KEYS = {"loginpassword", "password", "sessionid"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***" if key.lower() in _SECRET_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _brief_data(data: Any) -> Any:
    if isinstance(data, str) and data.startswith("%PDF"):
        return f"PDF {len(data)} bytes"
    data = _redact(data)
    if isinstance(data, (dict, list)):
        text = json.dumps(data, ensure_ascii=False, default=str)
        if len(text) > 1500:
            return f"{type(data).__name__} len={len(text)}"
    return data


def _actual_result(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "keys": list(response.keys()),
        "code": response.get("code"),
        "msg": response.get("msg") if "msg" in response else None,
        "data": _brief_data(response.get("data")),
    }


def _attach_assert(expected: dict[str, Any], response: dict[str, Any], message: str) -> None:
    allure.attach(
        json.dumps(expected, ensure_ascii=False, indent=2, default=str),
        name="期望结果",
        attachment_type=allure.attachment_type.JSON,
    )
    allure.attach(
        json.dumps(_actual_result(response), ensure_ascii=False, indent=2, default=str),
        name="实际结果",
        attachment_type=allure.attachment_type.JSON,
    )
    allure.attach(message, name="断言信息", attachment_type=allure.attachment_type.TEXT)


def assert_success(response: dict[str, Any], expected: dict[str, Any] | None = None) -> Any:
    expected = expected or {}
    actual_code = response.get("code")
    expected_code = expected.get("code", 0)

    try:
        assert actual_code == expected_code, (
            f"业务码不匹配: expected={expected_code}, actual={actual_code}, "
            f"msg={response.get('msg')}, trace={response.get('trace')}"
        )

        if "msg" in expected:
            assert response.get("msg") == expected["msg"], (
                f"msg 不匹配: expected={expected['msg']}, actual={response.get('msg')}"
            )

        data = response.get("data")
        if "data_type" in expected:
            data_type = DATA_TYPES[expected["data_type"]]
            assert data is not None, "响应 data 为空"
            assert isinstance(data, data_type), f"data 类型应为 {data_type}, 实际为 {type(data)}"
    except AssertionError as exc:
        _attach_assert(expected, response, f"失败：{exc}")
        raise

    _attach_assert(expected, response, "通过")
    return data


def assert_busy(response: dict[str, Any]) -> None:
    assert_success(response, expected=BUSY_EXPECTED)
