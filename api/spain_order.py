from __future__ import annotations

from typing import Any

from api import paths
from core.client import ApiClient


PASSPORT_URL = (
    "http://bn-visas.oss-cn-hangzhou.aliyuncs.com/browser-upload/"
    "17921398053500684148a-140a-232e-9753-8fd9f8686dfb.jpg"
)


class SpainOrderApi:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def create_order(
        self,
        consulate_city: str | None = None,
        appointment_type: str | None = None,
        apply_num: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if consulate_city is not None:
            body["consulateCity"] = consulate_city
        if appointment_type is not None:
            body["appointmentType"] = appointment_type
        if apply_num is not None:
            body["applyNum"] = apply_num
        return self._client.post(paths.ORDER_CREATE, json_body=body)

    def save_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.post(paths.ORDER_SAVE, json_body=payload)

    def save_apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.post(paths.ORDER_SAVE_APPLY, json_body=payload)

    def create_apply_info(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(
            paths.APPLY_CREATE_INFO,
            json_body={
                "visaOrderId": visa_order_id,
                "passportUrl": PASSPORT_URL,
            },
        )

    def delete_apply(self, visa_order_apply_id: int) -> dict[str, Any]:
        return self._client.post(
            paths.ORDER_DELETE_APPLY,
            params={"visaOrderApplyId": visa_order_apply_id},
        )

    def get_order_detail(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(paths.ORDER_DETAIL, params={"visaOrderId": visa_order_id})

    def list_order(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client.post(paths.ORDER_LIST, json_body=payload or {})

    def get_apply_detail(self, visa_order_apply_id: int) -> dict[str, Any]:
        return self._client.post(
            paths.ORDER_APPLY_DETAIL,
            params={"visaOrderApplyId": visa_order_apply_id},
        )

    def set_position(self, visa_order_apply_id: int, position: int) -> dict[str, Any]:
        return self._client.post(
            paths.ORDER_SET_POSITION,
            params={"visaOrderApplyId": visa_order_apply_id, "position": position},
        )

    def download_file(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(paths.ORDER_DOWNLOAD_FILE, params={"visaOrderId": visa_order_id})

    def export_name_list(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client.post(paths.ORDER_EXPORT_NAME_LIST, json_body=payload or {})

    def batch_download_file(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client.post(paths.ORDER_BATCH_DOWNLOAD, json_body=payload or {})

    def count_wait_pay_order(self) -> dict[str, Any]:
        return self._client.post(paths.ORDER_COUNT_WAIT_PAY)
