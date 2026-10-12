from __future__ import annotations

import json
from pathlib import Path

SOURCE_FILES = ["lib.rs", "error.rs", "state.rs", "instruction.rs", "pda.rs", "ed25519.rs", "processor.rs"]


def read_program_source(program_dir: Path) -> str:
    parts = []
    for name in SOURCE_FILES:
        path = program_dir / "src" / name
        if path.exists():
            parts.append(f"// === {name} ===\n{path.read_text()}")
    return "\n\n".join(parts)


TIMING_STEP_FIELDS = ("submittedAt", "confirmedAt", "slot")


def read_trace(trace_path: Path, include_timing: bool = False, baseline: dict | None = None) -> dict:
    """Load a captured trace and strip anything that gives away the ground-truth
    answer — not just the exploit script's own "outcome" verdict, but also the
    narrative step names we wrote for our own debugging convenience (e.g. "strike:
    lock (fake mint)"), which describe intent a real observer would never see. The
    model should only see what's genuinely on-chain: program logs, signatures,
    errors, balances — not our own labels for what we were testing.

    include_timing toggles the temporal channel for the ablation. When on, step
    times are shown relative to the first step (absolute epoch ms is just noise),
    along with D and, if given, the normal-D baseline a monitor would already know.
    When off, every timing field is removed."""
    data = json.loads(trace_path.read_text())
    data.pop("outcome", None)
    steps = data.get("steps", [])
    for i, step in enumerate(steps):
        step["name"] = f"step {i + 1}"

    if not include_timing:
        data.pop("relayDelayMs", None)
        for step in steps:
            for field in TIMING_STEP_FIELDS:
                step.pop(field, None)
        return data

    t0 = min((s["submittedAt"] for s in steps if "submittedAt" in s), default=0)
    for step in steps:
        for field in ("submittedAt", "confirmedAt"):
            if field in step:
                step[field] = step[field] - t0
    if baseline is not None:
        data["normalRelayDelayMs"] = {
            k: round(baseline[k]) for k in ("mean", "std", "p95", "p99", "thresholdMean3Std")
        }
    return data


def load_baseline(root: Path) -> dict:
    return json.loads((root / "traces" / "recon" / "baseline-d.json").read_text())["summary"]
