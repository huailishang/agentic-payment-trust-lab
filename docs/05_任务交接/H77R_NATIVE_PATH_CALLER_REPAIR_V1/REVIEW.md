# H77R Evaluator Review / 再次独立复核

Task ID: H77R_NATIVE_PATH_CALLER_REPAIR_V1
Reviewed baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e

## Project context before review / 全局位置

目标为授权→可信主体→交易绑定→治理→支付→恢复→可消费审计。r130中A–D本地阶段关闭、E受控本地代表闭合、F受控外部切片关闭。第一瓶颈B-15仍是实际来源独立复验，优先于生命周期建设、第二支付平台或已关闭B-22的字段扩展。本包只修Windows测量入口。

## Pre-review checks

原L2六项及EV命令/长度/摘要通过；六份复制来源与唯一.as_posix()调用方差异一致。原15防护测试和130回归有原始输出；冻结12文件、1736保护项保持。接受1812份输入，evidence/ACCEPTED.json及evaluator_review/ACCEPT.py/原始日志保存了接受前结构与接口联调检查。接受后提交内容不可变。

## L3 Independent Gate

- Gate result: FAIL
- Gate summary: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/L3-GATE.json
- Validation plan: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/VALIDATION_PLAN.yaml
- Independent command differences: 使用冻结evaluator_command，正式L3一次，未改计划或原实现。

VP-01/04/06通过，VP-02/03/05失败。路径修复生效，进入WSL并核锁定archive，但在实际二进制提取前停止，SPIRE Server/Agent启动0，新根/叶/签名0。正式L3=1、发行尝试预算=1与SPIRE服务启动=0分开记录，不把未启动服务当作预算未消费。

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-01.stderr.log

## RV-EV-02

- AC: AC-02 AC-03
- Meta: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-02.stderr.log

## RV-EV-03

- AC: AC-04
- Meta: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-03.stderr.log

## RV-EV-04

- AC: AC-05
- Meta: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-04.stderr.log

## RV-EV-05

- AC: AC-06
- Meta: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-05.stderr.log

## RV-EV-06

- AC: AC-01 AC-07
- Meta: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/evidence/l3/RV-EV-06.stderr.log

## Acceptance matrix

| AC | 决定 | 独立证据与解释 |
| --- | --- | --- |
| AC-01 | 通过 | RV-EV-01/06、复制核对、POSTCHECK：1812接受文件零漂移，旧H77/H76材料不变，Executor实际发行0。 |
| AC-02 | 不通过 | Windows接口修复已通过且实际WSL调度成功；锁定archive长度/SHA匹配，随后提取器150 MiB单文件上限误拒官方Server，未得到新鲜来源。 |
| AC-03 | 不通过 | Server/Agent未启动，尚无本轮管理登记、内核UID取证或持有签名；不能用代码/历史样本替代。 |
| AC-04 | 不通过 | RV-EV-03无成功evaluator_current索引，没有本次新鲜材料；旧十负例仍成立。 |
| AC-05 | 通过 | RV-EV-04原28+19+9+74共130项全部通过，无产品/原断言变化。 |
| AC-06 | 通过 | 以原失败目录CLEANUP、raw/008独立检查输出及POSTCHECK补充人工回查：临时目录已移除、残余进程/公开私钥0、接受零漂移，唯一尝试保留。共享VP-05因失败运行未发布成功索引而失败，但失败分支实际清理原始证据充分；未把门禁改写为PASS。 |
| AC-07 | 不通过 | 离线统一提交/接受保持成立，但L3三项失败、来源目标未完成。 |

## Findings

Blocking：原WORKLOAD.extract_binaries为每个目标成员设置0<size<=150*1024*1024。真实固定官方包中的spire-server=179,378,008字节，超过157,286,400字节上限；Agent=78,437,656字节。目录路径、唯一性、普通文件类型均正确，归档本身未漂移。失败文本missing/nonregular/duplicate binary是合并错误，不能据此断言文件丢失/路径不符。

失败后仅做一次已授权固定archive的只读元数据/流摘要检查，未提取/执行二进制、未再发行。ARCHIVE_CATALOG.json列完整11成员、真实大小/类型/两个成员SHA；原archive为70,187,551字节，SHA与锁一致。两binary实际总量257,815,664字节。原模拟归档使用很小测试内容，未验证真实资产边界；接受阶段仅核复制一致也不足以证明实际来源可运行。

这暴露资产预检缺口，不是密码学验证器/UID选择器或SPIRE发行机制失败。下一包不得只随意抬高上限：应冻结真实成员精确路径/长度/SHA，并用同一生产提取器先对真实锁定archive做无服务预检，再允许一次独立发行。

Non-blocking：VP-03/05未找到成功索引是前置失败连带现象。现有失败目录有真实清理与摘要，不额外修改公共Runner或成功索引语义，以人工独立回查保留事实。

## Final verdict

REJECTED

- Failed AC: AC-02 AC-03 AC-04 AC-07
- Specific fact: 路径修复有效，但真实资产超过原任意单文件大小阈值，来源实验未到服务启动阶段。
- Minimum repair task: H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1。
- Required rerun: 同一提取器的真实锁定资产预检、严格负例/原回归、统一L2及接受后唯一L3；原H77R不重试或覆盖。
- Missing human fact or authorization: NONE，限负责人既有同一WSL实验/独立评估目的；无新平台/下载/安装或付款。Executor可做明确有界无服务资产预检，发行仍只由Evaluator接受后执行。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

本包为repair（修复），不将路径修复宣称产品能力改善。独立事实是入口已恢复、资产资格尚未闭合；B-15不减记，E整体不升级。新鲜来源无法复核，建议人工抽查；强制来源AC不通过。原H77拒收、H76三轮偏差、H75旧费用/UNKNOWN保持。

## Iteration value and continuation decision

Continuation decision: CONTINUE

已消费1次正式L3/1次发行尝试预算；正式WSL发行调度1，实际SPIRE启动0，另有1次只读目录/成员摘要WSL调用。无新下载/安装/API/付款/私钥。环境与archive确实可读，独立清理通过，原130通过、1812接受字节保持。时间窗见RV meta/RESULT，实际主动分钟UNKNOWN。

下一包应先完成真实固定输入的完整离线资格，而不是逐个现场碰运气。精确成员大小和摘要已独立测得，真实提取器预检成本低、无服务副作用，比换环境/支付平台或先建生命周期更直接；若资产资格失败便停止，不消费发行。通过后只有一次原目标实测，不扩新Case。

## Bottleneck movement after review

B-15未闭合，具体阻塞从Windows调用接口前移到实际资产边界。原路径假设得到支持，但发行/UID/签名假设仍未知。后续先修资产资格并验证真实输入；来源切片若通过即停止同类扩展，再重新比较生命周期/真实主体/消费者方向。

## Next execution package

- Dispatch mode: SINGLE
- Continuation action: repair task
- Next task ID: H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1
- Next contract path: docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/CONTRACT.md
- Initial state and role: CONTRACT_FROZEN / Executor
- Principal change: 任意大小阈值改为固定真实archive成员profile（精确路径/长度/SHA），并要求同生产提取器真实无服务预检。
- Budget: 至多2版任务实现、2正式离线L2/2次Executor资产预检，Evaluator1次资产预检+1正式L3/1发行；无总体时间上限。
- Executor-ready check: 原始来源目录与成员锁已取得，合同/范围/验收/计划/停止条件/原回归和完整来源要求齐备，无新增Human事实缺口。
