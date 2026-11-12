from __future__ import annotations

from typing import Any

from api import paths
from core.client import ApiClient


class VisaOrderApi:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def delete_order(self, visa_order_id: int) -> dict[str, Any]:
        return self._client.post(paths.VISA_ORDER_DELETE, params={"id": visa_order_id})
