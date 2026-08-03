from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>智能体支付交互沙盘 · 中文学习版</title>
  <style>
    :root { font-family: "Microsoft YaHei", system-ui, sans-serif; color: #172033; background: #f3f5f8; }
    * { box-sizing: border-box; }
    body { margin: 0; }
    button { font: inherit; }
    button:focus-visible, summary:focus-visible { outline: 3px solid #f59e0b; outline-offset: 2px; }
    header { padding: 18px 24px; background: #fff; border-bottom: 1px solid #dfe4ea; position: sticky; top: 0; z-index: 5; }
    header h1 { margin: 0 0 5px; font-size: 23px; }
    header p { margin: 0; color: #5d687a; font-size: 13px; }
    .offline-warning { margin-top: 10px; padding: 9px 12px; background: #fff4d6; border-left: 4px solid #c27a00; font-weight: 700; }
    .summary { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .pill { background: #eef2f7; padding: 5px 9px; border-radius: 999px; font-size: 12px; }
    .layout { min-height: calc(100vh - 140px); }
    main { padding: 18px; min-width: 0; max-width: 1280px; width: 100%; margin: 0 auto; }
    .module-controls { display: grid; grid-template-columns: minmax(220px, 0.7fr) minmax(280px, 1.3fr); gap: 10px; align-items: end; }
    .module-field { display: grid; gap: 5px; }
    .module-field label { color: #596579; font-size: 12px; font-weight: 700; }
    .module-field select { width: 100%; border: 1px solid #cad1da; border-radius: 8px; padding: 9px 10px; background: #fff; font: inherit; }
    .module-result { margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e9ef; }
    .module-result p { margin: 6px 0; }
    .module-result-title { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .module-result-title h2 { margin: 0; }
    .module-detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 10px; }
    .module-detail-row { background: #f7f9fc; border-radius: 8px; padding: 9px 10px; font-size: 13px; }
    .PASS { background: #e5f6eb; color: #176637; }
    .PARTIAL { background: #fff3d8; color: #825400; }
    .UNSUPPORTED { background: #eceef2; color: #414b5a; }
    .variant-button { width: 100%; text-align: left; border: 1px solid #dfe4ea; background: #fff; border-radius: 10px; padding: 11px; margin-bottom: 8px; cursor: pointer; }
    .variant-button:hover, .variant-button.active { border-color: #3559c7; background: #f1f4ff; }
    .card { background: #fff; border: 1px solid #dfe4ea; border-radius: 12px; padding: 16px; margin-bottom: 14px; }
    .card h2, .card h3, .card h4 { margin-top: 0; }
    .interactive-card { border-color: #cfd8ea; }
    .interactive-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 12px 0; }
    .interactive-field { display: grid; gap: 5px; }
    .interactive-field label { font-size: 12px; color: #596579; font-weight: 700; }
    .interactive-field input, .interactive-field select { width: 100%; border: 1px solid #cad1da; border-radius: 8px; padding: 9px 10px; background: #fff; font: inherit; }
    .interactive-field small { color: #7b8799; }
    .interactive-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .interactive-result { margin-top: 12px; border-top: 1px solid #e5e9ef; padding-top: 12px; }
    .interactive-result h4 { margin-bottom: 8px; }
    .interactive-result p { margin: 6px 0; }
    .interactive-status { font-size: 12px; color: #596579; }
    .title-row, .controls, .tabs, .variant-buttons { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .badge { padding: 5px 9px; border-radius: 999px; font-weight: 700; font-size: 12px; }
    .ALLOW { background: #e5f6eb; color: #176637; }
    .DENY { background: #fdebea; color: #a12a25; }
    .CONFIRMATION_REQUIRED { background: #fff3d8; color: #825400; }
    .INDETERMINATE { background: #eceef2; color: #414b5a; }
    .protocol-badge { background: #e8edff; color: #284bb5; }
    .neutral-badge { background: #eef1f4; color: #505a68; }
    .validation-badge { background: #f1faf4; color: #176637; }
    .muted { color: #687386; font-size: 13px; }
    .learning-grid, .data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .unified-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .unified-panel { border: 1px solid #dfe4ea; border-radius: 10px; padding: 12px; background: #fff; min-width: 0; }
    .unified-panel.wide { grid-column: 1 / -1; }
    .unified-panel h4 { margin-bottom: 10px; }
    .field-list { display: grid; gap: 6px; }
    .field-row { display: grid; grid-template-columns: minmax(125px, 0.8fr) minmax(0, 1.2fr); gap: 8px; padding: 7px 8px; border-radius: 8px; background: #f7f9fc; }
    .field-row .field-label { color: #596579; font-size: 12px; }
    .field-row .field-value { font-weight: 700; word-break: break-word; }
    .field-row.risk { background: #fdebea; border-left: 4px solid #a12a25; }
    .field-row.attention { background: #fff8e7; border-left: 4px solid #c27a00; }
    .field-row.indeterminate { background: #eceef2; border-left: 4px solid #596579; }
    .order-slots { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .order-slot { border: 1px solid #dfe4ea; border-radius: 9px; padding: 10px; background: #fafbfc; min-width: 0; }
    .order-slot h5 { margin: 0 0 6px; font-size: 13px; }
    .order-slot pre { max-height: 220px; margin-top: 8px; }
    .check-list { display: grid; gap: 7px; }
    .check-row { display: grid; grid-template-columns: minmax(170px, 0.8fr) 92px minmax(0, 1.5fr); gap: 8px; align-items: start; padding: 8px; border-radius: 8px; background: #f7f9fc; }
    .check-status { font-weight: 800; }
    .check-row.fail { background: #fdebea; }
    .check-row.confirmation_required { background: #fff8e7; }
    .check-row.indeterminate { background: #eceef2; }
    .check-row.not_applicable { color: #687386; }
    .learning-box, .reason-box { border: 1px solid #dfe4ea; border-radius: 10px; padding: 12px; background: #fafbfc; }
    .matrix-position { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin: 8px 0 12px; }
    .matrix-position strong { font-size: 15px; }
    .matrix-scroll { overflow-x: auto; }
    .matrix-table { min-width: 980px; table-layout: fixed; }
    .matrix-table th:first-child, .matrix-table td:first-child { width: 180px; position: sticky; left: 0; z-index: 1; }
    .matrix-table th:first-child { z-index: 2; }
    .matrix-table td:first-child { background: #fff; }
    .matrix-cell { text-align: center; min-width: 78px; height: 44px; color: #9aa3b1; }
    .matrix-cell.primary { background: #fdebea; color: #a12a25; font-weight: 800; box-shadow: inset 0 0 0 2px #a12a25; }
    .matrix-stage.detect { background: #fff8e7; color: #825400; font-weight: 800; }
    .matrix-legend { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 8px; color: #687386; font-size: 12px; }
    .matrix-dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; vertical-align: -1px; }
    .matrix-dot.primary { background: #fdebea; border: 1px solid #a12a25; }
    .matrix-dot.detect { background: #fff8e7; border: 1px solid #c27a00; }
    .key-stage-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; align-items: start; }
    .payment-mainline-card { border: 1px solid #dfe4ea; border-radius: 10px; background: #fafbfc; padding: 12px; }
    .payment-mainline-card h4 { margin-bottom: 10px; }
    .payment-mainline-card p { margin: 6px 0; font-size: 13px; }
    .key-stage-technical { margin-top: 12px; border: 1px solid #dfe4ea; border-radius: 10px; padding: 10px 12px; background: #fff; }
    .key-stage-technical > summary { font-weight: 800; }
    .technical-stage-block { margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e9ef; }
    .technical-stage-block:first-child { border-top: 0; padding-top: 0; }
    .trusted-execution-card { border: 1px solid #d9deee; border-radius: 10px; background: #f8f9fd; padding: 12px; }
    .trusted-execution-card h4 { margin-bottom: 10px; }
    .trusted-stage-item { padding: 10px 0; border-top: 1px solid #e1e5f0; }
    .trusted-stage-item:first-of-type { border-top: 0; padding-top: 0; }
    .trusted-stage-head { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 7px; }
    .trusted-stage-title { font-weight: 800; }
    .trusted-stage-status { padding: 3px 7px; border-radius: 999px; background: #e9edfb; color: #3d4f94; font-size: 12px; font-weight: 800; }
    .trusted-stage-item p { margin: 5px 0; font-size: 13px; }
    .trusted-capabilities-inline { color: #596579; font-size: 12px; margin-bottom: 7px; }
    .misconception { border-left: 4px solid #d07b00; background: #fff8e7; padding: 10px 12px; }
    .takeaway { border-left: 4px solid #176637; background: #f1faf4; padding: 10px 12px; }
    .control, .tab { border: 1px solid #cad1da; background: #fff; border-radius: 8px; padding: 7px 11px; cursor: pointer; }
    .control:hover, .tab:hover { border-color: #3559c7; }
    .control.primary, .tab.active { background: #3559c7; color: #fff; border-color: #3559c7; }
    .progress { color: #596579; font-size: 13px; margin-left: auto; }
    .flow { display: flex; align-items: stretch; overflow-x: auto; padding: 12px 2px; }
    .neutral-notice { background: #eef1f4; border-left: 4px solid #596579; padding: 9px 11px; font-size: 12px; }
    .step-button { min-width: 165px; max-width: 205px; border: 1px solid #dfe4ea; border-radius: 10px; padding: 11px; background: #fafbfc; cursor: pointer; text-align: left; }
    .step-button.done { border-color: #9bc9aa; background: #f1faf4; }
    .step-button.active { border: 2px solid #3559c7; background: #eef2ff; }
    .step-number { font-size: 11px; color: #7b8799; }
    .step-actor { font-weight: 700; margin: 4px 0; }
    .step-action { color: #596579; font-size: 12px; }
    .arrow { display: flex; align-items: center; padding: 0 8px; color: #7b8799; font-size: 20px; }
    .step-facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 12px 0; }
    .step-fact { background: #f7f9fc; border-radius: 8px; padding: 9px; font-size: 12px; }
    pre { margin: 0; padding: 12px; border-radius: 9px; background: #111827; color: #e5e7eb; white-space: pre-wrap; word-break: break-word; font-size: 12px; max-height: 380px; overflow: auto; }
    .plain-data { margin: 0; padding: 12px; border-radius: 9px; background: #f7f9fc; color: #172033; white-space: pre-wrap; word-break: break-word; font-size: 13px; max-height: 380px; overflow: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { border-bottom: 1px solid #e5e9ef; padding: 9px; text-align: left; vertical-align: top; }
    th { color: #596579; background: #fafbfc; }
    .reason-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 14px; }
    .reason-box h4 { margin-bottom: 5px; }
    .reason-box p { margin: 5px 0; }
    .variant-buttons { align-items: stretch; }
    .variant-button { width: auto; min-width: 150px; flex: 1 1 160px; }
    details summary { cursor: pointer; font-weight: 700; }
    .protocol-guide { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 12px; }
    .protocol-card { border: 1px solid #dfe4ea; border-radius: 10px; padding: 12px; background: #fafbfc; }
    .warning { background: #fff8e7; border-left: 4px solid #d39b1b; padding: 10px 12px; font-size: 13px; }
    .hidden { display: none; }
    ul { padding-left: 20px; }
    @media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
    @media (max-width: 850px) {
      .learning-grid, .data-grid, .reason-grid, .step-facts, .protocol-guide, .unified-grid, .order-slots, .key-stage-grid, .interactive-grid { grid-template-columns: 1fr; }
      .unified-panel.wide { grid-column: auto; }
      .module-controls, .module-detail-grid { grid-template-columns: 1fr; }
      .check-row { grid-template-columns: 1fr; }
      .progress { margin-left: 0; width: 100%; }
      .flow { flex-direction: column; overflow-x: visible; }
      .step-button { min-width: 0; max-width: none; width: 100%; }
      .arrow { justify-content: center; transform: rotate(90deg); }
      table { display: block; overflow-x: auto; }
    }
  </style>
</head>
<body>
<header>
  <h1>智能体支付可信实验室 · 中文交互版</h1>
  <p>先选择业务能力，理解系统要解决的支付信任问题；再进入内部场景、PayBench、AP2 或 Attack 等验证来源。</p>
  <div class="offline-warning">⚠ 离线模拟，不执行真实支付，不连接银行卡、商户或支付网络。</div>
  <div class="summary" id="summary"></div>
</header>
<div class="layout">
  <main>
    <section class="card" aria-label="业务能力选择" data-legacy-label="选择模块 / 选择场景 / 流程">
      <div class="module-controls">
        <div class="module-field">
          <label for="module-select">选择业务能力</label>
          <select id="module-select" aria-label="选择业务能力"></select>
        </div>
        <div class="module-field">
          <label for="module-item-select">选择验证来源 / 案例</label>
          <select id="module-item-select" aria-label="选择能力下的验证来源或案例"></select>
        </div>
      </div>
      <div class="module-result" id="module-result"></div>
    </section>

    <div id="m2-scenario-area">
    <section class="card" aria-labelledby="scenario-title">
      <div class="title-row">
        <h2 id="scenario-title"></h2>
        <span id="protocol-badge" class="badge"></span>
        <span id="validation-badge" class="badge validation-badge"></span>
      </div>
      <div class="learning-grid">
        <div class="learning-box"><h3>这个场景要学什么</h3><p id="objective"></p><p id="story"></p></div>
        <div><p class="misconception"><strong>常见误解：</strong><span id="misconception"></span></p><p class="takeaway"><strong>学习结论：</strong><span id="takeaway"></span></p></div>
      </div>
    </section>

    <section class="card interactive-card" id="interactive-card" aria-label="交互式实验">
      <h3>交互式实验</h3>
      <p class="muted">只改当前场景最关键的几个条件，然后由本地 Python 后端重新判断。这里不会执行真实支付。</p>
      <div id="interactive-fields" class="interactive-grid"></div>
      <div class="interactive-actions">
        <button class="control primary" id="interactive-run" type="button">执行验证</button>
        <button class="control" id="interactive-reset" type="button">恢复样品值</button>
        <span class="interactive-status" id="interactive-status"></span>
      </div>
      <div class="interactive-result hidden" id="interactive-result"></div>
    </section>

    <section class="card" aria-label="支付生命周期异常矩阵">
      <h3>支付生命周期异常矩阵</h3>
      <p class="muted">先定位问题发生在哪个生命周期阶段、属于哪类异常，再沿生命周期查看检测与处理过程。</p>
      <div class="matrix-position" id="matrix-position"></div>
      <div class="matrix-scroll">
        <table class="matrix-table" id="exception-matrix"></table>
      </div>
      <div class="matrix-legend">
        <span><i class="matrix-dot primary"></i>当前故障坐标</span>
        <span><i class="matrix-dot detect"></i>检测发生阶段</span>
      </div>
    </section>

    <section class="card" aria-label="当前场景关键环节">
      <h3>当前场景关键环节</h3>
      <div class="key-stage-grid">
        <div class="payment-mainline-card" id="payment-mainline-card"></div>
        <div class="trusted-execution-card" id="trusted-execution-card"></div>
      </div>
      <details class="key-stage-technical" id="key-stage-technical-details">
        <summary>开发者信息（可选）</summary>
        <div id="key-stage-technical-content"></div>
      </details>
    </section>

    <section class="card hidden" id="difference-card">
      <h3>用户确认订单与商户最终订单的差异</h3>
      <table><thead><tr><th>字段</th><th>用户确认/边界</th><th>商户最终/请求</th><th>变化说明</th></tr></thead><tbody id="difference-body"></tbody></table>
    </section>

    <section class="card hidden" id="variant-card">
      <h3>如果条件改变会怎样</h3>
      <p class="muted">这些结果均由 Python 后端调用真实验证器预先计算；按钮只切换展示，不在浏览器重新判断。</p>
      <div class="variant-buttons" id="variant-buttons"></div>
    </section>
    </div>

  </main>
</div>
<script>
const card = __CARD_JSON__;
const state = { scenarioIndex: 0, moduleIndex: 0, moduleItemIndex: 0, variantIndex: null, interactivePresentation: null };
const moduleSelect = document.getElementById('module-select');
const moduleItemSelect = document.getElementById('module-item-select');

function text(tag, value, className) {
  const node = document.createElement(tag);
  node.textContent = value == null ? '' : String(value);
  if (className) node.className = className;
  return node;
}
function pretty(value) { return JSON.stringify(value, null, 2); }
function scenario() { return card.scenarios[state.scenarioIndex]; }
function activeVariant() { return state.variantIndex == null ? null : scenario().learning_variants[state.variantIndex]; }
function view() {
  const base = scenario();
  const variant = activeVariant();
  if (!variant) return base;
  return {
    ...base,
    input: variant.input,
    actual: variant.actual,
    differences: variant.differences,
    walkthrough: variant.walkthrough,
    unified_view: variant.unified_view,
    lifecycle_teaching_view: variant.lifecycle_teaching_view,
    learning: { ...base.learning, story_zh: variant.story_zh },
  };
}
function displayView() { return state.interactivePresentation || view(); }
function currentStep() { return view().walkthrough[state.stepIndex]; }

function navigationModules() { return card.lab_overview?.capability_navigation || []; }
function currentModule() { return navigationModules()[state.moduleIndex]; }
function currentModuleItem() { return currentModule()?.validation_items?.[state.moduleItemIndex] || null; }

function renderSummary() {
  const box = document.getElementById('summary');
  box.replaceChildren();
  navigationModules().forEach(capability => {
    const value = capability.name_zh + ' · ' + capability.coverage_status_label_zh;
    box.appendChild(text('span', value, 'pill'));
  });
}

function renderModuleSelectors() {
  moduleSelect.replaceChildren();
  navigationModules().forEach((item, index) => {
    const option = document.createElement('option');
    option.value = String(index);
    option.textContent = item.name_zh + ' · ' + item.coverage_status_label_zh;
    moduleSelect.appendChild(option);
  });
  moduleSelect.addEventListener('change', () => selectModule(Number(moduleSelect.value)));
  moduleItemSelect.addEventListener('change', () => selectModuleItem(Number(moduleItemSelect.value)));
}

function populateModuleItems() {
  moduleItemSelect.replaceChildren();
  (currentModule()?.validation_items || []).forEach((item, index) => {
    const option = document.createElement('option');
    option.value = String(index);
    option.textContent = item.source_label_zh + ' · ' + item.name_zh;
    moduleItemSelect.appendChild(option);
  });
  moduleItemSelect.value = String(state.moduleItemIndex);
}

function selectModule(index) {
  state.moduleIndex = index;
  state.moduleItemIndex = 0;
  moduleSelect.value = String(index);
  populateModuleItems();
  renderModuleSelection();
}

function selectModuleItem(index) {
  state.moduleItemIndex = index;
  moduleItemSelect.value = String(index);
  renderModuleSelection();
}

function renderModuleSelection() {
  const capability = currentModule();
  const item = currentModuleItem();
  const panel = document.getElementById('module-result');
  panel.replaceChildren();
  if (!capability || !item) return;

  const titleRow = text('div', '', 'module-result-title');
  titleRow.appendChild(text('h2', capability.name_zh));
  titleRow.appendChild(text('span', capability.coverage_status_label_zh, 'badge ' + capability.coverage_status));
  panel.appendChild(titleRow);
  panel.appendChild(text('p', '业务问题：' + capability.business_question_zh));
  panel.appendChild(text('p', capability.coverage_summary_zh, 'muted'));

  const itemTitle = text('p', '');
  itemTitle.appendChild(text('strong', item.source_label_zh + ' · ' + item.name_zh + '：'));
  itemTitle.appendChild(document.createTextNode(item.headline_zh || ''));
  panel.appendChild(itemTitle);

  if (item.source_type === 'PAYBENCH' && item.details?.scenarios) {
    const grid = text('div', '', 'module-detail-grid');
    item.details.scenarios.forEach(row => {
      const kind = row.pair_type === 'trap' ? '危险案例' : '安全对照';
      const value = row.support_status === 'SUPPORTED'
        ? kind + ' · ' + row.evaluation_status + ' · ' + row.decision
        : kind + ' · 暂未支持';
      grid.appendChild(text('div', value, 'module-detail-row'));
    });
    panel.appendChild(grid);
  } else if (item.source_type === 'UNIFIED_EVALUATION' && item.details) {
    panel.appendChild(renderEvaluationMetrics(item.details));
  } else if (['AP2_SAMPLE', 'ATTACK_OVERLAY'].includes(item.source_type) && item.details) {
    const details = document.createElement('details');
    details.appendChild(text('summary', '开发者详情（可选）'));
    const grid = text('div', '', 'module-detail-grid');
    Object.entries(item.details).slice(0, 6).forEach(([key, value]) => {
      grid.appendChild(text('div', key + '：' + displayValue(value), 'module-detail-row'));
    });
    details.appendChild(grid);
    panel.appendChild(details);
  }

  const evaluator = document.createElement('details');
  evaluator.appendChild(text('summary', capability.evaluator_role.name_zh));
  evaluator.appendChild(text('p', capability.evaluator_role.description_zh, 'muted'));
  capability.evaluator_role.source_summaries.forEach(summary => {
    const block = text('div', '', 'module-detail-row');
    block.appendChild(text('strong', summary.source_label_zh + '：'));
    block.appendChild(document.createTextNode(
      summary.metrics.passed + '/' + summary.metrics.total + ' 通过，风险失败 ' + summary.metrics.failed
    ));
    evaluator.appendChild(block);
  });
  panel.appendChild(evaluator);

  const scenarioArea = document.getElementById('m2-scenario-area');
  const isInternalScenario = item.source_type === 'INTERNAL_SCENARIO';
  scenarioArea.classList.toggle('hidden', !isInternalScenario);
  if (isInternalScenario && Number.isInteger(item.scenario_index)) selectScenario(item.scenario_index);
}

function renderEvaluationMetrics(metrics) {
  const grid = text('div', '', 'module-detail-grid');
  [
    ['通过 / 总数', metrics.passed + '/' + metrics.total],
    ['错误放行', metrics.unsafe_allow],
    ['错误拒绝', metrics.false_refusal],
    ['漏人工确认', metrics.missed_confirmation],
    ['过度武断', metrics.overconfident_decision],
    ['禁止副作用', metrics.forbidden_side_effect],
  ].forEach(([label, value]) => grid.appendChild(text('div', label + '：' + value, 'module-detail-row')));
  return grid;
}

function selectScenario(index) {
  state.scenarioIndex = index;
  state.variantIndex = null;
  state.interactivePresentation = null;
  renderScenario();
}

function renderScenario() {
  const base = scenario();
  const item = view();
  document.getElementById('scenario-title').textContent = `${base.sample_id} · ${base.title}`;
  document.getElementById('objective').textContent = item.learning.objective_zh;
  document.getElementById('story').textContent = item.learning.story_zh;
  document.getElementById('misconception').textContent = item.learning.common_misconception_zh;
  document.getElementById('takeaway').textContent = item.learning.takeaway_zh;
  const protocolBadge = document.getElementById('protocol-badge');
  protocolBadge.textContent = base.protocol.name === 'AP2' ? `AP2 · ${base.protocol.version}` : '协议中立';
  protocolBadge.className = `badge ${base.protocol.name === 'AP2' ? 'protocol-badge' : 'neutral-badge'}`;
  const validationBadge = document.getElementById('validation-badge');
  const variant = activeVariant();
  validationBadge.textContent = variant ? '教学变体 · 后端预计算' : `样品验证 · ${item.status_presentation.label_zh}`;
  validationBadge.title = variant ? '该教学变体由 Python 验证器预先计算。' : item.status_presentation.explanation_zh;
  renderInteractiveLab(); renderExceptionMatrix(); renderKeyStageSummary(); renderDifferences(); renderVariants();
}

function interactiveSpec() {
  return card.interactive?.scenarios?.[scenario().sample_id] || null;
}

function renderInteractiveLab() {
  const panel = document.getElementById('interactive-card');
  const fields = document.getElementById('interactive-fields');
  const runButton = document.getElementById('interactive-run');
  const resetButton = document.getElementById('interactive-reset');
  const status = document.getElementById('interactive-status');
  const result = document.getElementById('interactive-result');
  const spec = interactiveSpec();
  panel.classList.toggle('hidden', !spec);
  if (!spec) return;

  fields.replaceChildren();
  result.replaceChildren();
  result.classList.add('hidden');
  spec.fields.forEach(field => {
    const wrapper = text('div', '', 'interactive-field');
    const label = text('label', field.label_zh);
    wrapper.appendChild(label);
    let input;
    if (field.type === 'choice' || field.type === 'boolean') {
      input = document.createElement('select');
      const choices = field.type === 'boolean' ? ['true', 'false'] : field.choices;
      choices.forEach(choice => {
        const option = document.createElement('option');
        option.value = String(choice);
        if (field.type === 'boolean') {
          option.textContent = String(choice) === 'true' ? '是' : '否';
        } else {
          option.textContent = field.choice_labels_zh?.[choice] || choice;
        }
        input.appendChild(option);
      });
      input.value = String(field.value);
    } else {
      input = document.createElement('input');
      input.type = field.type === 'integer' || field.type.includes('decimal') ? 'number' : 'text';
      if (input.type === 'number') input.step = field.type === 'integer' ? '1' : '0.01';
      input.value = field.value == null ? '' : String(field.value);
    }
    input.dataset.interactiveKey = field.key;
    input.dataset.interactiveType = field.type;
    wrapper.appendChild(input);
    if (field.help_zh) wrapper.appendChild(text('small', field.help_zh));
    fields.appendChild(wrapper);
  });

  const serverMode = location.protocol === 'http:' || location.protocol === 'https:';
  runButton.disabled = !serverMode;
  runButton.onclick = runInteractiveEvaluation;
  resetButton.onclick = resetInteractiveLab;
  status.textContent = serverMode
    ? '本地 Python 后端已连接；点击“执行验证”会真实重新计算。'
    : '当前是静态报告。要交互验证，请用：python run_experiment.py --serve --open';
}

function resetInteractiveLab() {
  state.interactivePresentation = null;
  renderInteractiveLab();
  renderExceptionMatrix();
  renderKeyStageSummary();
  renderDifferences();
}

async function runInteractiveEvaluation() {
  const runButton = document.getElementById('interactive-run');
  const status = document.getElementById('interactive-status');
  const result = document.getElementById('interactive-result');
  const overrides = {};
  document.querySelectorAll('#interactive-fields [data-interactive-key]').forEach(input => {
    let value = input.value;
    if (input.dataset.interactiveType === 'boolean') value = value === 'true';
    overrides[input.dataset.interactiveKey] = value;
  });
  runButton.disabled = true;
  status.textContent = '正在由本地 Python 重新计算…';
  try {
    const response = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sample_id: scenario().sample_id, overrides }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || payload.error || '验证失败');
    state.interactivePresentation = payload.presentation || null;
    renderInteractiveResult(payload);
    renderExceptionMatrix();
    renderKeyStageSummary();
    renderDifferences();
    status.textContent = '已重新计算；结果、生命周期矩阵和关键环节已同步刷新。';
  } catch (error) {
    result.replaceChildren(text('p', `验证失败：${error.message}`, 'warning'));
    result.classList.remove('hidden');
    status.textContent = '本次验证失败。';
  } finally {
    runButton.disabled = false;
  }
}

function renderInteractiveResult(payload) {
  const result = document.getElementById('interactive-result');
  result.replaceChildren();
  const titleRow = text('div', '', 'title-row');
  titleRow.appendChild(text('h4', '重新计算结果'));
  titleRow.appendChild(text('span', payload.decision.label_zh, `badge ${payload.decision.code}`));
  result.appendChild(titleRow);
  result.appendChild(text('p', payload.decision.explanation_zh));
  if (payload.reasons?.length) {
    payload.reasons.slice(0, 3).forEach(reason => {
      result.appendChild(text('p', `原因：${reason.title_zh}。${reason.explanation_zh}`));
    });
  } else {
    result.appendChild(text('p', '当前付款前检查没有发现需要阻止或重新确认的问题。'));
  }
  if (payload.lifecycle) {
    const lc = payload.lifecycle;
    const parts = [
      `支付 ${lc.payment_status}`,
      `履约 ${lc.fulfillment_status}`,
      `补救 ${lc.remediation_status}`,
      `用户任务 ${lc.task_status}`,
    ];
    if (lc.refund_status) parts.push(`退款 ${lc.refund_status}`);
    if (lc.dispute_status) parts.push(`争议 ${lc.dispute_status}`);
    result.appendChild(text('p', '生命周期：' + parts.join(' → ')));
  }
  if (payload.payment_recovery) {
    const recovery = payload.payment_recovery;
    result.appendChild(text(
      'p',
      `支付恢复：${recovery.initial_status} → 查询 ${recovery.observed_status} → ${recovery.recovery_status}；允许进入重试候选：${recovery.retry_allowed ? '是' : '否'}`,
    ));
    recovery.reasons?.slice(0, 2).forEach(reason => {
      result.appendChild(text('p', `恢复原因：${reason.title_zh}。${reason.explanation_zh}`));
    });
  }
  result.appendChild(text('p', '边界：本地离线模拟，不执行真实支付。', 'muted'));
  result.classList.remove('hidden');
}

function renderExceptionMatrix() {
  const lifecycle = displayView().lifecycle_teaching_view;
  const matrix = lifecycle.matrix;
  const position = document.getElementById('matrix-position');
  position.replaceChildren();
  position.appendChild(text('strong', `当前坐标：${matrix.primary_stage} × ${matrix.failure_type_code === 'NONE' ? '正常基线' : matrix.failure_type_code}`));
  position.appendChild(text('span', matrix.failure_type_label, 'badge neutral-badge'));
  position.appendChild(text('span', `检测阶段：${matrix.detection_stage}`, 'badge'));

  const table = document.getElementById('exception-matrix');
  table.replaceChildren();
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  headRow.appendChild(text('th', '异常类型 \\ 生命周期'));
  matrix.stage_catalog.forEach(stage => {
    const th = text('th', `${stage.id}\n${stage.name_zh}`, 'matrix-stage');
    if (stage.id === matrix.detection_stage) th.classList.add('detect');
    headRow.appendChild(th);
  });
  head.appendChild(headRow);
  table.appendChild(head);

  const body = document.createElement('tbody');
  matrix.failure_type_catalog.forEach(failure => {
    const row = document.createElement('tr');
    row.appendChild(text('td', `${failure.code === 'NONE' ? '正常' : failure.code} · ${failure.label_zh}`));
    matrix.stage_catalog.forEach(stage => {
      const cell = text('td', '·', 'matrix-cell');
      if (failure.code === matrix.failure_type_code && stage.id === matrix.primary_stage) {
        cell.textContent = '当前';
        cell.classList.add('primary');
      }
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
  table.appendChild(body);
}

function renderKeyStageSummary() {
  const lifecycle = displayView().lifecycle_teaching_view;
  const matrix = lifecycle.matrix;
  const exception = lifecycle.exception_card;
  const stageById = Object.fromEntries(lifecycle.stages.map(stage => [stage.id, stage]));
  const keyStageIds = [...new Set([matrix.primary_stage, matrix.detection_stage])];
  const keyStages = keyStageIds.map(stageId => stageById[stageId]).filter(Boolean);

  const payment = document.getElementById('payment-mainline-card');
  payment.replaceChildren();
  payment.appendChild(text('h4', '支付主线'));
  payment.appendChild(text('p', '这里说明当前 S 场景在 Payment Domain 里发生了什么，以及问题如何被检测和处理。', 'muted'));
  const statusParts = [];
  if (exception.payment_status) statusParts.push('支付：' + exception.payment_status);
  if (exception.fulfillment_status) statusParts.push('履约：' + exception.fulfillment_status);
  if (exception.refund_status) statusParts.push('退款：' + exception.refund_status);
  if (exception.dispute_status) statusParts.push('争议：' + exception.dispute_status);
  if (exception.remediation_status) statusParts.push('补救：' + exception.remediation_status);
  if (exception.task_status) statusParts.push('用户任务：' + exception.task_status);
  if (exception.initial_payment_status) statusParts.push('初始支付：' + exception.initial_payment_status);
  if (exception.observed_payment_status) statusParts.push('查询结果：' + exception.observed_payment_status);
  if (exception.effective_payment_status) statusParts.push('可信支付：' + exception.effective_payment_status);
  if (exception.recovery_status) statusParts.push('恢复：' + exception.recovery_status);
  if (exception.retry_allowed !== null && exception.retry_allowed !== undefined) statusParts.push('允许重试：' + (exception.retry_allowed ? '是' : '否'));
  const paymentItems = [
    ['问题发生在哪', exception.stage],
    ['在哪检测到', exception.detection_stage],
    ['发生了什么', exception.basis],
    ['谁检测', exception.detector],
    ['谁处理', exception.handler],
    ['怎么恢复', exception.recovery],
    ['最终影响', exception.final_impact],
    ['当前实现边界', exception.handler_status],
  ];
  if (statusParts.length) paymentItems.push(['相关状态', statusParts.join('；')]);
  paymentItems.forEach(([label, value]) => {
    const line = document.createElement('p');
    line.appendChild(text('strong', label + '：'));
    line.appendChild(document.createTextNode(value));
    payment.appendChild(line);
  });

  const card = document.getElementById('trusted-execution-card');
  card.replaceChildren();
  card.appendChild(text('h4', '可信执行侧支'));
  card.appendChild(text('p', '这里补充关键环节旁边的确定性验证能力；它向 Payment Domain 提供验证事实，但不替业务主线做 ALLOW、DENY、确认、退款或恢复决策。', 'muted'));
  keyStages.forEach(stage => {
    const trusted = stage.trusted_execution;
    const item = text('div', '', 'trusted-stage-item');
    const head = text('div', '', 'trusted-stage-head');
    head.appendChild(text('span', stage.id + ' ' + stage.name_zh, 'trusted-stage-title'));
    head.appendChild(text('span', trusted.status_zh, 'trusted-stage-status'));
    item.appendChild(head);
    if (trusted.capabilities.length) {
      item.appendChild(text('div', '能力：' + trusted.capabilities.join(' / '), 'trusted-capabilities-inline'));
    }
    [
      ['能验证什么', trusted.purpose_zh],
      ['当前做到哪里', trusted.current_state_zh],
      ['向支付主线返回什么', trusted.returns_zh],
      ['不负责什么', trusted.does_not_decide_zh],
    ].forEach(([label, value]) => {
      const line = document.createElement('p');
      line.appendChild(text('strong', label + '：'));
      line.appendChild(document.createTextNode(value));
      item.appendChild(line);
    });
    card.appendChild(item);
  });

  const technicalContent = document.getElementById('key-stage-technical-content');
  technicalContent.replaceChildren();
  keyStages.forEach(stage => {
    const block = text('div', '', 'technical-stage-block');
    block.appendChild(text('h4', stage.id + ' ' + stage.name_zh));
    block.appendChild(text('p', stage.neutral_data.notice_zh, 'neutral-notice'));

    block.appendChild(text('h4', '协议中立字段'));
    block.appendChild(text('p', '本环节收到的数据', 'muted'));
    block.appendChild(text('pre', pretty(stage.neutral_data.inputs)));
    block.appendChild(text('p', '本环节输出的数据', 'muted'));
    block.appendChild(text('pre', pretty(stage.neutral_data.outputs)));

    block.appendChild(text('h4', '协议映射'));
    block.appendChild(text('p', stage.protocol_mapping.message_zh, 'muted'));
    if (stage.protocol_mapping.available) {
      block.appendChild(text('p', '来源：' + (stage.protocol_mapping.source || '未提供'), 'muted'));
      const mappingTable = document.createElement('table');
      const mappingHead = document.createElement('thead');
      const mappingHeadRow = document.createElement('tr');
      ['协议原字段', '中立字段', '转换'].forEach(value => mappingHeadRow.appendChild(text('th', value)));
      mappingHead.appendChild(mappingHeadRow);
      mappingTable.appendChild(mappingHead);
      const mappingBody = document.createElement('tbody');
      stage.protocol_mapping.field_mapping.forEach(item => {
        const row = document.createElement('tr');
        [item.from, item.to, item.transform].forEach(value => row.appendChild(text('td', value)));
        mappingBody.appendChild(row);
      });
      mappingTable.appendChild(mappingBody);
      block.appendChild(mappingTable);
    }

    block.appendChild(text('h4', '判断证据 ' + stage.evidence.length + ' 项'));
    block.appendChild(text('pre', pretty(stage.evidence)));
    block.appendChild(text('h4', '原始 JSON'));
    block.appendChild(text('pre', pretty(stage.raw_data)));
    technicalContent.appendChild(block);
  });
}

function renderUnifiedView() {
  const unified = view().unified_view;
  renderFieldSection('unified-mandate', unified.mandate);
  renderFieldSection('unified-agent', unified.agent);
  renderFieldSection('unified-request', unified.request);
  renderOrderSection('unified-order', unified.order);
  renderFieldSection('unified-execution-state', unified.execution_state, unified.execution_state.note_zh);
  renderCheckSection('unified-checks', unified.checks);
  renderResultSection('unified-result', unified.result);
}

function renderFieldSection(elementId, section, note) {
  const box = document.getElementById(elementId);
  box.replaceChildren();
  box.appendChild(text('h4', section.title_zh));
  box.appendChild(renderFieldList(section.fields || []));
  if (note) box.appendChild(text('p', note, 'muted'));
}

function renderFieldList(fields) {
  const listNode = text('div', '', 'field-list');
  fields.forEach(field => {
    const row = text('div', '', `field-row ${field.state || 'normal'}`);
    row.appendChild(text('div', field.label_zh, 'field-label'));
    row.appendChild(text('div', displayValue(field.value), 'field-value'));
    listNode.appendChild(row);
  });
  return listNode;
}

function renderOrderSection(elementId, section) {
  const box = document.getElementById(elementId);
  box.replaceChildren();
  box.appendChild(text('h4', section.title_zh));
  const slots = text('div', '', 'order-slots');
  [section.authorized_order, section.final_order].forEach(slot => {
    const node = text('div', '', `order-slot ${slot.status_code || ''}`);
    node.appendChild(text('h5', slot.label_zh));
    node.appendChild(text('div', `${slot.status_zh} · ${slot.message_zh}`, 'muted'));
    if (slot.value != null) node.appendChild(text('pre', pretty(slot.value)));
    slots.appendChild(node);
  });
  box.appendChild(slots);
  const differences = section.differences || [];
  box.appendChild(text('p', differences.length ? `订单差异 ${differences.length} 项；详细差异见下方差异表。` : '当前没有订单差异。', 'muted'));
}

function renderCheckSection(elementId, section) {
  const box = document.getElementById(elementId);
  box.replaceChildren();
  box.appendChild(text('h4', section.title_zh));
  const listNode = text('div', '', 'check-list');
  section.items.forEach(item => {
    const row = text('div', '', `check-row ${item.status_code}`);
    row.appendChild(text('strong', item.label_zh));
    row.appendChild(text('span', item.status_zh, 'check-status'));
    row.appendChild(text('span', item.explanation_zh, 'muted'));
    listNode.appendChild(row);
  });
  box.appendChild(listNode);
}

function renderResultSection(elementId, section) {
  renderFieldSection(elementId, section);
  const box = document.getElementById(elementId);
  const evidence = section.evidence || [];
  const details = document.createElement('details');
  details.appendChild(text('summary', `字段证据 ${evidence.length} 项`));
  const table = document.createElement('table');
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  ['字段', '观察值', '期望/边界'].forEach(value => headRow.appendChild(text('th', value)));
  head.appendChild(headRow);
  table.appendChild(head);
  const body = document.createElement('tbody');
  evidence.forEach(item => {
    const row = document.createElement('tr');
    [item.field_label_zh, item.observed, item.expected || '—'].forEach(value => row.appendChild(text('td', value)));
    body.appendChild(row);
  });
  table.appendChild(body);
  details.appendChild(table);
  box.appendChild(details);

  const lifecycleEvidence = section.lifecycle_evidence || [];
  if (lifecycleEvidence.length) {
    const lifecycleDetails = document.createElement('details');
    lifecycleDetails.appendChild(text('summary', `支付后生命周期证据 ${lifecycleEvidence.length} 项`));
    const lifecycleTable = document.createElement('table');
    const lifecycleHead = document.createElement('thead');
    const lifecycleHeadRow = document.createElement('tr');
    ['字段', '观察值', '期望/边界'].forEach(value => lifecycleHeadRow.appendChild(text('th', value)));
    lifecycleHead.appendChild(lifecycleHeadRow);
    lifecycleTable.appendChild(lifecycleHead);
    const lifecycleBody = document.createElement('tbody');
    lifecycleEvidence.forEach(item => {
      const row = document.createElement('tr');
      [item.field_label_zh, item.observed, item.expected || '—'].forEach(value => row.appendChild(text('td', value)));
      lifecycleBody.appendChild(row);
    });
    lifecycleTable.appendChild(lifecycleBody);
    lifecycleDetails.appendChild(lifecycleTable);
    box.appendChild(lifecycleDetails);
  }
}

function displayValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(', ') : '[]';
  if (value && typeof value === 'object') return JSON.stringify(value);
  if (value == null || value === '') return '—';
  return String(value);
}

function renderFlow() {
  const flow = document.getElementById('flow');
  flow.replaceChildren();
  view().walkthrough.forEach((item, index) => {
    if (index > 0) flow.appendChild(text('div', '→', 'arrow'));
    const button = document.createElement('button');
    button.className = 'step-button';
    if (index < state.stepIndex) button.classList.add('done');
    if (index === state.stepIndex) button.classList.add('active');
    button.appendChild(text('div', `第 ${index + 1} 步`, 'step-number'));
    button.appendChild(text('div', item.actor, 'step-actor'));
    button.appendChild(text('div', item.action, 'step-action'));
    button.addEventListener('click', () => { stopPlayback(); state.stepIndex = index; renderFlow(); renderStep(); });
    flow.appendChild(button);
  });
  document.getElementById('progress').textContent = `步骤 ${state.stepIndex + 1} / ${view().walkthrough.length}`;
}

function renderStep() {
  const item = currentStep();
  document.getElementById('step-title').textContent = item.actor;
  document.getElementById('step-action').textContent = item.action;
  document.getElementById('step-description').textContent = item.description;
  document.getElementById('step-origin').textContent = item.data_origin_zh;
  document.getElementById('step-operation').textContent = item.operation_type_zh;
  document.getElementById('step-output-summary').textContent = item.output_summary_zh;
  document.getElementById('step-not-do').textContent = item.does_not_do_zh;
  document.getElementById('step-input-zh').textContent = pretty(item.input_presentation_zh);
  document.getElementById('step-output-zh').textContent = pretty(item.output_presentation_zh);
  document.getElementById('step-input').textContent = pretty(item.input);
  document.getElementById('step-output').textContent = pretty(item.output);
  document.getElementById('prev-button').disabled = state.stepIndex === 0;
  document.getElementById('next-button').disabled = state.stepIndex === view().walkthrough.length - 1;
  renderDetailTabs();
}

function renderDetailTabs() {
  const plain = state.detailView === 'plain';
  document.getElementById('plain-panel').classList.toggle('hidden', !plain);
  document.getElementById('technical-panel').classList.toggle('hidden', plain);
  document.querySelectorAll('[data-detail]').forEach(node => node.classList.toggle('active', node.dataset.detail === state.detailView));
}

function renderDifferences() {
  const items = displayView().differences || [];
  document.getElementById('difference-card').classList.toggle('hidden', items.length === 0);
  const body = document.getElementById('difference-body');
  body.replaceChildren();
  items.forEach(item => {
    const row = document.createElement('tr');
    [item.field_label_zh, item.before, item.after, item.explanation_zh].forEach(value => row.appendChild(text('td', value)));
    body.appendChild(row);
  });
}

function renderReasons() {
  const actual = view().actual;
  const grid = document.getElementById('reason-grid');
  grid.replaceChildren();
  if (!actual.reason_presentations.length) {
    const box = text('div', '', 'reason-box');
    box.appendChild(text('h4', '未发现阻止原因'));
    box.appendChild(text('p', actual.decision_presentation.explanation_zh));
    grid.appendChild(box);
  }
  actual.reason_presentations.forEach(reason => {
    const box = text('div', '', 'reason-box');
    box.appendChild(text('h4', reason.title_zh));
    box.appendChild(text('p', reason.explanation_zh));
    box.appendChild(text('p', `技术码：${reason.code}`, 'muted'));
    grid.appendChild(box);
  });
  const body = document.getElementById('evidence');
  body.replaceChildren();
  actual.evidence_presentations.forEach(item => {
    const row = document.createElement('tr');
    [item.field_label_zh, `${item.code}\n${item.field_path}`, item.observed, item.expected || '—'].forEach(value => row.appendChild(text('td', value)));
    body.appendChild(row);
  });
  document.getElementById('next-action').textContent = actual.decision_presentation.next_action_zh;
}

function renderVariants() {
  const variants = scenario().learning_variants || [];
  document.getElementById('variant-card').classList.toggle('hidden', variants.length === 0);
  const box = document.getElementById('variant-buttons');
  box.replaceChildren();
  variants.forEach((item, index) => {
    const button = text('button', item.label_zh, 'variant-button');
    button.classList.toggle('active', state.variantIndex === index);
    button.addEventListener('click', () => {
      state.variantIndex = index;
      state.interactivePresentation = null;
      renderScenario();
    });
    box.appendChild(button);
  });
}

function renderProtocolGuide() {
  const box = document.getElementById('protocol-guide');
  card.protocol_guide.forEach(item => {
    const node = text('div', '', 'protocol-card');
    node.appendChild(text('h4', `${item.name} · ${item.position}`));
    node.appendChild(text('p', item.plain_language));
    box.appendChild(node);
  });
  document.getElementById('why-ap2').textContent = card.why_ap2_first;
}

function renderProtocolPanel() {
  const item = scenario();
  const panel = document.getElementById('mapping-card');
  const isAP2 = item.protocol.name === 'AP2';
  panel.classList.toggle('hidden', !isAP2);
  if (!isAP2) return;
  const value = state.protocolView === 'raw' ? item.protocol.raw_input : item.protocol.neutral_output;
  document.getElementById('protocol-view').textContent = pretty(value);
  const body = document.getElementById('mapping-body');
  body.replaceChildren();
  item.protocol.field_mapping.forEach(mapping => {
    const row = document.createElement('tr');
    [mapping.from, mapping.to, mapping.transform].forEach(value => row.appendChild(text('td', value)));
    body.appendChild(row);
  });
  const gaps = document.getElementById('protocol-gaps');
  gaps.replaceChildren();
  item.protocol.unverified_gaps.forEach(value => gaps.appendChild(text('li', value)));
  document.querySelectorAll('[data-protocol]').forEach(node => node.classList.toggle('active', node.dataset.protocol === state.protocolView));
}

function move(delta) {
  const target = Math.max(0, Math.min(view().walkthrough.length - 1, state.stepIndex + delta));
  if (target === state.stepIndex) return;
  state.stepIndex = target; renderFlow(); renderStep();
}
function stopPlayback() {
  if (state.timer) clearInterval(state.timer);
  state.timer = null;
  document.getElementById('play-button').textContent = '自动播放';
}
function togglePlayback() {
  if (state.timer) { stopPlayback(); return; }
  if (state.stepIndex === view().walkthrough.length - 1) state.stepIndex = 0;
  renderFlow(); renderStep();
  document.getElementById('play-button').textContent = '暂停';
  state.timer = setInterval(() => {
    if (state.stepIndex >= view().walkthrough.length - 1) { stopPlayback(); return; }
    move(1);
  }, 1500);
}

renderSummary();
renderModuleSelectors();
selectModule(0);
</script>
</body>
</html>
"""


def write_html_report(card: dict[str, Any], output_path: Path) -> None:
    """Write one self-contained teaching report with no frontend dependencies."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(card, ensure_ascii=False).replace("</", "<\\/")
    output_path.write_text(
        _HTML_TEMPLATE.replace("__CARD_JSON__", payload),
        encoding="utf-8",
    )
