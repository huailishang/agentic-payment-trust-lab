# H51 执行入口

Task ID: H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
State: CONTRACT_FROZEN / Executor / one_off / SINGLE

先读CURRENT、地图r82、CONTRACT、H50R2最终REVIEW、HTTP_CHECKER和VALIDATION_PLAN。本地方法锁修复已接受并停止；当前测量真实HTTP路由如何连接已接受控制，不改商家实现。默认工厂没有注入控制是已知源码事实，C07必须保持无注入对照；不要用全局替换掩盖它。

只编写HTTP_RUNTIME.py及HTTP_MEASURE.py和材料。复用H47/FROZEN_RUNTIME的实际应用启动、签名与全离线profile方式；H50R2副本已逐字复制，原服务/业务/路由/签名不改。以FastAPI.get_checkout_service的依赖覆盖传入既有execution_control，原生请求级会话保持。无TCP端口、无真实HTTP外连，实际入站HTTP使用进程内ASGI传输；原native/guarded脚本只算回归，不能充HTTP场景。

串行完成夹具及接线审计→8个冻结HTTP场景→独立SQLite假PSP/DB/原始HTTP观察→材料与成本→完整8项L2→一次交Evaluator。签名检查不能跳过，确认只能标本地合成信任；真实身份/Provider/客户继续未知。4小时/2次L2，Executor进程内HTTP总<=160，单次观察<=40，外部/Git/代理0。超范围即停回Evaluator。
