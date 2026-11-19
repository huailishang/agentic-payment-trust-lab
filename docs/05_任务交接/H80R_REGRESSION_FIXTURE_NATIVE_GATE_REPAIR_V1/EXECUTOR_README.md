# H80R 执行入口

先读CONTRACT、父H80/REPORT与REVIEW、SOURCE，确认CURRENT指向本包CONTRACT_FROZEN/Executor。父H80已拒收，不覆盖旧L2、不修改旧报告，不把本包当旧包额度续期。

只使用原生Windows PowerShell和已有agent Python。以下路径是本机现有环境，不安装或激活新环境；禁止经Bash/WSL/WSLENV中转。

1. CURRENT仅执行状态改为EXECUTING；执行 `& 'D:/SoftWare/Anaconda/workspace/.conda/envs/agent/python.exe' -B 'docs/05_任务交接/H80R_REGRESSION_FIXTURE_NATIVE_GATE_REPAIR_V1/BOOTSTRAP.py' --mode implementation --attempt 1`。
2. 只在唯一失败测试的self.consume调用追加合同指定identity关键字；产品、原支付测试和任何断言不改。最多一次廉价目标L1，不能通过反复跑完整回归绕过L2额度。
3. 同解释器执行 `-B 'docs/05_任务交接/H80R_REGRESSION_FIXTURE_NATIVE_GATE_REPAIR_V1/BOOTSTRAP.py' --mode executor --attempt 1`。启动器在首项测试前设置原生子进程环境，全程无Bash/WSL。PASS即停止。
4. 业务/安全断言失败立即BLOCKED（阻塞），不改代码重试。只有明确导入环境故障可按合同写ENVIRONMENT_RETRY.json，保持代码摘要，使用唯一`--mode executor --attempt 2`；不登记第二implementation。
5. 根据REPORT_TEMPLATE.md新建REPORT.md，必须填真实结果、EV四组三件套、失败/成本与偏差。BLOCKED时如实保留，不封包。成功时保持CURRENT为EXECUTING/Executor、Executor status=SUBMITTED_FOR_REVIEW，运行同解释器`-B 本包/SEAL.py`，它先工作流结构校验后封diff/摘要/SUBMISSION。不为修报告格式重跑成功L2。
6. 一次交Evaluator验收；Evaluator先接受不变快照后才运行唯一L3。执行者不能签PASS。

完整原28+18+6、130及来源16/4正21负/8门禁均必须运行通过。旧H80实际启动祖先未知保留；本包不新增服务/凭据/私钥/网络/安装/下载/API/浏览器/真实付款/Git权限。
