"""Deterministic, read-only HTML player for accepted authoritative trace read models."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .authoritative_trace_consumer import (
    AuthoritativeTraceReadModel,
    trace_read_model_to_primitive,
)


class TracePlayerInputError(ValueError):
    """Raised when the generic read-model boundary is structurally unusable."""


_REQUIRED_TOP_LEVEL = {
    "trace_ref",
    "profile",
    "schema_version",
    "source",
    "completeness_status",
    "reason_codes",
    "events",
    "source_bindings",
}
_REQUIRED_EVENT = {
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
_REQUIRED_RELATION = {
    "relation_type",
    "target_entity_type",
    "target_entity_role",
    "target_entity_ref",
    "target_resolved",
    "target_binding_assertions",
}
_REQUIRED_ASSERTION = {
    "source_path",
    "target_path",
    "source_value",
    "target_value",
    "equal",
}
_REQUIRED_BINDING = {
    "binding_ref",
    "source_object_type",
    "source_object_ref",
    "projection_schema",
    "projection",
}


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TracePlayerInputError(f"{label} must be an object")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise TracePlayerInputError(f"{label} has unexpected shape")


def _require_string(value: object, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        raise TracePlayerInputError(f"{label} must be a string")
    return value


def _require_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TracePlayerInputError(f"{label} must be a string list")
    return value


def _validate_payload(payload: object) -> dict[str, Any]:
    top = _require_mapping(payload, "read model")
    _require_exact_keys(top, _REQUIRED_TOP_LEVEL, "read model")
    for key in ("trace_ref", "profile", "schema_version", "source", "completeness_status"):
        _require_string(top[key], key)
    _require_string_list(top["reason_codes"], "reason_codes")

    events = top["events"]
    bindings = top["source_bindings"]
    if not isinstance(events, list) or not events:
        raise TracePlayerInputError("events must be a non-empty list")
    if not isinstance(bindings, list) or not bindings:
        raise TracePlayerInputError("source_bindings must be a non-empty list")

    binding_refs: list[str] = []
    for index, raw_binding in enumerate(bindings):
        binding = _require_mapping(raw_binding, f"source_bindings[{index}]")
        _require_exact_keys(binding, _REQUIRED_BINDING, f"source_bindings[{index}]")
        ref = _require_string(binding["binding_ref"], f"source_bindings[{index}].binding_ref")
        binding_refs.append(ref)
        for key in ("source_object_type", "source_object_ref", "projection_schema"):
            _require_string(binding[key], f"source_bindings[{index}].{key}")
        _require_mapping(binding["projection"], f"source_bindings[{index}].projection")
    if len(binding_refs) != len(set(binding_refs)):
        raise TracePlayerInputError("source binding refs must be unique")
    binding_ref_set = set(binding_refs)

    for event_index, raw_event in enumerate(events):
        event = _require_mapping(raw_event, f"events[{event_index}]")
        _require_exact_keys(event, _REQUIRED_EVENT, f"events[{event_index}]")
        if not isinstance(event["sequence_no"], int) or isinstance(event["sequence_no"], bool):
            raise TracePlayerInputError(f"events[{event_index}].sequence_no must be an integer")
        for key in ("event_type", "entity_type", "entity_role", "entity_ref", "source_binding_ref"):
            _require_string(event[key], f"events[{event_index}].{key}")
        for key in ("decision", "status"):
            if event[key] is not None and not isinstance(event[key], str):
                raise TracePlayerInputError(f"events[{event_index}].{key} must be a string or null")
        _require_string_list(event["reason_codes"], f"events[{event_index}].reason_codes")
        if event["source_binding_ref"] not in binding_ref_set:
            raise TracePlayerInputError(f"events[{event_index}].source_binding_ref is unresolved")

        relations = event["relations"]
        if not isinstance(relations, list):
            raise TracePlayerInputError(f"events[{event_index}].relations must be a list")
        for relation_index, raw_relation in enumerate(relations):
            relation = _require_mapping(
                raw_relation,
                f"events[{event_index}].relations[{relation_index}]",
            )
            _require_exact_keys(
                relation,
                _REQUIRED_RELATION,
                f"events[{event_index}].relations[{relation_index}]",
            )
            for key in (
                "relation_type",
                "target_entity_type",
                "target_entity_role",
                "target_entity_ref",
            ):
                _require_string(
                    relation[key],
                    f"events[{event_index}].relations[{relation_index}].{key}",
                )
            if relation["target_resolved"] is not None and not isinstance(
                relation["target_resolved"], bool
            ):
                raise TracePlayerInputError("relation target_resolved must be bool or null")
            assertions = relation["target_binding_assertions"]
            if not isinstance(assertions, list):
                raise TracePlayerInputError("target_binding_assertions must be a list")
            for assertion_index, raw_assertion in enumerate(assertions):
                assertion = _require_mapping(raw_assertion, "binding assertion")
                _require_exact_keys(assertion, _REQUIRED_ASSERTION, "binding assertion")
                _require_string(assertion["source_path"], "binding assertion source_path")
                _require_string(assertion["target_path"], "binding assertion target_path")
                if assertion["equal"] is not None and not isinstance(assertion["equal"], bool):
                    raise TracePlayerInputError("binding assertion equal must be bool or null")

    return top


def build_trace_player_payload(read_model: object) -> dict[str, Any]:
    """Return the accepted Read Model primitive unchanged after structural UI checks."""

    if not isinstance(read_model, AuthoritativeTraceReadModel):
        raise TracePlayerInputError("player requires AuthoritativeTraceReadModel")
    try:
        primitive = trace_read_model_to_primitive(read_model)
    except (AttributeError, AssertionError, TypeError, ValueError) as exc:
        raise TracePlayerInputError("read model cannot be projected") from exc
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


def trace_player_payload_json(read_model: object) -> str:
    """Return deterministic JSON safe for an HTML script-data boundary."""

    payload = build_trace_player_payload(read_model)
    return _escape_script_data(_canonical_payload_json(payload))


_HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>权威轨迹只读播放器</title>
<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#1f2328;background:#f6f8fa}
body{margin:0}.page{max-width:1100px;margin:0 auto;padding:24px}.card{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:18px;margin:14px 0}.notice{border-left:4px solid #57606a;padding-left:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}.field{border-bottom:1px solid #eaeef2;padding:8px 0}.label{display:block;font-size:12px;color:#57606a;margin-bottom:4px}.value{white-space:pre-wrap;overflow-wrap:anywhere}.controls{display:flex;gap:8px;flex-wrap:wrap}.controls button{padding:8px 14px;border:1px solid #8c959f;border-radius:6px;background:#fff;cursor:pointer}.controls button:disabled{opacity:.45;cursor:not-allowed}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fa;border-radius:6px;padding:10px}.step{font-size:14px;color:#57606a}.empty{color:#6e7781}</style>
</head>
<body>
<main class="page">
<h1>权威轨迹只读播放器</h1>
<p class="notice">离线只读：播放仅展示已冻结证据，不会执行 WebShop、Buy Now、支付、订单或履约动作。</p>
<section class="card"><h2>轨迹元数据</h2><div id="metadata" class="grid"></div></section>
<section class="card"><div class="controls"><button id="previous" type="button">上一步</button><button id="next" type="button">下一步</button><button id="reset" type="button">回到起点</button><button id="playPause" type="button">自动播放</button></div><p id="step" class="step"></p></section>
<section class="card"><h2>当前事件</h2><div id="event"></div></section>
<section class="card"><h2>关系证据</h2><div id="relations"></div></section>
<section class="card"><h2>来源绑定证据</h2><div id="binding"></div></section>
</main>
<script id="trace-payload" type="application/json">__TRACE_PAYLOAD__</script>
<script>
"use strict";
const payload = JSON.parse(document.getElementById("trace-payload").textContent);
const metadataNode = document.getElementById("metadata");
const eventNode = document.getElementById("event");
const relationsNode = document.getElementById("relations");
const bindingNode = document.getElementById("binding");
const stepNode = document.getElementById("step");
const previousButton = document.getElementById("previous");
const nextButton = document.getElementById("next");
const resetButton = document.getElementById("reset");
const playPauseButton = document.getElementById("playPause");
const bindingsByRef = new Map(payload.source_bindings.map((item) => [item.binding_ref, item]));
let playbackIndex = 0;
let playbackTimer = null;

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

function renderMetadata() {
  metadataNode.replaceChildren();
  appendField(metadataNode, "轨迹引用（trace_ref）", payload.trace_ref);
  appendField(metadataNode, "轨迹配置（profile）", payload.profile);
  appendField(metadataNode, "模式版本（schema_version）", payload.schema_version);
  appendField(metadataNode, "证据来源（source）", payload.source);
  appendField(metadataNode, "完整性（completeness_status）", payload.completeness_status);
  appendJson(metadataNode, "轨迹原因码（reason_codes）", payload.reason_codes);
}

function renderRelations(event) {
  relationsNode.replaceChildren();
  if (event.relations.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "当前事件没有关系记录。";
    relationsNode.appendChild(empty);
    return;
  }
  event.relations.forEach((relation, index) => {
    const group = document.createElement("div");
    appendField(group, `关系 ${index + 1} 类型（relation_type）`, relation.relation_type);
    appendField(group, "目标实体类型（target_entity_type）", relation.target_entity_type);
    appendField(group, "目标实体角色（target_entity_role）", relation.target_entity_role);
    appendField(group, "目标实体引用（target_entity_ref）", relation.target_entity_ref);
    appendField(group, "目标已解析（target_resolved）", relation.target_resolved);
    appendJson(group, "绑定断言（target_binding_assertions）", relation.target_binding_assertions);
    relationsNode.appendChild(group);
  });
}

function renderBinding(event) {
  bindingNode.replaceChildren();
  const binding = bindingsByRef.get(event.source_binding_ref);
  appendField(bindingNode, "绑定引用（binding_ref）", binding.binding_ref);
  appendField(bindingNode, "来源对象类型（source_object_type）", binding.source_object_type);
  appendField(bindingNode, "来源对象引用（source_object_ref）", binding.source_object_ref);
  appendField(bindingNode, "投影模式（projection_schema）", binding.projection_schema);
  appendJson(bindingNode, "冻结投影（projection）", binding.projection);
}

function renderCurrentEvent() {
  const event = payload.events[playbackIndex];
  eventNode.replaceChildren();
  stepNode.textContent = `第 ${playbackIndex + 1} / ${payload.events.length} 步`;
  appendField(eventNode, "序号（sequence_no）", event.sequence_no);
  appendField(eventNode, "事件类型（event_type）", event.event_type);
  appendField(eventNode, "实体类型（entity_type）", event.entity_type);
  appendField(eventNode, "实体角色（entity_role）", event.entity_role);
  appendField(eventNode, "实体引用（entity_ref）", event.entity_ref);
  appendField(eventNode, "来源绑定（source_binding_ref）", event.source_binding_ref);
  appendField(eventNode, "决策（decision）", event.decision);
  appendField(eventNode, "状态（status）", event.status);
  appendJson(eventNode, "原因码（reason_codes）", event.reason_codes);
  renderRelations(event);
  renderBinding(event);
  previousButton.disabled = playbackIndex === 0;
  nextButton.disabled = playbackIndex === payload.events.length - 1;
}

function stopPlayback() {
  if (playbackTimer !== null) {
    clearInterval(playbackTimer);
    playbackTimer = null;
  }
  playPauseButton.textContent = "自动播放";
}

previousButton.addEventListener("click", () => {
  stopPlayback();
  playbackIndex = Math.max(0, playbackIndex - 1);
  renderCurrentEvent();
});
nextButton.addEventListener("click", () => {
  stopPlayback();
  playbackIndex = Math.min(payload.events.length - 1, playbackIndex + 1);
  renderCurrentEvent();
});
resetButton.addEventListener("click", () => {
  stopPlayback();
  playbackIndex = 0;
  renderCurrentEvent();
});
playPauseButton.addEventListener("click", () => {
  if (playbackTimer !== null) {
    stopPlayback();
    return;
  }
  playPauseButton.textContent = "暂停";
  playbackTimer = setInterval(() => {
    if (playbackIndex >= payload.events.length - 1) {
      stopPlayback();
      return;
    }
    playbackIndex += 1;
    renderCurrentEvent();
  }, 1200);
});
renderMetadata();
renderCurrentEvent();
</script>
</body>
</html>
"""


def render_authoritative_trace_player(read_model: object) -> str:
    """Render one self-contained deterministic HTML evidence player."""

    payload_json = trace_player_payload_json(read_model)
    return _HTML_TEMPLATE.replace("__TRACE_PAYLOAD__", payload_json, 1)


def trace_player_html_bytes(read_model: object) -> bytes:
    return render_authoritative_trace_player(read_model).encode("utf-8")


def trace_player_html_sha256(read_model: object) -> str:
    return hashlib.sha256(trace_player_html_bytes(read_model)).hexdigest()


def trace_player_payload_sha256(read_model: object) -> str:
    return hashlib.sha256(trace_player_payload_json(read_model).encode("utf-8")).hexdigest()


__all__ = [
    "TracePlayerInputError",
    "build_trace_player_payload",
    "render_authoritative_trace_player",
    "trace_player_html_bytes",
    "trace_player_html_sha256",
    "trace_player_payload_json",
    "trace_player_payload_sha256",
]
