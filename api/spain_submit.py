from __future__ import annotations

from typing import Any

from api import paths
from core.client import ApiClient


class SpainSubmitApi:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def find_have_time_querying(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(
            paths.SUBMIT_FIND_TIME_QUERYING,
            params={"visaOrderId": visa_order_id},
        )

    def submit(self, visa_order_id: int | None = None) -> dict[str, Any]:
        params = {"visaOrderId": visa_order_id} if visa_order_id is not None else None
        return self._client.post(paths.SUBMIT, params=params)

    def query_time(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(paths.SUBMIT_QUERY_TIME, params={"visaOrderId": visa_order_id})

    def submit_appointment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.post(paths.SUBMIT_APPOINTMENT, json_body=payload)

    def close_hosted(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(paths.SUBMIT_CLOSE_HOSTED, params={"visaOrderId": visa_order_id})

    def confirm_paid(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(paths.SUBMIT_CONFIRM_PAID, params={"visaOrderId": visa_order_id})

    def get_last_sync_appointment_task(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(
            paths.SUBMIT_LAST_SYNC_TASK,
            params={"visaOrderId": visa_order_id},
        )

    def update_hosted_times(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.post(paths.SUBMIT_UPDATE_HOSTED_TIMES, json_body=payload)
