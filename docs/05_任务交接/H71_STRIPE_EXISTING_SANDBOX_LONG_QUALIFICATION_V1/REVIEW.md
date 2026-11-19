# H71独立复核：整包拒收，保留三项真实读取成果

Task ID: H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1
Reviewed baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Review date: 2026-11-12

## Project context before review / 全局位置

目标是授权→绑定→执行前治理→支付/恢复→可消费审计的信任链。r115：A–D本地阶段关闭、E受控本地代表闭合、F当前。B-21第一瓶颈仍为外部入口/支付证据；H71集中测必要读取、监听及本地浏览器。H68R修复已有代表覆盖，H67人工延期，因此均不优先重开。入口受限可作为测量结果签收，但必须真实保存失败证据，不能因L2通过降低这条要求。

## Pre-review checks / 评估前检查

- CURRENT为READY_FOR_REVIEW / Evaluator，REPORT为SUBMITTED_FOR_REVIEW，L2八项PASS，公共结构验证OK。
- 1491保护文件、15冻结输入、HEAD及原H68/H69授权分配保持；产品/旧测试未修改，预算账本原22行闭合。
- 接受64文件的提交快照，见`evidence/l3_review/ACCEPTED_SNAPSHOT.json`。原REPORT/RESULT/矩阵/来源/运行代码/L2证据不回写；账本仅追加本次L3。原字节前缀和64文件保持，见RETENTION.json。
- 仓库外原文按SNAPSHOT字节SHA定位；H71凭据与H69原凭据相符，三GET响应逐字节核对均200、object=list/data=[]/has_more=false。8份L2 stdout/stderr的大小与摘要相符；敏感值精确扫描通过。

## L3 Independent Gate / L3独立门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/L3-GATE.json
- Validation plan: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/VALIDATION_PLAN.yaml
- Independent command differences: NONE；VP-04使用原冻结evaluator_command。

原生Windows独立执行八项均0；9项安全与74项回归通过。由于提交结果为INPUT_LIMIT，VP-04按合同只审停止分支，没有新增Stripe GET。整个独立复核没有重跑下载、来源获取、监听、浏览器或付款。

RV-EV-01至08的meta/stdout/stderr三件套均在`evidence/l3_review/gate/`，分别对应完整性、来源、原文、停止分支回查、安全9项、Windows74项、预算和判别器反例。RAW_AUDIT.json记录三GET和L2摘要独立核查；TRANSFER_COUNTEREXAMPLES.json为额外离线反例。Runner通过仅说明冻结检查器未拦截以下语义问题，不能代替逐AC验收。

## RV-EV-01

- AC: AC-01, AC-07
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-01.stderr.log

## RV-EV-02

- AC: AC-01, AC-02
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-02.stderr.log

## RV-EV-03

- AC: AC-02, AC-03, AC-04, AC-05, AC-07
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-03.stderr.log

## RV-EV-04

- AC: AC-02, AC-03, AC-07
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-04.stderr.log

## RV-EV-05

- AC: AC-06
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-05.stderr.log

## RV-EV-06

- AC: AC-06
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-06.stderr.log

## RV-EV-07

- AC: AC-01, AC-07
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-07.stderr.log

## RV-EV-08

- AC: AC-07
- Meta: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-08.meta.json
- Stdout: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-08.stdout.log
- Stderr: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/evidence/l3_review/gate/RV-EV-08.stderr.log

## Independent findings / 独立发现

### F-01：最终矩阵遗漏已测结果，引用只指向导航

PERMISSION_MATRIX.json的checkout_required_endpoints.observed仍为“NOT_MEASURED at source review”；unknown仍问列表GET能否放行/分页是否完整。同包三份实际响应已经回答这些问题。最终消费器矩阵没有反映实测，REPORT与矩阵相矛盾，违反AC-02。

另外三条refs引用为HTML导航片段：Restricted API keys-selector…或Listen for events…，虽是原始字节子串，却不能直接支持所述权限/监听语义。两份文档确实存在且摘要正确，但“匹配子串”不能替代“支持论断”。同凭据上下文的UNKNOWN与未测Checkout写权限应保留，三项读取成功不能继续写未测。

### F-02：失败传输丢失部分读取与HTTP阶段

RUN.py的_sources把response.read(MAX_RESPONSE+1)直接赋给raw；读取中途超时，赋值不完成，raw仍为空，两次已获HTTP200的来源请求均记录bytes=0。当前记录只能证明完整归档字节为0，不能证明实际接收字节为0。

