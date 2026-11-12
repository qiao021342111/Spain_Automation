from __future__ import annotations

from typing import Any

import allure

from config.settings import Settings
from core.assertor import assert_success
from core.client import ApiClient
from core.session import SessionManager


class AuthApi:
    def __init__(
        self,
        client: ApiClient,
        settings: Settings,
        session_manager: SessionManager,
    ) -> None:
        self.client = client
        self.settings = settings
        self.session_manager = session_manager

    def login(self) -> dict[str, Any]:
        with allure.step("登录并提取 sessionId"):
            response = self.client.post(
                self.settings.login_api,
                json_body={
                    "loginAccount": self.settings.account.login_account,
                    "loginPassword": self.settings.account.login_password,
                    **self.settings.login_request,
                },
                auth=False,
            )
            data = assert_success(response)
            self.session_manager.set_session_id(str(data[self.settings.session_key]))
            allure.attach(
                self.session_manager.session_id,
                name="sessionId",
                attachment_type=allure.attachment_type.TEXT,
            )
            return data
