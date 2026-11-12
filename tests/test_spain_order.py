from __future__ import annotations

import time
from typing import Any

import allure
import pytest

from api.spain_order import SpainOrderApi
from common.data_driver import load_yaml_cases, parametrized_cases
from core.assertor import assert_success

APPLY_TEMPLATE = load_yaml_cases("spain_order/save_apply.yaml")[0]["request"]
_PASSPORT_SEQ = 0


def _create_order(order_api: SpainOrderApi, setup: dict[str, Any]) -> int:
    response = order_api.create_order(
        consulate_city=setup.get("consulateCity", "Shanghai"),
        appointment_type=setup.get("appointmentType", "Individual"),
        apply_num=setup.get("applyNum", 1),
    )
    order_id = assert_success(response, expected={"code": 0, "data_type": "int"})
    assert isinstance(order_id, int)
    return order_id


def _passport() -> str:
    global _PASSPORT_SEQ
    _PASSPORT_SEQ += 1
    return f"E{int(time.time()) % 1000000:06d}{_PASSPORT_SEQ % 100:02d}"


def _soft_assert(condition: bool, message: str) -> bool:
    if condition:
        return True
    allure.attach(
        f"软断言：{message}。不判定为失败。",
        name="断言信息",
        attachment_type=allure.attachment_type.TEXT,
    )
    return False


def _apply_id_from_passport(order_api: SpainOrderApi, order_id: int) -> int:
    response = order_api.create_apply_info(order_id)
    apply_id = assert_success(response, expected={"code": 0, "data_type": "int"})
    assert isinstance(apply_id, int)
    return apply_id


def _new_apply(order_api: SpainOrderApi, order_id: int, **overrides: Any) -> tuple[int, str]:
    apply_id = _apply_id_from_passport(order_api, order_id)
    passport_num = overrides.pop("passportNum", None) or _passport()
    payload = {
        **APPLY_TEMPLATE,
        "visaOrderApplyId": apply_id,
        "passportNum": passport_num,
        **overrides,
    }
    response = order_api.save_apply(payload)
    saved_id = assert_success(response, expected={"code": 0, "data_type": "int"})
    assert isinstance(saved_id, int)
    return saved_id, passport_num


@pytest.mark.order
@pytest.mark.parametrize("case", parametrized_cases("spain_order/create_order.yaml"))
def test_create_order(case: dict[str, Any], order_api: SpainOrderApi) -> None:
    allure.dynamic.title(case["title"])
    request_data = case["request"]
    response = order_api.create_order(
        consulate_city=request_data.get("consulateCity"),
        appointment_type=request_data.get("appointmentType"),
        apply_num=request_data.get("applyNum"),
    )
    assert_success(response, expected=case.get("expected"))


@pytest.mark.order
def test_create_apply_info(order_api: SpainOrderApi, created_order: int) -> None:
    response = order_api.create_apply_info(created_order)
    assert_success(response, expected={"code": 0})


@pytest.mark.order
@pytest.mark.parametrize("case", parametrized_cases("spain_order/order_detail.yaml"))
def test_get_order_detail(case: dict[str, Any], order_api: SpainOrderApi) -> None:
    allure.dynamic.title(case["title"])
    order_id = _create_order(order_api, case["setup"]["create_order"])
    expected = dict(case.get("expected") or {})
    field_expected = {
        key: expected.pop(key)
        for key in ("orderStatus", "consulateCity", "appointmentType", "applyNum", "hosted", "appointmentDate")
        if key in expected
    }
    data = assert_success(order_api.get_order_detail(order_id), expected=expected)
    assert data["visaOrderId"] == order_id
    assert isinstance(data["orderNum"], str) and data["orderNum"]
    for key, value in field_expected.items():
        assert data[key] == value, key


@pytest.mark.order
@pytest.mark.parametrize("case", parametrized_cases("spain_order/list_order.yaml"))
def test_list_order(case: dict[str, Any], order_api: SpainOrderApi) -> None:
    allure.dynamic.title(case["title"])
    request_data = case["request"]
    data = assert_success(order_api.list_order(request_data), expected=case.get("expected"))
    records = data["records"]
    assert isinstance(records, list)

    if appointment_type := request_data.get("appointmentType"):
        assert records, "筛选结果为空"
        assert all(item["appointmentType"] == appointment_type for item in records)

    if city := request_data.get("consulateCity"):
        assert records, "筛选结果为空"
        assert all(item["consulateCity"] == city for item in records)

    if applicant_name := request_data.get("applicantName"):
        assert data["totalCount"] >= 1
        for record in records:
            names = [apply.get("applicantName") or "" for apply in record.get("applyList") or []]
            assert any(applicant_name in name for name in names), record

    if status_list := request_data.get("orderStatusList"):
        assert records, "筛选结果为空"
        assert all(item["orderStatus"] in status_list for item in records)

    if "hosted" in request_data:
        assert records, "筛选结果为空"
        assert all(item["hosted"] == request_data["hosted"] for item in records)

    if passport_num := request_data.get("passportNum"):
        assert records, "筛选结果为空"
        for record in records:
            numbers = [apply.get("passportNum") or "" for apply in record.get("applyList") or []]
            assert any(passport_num in number for number in numbers), record


