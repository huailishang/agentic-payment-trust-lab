"""Second-review variants of the same R1 fence-context requirement; offline only."""
import contextlib
import io
import json
from independent_gate_audit import FENCE, VALID, H38AuthorizationGateTests


def main():
    harness = H38AuthorizationGateTests()
    results = {}
    for spaces in (1, 2, 3):
        indent = " " * spaces
        variants = {
            f"outer_example_indent_{spaces}": (
                indent + FENCE + "`text\n" + VALID + indent + FENCE + "`\n"
            ),
            f"second_state_indent_{spaces}": (
                VALID + indent + FENCE + "yaml\nauthorization_api_call: false\n"
                + indent + FENCE + "\n"
            ),
        }
        for name, content in variants.items():
            with contextlib.redirect_stdout(io.StringIO()):
                actual = harness._run(content)
            results[name] = dict(
                passed=(actual["rc"] != 0 and actual["inspect"] == actual["sign"] ==
                        actual["network"] == 0 and not actual["reservation"]), **actual)
    print(json.dumps(dict(cases=results, live_calls=0, real_key_reads=0), indent=2))
    return 0 if all(result["passed"] for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
