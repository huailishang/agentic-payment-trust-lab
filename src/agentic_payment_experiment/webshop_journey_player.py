"""Deterministic, self-contained, read-only player for accepted WebShop journeys."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .webshop_journey_read_model import (
    EXPECTED_EXPERIMENT_CONTEXT_ORIGIN,
    JOURNEY_SCHEMA_VERSION,
    SOURCE_CLASSIFICATION_STATUS,
    WebShopJourneyReadModel,
    webshop_journey_read_model_to_primitive,
)


class WebShopJourneyPlayerInputError(ValueError):
    """Raised when an accepted Journey Read Model is structurally unusable by the UI."""


_REQUIRED_TOP_LEVEL = {
    "schema_version",
    "journey_ref",
    "source_classification_status",
    "correlations",
    "webshop_runtime",
    "experiment_context",
    "commerce_adaptation",
    "payment_authoritative_trace",
    "limitations",
}
_REQUIRED_RUNTIME = {
    "session_id",
    "task_identifier",
    "instruction_text",
    "actions_executed",
    "buy_now_available",
    "buy_now_executed",
    "product",
    "source",
}
_REQUIRED_CORRELATION = {
    "correlation_id",
    "source_path",
    "target_path",
    "source_value",
    "target_value",
    "equal",
}
_REQUIRED_PAYMENT_EVENT = {
    "sequence_no",
    "event_type",
    "entity_type",
    "entity_role",
    "entity_ref",
    "source_binding_ref",
    "decision",
    "status",
    "reason_codes",
    "relations",
}
_REQUIRED_PAYMENT_BINDING = {
    "binding_ref",
    "source_object_type",
    "source_object_ref",
    "projection_schema",
    "projection",
}
_REQUIRED_FIXED_SCRIPT_LIMITATION = "fixed_script_webshop_smoke_not_autonomous_agent"
_REQUIRED_SOURCE_LIMITATIONS = {
    "experiment_context_not_webshop_verified",
    "payment_authoritative_trace_is_separate_evidence_namespace",
}


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WebShopJourneyPlayerInputError(f"{label} must be an object")
    return value


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise WebShopJourneyPlayerInputError(f"{label} has unexpected shape")


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise WebShopJourneyPlayerInputError(f"{label} must be a non-empty string")
    return value


def _require_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise WebShopJourneyPlayerInputError(f"{label} must be a string list")
    return value


def _validate_payload(payload: object) -> dict[str, Any]:
    top = _require_mapping(payload, "journey read model")
    _require_exact_keys(top, _REQUIRED_TOP_LEVEL, "journey read model")
    if top["schema_version"] != JOURNEY_SCHEMA_VERSION:
        raise WebShopJourneyPlayerInputError(
            f"schema_version must be {JOURNEY_SCHEMA_VERSION}"
        )
    _require_text(top["journey_ref"], "journey_ref")
    if top["source_classification_status"] != SOURCE_CLASSIFICATION_STATUS:
        raise WebShopJourneyPlayerInputError(
            "source_classification_status must be "
            f"{SOURCE_CLASSIFICATION_STATUS}"
        )

    runtime = _require_mapping(top["webshop_runtime"], "webshop_runtime")
    _require_exact_keys(runtime, _REQUIRED_RUNTIME, "webshop_runtime")
    for key in ("session_id", "task_identifier", "instruction_text"):
        _require_text(runtime[key], f"webshop_runtime.{key}")
    _require_string_list(runtime["actions_executed"], "webshop_runtime.actions_executed")
    if not isinstance(runtime["buy_now_available"], bool):
        raise WebShopJourneyPlayerInputError("webshop_runtime.buy_now_available must be bool")
    if not isinstance(runtime["buy_now_executed"], bool):
        raise WebShopJourneyPlayerInputError("webshop_runtime.buy_now_executed must be bool")
    _require_mapping(runtime["product"], "webshop_runtime.product")
    _require_mapping(runtime["source"], "webshop_runtime.source")

    experiment = _require_mapping(top["experiment_context"], "experiment_context")
    if experiment.get("origin") != EXPECTED_EXPERIMENT_CONTEXT_ORIGIN:
        raise WebShopJourneyPlayerInputError(
            "experiment_context.origin must remain explicit_experiment_context_not_webshop_verified"
        )

    commerce = _require_mapping(top["commerce_adaptation"], "commerce_adaptation")
    _require_mapping(commerce.get("order"), "commerce_adaptation.order")
    _require_mapping(commerce.get("payment_request"), "commerce_adaptation.payment_request")
    if commerce.get("ready") is not True:
        raise WebShopJourneyPlayerInputError("commerce_adaptation.ready must be true")

    payment = _require_mapping(
        top["payment_authoritative_trace"], "payment_authoritative_trace"
    )
    events = payment.get("events")
    bindings = payment.get("source_bindings")
    if not isinstance(events, list) or not events:
        raise WebShopJourneyPlayerInputError(
            "payment_authoritative_trace.events must be a non-empty list"
        )
    if not isinstance(bindings, list) or not bindings:
        raise WebShopJourneyPlayerInputError(
            "payment_authoritative_trace.source_bindings must be a non-empty list"
        )
    binding_refs: list[str] = []
    for index, raw_binding in enumerate(bindings):
        binding = _require_mapping(
            raw_binding, f"payment_authoritative_trace.source_bindings[{index}]"
        )
        _require_exact_keys(
            binding,
            _REQUIRED_PAYMENT_BINDING,
            f"payment_authoritative_trace.source_bindings[{index}]",
        )
        ref = _require_text(
            binding["binding_ref"],
            f"payment_authoritative_trace.source_bindings[{index}].binding_ref",
        )
        binding_refs.append(ref)
        _require_mapping(
            binding["projection"],
            f"payment_authoritative_trace.source_bindings[{index}].projection",
        )
    if len(binding_refs) != len(set(binding_refs)):
        raise WebShopJourneyPlayerInputError("payment source binding refs must be unique")
    binding_ref_set = set(binding_refs)
    for index, raw_event in enumerate(events):
        event = _require_mapping(raw_event, f"payment_authoritative_trace.events[{index}]")
        _require_exact_keys(
            event,
            _REQUIRED_PAYMENT_EVENT,
            f"payment_authoritative_trace.events[{index}]",
        )
        if event.get("source_binding_ref") not in binding_ref_set:
            raise WebShopJourneyPlayerInputError(
                f"payment_authoritative_trace.events[{index}].source_binding_ref is unresolved"
            )
        if not isinstance(event.get("relations"), list):
            raise WebShopJourneyPlayerInputError(
                f"payment_authoritative_trace.events[{index}].relations must be a list"
            )

    correlations = top["correlations"]
    if not isinstance(correlations, list) or not correlations:
        raise WebShopJourneyPlayerInputError("correlations must be a non-empty list")
    for index, raw_correlation in enumerate(correlations):
        correlation = _require_mapping(raw_correlation, f"correlations[{index}]")
        _require_exact_keys(correlation, _REQUIRED_CORRELATION, f"correlations[{index}]")
        for key in ("correlation_id", "source_path", "target_path"):
            _require_text(correlation[key], f"correlations[{index}].{key}")
        if correlation["equal"] is not True:
            raise WebShopJourneyPlayerInputError(
                f"correlations[{index}] must remain verified equal"
            )

    limitations = _require_string_list(top["limitations"], "limitations")
    limitation_set = set(limitations)
    if _REQUIRED_FIXED_SCRIPT_LIMITATION not in limitation_set:
        raise WebShopJourneyPlayerInputError("fixed-script boundary limitation is required")
    if not _REQUIRED_SOURCE_LIMITATIONS.issubset(limitation_set):
        raise WebShopJourneyPlayerInputError("source-boundary limitations are required")
    return top


def build_webshop_journey_player_payload(read_model: object) -> dict[str, Any]:
    """Project the accepted Journey Read Model unchanged after local UI checks."""

    if type(read_model) is not WebShopJourneyReadModel:
        raise WebShopJourneyPlayerInputError("player requires WebShopJourneyReadModel")
    try:
        primitive = webshop_journey_read_model_to_primitive(read_model)
    except (AttributeError, AssertionError, TypeError, ValueError) as exc:
        raise WebShopJourneyPlayerInputError("journey read model cannot be projected") from exc
    return _validate_payload(primitive)


def _canonical_payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _escape_script_data(text: str) -> str:
    return (
        text.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def webshop_journey_player_payload_json(read_model: object) -> str:
    payload = build_webshop_journey_player_payload(read_model)
    return _escape_script_data(_canonical_payload_json(payload))


_HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WebShop 购买旅程只读播放器</title>
<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#1f2328;background:#f6f8fa}body{margin:0}.page{max-width:1180px;margin:0 auto;padding:24px}.card{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:18px;margin:14px 0}.notice{border-left:4px solid #57606a;padding:8px 12px;margin:10px 0;background:#f6f8fa}.warning{border-left-color:#9a6700}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.field{border-bottom:1px solid #eaeef2;padding:8px 0}.label{display:block;font-size:12px;color:#57606a;margin-bottom:4px}.value{white-space:pre-wrap;overflow-wrap:anywhere}.controls{display:flex;gap:8px;flex-wrap:wrap}.controls button{padding:8px 14px;border:1px solid #8c959f;border-radius:6px;background:#fff;cursor:pointer}.controls button:disabled{opacity:.45;cursor:not-allowed}.source-nav button[aria-pressed="true"]{font-weight:700;border-color:#57606a;background:#f6f8fa}.source-section[hidden]{display:none}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fa;border-radius:6px;padding:10px}.step{font-size:14px;color:#57606a}.empty{color:#6e7781}.pill{display:inline-block;border:1px solid #d0d7de;border-radius:999px;padding:3px 8px;margin:2px;font-size:12px}.ok{font-weight:700}.source-title{margin-bottom:4px}.subtle{color:#57606a}.correlation{border-top:1px solid #eaeef2;padding-top:12px;margin-top:12px}</style>
</head>
<body>
<main class="page">
<h1>WebShop 购买旅程只读播放器</h1>
<p class="notice warning">固定脚本轨迹，不代表自主 Agent。页面只展示已冻结证据，不会执行 WebShop、Buy Now、支付、订单、履约或任何网络动作。</p>
<p class="notice">实验补充字段不是 WebShop 核验事实；支付权威轨迹是独立证据源。</p>
<p class="notice warning">用户需求与所选商品会原样并列展示。本页面不判断二者是否匹配，也不会做语义修复。</p>
<section class="card"><h2>旅程摘要</h2><div id="summary" class="grid"></div></section>
<section class="card"><h2>事实源导航</h2><div class="controls source-nav" id="sourceNav"></div></section>
<section id="sourceSections">
<section class="card source-section" data-source="webshop_runtime"><h2 class="source-title">1. 用户需求与商城动作 / webshop_runtime</h2><p class="subtle">来自冻结 WebShop/runtime-facing evidence。</p><div id="webshopRuntime"></div></section>
<section class="card source-section" data-source="experiment_context" hidden><h2 class="source-title">2. 实验补充上下文 / experiment_context</h2><p class="subtle">显式实验上下文，不提升为 WebShop、支付或用户确认事实。</p><div id="experimentContext"></div></section>
<section class="card source-section" data-source="commerce_adaptation" hidden><h2 class="source-title">3. Commerce 派生对象 / commerce_adaptation</h2><p class="subtle">已接受 Adapter 的机械投影，不在页面重新映射业务。</p><div id="commerceAdaptation"></div></section>
<section class="card source-section" data-source="payment_authoritative_trace" hidden><h2 class="source-title">4. 支付权威证据 / payment_authoritative_trace</h2><p class="subtle">独立支付证据源；仅回放已接受的权威轨迹。</p><div class="controls"><button id="previousPayment" type="button">上一步</button><button id="nextPayment" type="button">下一步</button><button id="resetPayment" type="button">回到起点</button><button id="playPausePayment" type="button">自动播放</button></div><p id="paymentStep" class="step"></p><div id="paymentEvent"></div><h3>关系证据</h3><div id="paymentRelations"></div><h3>来源绑定</h3><div id="paymentBinding"></div></section>
<section class="card source-section" data-source="correlations" hidden><h2 class="source-title">5. 跨源关联 / correlations</h2><p class="subtle">只展示 Read Model 中已机械验证的路径、值与 equality。</p><div id="correlations"></div></section>
<section class="card source-section" data-source="limitations" hidden><h2 class="source-title">6. 限制与事实边界 / limitations</h2><div id="limitations"></div></section>
</section>
</main>
<script id="journey-payload" type="application/json">__JOURNEY_PAYLOAD__</script>
<script>
"use strict";
const payload = JSON.parse(document.getElementById("journey-payload").textContent);
const sourceDefinitions = [
  ["webshop_runtime", "商城事实"],
  ["experiment_context", "实验上下文"],
  ["commerce_adaptation", "Commerce 派生"],
  ["payment_authoritative_trace", "支付权威证据"],
  ["correlations", "跨源关联"],
  ["limitations", "事实边界"]
];
const sourceNav = document.getElementById("sourceNav");
const sourceSections = Array.from(document.querySelectorAll(".source-section"));
const summaryNode = document.getElementById("summary");
const runtimeNode = document.getElementById("webshopRuntime");
const experimentNode = document.getElementById("experimentContext");
const commerceNode = document.getElementById("commerceAdaptation");
const correlationNode = document.getElementById("correlations");
const limitationNode = document.getElementById("limitations");
const paymentEventNode = document.getElementById("paymentEvent");
const paymentRelationsNode = document.getElementById("paymentRelations");
const paymentBindingNode = document.getElementById("paymentBinding");
const paymentStepNode = document.getElementById("paymentStep");
const previousPayment = document.getElementById("previousPayment");
const nextPayment = document.getElementById("nextPayment");
const resetPayment = document.getElementById("resetPayment");
const playPausePayment = document.getElementById("playPausePayment");
const paymentBindings = new Map(payload.payment_authoritative_trace.source_bindings.map((item) => [item.binding_ref, item]));
let paymentIndex = 0;
let paymentTimer = null;

function appendField(parent, label, value) {
  const wrapper = document.createElement("div");
  wrapper.className = "field";
  const labelNode = document.createElement("span");
  labelNode.className = "label";
  labelNode.textContent = label;
  const valueNode = document.createElement("span");
  valueNode.className = "value";
  valueNode.textContent = value === null || value === undefined ? "—" : String(value);
  wrapper.append(labelNode, valueNode);
  parent.appendChild(wrapper);
}
function appendJson(parent, label, value) {
  const wrapper = document.createElement("div");
  const labelNode = document.createElement("div");
  labelNode.className = "label";
  labelNode.textContent = label;
  const valueNode = document.createElement("pre");
  valueNode.textContent = JSON.stringify(value, null, 2);
  wrapper.append(labelNode, valueNode);
  parent.appendChild(wrapper);
}
function showSource(name) {
  sourceSections.forEach((section) => { section.hidden = section.dataset.source !== name; });
  Array.from(sourceNav.querySelectorAll("button")).forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.source === name));
  });
}
function renderSourceNav() {
  sourceDefinitions.forEach(([name, label], index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.source = name;
    button.textContent = `${index + 1}. ${label}`;
    button.setAttribute("aria-pressed", String(index === 0));
    button.addEventListener("click", () => showSource(name));
    sourceNav.appendChild(button);
  });
}
function renderSummary() {
  const runtime = payload.webshop_runtime;
  const product = runtime.product;
  appendField(summaryNode, "Journey 引用", payload.journey_ref);
  appendField(summaryNode, "来源分类状态", payload.source_classification_status);
  appendField(summaryNode, "用户需求（原文）", runtime.instruction_text);
  appendField(summaryNode, "所选商品（原文）", product.title);
  appendField(summaryNode, "商品 ASIN", product.asin);
  appendField(summaryNode, "商品总额", product.order_total);
  appendField(summaryNode, "Buy Now 可用", runtime.buy_now_available);
  appendField(summaryNode, "Buy Now 已执行", runtime.buy_now_executed);
}
function renderRuntime() {
  runtimeNode.replaceChildren();
  appendField(runtimeNode, "会话（session_id）", payload.webshop_runtime.session_id);
  appendField(runtimeNode, "任务标识（task_identifier）", payload.webshop_runtime.task_identifier);
  appendField(runtimeNode, "用户需求（instruction_text）", payload.webshop_runtime.instruction_text);
  appendJson(runtimeNode, "商城动作（actions_executed）", payload.webshop_runtime.actions_executed);
  appendField(runtimeNode, "Buy Now 可用", payload.webshop_runtime.buy_now_available);
  appendField(runtimeNode, "Buy Now 已执行", payload.webshop_runtime.buy_now_executed);
  appendJson(runtimeNode, "所选商品（product）", payload.webshop_runtime.product);
  appendJson(runtimeNode, "商城证据来源（source）", payload.webshop_runtime.source);
}
function renderExperiment() {
  experimentNode.replaceChildren();
  appendField(experimentNode, "来源语义（origin）", payload.experiment_context.origin);
  appendJson(experimentNode, "实验补充上下文", payload.experiment_context);
}
function renderCommerce() {
  commerceNode.replaceChildren();
  appendField(commerceNode, "用户意图投影", payload.commerce_adaptation.user_intent_text);
  appendField(commerceNode, "Experiment Context 来源", payload.commerce_adaptation.experiment_context_origin);
  appendField(commerceNode, "Adapter ready", payload.commerce_adaptation.ready);
  appendJson(commerceNode, "订单（order）", payload.commerce_adaptation.order);
  appendJson(commerceNode, "支付请求（payment_request）", payload.commerce_adaptation.payment_request);
  appendJson(commerceNode, "来源元数据", {
    source_commit: payload.commerce_adaptation.source_commit,
    fixture_version: payload.commerce_adaptation.fixture_version,
    source_smoke_sha256: payload.commerce_adaptation.source_smoke_sha256,
    source_asset_hashes: payload.commerce_adaptation.source_asset_hashes
  });
  appendJson(commerceNode, "Adapter 限制", payload.commerce_adaptation.limitations);
}
function renderPaymentEvent() {
  const events = payload.payment_authoritative_trace.events;
  const event = events[paymentIndex];
  paymentEventNode.replaceChildren();
  paymentRelationsNode.replaceChildren();
  paymentBindingNode.replaceChildren();
  paymentStepNode.textContent = `支付轨迹第 ${paymentIndex + 1} / ${events.length} 步`;
  appendField(paymentEventNode, "序号", event.sequence_no);
  appendField(paymentEventNode, "事件类型", event.event_type);
  appendField(paymentEventNode, "实体类型", event.entity_type);
  appendField(paymentEventNode, "实体角色", event.entity_role);
  appendField(paymentEventNode, "实体引用", event.entity_ref);
  appendField(paymentEventNode, "来源绑定", event.source_binding_ref);
  appendField(paymentEventNode, "决策", event.decision);
  appendField(paymentEventNode, "状态", event.status);
  appendJson(paymentEventNode, "原因码", event.reason_codes);
  if (event.relations.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "当前支付事件没有关系记录。";
    paymentRelationsNode.appendChild(empty);
  } else {
    event.relations.forEach((relation, index) => appendJson(paymentRelationsNode, `关系 ${index + 1}`, relation));
  }
  const binding = paymentBindings.get(event.source_binding_ref);
  appendField(paymentBindingNode, "绑定引用", binding.binding_ref);
  appendField(paymentBindingNode, "来源对象类型", binding.source_object_type);
  appendField(paymentBindingNode, "来源对象引用", binding.source_object_ref);
  appendField(paymentBindingNode, "投影模式", binding.projection_schema);
  appendJson(paymentBindingNode, "冻结投影", binding.projection);
  previousPayment.disabled = paymentIndex === 0;
  nextPayment.disabled = paymentIndex === events.length - 1;
}
function stopPaymentPlayback() {
  if (paymentTimer !== null) {
    clearInterval(paymentTimer);
    paymentTimer = null;
  }
  playPausePayment.textContent = "自动播放";
}
function renderCorrelations() {
  correlationNode.replaceChildren();
  payload.correlations.forEach((item, index) => {
    const group = document.createElement("div");
    group.className = "correlation";
    appendField(group, `关联 ${index + 1}`, item.correlation_id);
    appendField(group, "来源路径", item.source_path);
    appendJson(group, "来源值", item.source_value);
    appendField(group, "目标路径", item.target_path);
    appendJson(group, "目标值", item.target_value);
    appendField(group, "机械相等（equal）", item.equal);
    correlationNode.appendChild(group);
  });
}
function renderLimitations() {
  limitationNode.replaceChildren();
  payload.limitations.forEach((item) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = item;
    limitationNode.appendChild(pill);
  });
}
previousPayment.addEventListener("click", () => { stopPaymentPlayback(); paymentIndex = Math.max(0, paymentIndex - 1); renderPaymentEvent(); });
nextPayment.addEventListener("click", () => { stopPaymentPlayback(); paymentIndex = Math.min(payload.payment_authoritative_trace.events.length - 1, paymentIndex + 1); renderPaymentEvent(); });
resetPayment.addEventListener("click", () => { stopPaymentPlayback(); paymentIndex = 0; renderPaymentEvent(); });
playPausePayment.addEventListener("click", () => {
  if (paymentTimer !== null) { stopPaymentPlayback(); return; }
  playPausePayment.textContent = "暂停";
  paymentTimer = setInterval(() => {
    if (paymentIndex >= payload.payment_authoritative_trace.events.length - 1) { stopPaymentPlayback(); return; }
    paymentIndex += 1;
    renderPaymentEvent();
  }, 1200);
});
renderSourceNav();
renderSummary();
renderRuntime();
renderExperiment();
renderCommerce();
renderPaymentEvent();
renderCorrelations();
renderLimitations();
</script>
</body>
</html>
"""


def render_webshop_journey_player(read_model: object) -> str:
    payload_json = webshop_journey_player_payload_json(read_model)
    return _HTML_TEMPLATE.replace("__JOURNEY_PAYLOAD__", payload_json, 1)


def webshop_journey_player_html_bytes(read_model: object) -> bytes:
    return render_webshop_journey_player(read_model).encode("utf-8")


def webshop_journey_player_html_sha256(read_model: object) -> str:
    return hashlib.sha256(webshop_journey_player_html_bytes(read_model)).hexdigest()


def webshop_journey_player_payload_sha256(read_model: object) -> str:
    return hashlib.sha256(webshop_journey_player_payload_json(read_model).encode("utf-8")).hexdigest()


__all__ = [
    "WebShopJourneyPlayerInputError",
    "build_webshop_journey_player_payload",
    "render_webshop_journey_player",
    "webshop_journey_player_html_bytes",
    "webshop_journey_player_html_sha256",
    "webshop_journey_player_payload_json",
    "webshop_journey_player_payload_sha256",
]