_download也使用整段read后赋值；任何URLError/TimeoutError/OSError会将status重设None，包含已经拿到HTTP状态、随后读正文失败的情况。其END不保留异常类别、阶段、响应头或部分正文；因此实际下载的“PINNED_DOWNLOAD_HTTP_NONE/0 bytes”无法区分建连/响应头前失败与响应体中途失败。没有足够原始遥测定位下载通道或根因。

独立无网络反例模拟HTTP200、响应体已有23字节后超时：下载仍输出status=null/bytes=0，来源输出status=200/bytes=0，均复现。证据见TRANSFER_COUNTEREXAMPLES.json；只使用临时合成响应，不改旧RUN或现场材料。这不能倒推出历史实际收到23字节，也不能证明历史超预算；正确结论是历史失败的接收字节及下载失败阶段UNKNOWN。

### Residual：尚未执行分支不能沿用为已验证实现

CLI配置函数仍覆盖HOME，浏览器函数直接返回工具不可用，且缺少本次工具探测。两分支没有实际执行，不作为本轮已发生的权限违规；但不能原样自动重启后便宣称隔离/工具限制已经验证。后续入口运行包须单独处理这些未验证接线。当前优先修复证据生成共同断点，不新增现场请求或更多攻击Case。

## Acceptance matrix / 逐AC裁决

| AC | 裁决 | 独立依据 |
| --- | --- | --- |
| AC-01 | 通过（保持/来源身份/授权范围） | VP-01、64文件保持、来源实际字节和原URL相符，旧包/产品保持。字节精度问题归AC-07，引用语义归AC-02。 |
| AC-02 | 不通过 | 三GET原文真实，但最终矩阵仍未测/未知，且导航引用不足以支持文档语义；F-01。 |
| AC-03 | 通过（受限分支） | 三个固定GET真实200且完整空列表；后续下载受限。按原合同停止分支无需新增双方GET；不认领READ_AND_LISTEN_READY。 |
| AC-04 | 通过（NOT_RUN分支） | 下载未完成，CLI、监听和接收器均未运行，符合前级受限的停止分支；不认领CLI资格。下载状态/字节信息丢失单列AC-07不通过，不把未到达的CLI分支当作已验证实现。 |
| AC-05 | 通过（NOT_RUN分支） | 前置未满足，浏览器没有执行，不采信未到达的硬编码不可用为实际浏览器资格结论。 |
| AC-06 | 通过 | 独立9安全、原生Windows74回归均通过，产品及旧测试未变。 |
| AC-07 | 不通过 | BEGIN/END与请求次数保持，但两个失败来源和下载的“接收0字节”无依据，下载HTTP状态可被抹去；公私摘要一致不能修复采集阶段的信息丢失。 |

## Final verdict

REJECTED

拒收整包证据质量与精确停止归因，不否定三个读取接口已实测200。旧报告、输入受限结果及L2/L3全部保留；不补写历史遥测，不将原数据追认为已修复。

## Project impact verdict / 项目影响

Impact verdict: NOT_APPLICABLE

本包为one_off测量；新增可保留事实为三个必要资源读取从未知变为实测接受，外部合格支付旅程仍0。监听/Checkout写入/Stripe前端/真实事件/主体认证仍未测；不能把下载信息丢失判成平台不可用。PCAC-06/12/15/20不提升外部成熟度或合规声明。

## Iteration value and continuation decision / 迭代与下一步

Continuation decision: CONTINUE

Next task ID: H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1
Next task path: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/CONTRACT.md
Next task state: CONTRACT_FROZEN / Executor

按Human较长包偏好，下一修复把历史纠正投影、四维矩阵消费、统一有界传输采集、独立故障注入、原安全回归和完整交接合为一次120主动分钟/3小时离线包。只改新任务脚本，网络/下载/API/浏览器/付款0；保留旧三GET，不重新测已满足项。

选择它优于直接换下载通道/重试：当前采集器会继续掩盖状态和部分字节，换通道可能得到可运行二进制却无法证明失败/成本；也优于重开H67或扩本地Case，后两者不能修复外部证据可信性。两类共同断点已有可复现反例，机制明确，不额外引入研究/讨论技能。

## Bottleneck movement / 瓶颈变化

B-21的资源读取权限不确定性已缩小；当前优先修复外部资格测量的证据生成可靠性。修复通过且保守预算可证明后，再考虑固定CLI剩余下载与监听/浏览器较长运行包，保留原截止与共享余额；证据不足则停止，不以原生安全、统计通过或本地模拟补齐外部链。
