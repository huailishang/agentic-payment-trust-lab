# H82 评估者源码复核：现有过期、撤销、轮换、重放能力不能重复建设

Date: 2026-11-19  
Source: 本地当前未提交工作区（不是远程过时 main）  
Scope: 原产品代码/现有用例只读复核；**未运行新L2/L3或增量行为测量**；H82仍 DRAFT_CONTRACT，未授权Executor。

## 已有确定性防护（不是缺失）

| 能力 | 实现证据 | 限定边界 |
| --- | --- | --- |
| X.509-SVID证书有效期 | `src/agentic_payment_experiment/trusted_execution/credential_possession.py:73-77,158-176,547-554` | 在调用方传入的`observed_at_epoch`时点验证证书有效期；不自动等于使用时点 |
| 持有挑战的新鲜度 | 同文件`:289-315,557-563` | 以`observed_at_epoch-issued_at_epoch`对`max_age_seconds`判定，超过窗口INVALID |
| Nonce防重放 | 同文件`:69,317-332`；`tests/trusted_execution/test_credential_possession.py:94-107` | 根据调用方提供的`consumed_nonce_refs`拒绝重放；本函数不持久化或查询全局已使用集合 |
| 身份失效/撤销标志 | `src/agentic_payment_experiment/trusted_execution/execution_facts.py:205-231`；`tests/trusted_execution/test_credential_context_consumption.py:129-137` | `identity.status=revoked/inactive`触发INVALID；没看到本函数自行拉取权威撤销状态 |
| 凭据引用/三元归属 | `execution_facts.py:196-204,248-319`；H81 L2/L3各5/5 | 当前credential_ref不匹配既有fact时只可BOUND，Agent/Provider/Executor不匹配不晋级VERIFIED |
| 签署指令有效期 | `trusted_execution/signed_instruction.py:120-132,331-346`；`tests/trusted_execution/test_signed_instruction_es256.py:121-127` | 对HMAC或ES256指令的signed/observed/expiry检查已经存在；不能自动证明X.509身份事实在未来消费时仍有效 |

## 唯一待核对的消费者时间边界

- `src/agentic_payment_experiment/payment_execution.py:61-90`：支付入口直接接收`credential_possession_fact`并调用`verify_agent_executor_identity`；没有`use_time_epoch`或新的吊销/轮换证明入参。
- `execution_facts.py:268-319`：用事先算好的`status/credential_valid/subject_binding_valid/proof_of_possession_valid/freshness_valid/replay_detected`及上下文判断是否晋级；本函数没有重新计算`observed_at_epoch`相对实际支付时点的年龄，也没有动态权威撤销查询。
- `payment_execution.py:124-141,165-170`：`identity.status=INVALID`会DENY，但身份`BOUND`和`VERIFIED`都可以通过P3门槛。凭据校验失败造成“未晋级VERIFIED”不等于整笔支付必定拒绝；只有业务策略明确要求VERIFIED才需要新增约束，不能自发改动现有允许策略。
- 这只能证明**当前函数责任边界**。本轮未独立复现“隔日复用旧fact后仍支付”的产品行为，也未证明生产端无上游刷新/撤销/可信时间源。现有代码自述`credential_possession.py:3-6`是不执行证书吊销与联邦验证的离线限定profile。不能把这些设计选择直接称为安全漏洞。

## H82草案收敛要求

1. 原有证书有效期、签名/挑战过期、Nonce、身份`revoked`、引用轮换不匹配、三元归属、原支付P2/P4不再重复开发或重测成新能力。
2. 下一包只回答“已有有效Fact从验签到执行的**时间间隔与权威状态来源**是否可证明”；先确认消费者是否被设计为实时认证责任主体，还是依赖外部上游按次再验签。如果依赖上游，优先记录接口/证据契约，而不是改支付允许策略。
3. 把`observed_at_epoch`与可信`use_time_epoch`分开；有权威状态与清晰合同才设计单变量有界测量。缺当前吊销/轮换来源就记UNKNOWN/NOT_JUDGEABLE，不伪造“真实撤销”或默认判生产危险。
4. H82仍为Evaluator草案，不引入任何新执行授权、真实SPIRE发行、下载/API/支付或产品改动。

这份记录纠正了此前把“已有过期/撤销基础防护”笼统表述成“尚未解决”的不严谨之处。B-24作为`use-time`与权威事实可判定性问题保留候选资格，不等于已证漏洞。
