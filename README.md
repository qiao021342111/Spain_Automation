# Spain Automation API Tests

Python + pytest + allure 接口自动化测试。

## 结构

```text
config/   环境与账号
core/     HTTP 客户端、session、断言
api/      业务接口封装
data/     参数化数据
tests/    用例
common/   日志与数据加载
scripts/  失败上下文导出（AI 排查）
.cursor/rules/  Agent 生成/排查规范
```

## 运行

```bash
pip install -r requirements.txt
brew install allure
pytest tests/test_spain_order.py tests/test_spain_submit.py --env=test --clean-alluredir
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

只跑这两个测试文件。`tests/test11.py` 会在导入时请求外部模型，不属于接口用例。

## 测试报告

原始结果在 `reports/allure-results`，静态报告在 `reports/allure-report`。`--clean-alluredir` 会清掉上一次的原始结果。

报告中每条接口调用包含：

| 内容 | 来源 |
|---|---|
| 环境 | `environment.properties`：`Environment`、`BaseURL`，对应 `--env` 和 `config.yaml` |
| 请求头 | `Content-Type`、`sessionId`、`visas_trace_id`。`sessionId` 的值写成 `***`。`visas_trace_id` 取自该次响应头，服务端生成，不回显客户端传入的值 |
| 请求参数 | query `params` 和 JSON body |
| 响应报文 | HTTP 状态码和响应体 |
| 期望结果 | 用例 `expected` |
| 实际结果 | 响应里的 `code`、`msg`、`data` |
| 断言信息 | 通过写「通过」；失败写断言差异。`TC_ORDER_018` 没有预约信时写明软断言，用例仍为通过 |

`TC_SUBMIT_001` 在报告中为跳过，原因是 QA 返回 HTTP 404。

## 登录

`conftest.py` 自动登录，从 `data.sessionId` 提取后注入 Header，无需单独登录用例。

登录参数在 `config/config.yaml` 中维护。

## 新增用例

1. 在 `data/` 添加 YAML 数据
2. 在 `tests/` 添加测试函数，调用 `api/` 封装方法

```python
response = order_api.create_order("Shanghai", "Individual", 1)
order_id = assert_success(response, expected={"code": 0, "data_type": "int"})
```

异常场景：

```python
from core.assertor import assert_busy

assert_busy(response)  # code=500, msg=服务繁忙
```

## 大模型协作（A/B 方案）

### 用例生成（Cursor Agent）

1. 打开 `Spain_TestDemo.md` 中带「待实现」的用例
2. 在对话中 @ `Spain_TestDemo.md`，并启用 YApi MCP 拉接口字段
3. 按 `.cursor/rules/spain-automation.mdc` 生成 YAML + pytest
4. 本地验证：`pytest -v -k TC_ORDER_xxx`

**示例提示词：**

```text
根据 Spain_TestDemo.md 的 TC_ORDER_008，用 YApi 拉 saveOrder 字段，
生成 data/spain_order/save_order.yaml 和 tests 中的 parametrized 用例。
不要写登录用例，不要改 config 密码。
```

### 失败排查

1. 运行 `pytest` 失败后，查看 `reports/last_failure.json`
2. 或执行：

```bash
python scripts/dump_failure_context.py
```

3. 将输出粘贴到 Cursor，要求「最小 diff 修复」并回归 `pytest -m smoke`

## 已封装接口（与 YApi cat_625/629/633 对齐，共 22 个）

**订单：** createOrder、saveOrder、saveApply、deleteApply、getOrderDetail、listOrder、getApplyDetail、setPosition、downloadFile、exportNameList、batchDownloadFile、countWaitPayOrder  

**预约提交/查询：** findHaveTimeQuerying、submit、queryTime、submitAppointment、closeHosted、confirmPaid、getLastSyncAppointmentTask、updateHostedTimes  

详见 `api/paths.py`、`Spain_TestDemo.md`。

## 日志

使用标准库 `logging` 写入 `logs/api_test.log`。Allure 报告中的请求、响应和断言见上文「测试报告」。
