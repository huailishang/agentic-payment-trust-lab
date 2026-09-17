from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1"
REPORT = TASK / "REPORT.md"

ALLOWED = {
    "NO_PRODUCT_GAP": "F1_OFFICIAL_SDK_EXECUTABLE_SLICE",
    "BOUNDED_ADAPTER_GAP": "BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE",
    "CORE_SEMANTIC_GAP": "CORE_SEMANTIC_REASSESSMENT",
    "SOURCE_ENV_BLOCKED": "SOURCE_ENV_PREPARATION",
}

assert REPORT.is_file(), f"missing REPORT: {REPORT.relative_to(ROOT)}"
text = REPORT.read_text(encoding="utf-8")


def one(label: str) -> str:
    pattern = rf"(?m)^{re.escape(label)}:\s*`?([A-Z0-9_]+)`?\s*$"
    values = re.findall(pattern, text)
    assert len(values) == 1, f"{label} must appear exactly once, got {values}"
    return values[0]


gap = one("Gap classification")
next_direction = one("Next direction")
impact = one("Project impact candidate")
product_changes = one("Product changes")

assert gap in ALLOWED, gap
assert next_direction == ALLOWED[gap], (gap, next_direction, ALLOWED[gap])
assert impact == "NOT_APPLICABLE", impact
assert product_changes == "NONE", product_changes

print(
    f"PASS: REPORT attribution is deterministic: {gap} -> {next_direction}; "
    "project impact NOT_APPLICABLE; product changes NONE"
)
