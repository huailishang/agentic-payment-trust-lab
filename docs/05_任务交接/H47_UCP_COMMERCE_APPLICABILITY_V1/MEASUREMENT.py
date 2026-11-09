"""Execute only the frozen client steps; the independent harness records facts."""


def run_case(ctx, case):
    for step in case["steps"]:
        ctx.request(**step)
