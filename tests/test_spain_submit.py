from __future__ import annotations

from typing import Any

import allure
import pytest

from api.spain_order import SpainOrderApi
from api.spain_submit import SpainSubmitApi
from common.data_driver import parametrized_cases
from core.assertor import assert_success


def _saved_order(order_api: SpainOrderApi, setup: dict[str, Any]) -> int:
    create_setup = setup.get("create_order", {})
    create_response = order_api.create_order(
        consulate_city=create_setup.get("consulateCity", "Shanghai"),
        appointment_type=create_setup.get("appointmentType", "Individual"),
        apply_num=create_setup.get("applyNum", 1),
    )
    visa_order_id = assert_success(create_response, expected={"code": 0, "data_type": "int"})
    assert isinstance(visa_order_id, int)
    if save_order := setup.get("save_order"):
        saved = assert_success(
            order_api.save_order({**save_order, "visaOrderId": visa_order_id}),
            expected={"code": 0, "data_type": "bool"},
        )
        assert saved is True
    return visa_order_id


def _assert_case(response: dict[str, Any], case: dict[str, Any]) -> None:
    expected = dict(case.get("expected") or {})
    data_is_null = expected.pop("data_is_null", False)
    data = assert_success(response, expected=expected)
    if data_is_null:
        assert data is None


@pytest.mark.submit
@pytest.mark.skip(reason="QA 环境 /spain/submit/findHaveTimeQuerying 返回 HTTP 404")
@pytest.mark.parametrize("case", parametrized_cases("spain_submit/find_time_querying.yaml"))
def test_find_have_time_querying(
    case: dict[str, Any],
    order_api: SpainOrderApi,
    submit_api: SpainSubmitApi,
) -> None:
    allure.dynamic.title(case["title"])
    visa_order_id = _saved_order(order_api, case.get("setup", {}))
    assert_success(
        submit_api.find_have_time_querying(visa_order_id),
        expected=case.get("expected"),
    )


@pytest.mark.submit
@pytest.mark.parametrize("case", parametrized_cases("spain_submit/submit.yaml"))
def test_submit(case: dict[str, Any], order_api: SpainOrderApi, submit_api: SpainSubmitApi) -> None:
    allure.dynamic.title(case["title"])
    visa_order_id = _saved_order(order_api, case["setup"])
    _assert_case(submit_api.submit(visa_order_id), case)


@pytest.mark.submit
@pytest.mark.parametrize("case", parametrized_cases("spain_submit/query_time.yaml"))
def test_query_time(case: dict[str, Any], order_api: SpainOrderApi, submit_api: SpainSubmitApi) -> None:
    allure.dynamic.title(case["title"])
    visa_order_id = _saved_order(order_api, case["setup"])
    _assert_case(submit_api.query_time(visa_order_id), case)


@pytest.mark.submit
@pytest.mark.parametrize("case", parametrized_cases("spain_submit/submit_appointment.yaml"))
def test_submit_appointment(
    case: dict[str, Any],
    order_api: SpainOrderApi,
    submit_api: SpainSubmitApi,
) -> None:
    allure.dynamic.title(case["title"])
    visa_order_id = _saved_order(order_api, case["setup"])
    _assert_case(submit_api.submit_appointment({**case["request"], "visaOrderId": visa_order_id}), case)


@pytest.mark.submit
@pytest.mark.parametrize("case", parametrized_cases("spain_submit/hosted_pay.yaml"))
def test_hosted_pay(case: dict[str, Any], order_api: SpainOrderApi, submit_api: SpainSubmitApi) -> None:
    allure.dynamic.title(case["title"])
    visa_order_id = _saved_order(order_api, case["setup"])
    case_id = case["case_id"]
    if case_id == "TC_SUBMIT_006":
        response = submit_api.close_hosted(visa_order_id)
    elif case_id == "TC_SUBMIT_007":
        response = submit_api.confirm_paid(visa_order_id)
    elif case_id == "TC_SUBMIT_008":
        response = submit_api.get_last_sync_appointment_task(visa_order_id)
    else:
        response = submit_api.update_hosted_times({**case["request"], "visaOrderId": visa_order_id})
    _assert_case(response, case)
