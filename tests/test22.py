"""data 目录接口用例完整性分析。

对照 Spain_TestDemo.md 与 YApi 项目 16。只记录缺口，未改用例。
"""

REPORT = """
data 里的接口用例不完整。对照 Spain_TestDemo.md 和 YApi 项目 16，文档里的 33 条接口用例只有 20 条写进了 YAML；预约提交模块基本是空的。

## 覆盖结论

| 范围 | 文档用例 | data 已有 | 缺口 |
|---|---:|---:|---|
| 订单 cat_633 | 21 | 20（另有详情接口写在测试代码里，没有 YAML） | 详情无数据文件；4 条申请人用例当前会 xfail |
| 预约提交 cat_629 | 文档总览写 11 条，正文只列出 8 条 | 0 | 8 条整段缺失 |
| 预约查询 cat_625 | 1 | 1（TC_SUBMIT_001，测试里 skip） | 用例在，但不会执行 |
| 端到端流程 | 2 | 0 | TC_FLOW_001、TC_FLOW_002 |

data 现有 21 条：create_order 5、save_order 2、save_apply 2、apply_ops 3、list_order 4、order_file 4、find_time_querying 1。

按文档 33 条算，YAML 覆盖约 61%（20/33），低于测试覆盖 90% 的标准。能稳定跑通的更少：TC_ORDER_010、011、012、017 依赖新建申请人，QA 返回 400 无申请人id，目前 xfail。

## 整条缺失（YAML 里没有）

| 用例 | 接口 | 优先级 | 说明 |
|---|---|---|---|
| TC_ORDER_013 | getOrderDetail | smoke | 测试函数 test_get_order_detail 已覆盖主路径，但没有 YAML，也没有校验 orderNum、orderStatus、consulateCity、appointmentType |
| TC_SUBMIT_002 | submit | P1 | 提交订单 |
| TC_SUBMIT_003 | queryTime | P1 | 获取最新时间 |
| TC_SUBMIT_004 / 005 | submitAppointment | P1 / P2 | 选时段预约 |
| TC_SUBMIT_006 | closeHosted | P1 | 关闭托管 |
| TC_SUBMIT_007 | confirmPaid | P1 | 我已付款 / 再查一次 |
| TC_SUBMIT_008 | getLastSyncAppointmentTask | P1 | 最近支付查单任务 |
| TC_SUBMIT_009 | updateHostedTimes | P2 | 托管中改期望时段 |
| TC_FLOW_001 | 个人订单全流程 | P0 | 创建 → 保存订单 → 保存申请人 → 详情 → 提交 → 查时间 → 选时段 → 查任务 → 下载预约信 |
| TC_FLOW_002 | 家庭 3 人流程 | P1 | 主申请人 + 2 名家属、relationToMain、排序、删除后重排、再提交 |

文档总览写预约提交 11 条，正文只定义了 TC_SUBMIT_002～009 这 8 条，另外 3 条没有标题和请求，补之前需要先定这 3 条是什么。

## 已有用例里的场景缺口

这些接口有正向用例，但边界、异常和枚举没有盖住。

创建订单 create_order.yaml
已有：上海个人 1 人、北京家庭 3 人、广州个人 1 人、家庭 6 人、个人 7 人超限。
缺：必填项缺失（consulateCity / appointmentType / applyNum）、非法领馆、非法预约类型、applyNum 为 0 或负数、家庭单 7 人、个人单是否允许大于 1 人。

保存订单 save_order.yaml
已有：旅游正向一条、缺字段一条。
缺：appointmentCategory=VIP；YApi 里的出行目的只覆盖了 Tourism，还有 Business、Visiting family、Study、Airport transit、Cultural reasons、Medical reasons、Official visit、Sport、Transit、Others；日期颠倒或过去日期；非法 visaOrderId；每个必填字段单独缺失。

保存 / 删除 / 排序申请人
已有：新建、更新、删除后重排、拖到 position=2。四条都会被新建申请人的 400 拦住。
缺：女（gender=2）、公务护照、家属 relationToMain、新建不传 visaOrderId、更新不传 visaOrderApplyId、重复护照号、删除不存在的申请人、只剩 1 人时删除、非法 position。

订单列表 list_order.yaml
已有：默认分页、个人类型、上海领馆、姓名「张」。
缺用户端筛选项：orderStatusList、visaSubType、创建时间范围、护照号模糊、hosted（0 手动 / 1 托管）、家庭类型、北京/广州、pageNum=0 或空结果。运营端字段（companyId、operatorAccount）建议先不纳入，除非要测运营端。

文件与角标 order_file.yaml
已有：预约成功订单下载 PDF、默认条件导出名单、默认条件批量下载、待支付数量 ≥ 0。
缺：无预约信订单的下载失败、按筛选条件导出/批量下载、创建待支付订单后角标是否增加。

查询时间任务 find_time_querying.yaml
只有 TC_SUBMIT_001，且 test_spain_submit.py 整文件 skip（QA 404）。缺非法 visaOrderId、无进行中任务时 data=false。

## 补之前要对齐的文档差异

按 YApi 写新用例时，这几处不能直接照 Spain_TestDemo.md 抄：

- submitAppointment：文档用 commonAppointmentTime（逗号分隔的时间点）。YApi 必填是 visaOrderId，时段字段是 appointmentDate（1～5 组 JSON，含 dateStart、dateEnd、timeStart、timeEnd），另有 hosted、payType（2 微信 / 3 支付宝）。
- queryTime：文档有 hopeTime。YApi 查询参数只有必填的 visaOrderId。
- updateHostedTimes：YApi 说明待付款不可调，请求只需 visaOrderId + appointmentDate。文档示例还带了 hosted: true。
- saveApply：文档示例是 passportType=Ordinary Passport、countryNum=86、nationalityEn=CHINA。现有 YAML 是 Ordinary、CHN、China，并多了签发地、出生地、婚姻状态。以哪套值为准需要确认，否则新建申请人会继续 400。

确认后可按这个清单补 YAML 和对应测试。建议先做这三块：预约提交 8 条按 YApi 字段重写、TC_FLOW_001、订单侧必填缺失和列表筛选。申请人 4 条 xfail 要等 saveApply 的字段约定定下来再改。
"""


if __name__ == "__main__":
    print(REPORT)
