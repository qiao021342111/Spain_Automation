from __future__ import annotations

import json
import logging
from typing import Any

import allure
import requests

from config.settings import Settings
from core.session import SessionManager

_SECRET_KEYS = {"loginpassword", "password", "sessionid"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items() if key.lower() not in _SECRET_KEYS}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _brief_data(data: Any) -> str | None:
    if data is None:
        return None
    if isinstance(data, str) and data.startswith("%PDF"):
        return f"PDF {len(data)} bytes"
    if isinstance(data, (int, float, bool)):
        return json.dumps(data, ensure_ascii=False)
    if isinstance(data, str):
        return json.dumps(data[:120], ensure_ascii=False)
    if isinstance(data, list):
        return f"list[{len(data)}]"
    if isinstance(data, dict):
        safe = _redact(data)
        text = json.dumps(safe, ensure_ascii=False, default=str)
        if len(text) > 180:
            return f"dict[{len(safe)} keys]"
        return text
    return type(data).__name__


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    body = payload.get("body")
    raw_text = body.get("raw_text") if isinstance(body, dict) else None
    if not isinstance(raw_text, str) or not raw_text.startswith("%PDF"):
        return payload
    stored = dict(payload)
    stored["body"] = {**body, "raw_text": f"<PDF {len(raw_text)} bytes>"}
    return stored


def _report_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in headers.items():
        masked[key] = "***" if key.lower() in _SECRET_KEYS else value
    return masked


def _allure_json(name: str, payload: Any) -> None:
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def _summary(label: str, path: str, payload: dict[str, Any]) -> str:
    if label == "REQUEST":
        shown: dict[str, Any] = {}
        params = payload.get("params") or {}
        if params:
            shown["params"] = params
        json_body = payload.get("json")
        if isinstance(json_body, dict):
            shown.update(_redact(json_body))
        elif json_body is not None:
            shown["json"] = json_body
        if not shown:
            return f"[Request] POST {path}"
        return f"[Request] POST {path} -> {json.dumps(shown, ensure_ascii=False, default=str)}"

    body = payload.get("body")
    if isinstance(body, dict) and isinstance(body.get("raw_text"), str) and body["raw_text"].startswith("%PDF"):
        return f"[Response] POST {path} -> PDF {len(body['raw_text'])} bytes"
    if not isinstance(body, dict):
        return f"[Response] POST {path} -> status={payload.get('status_code')}"

    parts = [f"code={body.get('code')}"]
    if body.get("msg"):
        parts.append(f"msg={body.get('msg')}")
    data_text = _brief_data(body.get("data"))
    if data_text is not None:
        parts.append(f"data={data_text}")
    return f"[Response] POST {path} -> " + ", ".join(parts)


class ApiClient:
    def __init__(
        self,
        settings: Settings,
        session_manager: SessionManager,
        logger: logging.Logger,
    ) -> None:
        self.settings = settings
        self.session_manager = session_manager
        self.logger = logger
        self._session = requests.Session()

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.settings.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if auth:
            headers = self.session_manager.apply_header(headers)

        with allure.step(f"POST {path}"):
            request_payload = {
                "url": url,
                "headers": headers,
                "params": params or {},
                "json": json_body,
            }
            self._log("REQUEST", path, request_payload, attach_headers=False)

            response = self._session.post(
                url,
                params=params,
                json=json_body,
                headers=headers,
                timeout=self.settings.timeout,
            )
            response.raise_for_status()

            trace_id = response.headers.get("visas_trace_id")
            if trace_id:
                headers = {**headers, "visas_trace_id": trace_id}
            if self.settings.log_enabled:
                _allure_json("请求头", _report_headers(headers))

            try:
                body = response.json()
            except ValueError:
                body = {"raw_text": response.text}

            self._log("RESPONSE", path, {"status_code": response.status_code, "body": body})
            return body

    def _log(
        self,
        label: str,
        path: str,
        payload: dict[str, Any],
        *,
        attach_headers: bool = True,
    ) -> None:
        if not self.settings.log_enabled:
            return

        stored = _sanitize_payload(payload)
        text = json.dumps(stored, ensure_ascii=False, default=str)
        file_logger = getattr(self.logger, "file", None)
        if file_logger is not None:
            file_logger.info("%s -> %s", label, text)
        self.logger.info(_summary(label, path, payload))
        if label == "REQUEST":
            if attach_headers:
                _allure_json("请求头", _report_headers(stored.get("headers") or {}))
            _allure_json(
                "请求参数",
                {"params": stored.get("params") or {}, "json": stored.get("json")},
            )
            return
        _allure_json(
            "响应报文",
            {"status_code": stored.get("status_code"), "body": _redact(stored.get("body"))},
        )

    def close(self) -> None:
        self._session.close()
