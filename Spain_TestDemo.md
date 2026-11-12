# 西班牙预约接口测试用例

> 测试环境：`http://visas-api.qa.visaapp6.com`  
> YApi 文档：[项目 16 - 西班牙预约](http://yapi.dev.visaapp6.com/project/16/interface/api)  
> 自动化框架：Python + pytest + allure

---

## 1. 前置条件

| 项目 | 说明 |
|------|------|
| 鉴权方式 | Header 携带 `sessionId` |
| 成功响应 | `{ "code": 0, "msg": "成功", "data": ..., "trace": "..." }` |
| 异常响应 | `{ "code": 500, "msg": "服务繁忙" }` |

> 登录仅作为前置鉴权步骤，不在本文档中编写登录接口测试用例。

---

## 2. 用例总览

| 模块 | 分类 | 接口数 | 用例数 | 已实现 | 待实现 |
|------|------|--------|--------|--------|--------|
| 订单 | cat_633 | 12 | 21 | 17 | 4 |
| 预约提交 | cat_629 | 7 | 11 | 0 | 11 |
| 预约查询 | cat_625 | 1 | 1 | 0 | 1 |
| **合计** | | **20** | **33** | **17** | **16** |

> **api 封装**：cat_625/629/633 共 20 个接口已与 YApi 对齐（`api/paths.py`）。订单 4 条待实现是 `saveApply` 新建申请人：QA 返回 `400 无申请人id`，用例已编写并标记 xfail。

---

## 3. 订单接口用例（cat_633）

### 3.1 创建订单 `POST /spain/order/createOrder`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_001 | 创建个人订单-上海领馆-1人 | smoke | ✅ 已实现 |
| TC_ORDER_002 | 创建家庭订单-北京领馆-3人 | P1 | ✅ 已实现 |
| TC_ORDER_005 | 创建个人订单-广州领馆-1人 | P2 | ✅ 已实现 |
| TC_ORDER_006 | 创建家庭订单-人数边界值6人 | P2 | ✅ 已实现 |
| TC_ORDER_007 | 创建订单-人数超限7人（异常） | P2 | ✅ 已实现 |

#### TC_ORDER_001 创建个人订单

**请求体：**
```json
{
  "consulateCity": "Shanghai",
  "appointmentType": "Individual",
  "applyNum": 1
}
```

**预期结果：**
- `code = 0`
- `data` 为整数（订单 ID）

**自动化：** `data/spain_order/create_order.yaml` → `test_create_order`

---

#### TC_ORDER_002 创建家庭订单

**请求体：**
```json
{
  "consulateCity": "Beijing",
  "appointmentType": "Family",
  "applyNum": 3
}
```

**预期结果：**
- `code = 0`
- `data` 为整数（订单 ID）

**自动化：** `data/spain_order/create_order.yaml` → `test_create_order`

---

#### TC_ORDER_005 创建个人订单-广州领馆

**请求体：**
```json
{
  "consulateCity": "Guangzhou",
  "appointmentType": "Individual",
  "applyNum": 1
}
```

**预期结果：** `code = 0`，`data` 为订单 ID

---

#### TC_ORDER_006 创建家庭订单-人数边界值6人

**请求体：**
```json
{
  "consulateCity": "Shanghai",
  "appointmentType": "Family",
  "applyNum": 6
}
```

**预期结果：** `code = 0`，`data` 为订单 ID

---

#### TC_ORDER_007 创建订单-人数超限（异常）

**请求体：**
```json
{
  "consulateCity": "Shanghai",
  "appointmentType": "Individual",
  "applyNum": 7
}
```

**预期结果：** `code = 41008`，`msg` 为 `[applyNum]:人数最多 6 人`

**自动化：** `data/spain_order/create_order.yaml` → `test_create_order`

---

### 3.2 保存订单信息 `POST /spain/order/saveOrder`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_008 | 保存订单基本信息 | P1 | ✅ 已实现 |
| TC_ORDER_009 | 保存订单-缺少必填字段（异常） | P2 | ✅ 已实现 |

#### TC_ORDER_008 保存订单基本信息

**前置：** 已创建订单，获取 `visaOrderId`

**请求体：**
```json
{
  "visaOrderId": 19428,
  "visaCategory": "Schengen Visa",
  "appointmentCategory": "Normal",
  "visaSubType": "Tourism",
  "departureDate": "2026-08-01",
  "expectedArrivalDate": "2026-08-02",
  "expectedDepartureDate": "2026-08-10",
  "travelPurpose": "Tourism",
  "destinationCountry": "Spain"
}
```

**预期结果：** `code = 0`，`data = true`

**自动化：** `data/spain_order/save_order.yaml` → `test_save_order`

---

#### TC_ORDER_009 保存订单-缺少必填字段（异常）

**请求体：**
```json
{
  "visaOrderId": 19428,
  "visaCategory": "Schengen Visa"
}
```

**预期结果：** `code = 41008`，`msg` 包含「不能为空」（QA 按第一个缺失字段返回，例如 `[expectedArrivalDate]:预计到达日期不能为空`）

**自动化：** `data/spain_order/save_order.yaml` → `test_save_order`

---

### 3.3 保存申请人 `POST /spain/order/saveApply`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_010 | 新建申请人 | P1 | ⚠️ xfail |
| TC_ORDER_011 | 更新已有申请人 | P1 | ⚠️ xfail |

#### TC_ORDER_010 新建申请人

**前置：** 已创建订单

**请求体：**
```json
{
  "visaOrderId": 19428,
  "surname": "张",
  "name": "三",
  "surnameEn": "ZHANG",
  "nameEn": "SAN",
  "birthDate": "1990-01-01",
  "gender": "1",
  "nationalityEn": "CHINA",
  "passportNum": "E12345678",
  "signDate": "2020-01-01",
  "effectiveDate": "2030-01-01",
  "passportType": "Ordinary Passport",
  "countryNum": "86",
  "mobile": "13800138000"
}
```

**预期结果：** `code = 0`，`data` 为申请人 ID（整数）

---

#### TC_ORDER_011 更新已有申请人

**请求体：**
```json
{
  "visaOrderApplyId": 10001,
  "surnameEn": "ZHANG",
  "nameEn": "SANUPDATED",
  "passportNum": "E12345678"
}
```

**预期结果：** `code = 0`，`data` 为申请人 ID

---

### 3.4 删除申请人 `POST /spain/order/deleteApply`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_012 | 删除申请人并重排序号 | P1 | ⚠️ xfail |

**Query 参数：** `visaOrderApplyId=10001`

**预期结果：** `code = 0`，`data = true`，剩余申请人 position 从 1 连续重排

---

### 3.5 获取订单详情 `POST /spain/order/getOrderDetail`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_013 | 获取已创建订单详情 | smoke | ✅ 已实现 |

**Query 参数：** `visaOrderId=19428`

**预期结果：**
- `code = 0`
- `data.visaOrderId` 与请求一致
- `data` 包含：`orderNum`、`orderStatus`、`consulateCity`、`appointmentType`

**自动化：** `test_get_order_detail`

---

### 3.6 订单列表 `POST /spain/order/listOrder`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_003 | 查询订单列表-默认分页 | smoke | ✅ 已实现 |
| TC_ORDER_004 | 查询订单列表-按预约类型筛选 | P1 | ✅ 已实现 |
| TC_ORDER_014 | 查询订单列表-按领馆筛选 | P2 | ✅ 已实现 |
| TC_ORDER_015 | 查询订单列表-按申请人姓名模糊搜索 | P2 | ✅ 已实现 |

#### TC_ORDER_003 默认分页查询

**请求体：**
```json
{
  "pageNum": 1,
  "pageSize": 10,
  "desc": true
}
```

**预期结果：**
- `code = 0`
- `data.records` 为数组
- `data.totalCount >= 0`

**自动化：** `data/spain_order/list_order.yaml` → `test_list_order`

---

#### TC_ORDER_004 按预约类型筛选

**请求体：**
```json
{
  "pageNum": 1,
  "pageSize": 10,
  "appointmentType": "Individual"
}
```

**预期结果：** `code = 0`，`data.records` 中 `appointmentType` 均为 `Individual`

---

#### TC_ORDER_014 按领馆筛选

**请求体：**
```json
{
  "pageNum": 1,
  "pageSize": 10,
  "consulateCity": "Shanghai"
}
```

**预期结果：** `code = 0`，返回上海领馆订单

---

#### TC_ORDER_015 按申请人姓名模糊搜索

**请求体：**
```json
{
  "pageNum": 1,
  "pageSize": 10,
  "applicantName": "张"
}
```

**预期结果：** `code = 0`，返回姓名包含"张"的订单

---

### 3.7 获取申请人详情 `POST /spain/order/getApplyDetail`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_016 | 获取申请人详情 | P1 | ✅ 已实现 |

**Query 参数：** `visaOrderApplyId=10001`

**预期结果：**
- `code = 0`
- `data` 包含：`surname`、`name`、`passportNum`、`signStatus`、`position`

---

### 3.8 拖动排序 `POST /spain/order/setPosition`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_017 | 设置申请人位置 | P2 | ⚠️ xfail |

**Query 参数：** `visaOrderApplyId=10001&position=2`

**预期结果：** `code = 0`，`data = true`

---

### 3.9 下载预约信 `POST /spain/order/downloadFile`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_018 | 下载预约信 | P2 | ✅ 已实现 |

**Query 参数：** `visaOrderId=19428`

**预期结果：** 返回文件流或下载地址

---

### 3.10 导出名单表 `POST /spain/order/exportNameList`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_019 | 导出名单表-默认筛选 | P2 | ✅ 已实现 |

**请求体：** 与 `listOrder` 筛选条件相同（如 `pageNum`、`pageSize`、`orderStatusList` 等）

**预期结果：** `code = 0`，`data = true` 或导出任务成功

**封装：** `order_api.export_name_list(payload)`

---

### 3.11 批量下载文件 `POST /spain/order/batchDownloadFile`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_020 | 批量下载文件 | P2 | ✅ 已实现 |

**请求体：** 与 `listOrder` 筛选条件相同

**预期结果：** `code = 0`，`data = true`

**封装：** `order_api.batch_download_file(payload)`

---

### 3.12 待支付订单数量 `POST /spain/order/countWaitPayOrder`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_ORDER_021 | 查询当前公司待支付订单角标 | P2 | ✅ 已实现 |

**请求体：** 无

**预期结果：** `code = 0`，`data` 为数量（整数或对象，以实际响应为准）

**封装：** `order_api.count_wait_pay_order()`

---

## 4. 预约提交接口用例（cat_629）

### 4.1 提交订单 `POST /spain/submit/submit`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_002 | 提交订单到预约系统 | P1 | ⏳ 待实现 |

**Query 参数：** `visaOrderId=19428`

**预期结果：** `code = 0`，`data = true`

---

### 4.2 获取最新时间 `POST /spain/submit/queryTime`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_003 | 获取最新可预约时间 | P1 | ⏳ 待实现 |

**Query 参数：**
```
visaOrderId=19428
hopeTime=2026-08-01 09:00
```

**预期结果：** `code = 0`，`data = true`

---

### 4.3 选时间预约提交 `POST /spain/submit/submitAppointment`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_004 | 选择时段提交预约 | P1 | ⏳ 待实现 |
| TC_SUBMIT_005 | 选择多个优先时段预约 | P2 | ⏳ 待实现 |

#### TC_SUBMIT_004 选择时段提交预约

**请求体：**
```json
{
  "visaOrderId": 19428,
  "commonAppointmentTime": "2026-08-01 09:00"
}
```

**预期结果：** `code = 0`，`data = true`

---

#### TC_SUBMIT_005 选择多个优先时段预约

**请求体：**
```json
{
  "visaOrderId": 19428,
  "commonAppointmentTime": "2026-08-01 09:00,2026-08-02 10:00,2026-08-03 14:00"
}
```

**预期结果：** `code = 0`，`data = true`（最多 3 个时段，逗号分隔）

---

### 4.4 关闭托管 `POST /spain/submit/closeHosted`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_006 | 关闭托管 | P1 | ⏳ 待实现 |

**Query 参数：** `visaOrderId=19428`

**预期结果：** `code = 0`（回待预约、停止托管任务）

**封装：** `submit_api.close_hosted(visa_order_id)`

---

### 4.5 我已付款/再查一次 `POST /spain/submit/confirmPaid`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_007 | 确认已付款并发起查单 | P1 | ⏳ 待实现 |

**Query 参数：** `visaOrderId=19428`

**预期结果：** `code = 0`

**封装：** `submit_api.confirm_paid(visa_order_id)`

---

### 4.6 最近支付查单任务 `POST /spain/submit/getLastSyncAppointmentTask`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_008 | 查询最近一次支付查单任务 | P1 | ⏳ 待实现 |

**Query 参数：** `visaOrderId=19428`

**预期结果：** `code = 0`，`data` 含任务信息（供前端轮询）

**封装：** `submit_api.get_last_sync_appointment_task(visa_order_id)`

---

### 4.7 托管修改期望时段 `POST /spain/submit/updateHostedTimes`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_009 | 托管刷号中修改期望时段 | P2 | ⏳ 待实现 |

**请求体：**
```json
{
  "visaOrderId": 19428,
  "hosted": true,
  "appointmentDate": "[{\"dateStart\":\"2026-09-08\",\"dateEnd\":\"2026-09-11\",\"timeStart\":\"07:30\",\"timeEnd\":\"14:40\"}]"
}
```

**预期结果：** `code = 0`

**封装：** `submit_api.update_hosted_times(payload)`

---

## 5. 预约查询接口用例（cat_625）

### 5.1 查询获取时间任务 `POST /spain/submit/findHaveTimeQuerying`

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_SUBMIT_001 | 查询是否有进行中的获取时间任务 | P1 | ⏳ 待实现（QA 404） |

**Query 参数：** `visaOrderId=19428`

**预期结果：** `code = 0`，`data` 为 boolean

**备注：** QA 环境该接口返回 404，待部署后启用自动化

---

## 6. 业务流程用例

### 6.1 完整预约流程（端到端）

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_FLOW_001 | 个人订单完整预约流程 | smoke | ⏳ 待实现 |

**测试步骤：**

| 步骤 | 操作 | 接口 | 验证点 |
|------|------|------|--------|
| 1 | 创建个人订单 | `createOrder` | 返回订单 ID |
| 2 | 保存订单信息 | `saveOrder` | `code = 0` |
| 3 | 保存申请人 | `saveApply` | 返回申请人 ID |
| 4 | 获取订单详情 | `getOrderDetail` | 信息完整 |
| 5 | 提交订单 | `submit` | `code = 0` |
| 6 | 获取最新时间 | `queryTime` | `code = 0` |
| 7 | 选时间预约 | `submitAppointment` | `code = 0` |
| 8 | 查询时间任务 | `findHaveTimeQuerying` | 返回 boolean |
| 9 | 下载预约信 | `downloadFile` | 文件可下载 |

---

### 6.2 家庭订单多人流程

| 用例ID | 用例标题 | 优先级 | 状态 |
|--------|----------|--------|------|
| TC_FLOW_002 | 家庭订单3人完整流程 | P1 | ⏳ 待实现 |

**测试步骤：**

| 步骤 | 操作 | 验证点 |
|------|------|--------|
| 1 | 创建家庭订单（3人） | 返回订单 ID |
| 2 | 保存订单信息 | `code = 0` |
| 3 | 保存主申请人 | 返回申请人 ID，position=1 |
| 4 | 保存家属1（relationToMain） | position=2 |
| 5 | 保存家属2 | position=3 |
| 6 | 获取订单详情 | `applyNum = 3` |
| 7 | 拖动排序家属1到 position=3 | `setPosition` 成功 |
| 8 | 删除家属2 | 剩余 position 重排 |
| 9 | 提交预约 | 流程完成 |

---

## 7. 自动化映射

| 用例ID | YAML 数据文件 | 测试文件 | 状态 |
|--------|---------------|----------|------|
| TC_ORDER_001 | `data/spain_order/create_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_002 | `data/spain_order/create_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_003 | `data/spain_order/list_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_004 | `data/spain_order/list_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_005 | `data/spain_order/create_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_006 | `data/spain_order/create_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_007 | `data/spain_order/create_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_008 | `data/spain_order/save_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_009 | `data/spain_order/save_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_010 | `data/spain_order/save_apply.yaml` | `test_spain_order.py` | ⚠️ xfail |
| TC_ORDER_011 | `data/spain_order/save_apply.yaml` | `test_spain_order.py` | ⚠️ xfail |
| TC_ORDER_012 | `data/spain_order/apply_ops.yaml` | `test_spain_order.py` | ⚠️ xfail |
| TC_ORDER_013 | — | `test_get_order_detail` | ✅ |
| TC_ORDER_014 | `data/spain_order/list_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_015 | `data/spain_order/list_order.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_016 | `data/spain_order/apply_ops.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_017 | `data/spain_order/apply_ops.yaml` | `test_spain_order.py` | ⚠️ xfail |
| TC_ORDER_018 | `data/spain_order/order_file.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_019 | `data/spain_order/order_file.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_020 | `data/spain_order/order_file.yaml` | `test_spain_order.py` | ✅ |
| TC_ORDER_021 | `data/spain_order/order_file.yaml` | `test_spain_order.py` | ✅ |
| TC_SUBMIT_001 | `data/spain_submit/find_time_querying.yaml` | `test_spain_submit.py` | ⏸️ skip |

---

## 8. 执行命令

```bash
# 全部用例
pytest

# 冒烟用例
pytest -m smoke

# 订单模块
pytest -m order

# 预约提交模块
pytest -m submit

# 生成报告
allure serve reports/allure-results
```

---

## 9. 待补充用例优先级

| 优先级 | 用例 | 说明 |
|--------|------|------|
| P0 | TC_FLOW_001 | 端到端主流程，覆盖核心业务 |
| P1 | TC_ORDER_010~012、TC_ORDER_017 | 已编写。QA `saveApply` 新建返回 `400 无申请人id`，当前 xfail |
| P1 | TC_SUBMIT_002~004 | 预约提交三步 |
| P1 | TC_SUBMIT_006~008 | 托管/支付查单 |
| P2 | TC_SUBMIT_009 | 托管改时段 |
