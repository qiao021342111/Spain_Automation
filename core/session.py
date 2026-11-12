from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SessionManager:
    session_key: str = "sessionId"
    session_id: str = ""

    def set_session_id(self, session_id: str) -> None:
        self.session_id = session_id

    @property
    def is_authenticated(self) -> bool:
        return bool(self.session_id)

    def apply_header(self, headers: dict[str, str]) -> dict[str, str]:
        if not self.is_authenticated:
            return headers
        return {**headers, self.session_key: self.session_id}
