from __future__ import annotations

from dataclasses import dataclass, field

from api.spain_order import SpainOrderApi
from api.visa_order import VisaOrderApi
from core.assertor import assert_success


@dataclass
class _OrderRecord:
    keep: bool = False
    apply_ids: list[int] = field(default_factory=list)


class OrderCleanup:
    """流程用例后置。先删除登记的申请人，再删除订单。"""

    def __init__(self, order_api: SpainOrderApi, visa_order_api: VisaOrderApi) -> None:
        self._order_api = order_api
        self._visa_order_api = visa_order_api
        self._orders: dict[int, _OrderRecord] = {}

    def register_order(self, visa_order_id: int, *, keep: bool = False) -> None:
        record = self._orders.setdefault(visa_order_id, _OrderRecord())
        if keep:
            record.keep = True

    def register_apply(self, visa_order_id: int, visa_order_apply_id: int) -> None:
        record = self._orders.setdefault(visa_order_id, _OrderRecord())
        if visa_order_apply_id not in record.apply_ids:
            record.apply_ids.append(visa_order_apply_id)

    def unregister_apply(self, visa_order_apply_id: int) -> None:
        for record in self._orders.values():
            if visa_order_apply_id in record.apply_ids:
                record.apply_ids.remove(visa_order_apply_id)

    def keep(self, visa_order_id: int) -> None:
        self.register_order(visa_order_id, keep=True)

    def cleanup(self) -> None:
        errors: list[str] = []
        for visa_order_id, record in self._orders.items():
            if record.keep:
                continue
            apply_failed = False
            for apply_id in record.apply_ids:
                error = self._delete_apply(apply_id)
                if error:
                    apply_failed = True
                    errors.append(error)
            if apply_failed:
                errors.append(f"订单 {visa_order_id} 仍有申请人删除失败，未删除订单")
                continue
            error = self._delete_order(visa_order_id)
            if error:
                errors.append(error)
        if errors:
            raise AssertionError("后置清理失败:\n" + "\n".join(errors))

    def _delete_apply(self, visa_order_apply_id: int) -> str | None:
        try:
            response = self._order_api.delete_apply(visa_order_apply_id)
            assert_success(response, expected={"code": 0})
        except Exception as exc:
            return f"删除申请人 {visa_order_apply_id} 失败: {exc}"
        return None

    def _delete_order(self, visa_order_id: int) -> str | None:
        try:
            response = self._visa_order_api.delete_order(visa_order_id)
            assert_success(response, expected={"code": 0})
        except Exception as exc:
            return f"删除订单 {visa_order_id} 失败: {exc}"
        return None
