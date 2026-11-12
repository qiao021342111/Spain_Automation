from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILE = Path(__file__).resolve().parent / "config.yaml"
ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


@dataclass
class AccountConfig:
    login_account: str
    login_password: str


@dataclass
class Settings:
    env_name: str
    base_url: str
    login_api: str
    login_request: dict[str, Any]
    timeout: int
    session_key: str
    log_enabled: bool
    log_level: str
    log_dir: str
    account: AccountConfig = field(default_factory=lambda: AccountConfig("", ""))


def _resolve_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        return ENV_VAR_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def get_settings(env_name: str | None = None) -> Settings:
    env_name = env_name or os.getenv("TEST_ENV", "test")

    with CONFIG_FILE.open(encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    defaults = _resolve_env_vars(raw.get("defaults", {}))
    environments = _resolve_env_vars(raw.get("environments", {}))

    if env_name not in environments:
        available = ", ".join(environments.keys())
        raise ValueError(f"Unknown environment '{env_name}'. Available: {available}")

    env_cfg = environments[env_name]
    log_cfg = defaults.get("log", {})
    account_cfg = env_cfg.get("accounts", {}).get("default", {})

    return Settings(
        env_name=env_name,
        base_url=env_cfg["base_url"].rstrip("/"),
        login_api=env_cfg["login_api"],
        login_request=dict(env_cfg.get("login_request", {})),
        timeout=int(defaults.get("timeout", 30)),
        session_key=defaults.get("session_key", "sessionId"),
        log_enabled=bool(log_cfg.get("enabled", True)),
        log_level=str(log_cfg.get("level", "INFO")),
        log_dir=str(log_cfg.get("dir", "logs")),
        account=AccountConfig(
            login_account=str(account_cfg.get("login_account", "")),
            login_password=str(account_cfg.get("login_password", "")),
        ),
    )
