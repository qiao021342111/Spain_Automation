import json
from datetime import datetime, timezone
from pathlib import Path

import allure
import pytest

from api.auth import AuthApi
from api.spain_order import SpainOrderApi
from api.spain_submit import SpainSubmitApi
from api.visa_order import VisaOrderApi
from tests.order_cleanup import OrderCleanup
from common.logger import setup_logger
from config.settings import Settings, get_settings
from core.assertor import assert_success
from core.client import ApiClient
from core.session import SessionManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FAILURE_FILE = PROJECT_ROOT / "reports" / "last_failure.json"
ALLURE_RESULTS = PROJECT_ROOT / "reports" / "allure-results"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--env", action="store", default="test", help="test or prod")


def pytest_sessionstart(session: pytest.Session) -> None:
    settings = get_settings(session.config.getoption("--env"))
    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)
    environment = "\n".join(
        [
            f"Environment={settings.env_name}",
            f"BaseURL={settings.base_url}",
        ]
    )
    (ALLURE_RESULTS / "environment.properties").write_text(environment + "\n", encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    outcome = yield
    report = outcome.get_result()
    if report.when not in ("setup", "call") or not report.failed:
        return

    settings = get_settings(item.config.getoption("--env"))
    log_file = PROJECT_ROOT / settings.log_dir / "api_test.log"
    last_log_lines: list[str] = []
    if log_file.exists():
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        last_log_lines = lines[-40:]

    case_id = ""
    if hasattr(item, "callspec") and item.callspec is not None:
        case_id = item.callspec.id or ""

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_name": item.nodeid,
        "case_id": case_id,
        "outcome": report.outcome,
        "longrepr": str(report.longrepr)[:2000] if report.longrepr else "",
        "last_log_lines": last_log_lines,
    }
    FAILURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    FAILURE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if report.when == "call" and report.longrepr:
        allure.attach(
            str(report.longrepr)[:2000],
            name="断言信息",
            attachment_type=allure.attachment_type.TEXT,
        )


@pytest.fixture(scope="session")
def settings(pytestconfig: pytest.Config) -> Settings:
    return get_settings(pytestconfig.getoption("--env"))


@pytest.fixture(scope="session")
def session_manager(settings: Settings) -> SessionManager:
    return SessionManager(session_key=settings.session_key)


@pytest.fixture(scope="session")
def api_client(settings: Settings, session_manager: SessionManager) -> ApiClient:
    logger = setup_logger("api_test", settings.log_dir, settings.log_level)
    client = ApiClient(settings, session_manager, logger)
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_api(api_client: ApiClient, settings: Settings, session_manager: SessionManager) -> AuthApi:
    return AuthApi(api_client, settings, session_manager)


@pytest.fixture(scope="session", autouse=True)
def auto_login(auth_api: AuthApi, session_manager: SessionManager) -> None:
    auth_api.login()
    assert session_manager.is_authenticated, "登录失败，未获取到 sessionId"


@pytest.fixture(scope="session")
def order_api(api_client: ApiClient) -> SpainOrderApi:
    return SpainOrderApi(api_client)


@pytest.fixture(scope="session")
def submit_api(api_client: ApiClient) -> SpainSubmitApi:
    return SpainSubmitApi(api_client)


@pytest.fixture(scope="session")
def visa_order_api(api_client: ApiClient) -> VisaOrderApi:
    return VisaOrderApi(api_client)


@pytest.fixture
def order_cleanup(order_api: SpainOrderApi, visa_order_api: VisaOrderApi) -> OrderCleanup:
    cleaner = OrderCleanup(order_api, visa_order_api)
    yield cleaner
    cleaner.cleanup()


@pytest.fixture
def created_order(order_api: SpainOrderApi) -> int:
    response = order_api.create_order("Shanghai", "Individual", 1)
    visa_order_id = assert_success(response, expected={"code": 0, "data_type": "int"})
    assert isinstance(visa_order_id, int)
    return visa_order_id
