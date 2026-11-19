"""Authority and raw-output helpers shared only by this frozen task."""
import json
from pathlib import Path
import CHECK

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def active(phase):
    data = CHECK.route()
    CHECK.need(phase in {"executor", "evaluator"}, "unknown phase")
    if phase == "executor":
        CHECK.need((data["state"], data["current_role"]) == ("EXECUTING", "Executor"), "execute under active Executor route")
        tag = "l2_retry_02" if (P / "evidence/FORMAL_l2_retry_02_START.json").exists() else "l2"
    else:
        CHECK.need((data["state"], data["current_role"]) == ("READY_FOR_REVIEW", "Evaluator") and (P / "evidence/ACCEPTED.json").exists(), "accept snapshot before independent L3")
        tag = "l3"
    CHECK.need((P / ("evidence/FORMAL_" + tag + "_START.json")).is_file(), "formal attempt must be registered")
    gate_name = "L3-GATE.json" if phase == "evaluator" else "L2-GATE.json"
    CHECK.need(not (P / "evidence" / tag / gate_name).exists(), "stop after completed formal gate")
    return tag


def json_lines(raw):
    values = []
    for line in raw.decode("utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            values.append(value)
    return values


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