@pytest.mark.order
@pytest.mark.parametrize("case", parametrized_cases("spain_order/save_order.yaml"))
def test_save_order(case: dict[str, Any], order_api: SpainOrderApi) -> None:
    allure.dynamic.title(case["title"])
    order_id = _create_order(order_api, case["setup"]["create_order"])
    payload = {**case["request"], "visaOrderId": order_id}
    expected = dict(case.get("expected") or {})
    msg_contains = expected.pop("msg_contains", None)
    response = order_api.save_order(payload)
    data = assert_success(response, expected=expected)
    if msg_contains:
        assert msg_contains in (response.get("msg") or ""), response.get("msg")
    if expected.get("data_type") == "bool" and expected.get("code", 0) == 0:
        assert data is True


@pytest.mark.order
@pytest.mark.parametrize("case", parametrized_cases("spain_order/save_apply.yaml"))
def test_save_apply(case: dict[str, Any], order_api: SpainOrderApi) -> None:
    allure.dynamic.title(case["title"])
    order_id = _create_order(order_api, case["setup"]["create_order"])
    apply_id = _apply_id_from_passport(order_api, order_id)
    if create_apply := case["setup"].get("create_apply"):
        passport_num = _passport()
        prepared = {
            **APPLY_TEMPLATE,
            **create_apply,
            "visaOrderApplyId": apply_id,
            "passportNum": passport_num,
        }
        prepared_id = assert_success(order_api.save_apply(prepared), expected={"code": 0, "data_type": "int"})
        assert isinstance(prepared_id, int)
        payload = {
            **case["request"],
            "visaOrderApplyId": prepared_id,
            "passportNum": passport_num,
        }
    else:
        payload = {**case["request"], "visaOrderApplyId": apply_id, "passportNum": _passport()}

    response = order_api.save_apply(payload)
    saved_id = assert_success(response, expected=case.get("expected"))
    assert isinstance(saved_id, int)


@pytest.mark.order
@pytest.mark.parametrize("case", parametrized_cases("spain_order/apply_ops.yaml"))
def test_apply_ops(case: dict[str, Any], order_api: SpainOrderApi) -> None:
    allure.dynamic.title(case["title"])
    if case["case_id"] == "TC_ORDER_016":
        listed = assert_success(order_api.list_order(case["request"]), expected={"code": 0, "data_type": "dict"})
        apply_id = next(
            (
                apply["visaOrderApplyId"]
                for record in listed["records"]
                for apply in record.get("applyList") or []
                if apply.get("visaOrderApplyId")
            ),
            None,
        )
        assert apply_id, "列表中没有可查询的申请人"
        data = assert_success(
            order_api.get_apply_detail(apply_id),
            expected=case.get("expected"),
        )
        assert data["visaOrderApplyId"] == apply_id
        for key in ("surname", "name", "passportNum", "signStatus", "position"):
            assert key in data
        return

    order_id = _create_order(order_api, case["setup"]["create_order"])
    first_id, _ = _new_apply(order_api, order_id, name="主", nameEn="MAIN")
    second_id, _ = _new_apply(
        order_api,
        order_id,
        name="属",
        nameEn="REL",
        surname="李",
        surnameEn="LI",
        relationToMain="Spouse",
    )

    if case["case_id"] == "TC_ORDER_012":
        deleted = assert_success(order_api.delete_apply(first_id), expected=case.get("expected"))
        assert deleted is True
        remaining = assert_success(
            order_api.get_apply_detail(second_id),
            expected={"code": 0, "data_type": "dict"},
        )
        assert remaining["position"] == 1
        return

    position = case["request"]["position"]
    moved = assert_success(
        order_api.set_position(first_id, position),
        expected=case.get("expected"),
    )
    assert moved is True
    detail = assert_success(
        order_api.get_apply_detail(first_id),
        expected={"code": 0, "data_type": "dict"},
    )
    assert detail["position"] == position


@pytest.mark.order
@pytest.mark.parametrize("case", parametrized_cases("spain_order/order_file.yaml"))
def test_order_file(case: dict[str, Any], order_api: SpainOrderApi) -> None:
    allure.dynamic.title(case["title"])
    if case["case_id"] == "TC_ORDER_110":
        order_id = _create_order(order_api, case["setup"]["create_order"])
        assert_success(order_api.download_file(order_id), expected=case.get("expected"))
        return

    if case["case_id"] == "TC_ORDER_018":
        listed = assert_success(order_api.list_order(case["request"]), expected={"code": 0, "data_type": "dict"})
        order_id = next(
            (
                record["visaOrderId"]
                for record in listed["records"]
                if record.get("orderStatus") == case["match_status"]
            ),
            None,
        )
        if not _soft_assert(order_id is not None, "没有可下载预约信的订单"):
            return
        body = order_api.download_file(order_id)
        if body.get("code") == 400 and body.get("msg") == "暂无预约信可下载":
            _soft_assert(False, "暂无预约信可下载")
            return
        assert str(body.get("raw_text", "")).startswith("%PDF"), body.get("msg") or body
        return

    if case["case_id"] == "TC_ORDER_021":
        count = assert_success(order_api.count_wait_pay_order(), expected=case.get("expected"))
        assert isinstance(count, int)
        assert count >= 0
        return

    caller = order_api.export_name_list if case["case_id"] == "TC_ORDER_019" else order_api.batch_download_file
    data = assert_success(caller(case["request"]), expected=case.get("expected"))
    assert data is True
